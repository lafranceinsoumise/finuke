from django.contrib import admin
from django.urls import reverse
import django.shortcuts
from django.utils.html import format_html

from finuke.admin import admin_site
from phones.models import PhoneNumber, SMS


@admin.register(PhoneNumber, site=admin_site)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'validated', 'created', 'updated')
    search_fields = ('phone_number',)
    list_filter = ('validated',)
    fields = ('phone_number', 'validated', 'bypass_code', 'voter_link', 'created', 'updated', )

    readonly_fields = ('phone_number', 'voter_link', 'created', 'updated')

    def voter_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:votes_voterlistitem_change', args=(obj.voter.pk, )),
            str(obj.voter)
        )
    voter_link.short_description = "Votant"

@admin.register(SMS, site=admin_site)
class SMSAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'created')
    list_display_links = ('code',)
    search_fields = ('phone_number__phone_number',)
    fields = ('phone_number', 'code', 'created')
