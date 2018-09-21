import secrets
import string
from collections import namedtuple

from django.db import models

from finuke.model_mixins import TimestampedModel
from bureaux.models import Bureau
from votes.data.geodata import communes_names
from phonenumber_field.modelfields import PhoneNumberField


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

    id = models.CharField(max_length=32, primary_key=True, editable=False, default=generate_vote_id)
    operation = models.ForeignKey('operations.Operation', on_delete=models.PROTECT, null=False,)
    vote = models.CharField(max_length=1, choices=VOTE_CHOICES, editable=False)
    with_list = models.BooleanField(editable=False)

    class Meta:
        verbose_name = 'Vote exprimé'
        verbose_name_plural = 'Votes exprimés'


class Participation(TimestampedModel):
    operation = models.ForeignKey('operations.Operation', on_delete=models.PROTECT, null=False)
    voter = models.ForeignKey('VoterListItem', on_delete=models.CASCADE, null=False, related_name='participations')
    contact_phone = PhoneNumberField('Numéro de téléphone', null=False, blank=True)
    contact_email = models.EmailField('Adresse email', null=False, blank=True)
    bureau = models.ForeignKey(Bureau, on_delete=models.CASCADE, null=True)


class FEVoterListItem(models.Model):
    email = models.EmailField('Adresse email donnée au consulat', unique=True)
    first_names = models.CharField('Prénoms', max_length=255)
    last_name = models.CharField('Nom', max_length=255)
    has_voted = models.BooleanField('Déjà voté', default=False, editable=False)

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

    origin_file = models.IntegerField('Identifiant du fichier d\'origine')
    file_line = models.IntegerField('Numéro de la ligne dans le fichier d\'origine')
    list_type = models.CharField('Type de liste', max_length=1, choices=LIST_TYPE_CHOICES)
    departement = models.CharField('Code INSEE département', max_length=5, db_index=True)
    commune = models.CharField('Code INSEE commune', max_length=5, db_index=True)
    civilite = models.CharField('Civilité', max_length=1, choices=CIVILITE_CHOICES, blank=True)
    last_name = models.CharField('Nom de naissance', max_length=255)
    use_last_name = models.CharField('Nom d\'usage', max_length=255, blank=True)
    first_names = models.CharField('Prénoms', max_length=255)
    birth_date = models.DateField('Date de naissance', blank=True, null=True)
    birth_city_name = models.CharField('Ville de naissance', max_length=255, blank=True)
    birth_departement_name = models.CharField('Département de naissance', max_length=255, blank=True)
    birth_country_name = models.CharField('Pays de naissance', max_length=255, blank=True)
    nationality = models.CharField('Nationalité', max_length=255, blank=True)
    address1 = models.CharField('Complément d\'adresse 1', max_length=255, blank=True)
    address2 = models.CharField('Complément d\'adresse 2', max_length=255, blank=True)
    street_number = models.CharField('Numéro de voie', max_length=255, blank=True)
    street_type = models.CharField('Type de voie', max_length=255, blank=True)
    street_label = models.CharField('Nom de la voie', max_length=255, blank=True)
    place_name = models.CharField('Lieu-dit', max_length=255, blank=True)
    zipcode = models.CharField('Code postal', max_length=255, blank=True)
    local_city_name = models.CharField('Ville ou localité', max_length=255, blank=True)
    country = models.CharField('Pays', max_length=255, blank=True)

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