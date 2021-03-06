from django.conf import settings
from django.urls import path

from votes.views import (
    AskForPhoneView, ValidateCodeView, MakeVoteView, CheckVoteView, commune_json_search, person_json_search,
    FindPersonInListView, CleanSessionView, ResendSms, FELogin, UnlockingRequestView, participation_view
)

urlpatterns = [
    path('clean_session', CleanSessionView.as_view(), name='clean_session'),
    path('json/communes/<departement>', commune_json_search, name='commune_json_search'),
    path('json/listes/<departement>', person_json_search, name='person_json_search'),
]

if settings.ENABLE_ELECTRONIC_VOTE:
    urlpatterns.extend([
        path('validation/listes', FindPersonInListView.as_view(), name='validate_list'),
        path('vote', MakeVoteView.as_view(), name='vote'),
        path('vote/<pk>', CheckVoteView.as_view(), name='check_vote'),
        path('fe/<token>', FELogin.as_view(), name='fe_login'),
        path('demande-deblocage', UnlockingRequestView.as_view(), name='unlocking_request'),
    ])

    if settings.ELECTRONIC_VOTE_REQUIRE_SMS:
        urlpatterns.extend([
            path('validation', AskForPhoneView.as_view(), name='validate_phone_number'),
            path('validation/renvoyer', ResendSms.as_view(), name='resend_sms'),
            path('validation/code', ValidateCodeView.as_view(), name='validate_code'),
        ])

if settings.ENABLE_PARTICIPATION:
    urlpatterns.append(
        path('participation', participation_view, name='view_participation')
    )
