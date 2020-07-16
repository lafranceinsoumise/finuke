# Generated by Django 2.1.2 on 2018-10-30 14:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bureaux', '0014_auto_20181030_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='bureauoperator',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Compte actif'),
        ),
        migrations.AlterField(
            model_name='bureau',
            name='operator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bureaux', to='bureaux.BureauOperator', verbose_name='opérateur du bureau'),
        ),
    ]