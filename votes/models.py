import secrets

from django.db import models
from django.db.models import fields


class Vote(models.Model):
    VOTE_CHOICES = (
        ('O', 'Oui'),
        ('N', 'Non'),
        ('B', 'Blanc'),
    )

    id = fields.CharField(max_length=32, primary_key=True)
    vote = fields.CharField(max_length=1, choices=VOTE_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = secrets.choice()
