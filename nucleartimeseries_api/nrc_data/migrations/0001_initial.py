# Generated by Django 5.2.3 on 2025-07-01 01:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ReactorStatus",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("report_date", models.DateField()),
                ("unit", models.CharField(max_length=30)),
                ("power", models.IntegerField()),
                ("changed", models.BooleanField(default=False)),
                (
                    "region",
                    models.CharField(
                        choices=[
                            ("I", "Region I"),
                            ("II", "Region II"),
                            ("III", "Region III"),
                            ("IV", "Region IV"),
                        ],
                        max_length=3,
                    ),
                ),
            ],
            options={
                "unique_together": {("report_date", "unit")},
            },
        ),
    ]
