from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic import RedirectView, ListView, DetailView, FormView, UpdateView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from finuke.exceptions import RateLimitedException
from bureaux.forms import OpenBureauForm, BureauResultsForm, AssistantCodeForm, SelectHomonymForm
from bureaux.models import LoginLink, Bureau
from . import actions

from votes.actions import AlreadyVotedException
from votes.forms import FindPersonInListForm


class OperatorViewMixin(UserPassesTestMixin):
    login_url = '/'

    def test_func(self):
        login_uuid = self.request.session.get(actions.OPERATOR_LOGIN_SESSION_KEY)

        if login_uuid is None:
            return False

        try:
            self.request.operator = LoginLink.objects.select_related('operator').get(uuid=login_uuid, valid=True).operator
            return True
        except LoginLink.DoesNotExist:
            return False


class LoginView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        login_link = actions.authenticate_operator(kwargs['uuid'])

        if login_link is not None:
            actions.login_operator(self.request, login_link)
            return reverse('list_bureaux')
        else:
            return reverse('login_error')


class ListBureauxView(OperatorViewMixin, ListView):
    model = Bureau
    context_object_name = 'bureaux'
    template_name = 'bureaux/list.html'

    def get_queryset(self):
        return Bureau.objects.filter(operator=self.request.operator)


class OpenBureauView(OperatorViewMixin, FormView):
    template_name = 'bureaux/create.html'
    form_class = OpenBureauForm

    def get_success_url(self):
        return reverse('detail_bureau', args=[self.bureau.id])

    def form_valid(self, form):
        try:
            self.bureau = actions.open_bureau(self.request, form.cleaned_data['place'])
            messages.add_message(self.request, messages.SUCCESS, "Le bureau a bien été créé.")
        except RateLimitedException:
            messages.add_message(self.request, messages.ERROR, "Vous avez ouvert trop de bureaux aujourd'hui, vous êtes bloqué par mesure de sécurité.")
            return super().form_invalid(form)
        return super().form_valid(form)


class DetailBureauView(OperatorViewMixin, DetailView):
    template_name = 'bureaux/detail.html'
    model = Bureau
    context_object_name = 'bureau'


class CloseBureauView(OperatorViewMixin, SingleObjectMixin, TemplateView):
    template_name = 'bureaux/close.html'
    queryset = Bureau.objects.open_only()
    context_object_name = 'bureau'
    success_url = reverse_lazy('list_bureaux')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        actions.close_bureau(request, self.object)
        messages.add_message(request, messages.SUCCESS, 'Le bureau de vote a été correctement fermé.')
        return HttpResponseRedirect(self.success_url)


class BureauResultsView(OperatorViewMixin, UpdateView):
    model = Bureau
    form_class = BureauResultsForm
    template_name = 'bureaux/results.html'

    def get_success_url(self):
        actions.bureaux_results_submitted.inc()
        return reverse('detail_bureau', args=[self.object.id])


class AssistantLoginView(FormView):
    form_class = AssistantCodeForm
    template_name = 'bureaux/assistant_login.html'

    def get(self, *args, **kwargs):
        self.request.session[actions.ASSISTANT_LOGIN_SESSION_KEY] = None
        return super().get(*args, **kwargs)

    def get_success_url(self):
        return reverse('vote_bureau', args=[self.bureau.id])

    def form_valid(self, form):
        code = form.cleaned_data['code']

        try:
            self.bureau = actions.authenticate_assistant(self.request, code)
        except RateLimitedException:
            messages.add_message(self.request, messages.ERROR,
                                 "Trop d'assesseur⋅e⋅s connectés sur ce bureau. Si vous avez plusieurs urnes, "
                                 "demandez au président ou à la présidente d'ouvrir un nouveau bureau.")
            return self.form_invalid(form)

        if self.bureau is None:
            form.add_error('code', 'Ce code est invalide.')
            return self.form_invalid(form)

        actions.login_assistant(self.request, self.bureau)
        return super().form_valid(form)


class MakePersonVoteMixin(SingleObjectMixin, OperatorViewMixin):
    queryset = Bureau.objects.open_only()
    login_url = reverse_lazy('assistant_login')

    def test_func(self):
        self.object = self.get_object()

        is_operator = super().test_func()
        if is_operator and self.object in self.request.operator.bureaux.all():
            return True
        if self.request.session.get(actions.ASSISTANT_LOGIN_SESSION_KEY) == self.object.assistant_code:
            return True
        return False

    def show_voting_message(self, person):
        messages.add_message(
            self.request, messages.SUCCESS,
            f'{person.get_full_name()} a bien été marqué⋅e comme votant⋅e. Vous pouvez lui donner une enveloppe et bulletin.')


class FindVoterInListView(MakePersonVoteMixin, FormView):
    template_name = 'bureaux/vote.html'
    form_class = FindPersonInListForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['birthdate_check'] = False

        return kwargs

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['display_no_list_info'] = not settings.ELECTRONIC_VOTE_REQUIRE_LIST

        return kwargs

    def get_success_url(self):
        return reverse('vote_bureau', args=[self.object.id])

    def form_invalid(self, form):
        print(form.errors)
        messages.add_message(
            self.request, messages.ERROR,
            "Vous n'avez pas sélectionné de personne dans la liste."
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        persons = form.cleaned_data['persons']

        if settings.ELECTRONIC_VOTE_REQUIRE_BIRTHDATE and len(persons) > 1:
            self.request.session[actions.HOMONYMS_CHOICES_KEY] = [p.pk for p in persons]
            return HttpResponseRedirect(reverse('select_homonym', args=[self.object.pk]))

        try:
            actions.mark_as_voted(self.request, persons[0].id, self.object)
        except AlreadyVotedException:
            return JsonResponse({'error': 'already voted'})

        self.show_voting_message(persons[0])

        return super().form_valid(form)


class SelectHomonymView(MakePersonVoteMixin, FormView):
    template_name = 'bureaux/select_homonym.html'
    form_class = SelectHomonymForm

    def get_success_url(self):
        return reverse('vote_bureau', args=[self.object.pk])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['ids'] = self.request.session.get(actions.HOMONYMS_CHOICES_KEY, [])

        return kwargs

    def form_valid(self, form):
        person = form.cleaned_data['person']

        try:
            actions.mark_as_voted(self.request, person.id, self.object)
        except AlreadyVotedException:
            return JsonResponse({'error': 'already voted'})

        self.show_voting_message(person)

        return super().form_valid(form)
