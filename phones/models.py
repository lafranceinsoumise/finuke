import secrets

from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from finuke.model_mixins import TimestampedModel


def generate_code():
    return str(secrets.randbelow(1000000)).zfill(6)


class PhoneNumber(TimestampedModel):
    phone_number = PhoneNumberField('Numéro de mobile', editable=False, unique=True)
    updated = models.DateTimeField(auto_now=True)
    validated = models.BooleanField(default=False, null=False)
    bypass_code = models.BooleanField(default=False, null=False)

    voter = models.OneToOneField('votes.VoterListItem', on_delete=models.PROTECT, null=True)

    def __str__(self):
        return str(self.phone_number)

    class Meta:
        verbose_name = 'numéro de téléphone'
        verbose_name_plural = 'numéros de téléphone'


class SMS(TimestampedModel):
    phone_number = models.ForeignKey('phones.PhoneNumber', on_delete=models.CASCADE, editable=False)
    code = models.CharField(max_length=8, editable=False, default=generate_code)

    class Meta:
        verbose_name = 'SMS'
        verbose_name_plural = 'SMS'