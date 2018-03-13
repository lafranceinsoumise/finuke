import csv

import sys
from django.core.management import BaseCommand

from bureaux.models import BureauOperator


class Command(BaseCommand):
    help = 'Importer une liste de mail d\'operateurs'

    def add_arguments(self, parser):
        parser.add_argument('host')
        parser.add_argument('-o', action='store')

    def handle(self, *args, **options):
        with (options.get('o') is not None and open(options['o'], 'w')) or sys.stdout as file:
            writer = csv.writer(file)
            for operator in BureauOperator.objects.filter(login_links__valid=True):
                writer.writerow([operator, options['host'] + operator.login_links.filter(valid=True).first().get_absolute_url()])

