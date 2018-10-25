# Generated by Django 2.1.2 on 2018-10-25 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bureaux', '0012_auto_20180924_1433'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bureau',
            name='result1_blank',
            field=models.IntegerField(blank=True, null=True, verbose_name='Bulletins inscrit⋅e⋅s : blancs'),
        ),
        migrations.AlterField(
            model_name='bureau',
            name='result1_no',
            field=models.IntegerField(blank=True, null=True, verbose_name='Bulletins inscrit⋅e⋅s : non'),
        ),
        migrations.AlterField(
            model_name='bureau',
            name='result1_null',
            field=models.IntegerField(blank=True, null=True, verbose_name='Bulletins inscrit⋅e⋅s : nuls'),
        ),
        migrations.AlterField(
            model_name='bureau',
            name='result1_yes',
            field=models.IntegerField(blank=True, null=True, verbose_name='Bulletins inscrit⋅e⋅s : oui'),
        ),
        migrations.AlterField(
            model_name='bureau',
            name='result2_blank',
            field=models.IntegerField(blank=True, null=True, verbose_name='Bulletins non-inscrit⋅e⋅s : blancs'),
        ),
        migrations.AlterField(
            model_name='bureau',
            name='result2_no',
            field=models.IntegerField(blank=True, null=True, verbose_name='Bulletins non-inscrit⋅e⋅s : non'),
        ),
        migrations.AlterField(
            model_name='bureau',
            name='result2_null',
            field=models.IntegerField(blank=True, null=True, verbose_name='Bulletins non-inscrit⋅e⋅s : nuls'),
        ),
        migrations.AlterField(
            model_name='bureau',
            name='result2_yes',
            field=models.IntegerField(blank=True, null=True, verbose_name='Bulletins non-inscrit⋅e⋅s : oui'),
        ),
    ]
