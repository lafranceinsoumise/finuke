import argparse
import sys
from urllib.parse import urljoin

import html2text
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.core.management import BaseCommand
from django.db import transaction, DatabaseError
from django.http import QueryDict
from django.urls import reverse

from bureaux.models import BureauOperator, LoginLink


_h = html2text.HTML2Text()
_h.ignore_images = True

class Command(BaseCommand):
    help = 'Importer une liste de mail d\'operateurs'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=argparse.FileType(mode='r', encoding='utf-8'), default=sys.stdin, nargs='?')
        parser.add_argument('--send-links', default=False, action='store_true', help="send operators login links by email")

    def handle(self, *args, filename, send_links, **options):
        for email in filename:
            try:
                with transaction.atomic():
                    operator = BureauOperator.objects.create(email=email.replace('\n',''))
                    login_link = LoginLink.objects.create(operator=operator)

                if send_links:
                    query = QueryDict(mutable=True)
                    query.update({
                        'OPERATOR_LINK': urljoin('https://' + settings.DOMAIN_NAME, reverse('login', args=[login_link.uuid])),
                        'VOTATION_NAME': settings.VOTATION_NAME,
                        'MANUAL': urljoin('https://' + settings.DOMAIN_NAME, reverse('manual'))
                    })
                    email_url = settings.EMAIL_OPERATOR + '?' + query.urlencode()
                    email = requests.get(email_url).text

                    send_mail(
                        'Présider vos bureaux de vote',
                        _h.handle(email),
                        settings.FROM_EMAIL,
                        [operator.email],
                        html_message=email,
                        fail_silently=True,
                    )
            except DatabaseError:
                pass

