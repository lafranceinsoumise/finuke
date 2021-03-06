"""finuke URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.urls import path, include, reverse_lazy
from django.views.generic import RedirectView

from finuke.admin import admin_site
from finuke.metrics import get_metrics

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', RedirectView.as_view(url=reverse_lazy(settings.MAIN_PAGE))),
    path('', include('custom_messages.urls')),
    path('', include('votes.urls'))
]

if settings.ENABLE_PHYSICAL_VOTE:
    urlpatterns.append(
        path('bureaux/', include('bureaux.urls'))
    )

if settings.BASE_URL:
    urlpatterns = [
        path(settings.BASE_URL, include(urlpatterns)),
        path('metrics', get_metrics)
    ]
else:
    urlpatterns += [
        path('metrics', get_metrics),
    ]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      url(r'^__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns


urlpatterns += [
    path('documentation/', include('documentation.urls'))
]