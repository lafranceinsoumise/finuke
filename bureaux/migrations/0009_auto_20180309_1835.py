# Generated by Django 2.0.3 on 2018-03-09 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bureaux', '0008_bureauoperator_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bureauoperator',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='Adresse email'),
        ),
    ]
