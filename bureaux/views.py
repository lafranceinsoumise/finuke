from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic import RedirectView, ListView, DetailView, FormView, UpdateView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from bureaux.forms import OpenBureauForm, BureauResultsForm, AssistantCodeForm
from bureaux.models import LoginLink, Bureau
from . import actions

from votes.actions import AlreadyVotedException
from votes.forms import FindPersonInListForm


def request_to_json(request):
    return {
        'ip': request.META['REMOTE_ADDR'],
        'operator': request.operator.id if getattr(request, 'operator', False) else None,
        'link_uuid': request.session.get('link_uuid', None),
    }


class OperatorViewMixin(UserPassesTestMixin):
    login_url = '/'

    def test_func(self):
        if self.request.session.get('login_uuid') is None:
            return False

        try:
            self.request.operator = LoginLink.objects.get(uuid=self.request.session['login_uuid'], valid=True).operator
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
        self.bureau = actions.open_bureau(self.request, form.cleaned_data['place'])
        messages.add_message(self.request, messages.SUCCESS, "Le bureau a bien été créé.")
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
        return reverse('detail_bureau', args=[self.object.id])


class AssistantLoginView(FormView):
    form_class = AssistantCodeForm
    template_name = 'bureaux/assistant_login.html'

    def get(self, *args, **kwargs):
        self.request.session['assistant_code'] = None
        return super().get(*args, **kwargs)

    def get_success_url(self):
        return reverse('vote_bureau', args=[self.bureau.id])

    def form_valid(self, form):
        self.bureau = form.bureau
        actions.login_assistant(self.request, self.bureau)
        return super().form_valid(form)


class FindVoterInListView(SingleObjectMixin, OperatorViewMixin, FormView):
    queryset = Bureau.objects.open_only()
    login_url = reverse_lazy('assistant_login')
    template_name = 'bureaux/vote.html'
    form_class = FindPersonInListForm

    def get_success_url(self):
        return reverse('vote_bureau', args=[self.object.id])

    def test_func(self):
        self.object = self.get_object()

        is_operator = super().test_func()
        if is_operator and self.object in self.request.operator.bureaux.all():
            return True
        if self.request.session.get('assistant_code') == self.object.assistant_code:
            return True
        return False

    def form_valid(self, form):
        person = form.cleaned_data['person']
        try:
            actions.mark_as_voted(self.request, person.id, self.object)
        except AlreadyVotedException:
            return JsonResponse({'error': 'already voted'})

        messages.add_message(
            self.request, messages.SUCCESS,
            f'{person.get_full_name()} a bien été marqué⋅e comme votant⋅e. Vous pouvez lui donner enveloppe et bulletin'
            f' vert.')

        return super().form_valid(form)
