# Generated by Django 4.2 on 2025-05-29 08:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchhistory',
            name='forecast_type',
        ),
    ]
