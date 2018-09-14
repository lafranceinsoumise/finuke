from django.contrib import admin
from finuke.admin import admin_site

from .models import PersistantMessage


@admin.register(PersistantMessage, site=admin_site)
class PersistantMessageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'level', 'text', 'enabled', 'url_name')
    fields = ('level', 'text', 'enabled', 'url_name')
