from django.db import models
from django.utils.translation import ugettext_lazy as _


class Operation(models.Model):
    name = models.CharField(_("Nom"))

    voting_question = models.CharField("Question soumise au vote", blank=True)
    ask_contact_information = models.BooleanField("Demander une information de contact")

    display_count = models.BooleanField("Afficher le nombre de participants")
