from itertools import groupby

from django.conf import settings
from django.contrib import admin
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import CharField, ExpressionWrapper, Value, F, Sum, Count
from django.urls import reverse
from django.views.generic import TemplateView

from bureaux.models import Bureau
from finuke.admin import admin_site
from votes.models import VoterListItem, Vote, FEVoterListItem, UnlockingRequest, Results
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


class ResultsAdminView(TemplateView):
    template_name = 'votes/admin/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context['title'] = 'Résultats'
        context['opts'] = Results._meta
        context['add'] = False
        context['change'] = False
        context['is_popup'] = False
        context['save_as'] = False
        context['has_add_permission'] = False
        context['has_change_permission'] = False
        context['has_view_permission'] = False
        context['has_editable_inline_admin_formsets'] = False
        context['has_delete_permission'] = False
        context['show_close'] = False

        online_results = list(Vote.objects.values('with_list', 'vote').annotate(count=Count('*')).order_by('with_list', 'vote'))
        context['vote'] = {
            'enable_voting': settings.ENABLE_VOTING,
            'question': settings.VOTE_QUESTION,
            'answers': settings.VOTE_ANSWERS,
            'bureau_results': Bureau.objects.filter(end_time__isnull=False).aggregate(
                result1_yes_sum=Sum('result1_yes'),
                result1_no_sum=Sum('result1_no'),
                result1_blank_sum=Sum('result1_blank'),
                result1_null_sum=Sum('result1_null'),
                result1_total_sum=Sum(F('result1_yes') + F('result1_no') + F('result1_blank') + F('result1_null')),
                result2_yes_sum=Sum('result2_yes'),
                result2_no_sum=Sum('result2_no'),
                result2_blank_sum=Sum('result2_blank'),
                result2_null_sum=Sum('result2_null'),
                result2_total_sum=Sum(F('result2_yes') + F('result2_no') + F('result2_blank') + F('result2_null')),
            ),
            'online_results': {
                str(key): dict([(e['vote'], e['count']) for e in g])
                    for key, g in groupby(online_results, lambda v:v['with_list'])
            }
        }

        for k in context['vote']['online_results']:
            context['vote']['online_results'][k]['T'] = sum(context['vote']['online_results'][k].values())
        context['vote']['total_results'] = {
            key: (value or 0) + context['vote']['online_results'].get(str(key[6] == '1'), {}).get(key[8].capitalize(), 0)
        for key, value in context['vote']['bureau_results'].items()}

        return context

    def dispatch(self, request, *args, **kwargs):
        request.current_app = 'finuke_admin'
        return super().dispatch(request, *args, **kwargs)
