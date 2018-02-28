from django.contrib import admin

from finuke.admin import admin_site
from votes.models import VoterListItem, Vote


@admin.register(VoterListItem, site=admin_site)
class VoterListItemAdmin(admin.ModelAdmin):
    list_display = ('import_id', 'first_names', 'last_name', 'departement')
    list_filter = ('departement',)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_fields = [f.name for f in self.model._meta.get_fields()] + ['id']

    def import_id(self, obj):
        return str(obj.origin_file) + ' #' + str(obj.file_line)

@admin.register(Vote, site=admin_site)
class VoteAdmin(admin.ModelAdmin):
    pass
