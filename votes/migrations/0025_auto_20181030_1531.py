# Generated by Django 2.1.2 on 2018-10-30 14:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('votes', '0024_auto_20180924_1656'),
    ]

    operations = [
        migrations.CreateModel(
            name='Results',
            fields=[
            ],
            options={
                'verbose_name': 'Résultats',
                'verbose_name_plural': 'Résultats',
                'proxy': True,
                'indexes': [],
            },
            bases=('votes.voterlistitem',),
        ),
        migrations.AlterField(
            model_name='voterlistitem',
            name='vote_bureau',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bureaux.Bureau'),
        ),
    ]
