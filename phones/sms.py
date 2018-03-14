from datetime import timedelta

import ovh
from django.conf import settings
from django.utils import timezone

from prometheus_client import Counter

from finuke.exceptions import RateLimitedException
from phones.models import SMS
from token_bucket import TokenBucket

client = ovh.Client(
    endpoint='ovh-eu',
    application_key=settings.OVH_APPLICATION_KEY,
    application_secret=settings.OVH_APPLICATION_SECRET,
    consumer_key=settings.OVH_CONSUMER_KEY,
)

SMSShortTokenBucket = TokenBucket('SMSShort', 1, 60)
SMSLongTokenBucket = TokenBucket('SMSLong', settings.SMS_BUCKET_MAX, settings.SMS_BUCKET_INTERVAL)
SMSIPTokenBucket = TokenBucket('SMSIp', settings.SMS_IP_BUCKET_MAX, settings.SMS_BUCKET_INTERVAL)
CodeValidationTokenBucket = TokenBucket('CodeValidation', 5, 60)

sms_counter = Counter('finuke_sms_requested_total', 'Number of SMS requested', ['result'])
code_counter = Counter('finuke_sms_code_checked_total', 'Number of code verifications requested', ['result'])


class SMSSendException(Exception):
    pass

class SMSCodeBypassed(Exception):
    pass


def send(message, phone_number):
    try:
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
    except Exception:
        raise SMSSendException('Le message n\'a pas été envoyé.')

    if len(result['invalidReceivers']) > 0:
        raise SMSSendException('Destinataire invalide.')

    if len(result['validReceivers']) < 1:
        raise SMSSendException('Le message n\'a pas été envoyé.')


def send_new_code(phone_number, ip):
    if ip and not SMSIPTokenBucket.has_tokens(ip):
        sms_counter.labels('ip_limited').inc()
        raise RateLimitedException('Trop de messages envoyés, réessayer dans quelques minutes.')

    if not (SMSShortTokenBucket.has_tokens(phone_number) and SMSLongTokenBucket.has_tokens(phone_number)):
        sms_counter.labels('number_limited').inc()
        raise RateLimitedException('Trop de messages envoyés, réessayer dans quelques minutes.')

    if phone_number.bypass_code:
        sms_counter.labels('bypassed').inc()
        raise SMSCodeBypassed()

    sms = SMS(phone_number=phone_number)
    formatted_code = sms.code[:3] + ' ' + sms.code[3:]
    message = 'Votre code de validation pour nucleaire.vote est {0}'.format(formatted_code)

    if not settings.OVH_SMS_DISABLE:
        send(message, phone_number.phone_number)
    sms_counter.labels('sent').inc()

    sms.save()
    return formatted_code


def is_valid_code(phone_number, code):
    if not CodeValidationTokenBucket.has_tokens(phone_number):
        code_counter.labels('rate_limited').inc()
        raise RateLimitedException()
    try:
        # TODO: possible timing attack here
        SMS.objects.get(phone_number=phone_number, code=code, created__gt=timezone.now()-timedelta(minutes=30))
        code_counter.labels('success').inc()
        return True
    except SMS.DoesNotExist:
        code_counter.labels('failure').inc()
        return False
