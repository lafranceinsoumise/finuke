import secrets
import string

from django.db import models
from django.db.models import fields


class Vote(models.Model):
    YES = 'Y'
    NO = 'N'
    BLANK = 'B'

    VOTE_CHOICES = (
        (YES, 'Oui'),
        (NO, 'Non'),
        (BLANK, 'Blanc'),
    )

    id = fields.CharField(max_length=32, primary_key=True, editable=False)
    vote = fields.CharField(max_length=1, choices=VOTE_CHOICES, editable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        alphabet = string.ascii_letters + string.digits
        self.id = ''.join(secrets.choice(alphabet) for i in range(32))
