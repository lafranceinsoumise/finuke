from django.contrib import admin
from finuke.admin import admin_site

from .models import PersistantMessage


@admin.register(PersistantMessage, site=admin_site)
class PersistantMessageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'level', 'enabled')
    fields = ('pk', 'level', 'text', 'enabled')
    readonly_fields = ('pk',)
