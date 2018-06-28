from django.contrib import admin
from django.conf import settings
from django.db.models import Count, F
from django.shortcuts import reverse

from bureaux.models import LoginLink, BureauOperator, Operation, Bureau
from finuke.admin import admin_site

if settings.ENABLE_PHYSICAL_VOTE:
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
        list_display = ('place', 'operator', 'start_time', 'end_time', 'has_results', 'result1', 'emargements', 'difference', 'result2')
        readonly_fields = ('has_results', 'result1', 'result2', 'emargements', 'difference')

        def get_queryset(self, request):
            return Bureau.objects.annotate(emargements=Count('voterlistitem'))\
                .annotate(difference=Count('voterlistitem') - F('result1_yes') - F('result1_no') - F('result1_blank') - F('result1_null'))\
                .annotate(result1=F('result1_yes') + F('result1_no') + F('result1_blank') + F('result1_null'))\
                .annotate(result2=F('result2_yes') + F('result2_no') + F('result2_blank') + F('result2_null'))

        def result1(self, obj):
            return obj.result1
        result1.short_description = "Bulletins inscrit⋅e⋅s"

        def result2(self, obj):
            return obj.result2
        result2.short_description = "Bulletins non-inscrit⋅e⋅s"

        def has_results(self, obj):
            return 'Oui' if obj.result1_yes is not None else 'Non'
        has_results.short_description = "Résultats remontés"

        def difference(self, obj):
            return obj.difference

        difference.short_description = 'Écart bulletins / émargements'
        difference.admin_order_field = 'difference'

        def emargements(self, obj):
            return obj.emargements

        emargements.short_description = 'Émargements'
        emargements.admin_order_field = 'emargements'



    @admin.register(Operation, site=admin_site)
    class OperationAdmin(admin.ModelAdmin):
        list_display = ('created', 'type', 'details')
