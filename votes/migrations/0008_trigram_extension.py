# Generated by Django 2.0.2 on 2018-02-26 17:50
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('votes', '0010_auto_20180227_1037'),
    ]

    operations = [
        TrigramExtension(),
    ]
