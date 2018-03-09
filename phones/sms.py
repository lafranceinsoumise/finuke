from datetime import timedelta

import ovh
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from phones.models import SMS

client = ovh.Client(
    endpoint='ovh-eu',
    application_key=settings.OVH_APPLICATION_KEY,
    application_secret=settings.OVH_APPLICATION_SECRET,
    consumer_key=settings.OVH_CONSUMER_KEY,
)


class SMSSendException(Exception):
    pass


def send(message, phone_number):
    result = client.post('/sms/' + settings.OVH_SMS_SERVICE + '/jobs',
                         charset='UTF-8',
                         coding='7bit',
                         receivers=[str(phone_number)],
                         message=message,
                         noStopClause=True,
                         priority='high',
                         senderForResponse=True,
                         validityPeriod=2880
                         )

    if len(result['invalidReceivers']) > 0:
        raise SMSSendException('Destinataire invalide.')

    if len(result['validReceivers']) < 1:
        raise SMSSendException('Le message n\'a pas été envoyé.')


class SMSCodeException(Exception):
    pass


def send_new_code(phone_number):

    if not phone_number.can_send_sms():
        raise SMSCodeException('Trop de messages envoyés, réessayer dans quelques minutes.')

    sms = SMS(phone_number=phone_number)
    message = 'Votre code de validation pour nucleaire.vote est {0}'.format(sms.code)

    if not settings.OVH_SMS_DISABLE:
        send(message, phone_number.phone_number)
    else:
        print('SMS envoyé à {0} : {1}'.format(str(phone_number.phone_number), message))

    sms.save()
    return sms.code


def is_valid_code(phone_number, code):
    try:
        # TODO: possible timing attack here
        SMS.objects.get(phone_number=phone_number, code=code, created__gt=timezone.now()-timedelta(minutes=30))
        return True
    except SMS.DoesNotExist:
        return False
