from django.core.management import BaseCommand
from django.db import transaction, DatabaseError

from bureaux.models import BureauOperator, LoginLink


class Command(BaseCommand):
    help = 'Importer une liste de mail d\'operateurs'

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):
        with open(options['filename'], encoding='utf-8-sig') as file:
            for email in file:
                try:
                    with transaction.atomic():
                        operator = BureauOperator.objects.create(email=email.replace('\n',''))
                        LoginLink.objects.create(operator=operator)
                except DatabaseError:
                    pass

