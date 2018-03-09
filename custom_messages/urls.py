from django.urls import path

from .views import mark_as_read


urlpatterns = [
    path('mark_as_read/<pk>', mark_as_read, name='mark_as_read')
]
