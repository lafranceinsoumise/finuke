from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView

from bureaux.views import LoginView, ListBureauxView, DetailBureauView, CloseBureauView, BureauResultsView, \
    OpenBureauView, AssistantLoginView, FindVoterInListView, SelectHomonymView

urlpatterns = [
    path('mode-emploi', TemplateView.as_view(template_name='bureaux/manual.html', extra_context={
        'app_domain': settings.DOMAIN_NAME,
        'votation_name': settings.VOTATION_NAME
    }), name='manual'),
    path('login/error', TemplateView.as_view(template_name='bureaux/login_error.html'), name='login_error'),
    path('login/<uuid>', LoginView.as_view(), name='login'),
    path('', ListBureauxView.as_view(), name='list_bureaux'),
    path('ouvrir', OpenBureauView.as_view(), name='open_bureau'),
    path('assister', AssistantLoginView.as_view(), name='assistant_login'),
    path('<pk>', DetailBureauView.as_view(), name='detail_bureau'),
    path('<pk>/fermer', CloseBureauView.as_view(), name='close_bureau'),
    path('<pk>/results', BureauResultsView.as_view(), name='results_bureau'),
    path('<pk>/vote', FindVoterInListView.as_view(), name='vote_bureau'),
    path('<pk>/vote/homonymes', SelectHomonymView.as_view(), name='select_homonym'),
]
