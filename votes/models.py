import secrets
import string

from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import fields

from votes.data.geodata import communes_names


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


class VoterListItem(models.Model):
    LIST_TYPE_CHOICES = (
        ('G', 'List générale'),
        ('E', 'Liste complémentaire européennes'),
        ('M', 'Liste complémentaire munucipales'),
    )

    CIVILITE_CHOICES = (
        ('M', 'M'),
        ('F', 'MME'),
    )

    def get_commune_display(self):
        return communes_names.get(self.commune, 'Commune inconnue')

    origin_file = fields.IntegerField('Identifiant du fichier d\'origine')
    file_line = fields.IntegerField('Numéro de la ligne dans le fichier d\'origine')
    list_type = fields.CharField('Type de liste', max_length=1, choices=LIST_TYPE_CHOICES)
    departement = fields.CharField('Code INSEE département', max_length=2, db_index=True)
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
    zipcode = fields.CharField('Code postal', max_length=10, blank=True)
    local_city_name = fields.CharField('Ville ou localité', max_length=255, blank=True)
    country = fields.CharField('Pays', max_length=255, blank=True)
