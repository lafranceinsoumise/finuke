from django.urls import path
from .views import DocumentationView

urlpatterns = [
    path('administrateurs', DocumentationView.as_view(), {'filename': 'administrateurs.md'}),
    path('presidents', DocumentationView.as_view(), {'filename': 'presidents.md'})
]
