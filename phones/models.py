import secrets

from django.conf import settings
from django.db import models
from django.db.models import fields


class PhoneNumber(models.Model):
    phonenumber = fields.CharField('Numéro de mobile', max_length=30, editable=False, unique=True)
    created = fields.DateTimeField(auto_now_add=True)
    updated = fields.DateTimeField(auto_now=True)
    validated = fields.BooleanField(default=False, blank=False)
    sms_bucket = fields.IntegerField(default=settings.SMS_BUCKET_MAX)


class SMS(models.Model):
    phone = models.ForeignKey('phones.PhoneNumber', on_delete=models.CASCADE)
    code = fields.CharField(max_length=8, editable=False)
    created = fields.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = str(secrets.randbelow(100000000)).zfill(8)