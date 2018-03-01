import secrets

from django.conf import settings
from django.db import models
from django.db.models import fields
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from token_bucket import TokenBucket


SMSTokenBucket = TokenBucket('SMS', settings.SMS_BUCKET_MAX, settings.SMS_BUCKET_INTERVAL)


class PhoneNumber(models.Model):
    phone_number = PhoneNumberField('Numéro de mobile', editable=False, unique=True)
    created = fields.DateTimeField(auto_now_add=True)
    updated = fields.DateTimeField(auto_now=True)
    validated = fields.BooleanField(default=False, blank=False)

    def __str__(self):
        return str(self.phone_number)

    def can_send_sms(self):
        return SMSTokenBucket.has_tokens(self)


class SMS(models.Model):
    phone_number = models.ForeignKey('phones.PhoneNumber', on_delete=models.CASCADE, editable=False)
    code = fields.CharField(max_length=8, editable=False)
    created = fields.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = str(secrets.randbelow(100000000)).zfill(8)