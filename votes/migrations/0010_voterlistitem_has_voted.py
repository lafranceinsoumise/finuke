# Generated by Django 2.0.2 on 2018-03-01 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('votes', '0009_trigram_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='voterlistitem',
            name='has_voted',
            field=models.BooleanField(default=False, verbose_name='La personne a voté'),
        ),
    ]
