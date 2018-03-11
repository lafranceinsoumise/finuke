import csv

from django.core.management import BaseCommand

from bureaux.models import BureauOperator


class Command(BaseCommand):
    help = 'Importer une liste de mail d\'operateurs'

    def add_arguments(self, parser):
        parser.add_argument('filename')
        parser.add_argument('host')

    def handle(self, *args, **options):
        with open(options['filename'], 'w', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            for operator in BureauOperator.objects.filter(login_links__valid=True):
                writer.writerow([operator, options['host'] + operator.login_links.filter(valid=True).first().get_absolute_url()])

