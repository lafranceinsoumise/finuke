from django.contrib import admin

from phones.models import PhoneNumber, SMS

@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'validated', 'sms_bucket', 'created', 'updated')
    search_fields = ('phone_number',)
    list_filter = ('validated',)

@admin.register(SMS)
class SMSAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'created')
    list_display_links = ('code',)
    search_fields = ('phone_number__phone_number',)
