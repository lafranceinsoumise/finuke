import csv
from collections import OrderedDict

import progressbar
from django.core.management import BaseCommand
from django.db import transaction

from votes.models import FEVoterListItem


class Command(BaseCommand):
    help = 'Importer un CSV de FE de Mailtrain'

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):

        fieldnames = [
            'email',
            'first_names',
            'last_name',
        ]

        filestructure = OrderedDict([
            ('email', 'email'), ('first_names', 'first_names'), ('last_name', 'last_name'),
        ])

        with open(options['filename']) as file:
            print('Counting lines in file...')
            lines = sum(1 for line in file)
            bar = progressbar.ProgressBar(max_value=lines)

            file.seek(0)
            file_reader = csv.DictReader(file, delimiter='\t', fieldnames=fieldnames)
            items = []

            for i, row in enumerate(file_reader):
                if i == 0:
                    if row != filestructure:
                        print('Le fichier n\'est pas structuré correctement')
                        print(row)
                        print(filestructure)
                        exit()
                    continue

                items.append(FEVoterListItem(**row))

                if i % 10000 == 0:
                    try:
                        with transaction.atomic():
                            FEVoterListItem.objects.bulk_create(items)
                        bar.update(i)
                        items = []
                    except Exception as e:
                        pass

                    try:
                        for j, item in enumerate(items):
                            item.save()
                    except Exception as e:
                        print('Error on line '  + str(i - len(items) + j))
                        print(item.__dict__)
                        raise e

