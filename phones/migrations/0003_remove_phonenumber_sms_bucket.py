# Generated by Django 2.0.2 on 2018-03-01 19:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('phones', '0002_auto_20180216_1538'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='phonenumber',
            name='sms_bucket',
        ),
    ]
