import secrets

from django.conf import settings
from django.db import models
from django.db.models import fields
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class PhoneNumber(models.Model):
    phone_number = PhoneNumberField('Numéro de mobile', editable=False, unique=True)
    created = fields.DateTimeField(auto_now_add=True)
    updated = fields.DateTimeField(auto_now=True)
    validated = fields.BooleanField(default=False, blank=False)
    sms_bucket = fields.IntegerField(default=settings.SMS_BUCKET_MAX)
    _bucket_updated = None

    def __str__(self):
        return str(self.phone_number)

    @property
    def bucket_updated(self):
        return self._bucket_updated or self.updated

    @bucket_updated.setter
    def bucket_updated(self, value):
        self._bucket_updated = value

    def update_bucket(self):
        new_tokens = int((timezone.now() - self.bucket_updated).total_seconds() / settings.SMS_BUCKET_INTERVAL)
        self.sms_bucket = min(
            settings.SMS_BUCKET_MAX,
            self.sms_bucket + new_tokens
        )

        if new_tokens:
            self.bucket_updated = timezone.now()


class SMS(models.Model):
    phone_number = models.ForeignKey('phones.PhoneNumber', on_delete=models.CASCADE, editable=False)
    code = fields.CharField(max_length=8, editable=False)
    created = fields.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = str(secrets.randbelow(100000000)).zfill(8)