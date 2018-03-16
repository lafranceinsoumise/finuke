import html2text
import requests
from django.conf import settings
from django.core.mail import send_mass_mail, send_mail
from django.core.management import BaseCommand
from django.utils import timezone

from bureaux.models import BureauOperator

FROM_EMAIL = "nepasrepondre@nucleaire.vote"

_h = html2text.HTML2Text()
_h.ignore_images = True

class Command(BaseCommand):
    help = 'Envoyer les rappels par mail'

    def handle(self, *args, **options):
        midnight = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        not_closed_bureau = BureauOperator.objects\
            .filter(bureaux__start_time__lt=midnight, bureaux__end_time__isnull=True)
        no_results_bureau = BureauOperator.objects\
            .filter(bureaux__end_time__isnull=False, bureaux__result1_yes__isnull=True)\
            .difference(not_closed_bureau)

        for operator in not_closed_bureau:
            mail = requests.get(settings.EMAIL_NOT_CLOSED + '?LINK_UUID=' + str(operator.login_links.first().uuid)).text
            send_mail(
                'Vous n\'avez pas fermé tous vos bureaux',
                _h.handle(mail),
                FROM_EMAIL,
                [operator.email],
                html_message=mail,
                fail_silently = True,
            )

        for operator in no_results_bureau:
            mail = requests.get(settings.EMAIL_NOT_CLOSED  + '?LINK_UUID=' + str(operator.login_links.first().uuid)).text
            send_mail(
                'Vous n\'avez pas remonté les résultats de tous vos bureaux',
                _h.handle(mail),
                FROM_EMAIL,
                [operator.email],
                html_message=mail,
                fail_silently=True,
            )


