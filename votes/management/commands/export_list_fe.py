import csv
from argparse import FileType
from django.core.management import BaseCommand
from tqdm import tqdm

from ...models import FEVoterListItem
from ...tokens import mail_token_generator


class Command(BaseCommand):
    help = 'Importer un CSV de FE de Mailtrain'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--output', type=FileType(mode='w'), default=self.stdout)

    def handle(self, *args, output, **kwargs):
        total = FEVoterListItem.objects.count()

        w = csv.writer(output)

        w.writerow(['email', 'code'])

        for vi in tqdm(FEVoterListItem.objects.values_list('email').iterator(), desc='Export', total=total):
            w.writerow((vi[0], mail_token_generator.make_token(vi[0])))
