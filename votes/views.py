from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from votes.forms import ValidatePhoneForm, ValidateCodeForm, VoteForm


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
        return super().form_valid(form)


class ValidateCodeView(UserPassesTestMixin, FormView):
    login_url = '/'
    template_name = 'validate_code.html'
    form_class = ValidateCodeForm
    success_url = reverse_lazy('vote')

    def test_func(self):
        if self.request.session.get('phone_valid'):
            del self.request.session['phone_valid']
        return self.request.session.get('phone_number') is not None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['phone_number'] = self.request.session['phone_number']

        return kwargs

    def form_valid(self, form):
        self.request.session['phone_valid'] = True
        return super().form_valid(form)


class VoteView(UserPassesTestMixin, FormView):
    login_url = '/'
    template_name = 'vote.html'
    form_class = VoteForm
    success_url = '/'

    def test_func(self):
        return self.request.session.get('phone_valid') is not None