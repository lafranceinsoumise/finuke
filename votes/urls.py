from django.urls import path

from votes.views import ValidatePhoneView, ValidateCodeView, HomeView, VoteView, CheckVoteView, CheckOwnVoteView, \
    commune_json_search, person_json_search, FindPersonInListView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('json/communes/<departement>', commune_json_search, name='commune_json_search'),
    path('json/listes/<departement>/<search>', person_json_search, name='person_json_search'),
    path('validation/listes', FindPersonInListView.as_view(), name='validate_list'),
    path('validation/telephone', ValidatePhoneView.as_view(), name='validate_phone_number'),
    path('validation/telephone/code', ValidateCodeView.as_view(), name='validate_code'),
    path('vote', VoteView.as_view(), name='vote'),
    path('vote/confirmation', CheckOwnVoteView.as_view(), name='check_own_vote'),
    path('vote/<pk>', CheckVoteView.as_view(), name='check_vote')
]