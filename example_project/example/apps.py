"""App configuration for the django-tomselect example app."""

from django.apps import AppConfig


class ExampleConfig(AppConfig):
    """App configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "example_project.example"
