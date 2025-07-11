# Generated by Django 5.2.3 on 2025-07-01 01:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nrc_data", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reactorstatus",
            name="down_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reactorstatus",
            name="reason",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="reactorstatus",
            name="scrams",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
