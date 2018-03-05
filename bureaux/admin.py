from django.contrib import admin

from bureaux.models import LoginLink, BureauOperator, Operation, Bureau
from finuke.admin import admin_site


@admin.register(LoginLink, site=admin_site)
class LoginLinkAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'operator', 'valid')
    fields = ('uuid', 'operator', 'valid')
    readonly_fields = ('uuid',)


@admin.register(BureauOperator, site=admin_site)
class BureauOperatorAdmin(admin.ModelAdmin):
    list_display = ('email', 'bureau_count')
    readonly_fields = ('bureau_count',)

    def bureau_count(self, obj):
        return obj.bureaux.all().count()
    bureau_count.short_description = "Nombre de bureaux"


@admin.register(Bureau, site=admin_site)
class BureauAdmin(admin.ModelAdmin):
    pass


@admin.register(Operation, site=admin_site)
class OperationAdmin(admin.ModelAdmin):
    pass