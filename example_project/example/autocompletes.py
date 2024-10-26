"""Autocomplete views for the example app."""

from django_tomselect.views import AutocompleteView

from .models import Edition, Magazine


class DemoEditionAutocompleteView(AutocompleteView):
    """Autocomplete that returns all Edition objects."""

    model = Edition
    search_lookups = [
        "pages__icontains",
        "year__icontains",
        "pub_num__icontains",
    ]

    def has_add_permission(self, request):  # pylint: disable=W0613
        """Return True if the user has permission to add a new object (always True in this example app)."""
        return True  # no auth in this example app

    def get_queryset(self):
        """Return a queryset of objects that match the search parameters and filters."""
        queryset = super().get_queryset().all()
        return queryset


class DemoEditionDependentAutocompleteView(AutocompleteView):
    """Autocomplete that returns only Edition objects that contain the number 3 in one of the search lookups."""

    model = Edition
    search_lookups = [
        "pages__icontains",
        "year__icontains",
        "pub_num__icontains",
    ]

    def has_add_permission(self, request):  # pylint: disable=W0613
        """Return True if the user has permission to add a new object (always True in this example app)."""
        return True  # no auth in this example app

    def get_queryset(self):
        """Return a queryset of objects that match the search parameters and filters."""
        queryset = super().get_queryset().filter(name__icontains="3")
        return queryset


class DemoMagazineAutocompleteView(AutocompleteView):
    """Autocomplete that returns all Magazine objects."""

    model = Magazine

    def has_add_permission(self, request):  # pylint: disable=W0613
        """Return True if the user has permission to add a new object (always True in this example app)."""
        return True  # no auth in this example app

    def get_queryset(self):
        """Return a queryset of objects that match the search parameters and filters."""
        queryset = super().get_queryset().all()
        return queryset
