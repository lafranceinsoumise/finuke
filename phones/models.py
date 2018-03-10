import secrets

from django.conf import settings
from django.db import models
from django.db.models import fields
from phonenumber_field.modelfields import PhoneNumberField


def generate_code():
    return str(secrets.randbelow(100000000)).zfill(8)


class PhoneNumber(models.Model):
    phone_number = PhoneNumberField('Numéro de mobile', editable=False, unique=True)
    created = fields.DateTimeField(auto_now_add=True)
    updated = fields.DateTimeField(auto_now=True)
    validated = fields.BooleanField(default=False, blank=False)

    def __str__(self):
        return str(self.phone_number)


class SMS(models.Model):
    phone_number = models.ForeignKey('phones.PhoneNumber', on_delete=models.CASCADE, editable=False)
    code = fields.CharField(max_length=8, editable=False, default=generate_code)
    created = fields.DateTimeField(auto_now_add=True)
