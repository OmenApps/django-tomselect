"""Admin configuration for the example app."""

from django.contrib import admin

from .models import Edition, Magazine, ModelFormTestModel


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    """Admin configuration for the Edition model."""


@admin.register(Magazine)
class MagazineAdmin(admin.ModelAdmin):
    """Admin configuration for the Magazine model."""


@admin.register(ModelFormTestModel)
class ModelFormTestModelAdmin(admin.ModelAdmin):
    """Admin configuration for the ModelFormTestModel model."""
