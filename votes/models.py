import secrets
import string
from collections import namedtuple

from django.db import models
from django.db.models import fields, ForeignKey
from phonenumber_field.modelfields import PhoneNumberField

from finuke.model_mixins import TimestampedModel
from bureaux.models import Bureau
from votes.data.geodata import communes_names


def generate_vote_id():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(32))


class Vote(TimestampedModel):
    YES = 'Y'
    NO = 'N'
    BLANK = 'B'

    VOTE_CHOICES = (
        (YES, 'Oui'),
        (NO, 'Non'),
        (BLANK, 'Blanc'),
    )

    id = fields.CharField(max_length=32, primary_key=True, editable=False, default=generate_vote_id)
    vote = fields.CharField(max_length=1, choices=VOTE_CHOICES, editable=False)
    with_list = fields.BooleanField(editable=False)

    class Meta:
        verbose_name = 'Vote exprimé'
        verbose_name_plural = 'Votes exprimés'


class VoterInformation(models.Model):
    voter = models.OneToOneField('VoterListItem', models.CASCADE)
    phone = PhoneNumberField('Numéro de téléphone', blank=True)
    email = models.EmailField('Adresse email', blank=True)


class FEVoterListItem(models.Model):
    email = fields.EmailField('Adresse email donnée au consulat', unique=True)
    first_names = fields.CharField('Prénoms', max_length=255)
    last_name = fields.CharField('Nom', max_length=255)
    has_voted = fields.BooleanField('Déjà voté', default=False, editable=False)

    class Meta:
        verbose_name = "électeur Français de l'étranger"
        verbose_name_plural = "électeurs Français de l'étranger"


class VoterListItem(models.Model):
    LIST_TYPE_CHOICES = (
        ('G', 'Liste générale'),
        ('E', 'Liste complémentaire européennes'),
        ('M', 'Liste complémentaire municipales'),
    )

    CIVILITE_CHOICES = (
        ('M', 'M'),
        ('F', 'MME'),
    )

    VOTE_STATUS_NONE = "N"
    VOTE_STATUS_ONLINE = "O"
    VOTE_STATUS_PHYSICAL = "P"
    VOTED_CHOICES = (
        (VOTE_STATUS_NONE, 'Pas voté'),
        (VOTE_STATUS_ONLINE, 'Vote en ligne'),
        (VOTE_STATUS_PHYSICAL, 'Vote physique')
    )

    def get_commune_display(self):
        return communes_names.get(self.commune, 'Commune inconnue')

    vote_status = fields.CharField('Statut du vote', max_length=1, choices=VOTED_CHOICES, default=VOTE_STATUS_NONE)
    vote_bureau = ForeignKey(Bureau, on_delete=models.CASCADE, null=True)

    origin_file = fields.IntegerField('Identifiant du fichier d\'origine')
    file_line = fields.IntegerField('Numéro de la ligne dans le fichier d\'origine')
    list_type = fields.CharField('Type de liste', max_length=1, choices=LIST_TYPE_CHOICES)
    departement = fields.CharField('Code INSEE département', max_length=5, db_index=True)
    commune = fields.CharField('Code INSEE commune', max_length=5, db_index=True)
    civilite = fields.CharField('Civilité', max_length=1, choices=CIVILITE_CHOICES, blank=True)
    last_name = fields.CharField('Nom de naissance', max_length=255)
    use_last_name = fields.CharField('Nom d\'usage', max_length=255, blank=True)
    first_names = fields.CharField('Prénoms', max_length=255)
    birth_date = fields.DateField('Date de naissance', blank=True, null=True)
    birth_city_name = fields.CharField('Ville de naissance', max_length=255, blank=True)
    birth_departement_name = fields.CharField('Département de naissance', max_length=255, blank=True)
    birth_country_name = fields.CharField('Pays de naissance', max_length=255, blank=True)
    nationality = fields.CharField('Nationalité', max_length=255, blank=True)
    address1 = fields.CharField('Complément d\'adresse 1', max_length=255, blank=True)
    address2 = fields.CharField('Complément d\'adresse 2', max_length=255, blank=True)
    street_number = fields.CharField('Numéro de voie', max_length=255, blank=True)
    street_type = fields.CharField('Type de voie', max_length=255, blank=True)
    street_label = fields.CharField('Nom de la voie', max_length=255, blank=True)
    place_name = fields.CharField('Lieu-dit', max_length=255, blank=True)
    zipcode = fields.CharField('Code postal', max_length=255, blank=True)
    local_city_name = fields.CharField('Ville ou localité', max_length=255, blank=True)
    country = fields.CharField('Pays', max_length=255, blank=True)

    def get_full_name(self):
        return '{}, {}'.format(self.last_name, self.first_names)

    def __str__(self):
        return f"{self.get_full_name()} ({self.departement})"

    HomonymyKey = namedtuple('HomonymyKey', ['first_names', 'last_name', 'commune'])

    def homonymy_key(self):
        return self.HomonymyKey(self.first_names.upper(), self.last_name.upper(), self.commune)

    class Meta:
        verbose_name = 'électeur inscrit'
        verbose_name_plural = 'électeurs inscrits'


class UnlockingRequest(models.Model):
    email = models.EmailField('adresse email')
    raw_number = models.CharField('Numéro (brut)', max_length=40)
    requester = models.CharField('Demandeur', max_length=255)
    declared_voter = models.CharField('Votant déclaré', max_length=255)

    phone_number = models.ForeignKey('phones.PhoneNumber', on_delete=models.CASCADE, null=True)
    voter = models.ForeignKey('VoterListItem', on_delete=models.CASCADE, null=True)

    STATUS_REVIEW = 're'
    STATUS_OK = 'ok'
    STATUS_KO = 'ko'
    STATUS_DUPLICATE = 'du'
    STATUS_INVALID_NUMBER = 'in'
    STATUS_UNUSED = 'un'
    STATUS_UNLISTED = 'ul'
    STATUS_IGNORE = 'ig'
    STATUS_CHOICES = (
        (STATUS_REVIEW, 'À vérifier'),
        (STATUS_OK, 'Acceptée'),
        (STATUS_KO, 'Refusée'),
        (STATUS_DUPLICATE, 'Numéro déjà débloqué une fois'),
        (STATUS_INVALID_NUMBER, 'Le numéro transmis n\'est pas un numéro valide'),
        (STATUS_UNUSED, "Le numéro n'a pas encore été utilisé"),
        (STATUS_UNLISTED, "Le numéro a été utilisé par quelqu'un de non-inscrit"),
        (STATUS_IGNORE, "Demande à ignore (pas de réponse)")
    )

    status = models.CharField('Statut de la demande', max_length=2, choices=STATUS_CHOICES, blank=None,
                              default=STATUS_REVIEW)

    answer_sent = models.BooleanField('Message parti ?', editable=False, default=False)

    class Meta:
        verbose_name = "demande de déblocage d'un numéro de téléphone"
        verbose_name_plural = 'demandes de déblocages de numéros de téléphone'