# Generated by Django 2.0.2 on 2018-03-05 17:11

import bureaux.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bureau',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lieu', models.CharField(max_length=255, verbose_name='Lieu')),
                ('start_time', models.DateTimeField(editable=False, verbose_name="Heure de d'ouverture du bureau")),
                ('end_time', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Heure de fermeture du bureau')),
                ('result1_yes', models.IntegerField(blank=True, null=True, verbose_name='Bulletins verts : oui')),
                ('result1_no', models.IntegerField(blank=True, null=True, verbose_name='Bulletins verts : non')),
                ('result1_blank', models.IntegerField(blank=True, null=True, verbose_name='Bulletins verts : blancs')),
                ('result1_null', models.IntegerField(blank=True, null=True, verbose_name='Bulletins verts : nuls')),
                ('result2_yes', models.IntegerField(blank=True, null=True, verbose_name='Bulletins rouge : oui')),
                ('result2_no', models.IntegerField(blank=True, null=True, verbose_name='Bulletins rouge : non')),
                ('result2_blank', models.IntegerField(blank=True, null=True, verbose_name='Bulletins rouge : blancs')),
                ('result2_null', models.IntegerField(blank=True, null=True, verbose_name='Bulletins rouge : nuls')),
                ('assistant_code', models.CharField(max_length=10, verbose_name="Code d'accès pour les assistant⋅e⋅s")),
            ],
        ),
        migrations.CreateModel(
            name='BureauOperator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, verbose_name='Adresse email')),
            ],
        ),
        migrations.CreateModel(
            name='LoginLink',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('valid', models.BooleanField(default=True, verbose_name='Valide')),
                ('operator', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='bureaux.BureauOperator')),
            ],
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Date et heure')),
                ('details', django.contrib.postgres.fields.jsonb.JSONField(editable=False, verbose_name='Détails')),
                ('type', models.CharField(choices=[('OPERATOR_LOGIN', "Connexion d'un⋅e opérateur⋅rice"), ('START_BUREAU', 'Ouverture de bureau'), ('END_BUREAU', 'Fermeture de bureau'), ('SEND_RESULTS', 'Envoi des résultats'), ('ASSISTANT_LOGIN', "Connexion d'un⋅e assistant⋅e"), ('PERSON_VOTE', "Validation du vote d'un⋅e personne inscrite sur les listes")], editable=False, max_length=255, verbose_name="Type d'opération")),
            ],
        ),
    ]
