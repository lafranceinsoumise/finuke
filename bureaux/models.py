import string
import uuid as uuid
from secrets import choice

from finuke.model_mixins import TimestampedModel
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import fields
from django.urls import reverse


class LoginLink(TimestampedModel):
    uuid = fields.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operator = models.ForeignKey('BureauOperator', on_delete=models.CASCADE, related_name='login_links')
    valid = models.BooleanField("Valide", default=True)

    def get_absolute_url(self):
        return reverse('login', args=[str(self.uuid)])

    class Meta:
        verbose_name = 'lien de connexion'
        verbose_name_plural = 'liens de connexions'


class BureauOperator(TimestampedModel):
    email = fields.EmailField("Adresse email", unique=True)
    active = fields.BooleanField("Compte actif", default=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'président⋅e de bureaux de vote'
        verbose_name_plural = 'président⋅e⋅s de bureaux de votes'


def new_assistant_code():
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(choice(alphabet) for i in range(8))


class BureauQueryset(models.QuerySet):
    def open_only(self):
        return self.filter(end_time__isnull=True)

    def closed_only(self):
        return self.filter(end_time__isnull=False)


class Bureau(models.Model):
    objects = BureauQueryset.as_manager()

    operator = models.ForeignKey('BureauOperator', on_delete=models.CASCADE, related_name='bureaux',
                                 verbose_name='président⋅e du bureau')
    operator = models.ForeignKey('BureauOperator', on_delete=models.PROTECT, related_name='bureaux',
                                 verbose_name='opérateur du bureau')
    place = fields.CharField("Lieu", max_length=255)
    start_time = fields.DateTimeField("Heure de d'ouverture du bureau", auto_now_add=True, editable=False)
    end_time = fields.DateTimeField("Heure de fermeture du bureau", blank=True, null=True, editable=False)
    result1_yes = fields.IntegerField("Bulletins inscrit⋅e⋅s : oui", blank=True, null=True)
    result1_no = fields.IntegerField("Bulletins inscrit⋅e⋅s : non", blank=True, null=True)
    result1_blank = fields.IntegerField("Bulletins inscrit⋅e⋅s : blancs", blank=True, null=True)
    result1_null = fields.IntegerField("Bulletins inscrit⋅e⋅s : nuls", blank=True, null=True)
    result2_yes = fields.IntegerField("Bulletins non-inscrit⋅e⋅s : oui", blank=True, null=True)
    result2_no = fields.IntegerField("Bulletins non-inscrit⋅e⋅s : non", blank=True, null=True)
    result2_blank = fields.IntegerField("Bulletins non-inscrit⋅e⋅s : blancs", blank=True, null=True)
    result2_null = fields.IntegerField("Bulletins non-inscrit⋅e⋅s : nuls", blank=True, null=True)
    results_comment = fields.TextField("Remarques", blank=True)

    assistant_code = fields.CharField("Code d'accès pour les assistant⋅e⋅s", default=new_assistant_code, max_length=10)

    def has_results(self):
        return self.result1_yes is not None

    def __str__(self):
        return f'Bureau {self.pk} "{self.place}" <{self.operator.email}>'

    class Meta:
        verbose_name = 'bureau de vote'
        verbose_name_plural = 'bureaux de vote'


class Operation(TimestampedModel):
    OPERATOR_LOGIN = "OPERATOR_LOGIN"
    START_BUREAU = "START_BUREAU"
    END_BUREAU = "END_BUREAU"
    SEND_RESULTS = "SEND_RESULTS"
    ASSISTANT_LOGIN = "ASSISTANT_LOGIN"
    PERSON_VOTE = "PERSON_VOTE"

    OPERATION_CHOICES = (
        (OPERATOR_LOGIN, "Connexion d'un⋅e président⋅e"),
        (START_BUREAU, "Ouverture de bureau"),
        (END_BUREAU, "Fermeture de bureau"),
        (SEND_RESULTS, "Envoi des résultats"),
        (ASSISTANT_LOGIN, "Connexion d'un⋅e assistant⋅e"),
        (PERSON_VOTE, "Validation du vote d'un⋅e personne inscrite sur les listes")
    )

    details = JSONField("Détails", editable=False)
    type = fields.CharField("Type d'opération", choices=OPERATION_CHOICES, max_length=255, editable=False)

    class Meta:
        verbose_name = 'opération sur un bureau'
        verbose_name_plural = 'opérations sur les bureaux'
