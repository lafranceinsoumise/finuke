from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import PermissionDenied
from django.db.models import F, Value, CharField, ExpressionWrapper
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, DetailView, RedirectView
from django.views.decorators.cache import cache_control
from django.contrib import messages

from bureaux import actions
from finuke.exceptions import RateLimitedException
from phones.models import PhoneNumber
from phones.sms import send_new_code, SMSCodeBypassed
from token_bucket import TokenBucket
from .data.geodata import communes, communes_names
from .forms import ValidatePhoneForm, ValidateCodeForm, VoteForm, FindPersonInListForm
from .models import Vote, VoterListItem
from .actions import make_online_vote, AlreadyVotedException, VoteLimitException

PHONE_NUMBER_KEY = 'phone_number'
PHONE_NUMBER_VALID_KEY = 'phone_valid'
VOTER_ID_KEY = 'list_voter'
SESSIONS_KEY = [PHONE_NUMBER_KEY, PHONE_NUMBER_VALID_KEY, VOTER_ID_KEY]

ListSearchTokenBucket = TokenBucket('ListSearch', 100, 1)


def clean_session(request):
    for key in SESSIONS_KEY:
        if key in request.session:
            del request.session[key]


class CleanSessionView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        clean_session(self.request)
        return '/'


@cache_control(max_age=3600, public=True)
def commune_json_search(request, departement):
    return JsonResponse([commune for commune in communes if commune['dep'].zfill(2) == departement.zfill(2)], safe=False)


def person_json_search(request, departement, search):
    if not (request.session.get(PHONE_NUMBER_VALID_KEY) or request.session.get('assistant_code') or request.session.get(
            actions.OPERATOR_LOGIN_SESSION_KEY)):
        raise PermissionDenied("not allowed")

    if not ListSearchTokenBucket.has_tokens(request.session.session_key):
        return HttpResponse(status=429)

    commune = request.GET.get('commune')

    qs = VoterListItem.objects.filter(vote_status=VoterListItem.VOTE_STATUS_NONE, departement=departement)
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
    response = list(map(lambda item: {
        'id': item.id,
        'first_names': item.first_names,
        'last_name': item.last_name,
        'commune_name': communes_names.get(item.commune, 'Commune inconnue')
    }, qs))

    return JsonResponse(response, safe=False)


class AskForPhoneView(FormView):
    template_name = 'votes/ask_for_phone.html'
    form_class = ValidatePhoneForm
    success_url = reverse_lazy('validate_code')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['ip'] = self.request.META['REMOTE_ADDR']

        return kwargs

    def form_valid(self, form):
        if self.request.session.get(PHONE_NUMBER_VALID_KEY) and \
                self.request.session.get(PHONE_NUMBER_KEY) == form.cleaned_data['phone_number']:
            return HttpResponseRedirect(reverse('validate_list'))

        clean_session(self.request)

        try:
            code = form.send_code()
        except SMSCodeBypassed:
            # bypass code validation for phone numbers we already know about
            self.request.session[PHONE_NUMBER_KEY] = str(form.cleaned_data['phone_number'])
            self.request.session[PHONE_NUMBER_VALID_KEY] = True
            return HttpResponseRedirect(reverse('validate_list'))

        if code is None:
            return super().form_invalid(form)

        messages.add_message(self.request, messages.DEBUG, f'Le code envoyé est {code}')
        self.request.session[PHONE_NUMBER_KEY] = str(form.cleaned_data['phone_number'])
        return super().form_valid(form)


class ResendSms(RedirectView):
    url = reverse_lazy('validate_code')

    def get(self, request, *args, **kwargs):
        if PHONE_NUMBER_KEY not in request.session:
            return HttpResponseRedirect(reverse('validate_phone_number'))
        try:
            code = send_new_code(
                PhoneNumber.objects.get(phone_number=request.session[PHONE_NUMBER_KEY]),
                request.META['REMOTE_ADDR']
            )
            messages.add_message(request, messages.INFO, 'Le SMS a bien été renvoyé')
            messages.add_message(request, messages.DEBUG, f'Le code envoyé est {code}')
        except RateLimitedException:
            messages.add_message(request, messages.ERROR, 'Vous avez demandé trop de SMS. Merci de patienter un peu.')

        return super().get(request, *args, **kwargs)


class HasNotVotedMixin(UserPassesTestMixin):
    login_url = reverse_lazy('validate_phone_number')

    def test_func(self):
        session_phone = self.request.session.get(PHONE_NUMBER_KEY)
        if session_phone is None:
            return False
        phone_number = PhoneNumber.objects.get(phone_number=session_phone)
        if phone_number.validated:
            return False

        return True


class ValidateCodeView(HasNotVotedMixin, FormView):
    login_url = '/'
    template_name = 'votes/validate_code.html'
    form_class = ValidateCodeForm
    success_url = reverse_lazy('validate_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['phone_number'] = self.request.session[PHONE_NUMBER_KEY]

        return kwargs

    def form_valid(self, form):
        self.request.session[PHONE_NUMBER_VALID_KEY] = True
        return super().form_valid(form)


class FindPersonInListView(HasNotVotedMixin, FormView):
    template_name = 'votes/find_person.html'
    form_class = FindPersonInListForm
    success_url = reverse_lazy('vote')

    def form_invalid(self, form):
        messages.add_message(
            self.request, messages.ERROR,
            "Vous n'avez pas sélectionné de nom dans la liste."
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        self.request.session[VOTER_ID_KEY] = form.cleaned_data['person'].id
        return super().form_valid(form)


class MakeVoteView(HasNotVotedMixin, FormView):
    login_url = '/'
    template_name = 'votes/vote.html'
    form_class = VoteForm

    def get_success_url(self):
        return '/merci?id=' + self.vote_id

    def test_func(self):
        return self.request.session.get(PHONE_NUMBER_VALID_KEY) is not None and super().test_func()

    def get_context_data(self, **kwargs):
        list_voter_id = self.request.session.get(VOTER_ID_KEY, None)
        if list_voter_id:
            try:
                kwargs['person'] = VoterListItem.objects.get(pk=list_voter_id)
            except VoterListItem.DoesNotExist:
                del self.request.session[VOTER_ID_KEY]

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        try:
            self.vote_id = make_online_vote(
                ip=self.request.META['REMOTE_ADDR'],
                phone_number=self.request.session['phone_number'],
                voter_list_id=self.request.session.get(VOTER_ID_KEY, None),
                vote=form.cleaned_data['choice']
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
