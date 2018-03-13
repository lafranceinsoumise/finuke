from django.contrib import admin

from finuke.admin import admin_site
from votes.models import VoterListItem, Vote, FEVoterListItem


@admin.register(FEVoterListItem, site=admin_site)
class FEVoterListItemAdmin(admin.ModelAdmin):
    list_display = ('email', 'last_name', 'first_names')


@admin.register(VoterListItem, site=admin_site)
class VoterListItemAdmin(admin.ModelAdmin):
    list_display = ('import_id', 'first_names', 'last_name', 'departement')
    list_filter = ('departement',)


    fieldsets = (
        (None, {'fields': ('import_id', 'last_name', 'first_names', 'departement')}),
        ('Informations de vote', {'fields': ('vote_status', 'vote_bureau', 'phonenumber')})
    )

    readonly_fields = ('import_id', 'last_name', 'first_names', 'departement', 'phonenumber', 'vote_status', 'vote_bureau')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def import_id(self, obj):
        return str(obj.origin_file) + ' #' + str(obj.file_line)
    import_id.short_description = "ID importation"


@admin.register(Vote, site=admin_site)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'vote', 'with_list')
