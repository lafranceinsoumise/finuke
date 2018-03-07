from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import RedirectView, ListView, DetailView, FormView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from bureaux.forms import OpenBureauForm, CloseBureauForm, BureauResultsForm, AssistantCodeForm
from bureaux.models import LoginLink, Bureau, Operation
from votes.actions import make_physical_vote, AlreadyVotedException
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
        try:
            LoginLink.objects.get(uuid=kwargs['uuid'], valid=True)
        except LoginLink.DoesNotExist:
            return reverse('login_error')

        self.request.session['login_uuid'] = kwargs['uuid']

        return reverse('list_bureaux')


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
        with transaction.atomic():
            self.bureau = form.save(commit=False)
            self.bureau.operator = self.request.operator
            self.bureau.save()
            Operation.objects.create(
                type=Operation.START_BUREAU,
                details={**request_to_json(self.request), 'bureau': self.bureau.id}
            )
        return super().form_valid(form)


class DetailBureauView(OperatorViewMixin, DetailView):
    template_name = 'bureaux/detail.html'
    model = Bureau
    context_object_name = 'bureau'


class CloseBureauView(OperatorViewMixin, SingleObjectMixin, FormView):
    template_name = 'bureaux/close.html'
    model = Bureau
    context_object_name = 'bureau'
    form_class = CloseBureauForm
    success_url = reverse_lazy('list_bureaux')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'object'):
            kwargs.update({'instance': self.object})
        return kwargs

    def form_valid(self, form):
        form.instance.end_time = timezone.now()
        form.save()

        return super().form_valid(form)


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
        self.request.session['assistant_code'] = form.cleaned_data['code']
        self.bureau = Bureau.objects.get(assistant_code=form.cleaned_data['code'])
        return super().form_valid(form)


class FindVoterInListView(SingleObjectMixin, OperatorViewMixin, FormView):
    model = Bureau
    login_url = reverse_lazy('assistant_login')
    template_name = 'bureaux/vote.html'

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

    form_class = FindPersonInListForm

    # TODO: ajouter une page de confirmation ou un flash message ?
    def form_valid(self, form):
        try:
            make_physical_vote(form.cleaned_data['person'].id, self.object)
        except AlreadyVotedException:
            return JsonResponse({'error': 'already voted'})

        return super().form_valid(form)