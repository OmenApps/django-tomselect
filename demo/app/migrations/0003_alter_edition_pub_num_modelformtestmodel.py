# Generated by Django 4.2.5 on 2023-09-17 01:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0002_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="edition",
            name="pub_num",
            field=models.CharField(max_length=50, verbose_name="Publication Number"),
        ),
        migrations.CreateModel(
            name="ModelFormTestModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, verbose_name="Name")),
                (
                    "tomselect",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tomselect_test_model_instances",
                        to="app.edition",
                    ),
                ),
                (
                    "tomselect_multiple",
                    models.ManyToManyField(
                        blank=True, related_name="tomselect_multiple_test_model_instances", to="app.edition"
                    ),
                ),
                (
                    "tomselect_tabular",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tomselect_tabular_test_model_instances",
                        to="app.edition",
                    ),
                ),
                (
                    "tomselect_tabular_multiple_with_value_field",
                    models.ManyToManyField(
                        blank=True,
                        related_name="tomselect_tabular_multiple_with_value_field_test_model_instances",
                        to="app.edition",
                    ),
                ),
            ],
            options={
                "verbose_name": "Model Form Test Model",
                "verbose_name_plural": "Model Form Test Models",
            },
        ),
    ]
