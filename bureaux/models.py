import string
import uuid as uuid
from secrets import choice

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import fields


class LoginLink(models.Model):
    uuid = fields.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operator = models.ForeignKey('BureauOperator', on_delete=models.CASCADE, related_name='login_links')
    valid = models.BooleanField("Valide", default=True)


class BureauOperator(models.Model):
    email = fields.EmailField("Adresse email")
    created = fields.DateTimeField("Date d'import", auto_now_add=True)

    def __str__(self):
        return self.email


def new_assistant_code():
    alphabet = string.ascii_letters + string.digits
    return ''.join(choice(alphabet) for i in range(10))


class Bureau(models.Model):
    operator = models.ForeignKey('BureauOperator', on_delete=models.CASCADE, related_name='bureaux')
    place = fields.CharField("Lieu", max_length=255)
    start_time = fields.DateTimeField("Heure de d'ouverture du bureau", auto_now_add=True, editable=False)
    end_time = fields.DateTimeField("Heure de fermeture du bureau", blank=True, null=True, editable=False)
    result1_yes = fields.IntegerField("Bulletins verts : oui", blank=True, null=True)
    result1_no = fields.IntegerField("Bulletins verts : non", blank=True, null=True)
    result1_blank = fields.IntegerField("Bulletins verts : blancs", blank=True, null=True)
    result1_null = fields.IntegerField("Bulletins verts : nuls", blank=True, null=True)
    result2_yes = fields.IntegerField("Bulletins oranges : oui", blank=True, null=True)
    result2_no = fields.IntegerField("Bulletins oranges : non", blank=True, null=True)
    result2_blank = fields.IntegerField("Bulletins oranges : blancs", blank=True, null=True)
    result2_null = fields.IntegerField("Bulletins oranges : nuls", blank=True, null=True)
    results_comment = fields.TextField("Remarques", blank=True)

    assistant_code = fields.CharField("Code d'accès pour les assistant⋅e⋅s", default=new_assistant_code, max_length=10)

    def has_results(self):
        return self.result1_yes is not None


class Operation(models.Model):
    OPERATOR_LOGIN = "OPERATOR_LOGIN"
    START_BUREAU = "START_BUREAU"
    END_BUREAU = "END_BUREAU"
    SEND_RESULTS = "SEND_RESULTS"
    ASSISTANT_LOGIN = "ASSISTANT_LOGIN"
    PERSON_VOTE = "PERSON_VOTE"

    OPERATION_CHOICES = (
        (OPERATOR_LOGIN, "Connexion d'un⋅e opérateur⋅rice"),
        (START_BUREAU, "Ouverture de bureau"),
        (END_BUREAU, "Fermeture de bureau"),
        (SEND_RESULTS, "Envoi des résultats"),
        (ASSISTANT_LOGIN, "Connexion d'un⋅e assistant⋅e"),
        (PERSON_VOTE, "Validation du vote d'un⋅e personne inscrite sur les listes")
    )

    created = fields.DateTimeField("Date et heure", auto_now_add=True, editable=False)
    details = JSONField("Détails", editable=False)
    type = fields.CharField("Type d'opération", choices=OPERATION_CHOICES, max_length=255, editable=False)
