# Generated by Django 2.0.2 on 2018-03-06 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bureaux', '0005_auto_20180306_1509'),
    ]

    operations = [
        migrations.AddField(
            model_name='bureau',
            name='results_comment',
            field=models.TextField(blank=True, verbose_name='Remarques'),
        ),
    ]
