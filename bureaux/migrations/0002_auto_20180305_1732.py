# Generated by Django 2.0.2 on 2018-03-05 17:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bureaux', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bureau',
            name='operator',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='bureaux', to='bureaux.BureauOperator'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='loginlink',
            name='operator',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='login_links', to='bureaux.BureauOperator'),
        ),
    ]
