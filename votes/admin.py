from django.contrib import admin
from django.urls import reverse

from finuke.admin import admin_site
from votes.models import VoterListItem, Vote, FEVoterListItem, UnlockingRequest
from .tokens import mail_token_generator


@admin.register(FEVoterListItem, site=admin_site)
class FEVoterListItemAdmin(admin.ModelAdmin):
    list_display = ('email', 'last_name', 'first_names', 'has_voted')

    fields = ('email', 'last_name', 'first_names', 'login_link')

    readonly_fields = ('login_link',)

    def login_link(self, obj):
        return reverse('fe_login', args=[mail_token_generator.make_token(obj.email)])
    login_link.short_description = 'Lien de connexion'

@admin.register(VoterListItem, site=admin_site)
class VoterListItemAdmin(admin.ModelAdmin):
    list_display = ('import_id', 'first_names', 'last_name', 'departement')
    list_filter = ('departement',)

    fieldsets = (
        (None, {'fields': ('import_id', 'last_name', 'first_names', 'departement', 'commune')}),
        ('Informations de vote', {'fields': ('vote_status', 'vote_bureau', 'phonenumber')})
    )

    readonly_fields = ('import_id', 'last_name', 'first_names', 'departement', 'commune', 'phonenumber', 'vote_status', 'vote_bureau')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def import_id(self, obj):
        return str(obj.origin_file) + ' #' + str(obj.file_line)
    import_id.short_description = "ID importation"


@admin.register(Vote, site=admin_site)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'vote', 'with_list')


@admin.register(UnlockingRequest, site=admin_site)
class UnlockingRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'display_number', 'declared_voter', 'actual_voter', 'status', 'answer_sent')
    list_filter = ('status', 'answer_sent')

    fields = ('email', 'requester', 'declared_voter', 'actual_voter', 'status', 'answer_sent')
    readonly_fields = ('email', 'requester', 'declared_voter', 'actual_voter', 'answer_sent')

    def display_number(self, obj):
        if obj.phone_number:
            return obj.phone_number.phone_number.as_international
        return obj.raw_number
    display_number.short_description = 'Numéro'

    def actual_voter(self, obj):
        if obj.voter:
            if obj.voter.use_last_name:
                return obj.voter.get_full_name() + ' ' + obj.voter.use_last_name
            else:
                return obj.voter.get_full_name()
        else:
            return '-'
    actual_voter.short_description = 'Nom du votant'
