from django.core.management import BaseCommand
from django.db.models import Count, Sum

from bureaux.models import Bureau
from votes.models import VoterListItem, Vote


class Command(BaseCommand):
    help = 'Résultats'

    def handle(self, *args, **options):
        online_votes = list(Vote.objects.values('vote', 'with_list').annotate(count=Count('id')).order_by('with_list', 'vote'))

        non_inscrits = [choice for choice in online_votes if choice['with_list'] == False]
        inscrits = [choice for choice in online_votes if choice['with_list'] == True]

        print("# Votes en ligne")
        print("## Votes non-inscrits")

        for choice in non_inscrits:
            print(f"{choice['count']} votes {dict(Vote.VOTE_CHOICES)[choice['vote']]}")

        print("## Votes inscrits")

        for choice in inscrits:
            print(f"{choice['count']} votes {dict(Vote.VOTE_CHOICES)[choice['vote']]}")

        print("\n# Votes en bureau")

        open_bureaux = Bureau.objects.filter(end_time__isnull=True).count()
        closed_bureaux = Bureau.objects.filter(end_time__isnull=False).count()
        results_bureaux = Bureau.objects.filter(result2_yes__isnull=False).count()

        print(f"{open_bureaux} bureaux ouverts")
        print(f"{closed_bureaux} bureaux fermés")
        print(f"dont {results_bureaux} avec résultats")

        results = Bureau.objects.filter(result2_yes__isnull=False).aggregate(
            Sum('result1_yes'),
            Sum('result1_no'),
            Sum('result1_blank'),
            Sum('result1_null'),
            Sum('result2_yes'),
            Sum('result2_no'),
            Sum('result2_blank'),
            Sum('result2_null')
        )

        print("## Bulletins verts")
        print(f"{results['result1_null__sum']} bulletins nuls")
        print(f"{results['result1_blank__sum']} bulletins blanc")
        print(f"{results['result1_no__sum']} bulletins non")
        print(f"{results['result1_yes__sum']} bulletins oui")

        print("## Bulletins orange")
        print(f"{results['result2_null__sum']} bulletins nuls")
        print(f"{results['result2_blank__sum']} bulletins blanc")
        print(f"{results['result2_no__sum']} bulletins non")
        print(f"{results['result2_yes__sum']} bulletins oui")
