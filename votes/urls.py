from django.urls import path
from django.views.generic import TemplateView

from votes.views import ValidatePhoneView, ValidateCodeView, HomeView, VoteView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('validation/telephone', ValidatePhoneView.as_view(), name='validate_phone_number'),
    path('validation/telephone/code', ValidateCodeView.as_view(), name='validate_code'),
    path('vote', VoteView.as_view(), name='vote')
]