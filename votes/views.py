from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, Value, CharField, ExpressionWrapper
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, DetailView, RedirectView

from phones.models import PhoneNumber
from .data.geodata import communes, communes_names
from .forms import ValidatePhoneForm, ValidateCodeForm, VoteForm, FindPersonInListForm
from .models import Vote, VoterListItem
from .actions import make_online_vote, AlreadyVotedException


class CleanSessionView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        self.request.session.flush()
        return '/'


def commune_json_search(request, departement):
    return JsonResponse([commune for commune in communes if commune['dep'] == departement], safe=False)


def person_json_search(request, departement, search):
    commune = request.GET.get('commune')

    qs = VoterListItem.objects.filter(departement=departement)
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
        'commune_name': communes_names[item.commune]
    }, qs))

    return JsonResponse(response, safe=False)


class FindPersonInListView(FormView):
    template_name = 'find_person.html'
    form_class = FindPersonInListForm
    success_url = reverse_lazy('validate_phone_number')

    def form_invalid(self, form):
        print(form)

    def form_valid(self, form):
        self.request.session['list_voter'] = form.cleaned_data['person'].id
        return super().form_valid(form)


class AskForPhoneView(FormView):
    template_name = 'ask_for_phone.html'
    form_class = ValidatePhoneForm
    success_url = reverse_lazy('validate_code')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        list_voter_id = self.request.session.get('list_voter', None)
        if list_voter_id:
            data['person'] = VoterListItem.objects.filter(vote_status=VoterListItem.VOTE_STATUS_NONE).get(pk=list_voter_id)

        return data

    def form_valid(self, form):
        self.request.session['phone_number'] = str(form.cleaned_data['phone_number'])
        if self.request.session.get('phone_valid'):
            del self.request.session['phone_valid']
        if self.request.session.get('id'):
            del self.request.session['id']
        return super().form_valid(form)


class HasNotVotedMixin(UserPassesTestMixin):
    def test_func(self):
        session_phone = self.request.session.get('phone_number')
        print(session_phone)
        if session_phone is None:
            return False
        phone_number = PhoneNumber.objects.get(phone_number=session_phone)
        if phone_number.validated:
            return False

        return True


class ValidateCodeView(HasNotVotedMixin, FormView):
    login_url = '/'
    template_name = 'validate_code.html'
    form_class = ValidateCodeForm
    success_url = reverse_lazy('vote')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['phone_number'] = self.request.session['phone_number']

        return kwargs

    def form_valid(self, form):
        self.request.session['phone_valid'] = True
        return super().form_valid(form)


class MakeVoteView(HasNotVotedMixin, FormView):
    login_url = '/'
    template_name = 'vote.html'
    form_class = VoteForm

    def get_success_url(self):
        return reverse('check_own_vote')

    def test_func(self):
        return self.request.session.get('phone_valid') is not None and super().test_func()

    def form_valid(self, form):
        try:
            make_online_vote(
                phone_number=self.request.session['phone_number'],
                voter_list_id=self.request.session['list_voter'],
                vote=form.cleaned_date['choice']
            )
        except AlreadyVotedException:
            return JsonResponse({'error': 'already voted'})


class CheckOwnVoteView(UserPassesTestMixin, DetailView):
    login_url = '/'
    template_name = 'check_own_vote.html'
    context_object_name = 'vote'
    model = Vote

    def test_func(self):
        return self.request.session.get('id') is not None

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        return queryset.get(id=self.request.session.get('id'))


class CheckVoteView(DetailView):
    model = Vote
    context_object_name = 'vote'
    template_name = 'check_vote.html'
