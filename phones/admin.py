from django.contrib import admin

from finuke.admin import admin_site
from phones.models import PhoneNumber, SMS


@admin.register(PhoneNumber, site=admin_site)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'validated', 'created', 'updated')
    search_fields = ('phone_number',)
    list_filter = ('validated',)
    fields = ('phone_number', 'validated', 'bypass_code', 'voter', 'created', 'updated', )

    readonly_fields = ('phone_number', 'voter', 'created', 'updated')


@admin.register(SMS, site=admin_site)
class SMSAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'created')
    list_display_links = ('code',)
    search_fields = ('phone_number__phone_number',)
    fields = ('phone_number', 'code', 'created')
