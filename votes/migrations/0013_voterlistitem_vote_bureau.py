# Generated by Django 2.0.3 on 2018-03-07 13:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bureaux', '0006_bureau_results_comment'),
        ('votes', '0012_auto_20180305_1535'),
    ]

    operations = [
        migrations.AddField(
            model_name='voterlistitem',
            name='vote_bureau',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bureaux.Bureau'),
        ),
    ]
