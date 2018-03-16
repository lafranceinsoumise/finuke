import re
import csv
import quopri
from collections import defaultdict
from django.core.management import BaseCommand
from django.conf import settings
from phonenumber_field.phonenumber import PhoneNumber as PhoneNumberObj
from argparse import FileType
import imapclient

from phones.models import PhoneNumber


requester_re = re.compile(r'De\s:\s(?P<nom>[^<]+) <(?P<email>[^>]+)>')
number_re = re.compile(r'numéro_([0-9_+-]+)\?')
votant_re = re.compile(r'personne ayant déjà voté avec\s:\s([^\r]+)\r')

body_key = 'BODY[1]'
subject_key  = 'BODY[HEADER.FIELDS ("SUBJECT")]'


class Command(BaseCommand):
    help = 'Importer un CSV de FE de Mailtrain'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--output', type=FileType(mode='w'), default=self.stdout)

    def get_fields(self, body):
        requester_match = requester_re.search(body)
        voter_match = votant_re.search(body)

        res = {}

        if requester_match:
            res['requester'] = requester_match.group('nom')
            res['email'] = requester_match.group('email')

        if voter_match:
            res['voter_declared'] = votant_re.search(body).group(1)

        return res

    def handle(self, *args, output, **kwargs):

        c = imapclient.IMAPClient(settings.CONTACT_EMAIL_SERVER)
        c.login(settings.CONTACT_EMAIL, settings.CONTACT_EMAIL_PASSWORD)

        c.select_folder('DEBLOCAGE TEL')

        ids = c.search()
        raw_messages = c.fetch(ids, [subject_key, body_key])
        messages = [{k.decode('utf8'): quopri.decodestring(v).decode('utf8') for k, v in d.items() if k != b'SEQ'}
                    for d in raw_messages.values()]

        w = csv.DictWriter(
            output,
            fieldnames=['status', 'phone_number', 'email', 'requester', 'voter_declared', 'voter_actual']
        )

        w.writerow({
            'status': 'Statut',
            'phone_number': 'Numéro',
            'email': 'Email',
            'requester': 'Nom demandeur',
            'voter_declared': 'Nom supposé votant',
            'voter_actual': 'Nom réel votant'
        })

        for m in messages:
            if m[subject_key].startswith('Subject: =?UTF-8?Q?Demande_de_déblocage'):
                row = defaultdict(str)
                row['phone_number'] = number_re.search(m[subject_key]).group(1).replace('_', '')
                row.update(self.get_fields(m[body_key]))

                try:
                    phone_number = PhoneNumberObj.from_string(row['phone_number'], 'FR')
                except ValueError:
                    row['status'] = 'Numéro invalide'
                    w.writerow(row)
                    continue

                if not phone_number.is_valid():
                    row['status'] = 'Numéro invalide'
                    w.writerow(row)
                    continue

                row['phone_number'] = phone_number.as_e164

                try:
                    phone_number_model = PhoneNumber.objects.select_related('voter').get(phone_number=phone_number)
                except PhoneNumber.DoesNotExist:
                    row['status'] = 'Numéro non utilisé'
                    w.writerow(row)
                    continue

                if not phone_number_model.validated:
                    row['status'] = 'Numéro non utilisé'
                    w.writerow(row)
                    continue

                if phone_number_model.voter:
                    row['status'] = 'Personne trouvée'
                    voter = phone_number_model.voter
                    row['voter_actual'] = voter.get_full_name()
                    if voter.use_last_name:
                        row['voter_actual'] += f' ({voter.use_last_name})'
                else:
                    row['status'] = 'Personne non indiquée'

                w.writerow(row)
