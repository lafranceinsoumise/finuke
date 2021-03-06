# Generated by Django 2.0.3 on 2018-03-16 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('votes', '0021_auto_20180316_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unlockingrequest',
            name='status',
            field=models.CharField(blank=None, choices=[('re', 'À vérifier'), ('ok', 'Acceptée'), ('ko', 'Refusée'), ('du', 'Numéro déjà débloqué une fois'), ('in', "Le numéro transmis n'est pas un numéro valide"), ('un', "Le numéro n'a pas encore été utilisé"), ('ul', "Le numéro a été utilisé par quelqu'un de non-inscrit")], default='re', max_length=2, verbose_name='Statut de la demande'),
        ),
    ]
