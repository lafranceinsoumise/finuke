from django.conf import settings
from django.contrib import admin
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import CharField, ExpressionWrapper, Value, F
from django.urls import reverse

from finuke.admin import admin_site
from votes.models import VoterListItem, Vote, FEVoterListItem, UnlockingRequest
from .tokens import mail_token_generator


class CF(F):
    ADD = '||'


class CV(Value):
    ADD = '||'


class CC(ExpressionWrapper):
    ADD = '||'

    def __init__(self, expression):
        super().__init__(expression, output_field=CharField())


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
    list_display = ('import_id', 'first_names', 'last_name', 'departement', 'commune', 'birth_date')
    list_filter = ('departement', 'vote_status')

    fieldsets = (
        (None, {'fields': ('import_id', 'last_name', 'first_names', 'departement', 'commune')}),
        ('Informations de vote', {'fields': ('vote_status', 'vote_bureau', 'phonenumber')})
    )

    readonly_fields = ('import_id', 'last_name', 'first_names', 'departement', 'commune', 'phonenumber', 'vote_status', 'vote_bureau')
    search_fields = ('last_name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def import_id(self, obj):
        return str(obj.origin_file) + ' #' + str(obj.file_line)
    import_id.short_description = "ID importation"

    def get_search_results(self, request, queryset, search_term):
        if (len(search_term) < 1):
            return queryset, False

        coumpound_field = CC(CC(CC(CF('first_names') + CV(' ')) + CF('use_last_name')) + CV(' ')) + CF('last_name')
        queryset = queryset.annotate(
            similarity=TrigramSimilarity(coumpound_field, str(search_term)),
            full_name=coumpound_field
        ).filter(full_name__trigram_similar=str(search_term)).order_by('-similarity')

        return queryset, False

if settings.ENABLE_ELECTRONIC_VOTE:
    @admin.register(Vote, site=admin_site)
    class VoteAdmin(admin.ModelAdmin):
        list_display = ('id', 'vote', 'with_list')


    def accept_request(model_admin, request, queryset):
        queryset.update(status=UnlockingRequest.STATUS_OK)
    accept_request.short_description = "Accepter les requêtes"


    def refuse_request(model_admin, request, queryset):
        queryset.update(status=UnlockingRequest.STATUS_KO)
    refuse_request.short_description = "Refuser les requêtes"


    @admin.register(UnlockingRequest, site=admin_site)
    class UnlockingRequestAdmin(admin.ModelAdmin):
        list_display = ('requester', 'display_number', 'declared_voter', 'actual_voter', 'status', 'answer_sent')
        list_filter = ('status', 'answer_sent')
        search_fields = ('email', 'requester', 'declared_voter', 'raw_number', 'phone_number__phone_number')

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

        actions = [accept_request, refuse_request]
