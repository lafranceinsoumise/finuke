# Generated by Django 2.0.2 on 2018-03-05 17:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bureaux', '0002_auto_20180305_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loginlink',
            name='operator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='login_links', to='bureaux.BureauOperator'),
        ),
    ]