# Generated by Django 4.2.1 on 2023-05-24 12:34

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Edition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, verbose_name="Edition")),
                ("year", models.CharField(max_length=50, verbose_name="Year")),
                ("pages", models.CharField(max_length=50, verbose_name="Pages")),
                ("pub_num", models.CharField(max_length=50, verbose_name="Publication Number")),
            ],
            options={
                "verbose_name": "Edition",
                "verbose_name_plural": "Editions",
            },
        ),
    ]
