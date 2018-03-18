from django.contrib import admin
from django.conf import settings
from django.shortcuts import reverse

from bureaux.models import LoginLink, BureauOperator, Operation, Bureau
from finuke.admin import admin_site


@admin.register(LoginLink, site=admin_site)
class LoginLinkAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'operator', 'valid')
    fields = ('uuid', 'operator', 'valid')
    readonly_fields = ('uuid',)
    search_fields = ('operator__email',)


@admin.register(BureauOperator, site=admin_site)
class BureauOperatorAdmin(admin.ModelAdmin):
    list_display = ('email', 'bureau_count')
    search_fields = ('email',)

    readonly_fields = ('bureau_count', 'login_link')

    def bureau_count(self, obj):
        return obj.bureaux.all().count()
    bureau_count.short_description = "Nombre de bureaux"

    def login_link(self, obj):
        return f"https://{settings.DOMAIN_NAME}{reverse('login', args=[obj.login_links.first().uuid])}"
    login_link.short_description = "Lien de connexion"


@admin.register(Bureau, site=admin_site)
class BureauAdmin(admin.ModelAdmin):
    search_fields = ('place', 'operator__email')
    list_display = ('place', 'operator', 'start_time', 'end_time', 'has_results')
    readonly_fields = ('has_results',)

    def has_results(self, obj):
        return 'Oui' if obj.result1_yes is not None else 'Non'
    has_results.short_description = "Résultats remontés"


@admin.register(Operation, site=admin_site)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('created', 'type', 'details')
