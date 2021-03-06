import csv
import datetime
from collections import OrderedDict
from itertools import chain, islice
from tqdm import tqdm

from django.core.management import BaseCommand

from votes.models import VoterListItem


def group_by(it, n):
    it = iter(it)
    while True:
        try:
            e = next(it)
        except StopIteration:
            return

        yield chain((e, ), islice(it, n-1))


class Command(BaseCommand):
    help = 'Importer un CSV de Yannick'

    def add_arguments(self, parser):
        parser.add_argument('filename')
        parser.add_argument('file_id')
        parser.add_argument('--flush', action='store_true', dest='flush')

    def handle(self, *args, **options):
        if options['flush']:
            VoterListItem.objects.filter(origin_file=options['file_id']).delete()

        fieldnames = [
            'list_type',
            'departement',
            'commune',
            'civilite',
            'last_name',
            'use_last_name',
            'first_names',
            'birth_date',
            'birth_city_name',
            'birth_departement_name',
            'birth_country_name',
            'nationality',
            'address1',
            'address2',
            'street_number',
            'street_type',
            'street_label',
            'place_name',
            'zipcode',
            'local_city_name',
            'country',
        ]

        filestructure = OrderedDict([
            ('list_type', 'TypeListe'), ('departement', 'CodeDepartement'), ('commune', 'CodeCommune'),
            ('civilite', 'Civilite'), ('last_name', 'NomdeNaissance'), ('use_last_name', 'NomDusage'),
            ('first_names', 'Prenoms'), ('birth_date', 'DateDeNaissance'),
            ('birth_city_name', 'NomComNaissance'), ('birth_departement_name', 'DeptNaissance'),
            ('birth_country_name', 'PaysNaissance'), ('nationality', 'Nationalite'),
            ('address1', 'ComplementDeLocalisation1'), ('address2', 'ComplementDeLocalisation2'),
            ('street_number', 'NumeroVoie'), ('street_type', 'TypeVoie'), ('street_label', 'LibelleVoie'),
            ('place_name', 'LieuDit'), ('zipcode', 'CodePostal'), ('local_city_name', 'VilleLocalite'),
            ('country', 'Pays')
        ])

        with open(options['filename'], encoding='utf-8-sig') as file:
            last_created = VoterListItem.objects.filter(origin_file=options['file_id']).order_by('-file_line').first()
            last_created = last_created.file_line if last_created else 0

            file.seek(0)
            file_reader = tqdm(csv.DictReader(file, delimiter=';', fieldnames=fieldnames, restkey="more_fields"), desc="Import")
            items = []
            date_errors = 0

            for chunk in group_by(enumerate(file_reader), 2000):
                for i, row in chunk:
                    if "more_fields" in row: del row["more_fields"]
                    if i == 0:
                        if not row.items() == filestructure.items():
                            print('Le fichier n\'est pas structuré correctement')
                            print('Fichier : ' + str(row))
                            print('Attendu : ' + str(filestructure))
                            exit()
                        continue

                    if i <= last_created:
                        continue

                    row['list_type'] = row['list_type'].replace('\ufeff', '')
                    row['civilite'] = dict(map(reversed, VoterListItem.CIVILITE_CHOICES)).get(row['civilite'], '')
                    try:
                        row['birth_date'] = datetime.datetime.strptime(row['birth_date'], "%d/%m/%Y %H:%M:%S") if row['birth_date'] else None
                    except ValueError:
                        try:
                            row['birth_date'] = datetime.datetime.strptime(row['birth_date'], "%d/%m/%Y") if row['birth_date'] else None
                        except ValueError:
                            date_errors = date_errors + 1
                            continue

                    items.append(VoterListItem(origin_file=options['file_id'], file_line=i, **row))

                if len(items) == 0:
                    continue

                try:
                    VoterListItem.objects.bulk_create(items)
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

            print(f'{date_errors} erreurs de date')
