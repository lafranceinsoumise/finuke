import csv
from collections import OrderedDict
from itertools import islice, chain

import progressbar
from django.core.management import BaseCommand

from votes.models import FEVoterListItem


def group_by(it, n):
    it = iter(it)
    while True:
        try:
            e = next(it)
        except StopIteration:
            return

        yield chain((e, ), islice(it, n-1))


class Command(BaseCommand):
    help = 'Importer un CSV de FE de Mailtrain'

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):
        last_created = FEVoterListItem.objects.all().count()

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

            for chunk in group_by(enumerate(file_reader), 10000):
                for i, row in chunk:
                    if i < last_created:
                        continue

                    if i == 0:
                        if row != filestructure:
                            print('Le fichier n\'est pas structuré correctement')
                            print(row)
                            print(filestructure)
                            exit()
                        continue

                    items.append(FEVoterListItem(**row))

                if len(items) == 0:
                    continue

                try:
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

