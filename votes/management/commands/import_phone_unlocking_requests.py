import re
import quopri
from django.core.management import BaseCommand
from django.conf import settings
from phonenumber_field.phonenumber import PhoneNumber as PhoneNumberObj
from argparse import FileType
import imapclient

from phones.models import PhoneNumber
from ...models import UnlockingRequest


requester_re = re.compile(r'De\s:\s(?P<nom>[^<]+) <(?P<email>[^>]+)>')
number_re = re.compile(r'numéro_([0-9_+-]+)\?')
votant_re = re.compile(r'personne ayant déjà voté avec\s:\s([^\r]+)\r')

body_key = 'BODY[1]'
subject_key  = 'BODY[HEADER.FIELDS ("SUBJECT")]'


class SkipException(Exception):
    pass


class Command(BaseCommand):
    help = 'Importer les demandes de déblocage'

    def get_fields(self, body):
        requester_match = requester_re.search(body)
        voter_match = votant_re.search(body)

        if not requester_match or not voter_match:
            raise SkipException()

        return requester_match.group('email'), requester_match.group('nom'), voter_match.group(1)

    def handle(self, *args, **kwargs):

        c = imapclient.IMAPClient(settings.CONTACT_EMAIL_SERVER)
        c.login(settings.CONTACT_EMAIL, settings.CONTACT_EMAIL_PASSWORD)

        c.select_folder('DEBLOCAGE TEL')

        ids = c.search()
        raw_messages = c.fetch(ids, [subject_key, body_key])
        messages = {i: {k.decode('utf8'): quopri.decodestring(v).decode('utf8') for k, v in m.items() if k != b'SEQ'}
                    for i, m in raw_messages.items()}

        def resolve(unlock_request, id, status):
            unlock_request.status = status
            unlock_request.save()
            c.move(id, 'DEBLOCAGE TRAITE')

        for uid, m in messages.items():
            if m[subject_key].startswith('Subject: =?UTF-8?Q?Demande_de_déblocage'):
                unlock_request = UnlockingRequest()
                unlock_request.raw_number = number_re.search(m[subject_key]).group(1).replace('_', '')

                unlock_request.email, unlock_request.requester, unlock_request.declared_voter = self.get_fields(m[body_key])

                try:
                    phone_number = PhoneNumberObj.from_string(unlock_request.raw_number, 'FR')
                except ValueError:
                    resolve(unlock_request, uid, UnlockingRequest.STATUS_INVALID_NUMBER)
                    continue

                if not phone_number.is_valid():
                    resolve(unlock_request, uid, UnlockingRequest.STATUS_INVALID_NUMBER)
                    continue

                try:
                    phone_number_model = PhoneNumber.objects.select_related('voter').get(phone_number=phone_number)
                except PhoneNumber.DoesNotExist:
                    resolve(unlock_request, uid, UnlockingRequest.STATUS_UNUSED)
                    continue

                unlock_request.phone_number = phone_number_model

                if not phone_number_model.validated:
                    resolve(unlock_request, uid, UnlockingRequest.STATUS_UNUSED)
                    continue

                if UnlockingRequest.objects.filter(phone_number=phone_number_model).exists():
                    resolve(unlock_request, uid, UnlockingRequest.STATUS_DUPLICATE)

                if phone_number_model.voter:
                    unlock_request.voter = phone_number_model.voter

                    resolve(unlock_request, uid, UnlockingRequest.STATUS_REVIEW)
                else:
                    resolve(unlock_request, uid, UnlockingRequest.STATUS_UNLISTED)
