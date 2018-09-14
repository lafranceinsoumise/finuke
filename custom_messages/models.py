from django.contrib.messages.constants import INFO, SUCCESS, WARNING, ERROR
from django.db import models


class PersistantMessage(models.Model):
    levels = (
        (INFO, "Info"),
        (SUCCESS, "Success"),
        (WARNING, "Warning"),
        (ERROR, "Error"),
    )

    level = models.PositiveSmallIntegerField(default=INFO, choices=levels)
    text = models.TextField(blank=False)
    enabled = models.BooleanField(default=True)
    url_name = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'annonce'
