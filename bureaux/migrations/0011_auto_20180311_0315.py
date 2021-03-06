# Generated by Django 2.0.3 on 2018-03-11 03:15

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bureaux', '0010_auto_20180310_1730'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginlink',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bureauoperator',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='operation',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
