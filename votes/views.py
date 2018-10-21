from collections import namedtuple
from itertools import groupby
from operator import itemgetter

from elasticsearch import Elasticsearch

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import PermissionDenied
from django.db.models import F, Value, CharField, ExpressionWrapper
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.views.generic import FormView, DetailView, RedirectView, CreateView
from django.views.decorators.cache import cache_control
from django.contrib import messages

from bureaux import actions
from finuke.exceptions import RateLimitedException
from phones.sms import send_new_code, SMSCodeBypassed
from token_bucket import TokenBucket
from .data.geodata import communes, communes_names
from .forms import ValidatePhoneForm, ValidateCodeForm, VoteForm, FindPersonInListForm, PhoneUnlockingRequestForm
from .models import Vote, VoterListItem, FEVoterListItem, UnlockingRequest
from .actions import make_online_validation, AlreadyVotedException, VoteLimitException, VoterState, \
    participation_counter
from .tokens import mail_token_generator

ListSearchTokenBucket = TokenBucket('ListSearch', 100, 1)


class CleanSessionView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        VoterState(self.request).clean_session()
        return reverse('validate_list')


@cache_control(max_age=3600, public=True)
def commune_json_search(request, departement):
    return JsonResponse([commune for commune in communes if commune['dep'].zfill(2) == departement.zfill(2)],
                        safe=False)


HomonymyKey = namedtuple('HomonymyKey', ['first_names', 'last_name', 'commune'])


def homonymy_key(item):
    return HomonymyKey(item['first_names'].upper(), item['last_name'].upper(), item['commune'])


def group_by_homonyms(items):
    sorted_voters = sorted(items, key=homonymy_key)
    for k, voters in groupby(sorted_voters, key=homonymy_key):
        voters = list(voters)
        yield {
            'id': [item['id'] for item in voters],
            'first_names': k.first_names,
            'last_name': k.last_name,
            'commune_name': communes_names.get(k.commune, 'Commune inconnue'),
            'similarity': max(item['similarity'] for item in voters)
        }


def sql_search(departement, commune, search):
    qs = VoterListItem.objects.filter(departement=departement.zfill(2))
    if settings.ENABLE_HIDING_VOTERS:
        qs = qs.filter(vote_status=VoterListItem.VOTE_STATUS_NONE)
    if commune:
        qs = qs.filter(commune=commune)

    class CF(F):
        ADD = '||'

    class CV(Value):
        ADD = '||'

    class CC(ExpressionWrapper):
        ADD = '||'

        def __init__(self, expression):
            super().__init__(expression, output_field=CharField())

    coumpound_field = CC(CC(CC(CF('first_names') + CV(' ')) + CF('use_last_name')) + CV(' ')) + CF('last_name')
    qs = qs.annotate(
        similarity=TrigramSimilarity(coumpound_field, str(search)),
        full_name=coumpound_field
    ).filter(full_name__trigram_similar=str(search)).order_by('-similarity')[:20]

    return [
        {'id': v.id, 'first_names': v.first_names, 'last_name': v.last_name, 'commune': v.commune,
         'similarity': v.similarity} for v in qs
    ]


def elasticsearch_search(departement: str, commune: str, search: str):
    es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])

    fields = ["first_names{suffix}", "last_name{suffix}", "use_last_name{suffix}^0.7"]
    suffixes = {'': 2, '.ngrams': 1, '.phonetic': 1}

    query = {
        "query": {
            "bool": {
                "should": [{
                    "multi_match": {
                        "query": search,
                        "type": "cross_fields",
                        "fields": [f.format(suffix=suffix) for f in fields],
                        "boost": boost
                    }
                } for suffix, boost in suffixes.items()]
            }
        }
    }

    if commune:
        query['query']['bool']['filter'] = {'term': {'commune': commune}}
    elif departement:
        query['query']['bool']['filter'] = {'term': {'departement': departement.zfill(2)}}

    res = es.search(index='voters', doc_type='voter', body=query)
    import json

    return [{'id': v['_id'], **v['_source'], 'similarity': v['_score']} for v in res['hits'].get('hits', [])]


def person_json_search(request, departement):
    voter_state = VoterState(request)
    if not (voter_state.can_see_list or request.session.get(
            actions.ASSISTANT_LOGIN_SESSION_KEY) or request.session.get(
        actions.OPERATOR_LOGIN_SESSION_KEY)):
        raise PermissionDenied("not allowed")

    if not ListSearchTokenBucket.has_tokens(request.session.session_key):
        return HttpResponse(status=429)

    query = request.GET.get('query')
    commune = request.GET.get('commune')

    if not query:
        return HttpResponse(status=400)

    if settings.ELASTICSEARCH_ENABLED:
        results = elasticsearch_search(departement, commune, query)
    else:
        results = sql_search(departement, commune, query)

    response = sorted(group_by_homonyms(results), reverse=True, key=itemgetter('similarity'))

    return JsonResponse(response, safe=False)


class VoterStateMixin():
    def dispatch(self, request, *args, **kwargs):
        self.voter_state = VoterState(request)

        if "multiple" in request.GET:
            request.session['multiple'] = request.GET['multiple'] == True

        return super().dispatch(request, *args, **kwargs)


class AskForPhoneView(VoterStateMixin, FormView):
    template_name = 'votes/ask_for_phone.html'
    form_class = ValidatePhoneForm
    success_url = reverse_lazy('validate_code')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['ip'] = self.request.META['REMOTE_ADDR']

        return kwargs

    def form_valid(self, form):
        if self.voter_state.is_phone_valid and self.voter_state.phone_number and \
                self.voter_state.phone_number.phone_number == form.cleaned_data['phone_number']:
            return HttpResponseRedirect(reverse('validate_list'))

        self.voter_state.clean_session()

        try:
            code = form.send_code()
        except SMSCodeBypassed:
            # bypass code validation for phone numbers we already know about
            self.voter_state.phone_number = form.phone_number
            self.voter_state.is_phone_valid = True
            return HttpResponseRedirect(reverse('validate_list'))

        if code is None:
            return super().form_invalid(form)

        messages.add_message(self.request, messages.DEBUG, f'Le code envoyé est {code}')
        self.voter_state.phone_number = form.phone_number
        return super().form_valid(form)


class ResendSms(VoterStateMixin, RedirectView):
    url = reverse_lazy('validate_code')

    def get(self, request, *args, **kwargs):
        if self.voter_state.phone_number is None:
            return HttpResponseRedirect(reverse('validate_phone_number'))
        try:
            code = send_new_code(
                self.voter_state.phone_number,
                request.META['REMOTE_ADDR']
            )
            messages.add_message(request, messages.INFO, 'Le SMS a bien été renvoyé')
            messages.add_message(request, messages.DEBUG, f'Le code envoyé est {code}')
        except RateLimitedException:
            messages.add_message(request, messages.ERROR, 'Vous avez demandé trop de SMS. Merci de patienter un peu.')

        return super().get(request, *args, **kwargs)


class ValidateCodeView(VoterStateMixin, UserPassesTestMixin, FormView):
    login_url = reverse_lazy('validate_phone_number')
    template_name = 'votes/validate_code.html'
    form_class = ValidateCodeForm
    success_url = reverse_lazy('validate_list')

    def test_func(self):
        if self.voter_state.phone_number is None:
            return False
        if self.voter_state.phone_number.validated:
            return False

        return True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['phone_number'] = self.voter_state.phone_number

        return kwargs

    def form_valid(self, form):
        self.voter_state.is_phone_valid = True
        return super().form_valid(form)


class FindPersonInListView(VoterStateMixin, UserPassesTestMixin, FormView):
    login_url = reverse_lazy('validate_phone_number')
    template_name = 'votes/find_person.html'
    form_class = FindPersonInListForm
    success_url = reverse_lazy('vote')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['birthdate_check'] = settings.ELECTRONIC_VOTE_REQUIRE_BIRTHDATE

        return kwargs

    def test_func(self):
        return self.voter_state.can_see_list

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.add_message(
                self.request, messages.ERROR,
                error
            )
        return super().form_invalid(form)

    def form_valid(self, form):
        self.voter_state.voter = form.cleaned_data['person']
        return super().form_valid(form)


class MakeVoteView(VoterStateMixin, UserPassesTestMixin, FormView):
    login_url = reverse_lazy('validate_list')
    template_name = 'votes/vote.html'
    form_class = VoteForm
    success_url = settings.THANK_YOU_URL

    def get_success_url(self):
        if self.request.session.get('multiple', False):
            messages.add_message(
                self.request,
                messages.SUCCESS,
                'La participation de cette personne a bien été prise en compte.'
            )
            return reverse('validate_list')
        return super().get_success_url()

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if isinstance(response, HttpResponseRedirect) and hasattr(self, 'vote_id'):
            response.set_cookie('vote_id', self.vote_id, max_age=600)

        return response

    def test_func(self):
        voter_state = self.voter_state

        return voter_state.can_vote

    def get_context_data(self, **kwargs):
        kwargs['person'] = self.voter_state.voter
        kwargs['question'] = settings.VOTE_QUESTION
        kwargs['text'] = mark_safe(settings.VOTE_TEXT)

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        try:
            self.vote_id, self.contact_information_id = make_online_validation(
                ip=self.request.META['REMOTE_ADDR'],
                phone_number=self.voter_state.phone_number,
                voter=self.voter_state.voter,
                is_foreign_french=self.voter_state.is_foreign_french,
                vote=form.cleaned_data.get('choice'),
                contact_information=form.cleaned_data.get('contact_information')
            )
        except AlreadyVotedException:
            return JsonResponse({'error': 'already voted'})
        except VoteLimitException:
            messages.add_message(
                self.request,
                messages.ERROR,
                "Trop de votes sur cette connexion, merci de réessayer plus tard."
            )
            return super().form_invalid(form)

        return super().form_valid(form)


class CheckVoteView(DetailView):
    model = Vote
    context_object_name = 'vote'
    template_name = 'votes/check_vote.html'


class FELogin(RedirectView):
    url = reverse_lazy('vote')

    def get(self, request, *args, token, **kwargs):
        email = mail_token_generator.check_token(token)

        if email is None:
            return TemplateResponse(request, 'votes/fe_login_error.html')

        try:
            voter = FEVoterListItem.objects.get(email=email, has_voted=False)
        except FEVoterListItem.DoesNotExist:
            return TemplateResponse(request, 'votes/fe_login_error.html')

        voter_state = VoterState(request)
        voter_state.voter = voter
        voter_state.is_foreign = True

        return super().get(request, *args, **kwargs)


class UnlockingRequestView(CreateView):
    model = UnlockingRequest
    form_class = PhoneUnlockingRequestForm

    success_url = reverse_lazy('validate_phone_number')

    template_name = 'votes/unlocking_request.html'

    def form_valid(self, form):
        res = super().form_valid(form)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Votre demande a été prise en compte. Elle sera vérifiée et vous recevez un email de confirmation."
        )

        return res


def participation_view(request):
    return JsonResponse({"participation": participation_counter.get()})
