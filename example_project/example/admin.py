"""Admin configuration for the example app."""

from django.apps import apps
from django.contrib import admin


# Autoregister any models not already registered
class ListAdminMixin:
    """Mixin to automatically set list_display to all fields."""

    def __init__(self, model, admin_site):
        """Class initialization."""
        self.list_display = [field.name for field in model._meta.fields]
        super().__init__(model, admin_site)


for model in apps.get_app_config("example").get_models():
    admin_class = type("AdminClass", (ListAdminMixin, admin.ModelAdmin), {})
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        pass
