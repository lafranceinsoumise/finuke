# Generated by Django 2.0.2 on 2018-02-27 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('votes', '0007_auto_20180226_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voterlistitem',
            name='commune',
            field=models.CharField(db_index=True, max_length=5, verbose_name='Code INSEE commune'),
        ),
        migrations.AlterField(
            model_name='voterlistitem',
            name='departement',
            field=models.CharField(db_index=True, max_length=2, verbose_name='Code INSEE département'),
        ),
    ]
