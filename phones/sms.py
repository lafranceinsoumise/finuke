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


def send(message, number):
    result = client.post('/sms/' + settings.OVH_SMS_SERVICE + '/jobs',
                         charset='UTF-8',
                         coding='7bit',
                         receivers=[number],
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


def send_new_code(phonenumber):
    phonenumber.sms_bucket = min(
        settings.SMS_BUCKET_MAX,
        phonenumber.sms_bucket + int((timezone.now() - phonenumber.updated ).total_seconds() / settings.SMS_BUCKET_INTERVAL)
    )

    if phonenumber.sms_bucket == 0:
        raise SMSCodeException('Trop de messages envoyés, réessayer dans quelques minutes.')

    sms = SMS(phonenumber=phonenumber)
    message = 'Votre code est {0}'.format(sms.code)

    if not settings.DEBUG:
        send(message, phonenumber.phonenumber)
    else:
        print('SMS envoyé à {0} : {1}'.format(phonenumber.phonenumber, message))

    with transaction.atomic():
        sms.save()
        phonenumber.sms_bucket = phonenumber.sms_bucket - 1
        phonenumber.save()

    return sms.code


def is_valid_code(phonenumber, code):
    try:
        SMS.objects.get(phonenumber=phonenumber, code=code, created__gt=timezone.now()-timedelta(minutes=30))
        return True
    except SMS.DoesNotExist:
        return False

