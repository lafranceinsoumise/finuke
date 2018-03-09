from django.contrib.messages.constants import INFO
from django.db import models


class PersistantMessage(models.Model):
    level = models.PositiveSmallIntegerField(default=INFO)
    text = models.TextField(blank=False)
    enabled = models.BooleanField(default=True)
