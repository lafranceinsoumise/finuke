from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView, DetailView

from phones.models import PhoneNumber
from votes.forms import ValidatePhoneForm, ValidateCodeForm, VoteForm
from votes.models import Vote


class HomeView(TemplateView):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        request.session.flush()
        return super().get(request, *args, **kwargs)


class ValidatePhoneView(FormView):
    template_name = 'validate_phone.html'
    form_class = ValidatePhoneForm
    success_url = reverse_lazy('validate_code')

    def form_valid(self, form):
        self.request.session['phone_number'] = str(form.cleaned_data['phone_number'])
        if self.request.session.get('phone_valid'):
            del self.request.session['phone_valid']
        if self.request.session.get('id'):
            del self.request.session['id']
        return super().form_valid(form)


class HasNotVotedMixin(object):
    def test_func(self):
        session_phone = self.request.session.get('phone_number')
        if session_phone is None:
            return False
        phone_number = PhoneNumber.objects.get(phone_number=session_phone)
        if phone_number.validated:
            return False


class ValidateCodeView(UserPassesTestMixin, HasNotVotedMixin, FormView):
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


class VoteView(UserPassesTestMixin, HasNotVotedMixin, FormView):
    login_url = '/'
    template_name = 'vote.html'
    form_class = VoteForm

    def get_success_url(self):
        return reverse('check_own_vote')

    def test_func(self):
        return self.request.session.get('phone_valid') is not None and super().test_func()

    def form_valid(self, form):
        phone_number = PhoneNumber.objects.get(phone_number=self.request.session.get('phone_number'))
        self.vote = Vote(vote=form.cleaned_data['choice'])
        phone_number.validated = True
        with transaction.atomic():
            phone_number.save()
            self.vote.save()
            self.request.session['id'] = self.vote.id
            del self.request.session['phone_valid']
            del self.request.session['phone_number']

            return super().form_valid(form)


class CheckOwnVoteView(UserPassesTestMixin, DetailView):
    login_url = '/'
    template_name = 'check_own_vote.html'
    context_object_name = 'vote'

    def test_func(self):
        return self.request.session.get('id') is not None

    def get_object(self):
        return Vote.objects.get(id=self.request.session.get('id'))


class CheckVoteView(DetailView):
    model = Vote
    context_object_name = 'vote'
    template_name = 'check_vote.html'