"""Django TomSelect - Integrate Tom Select with Django forms.

This package provides form widgets, fields, and autocomplete views for integrating
Tom Select (a pure JavaScript autocomplete library) with Django applications.
"""

__all__ = [
    # Configuration
    "TomSelectConfig",
    "FilterSpec",
    "Const",
    "AllowedCSSFrameworks",
    "GLOBAL_DEFAULT_CONFIG",
    "merge_configs",
    # Plugin configurations
    "PluginCheckboxOptions",
    "PluginClearButton",
    "PluginDropdownHeader",
    "PluginDropdownFooter",
    "PluginDropdownInput",
    "PluginRemoveButton",
    # Autocomplete views
    "AutocompleteModelView",
    "AutocompleteIterablesView",
    "MAX_PAGE_SIZE",
    # Form fields
    "TomSelectChoiceField",
    "TomSelectMultipleChoiceField",
    "TomSelectModelChoiceField",
    "TomSelectModelMultipleChoiceField",
    # Widgets
    "TomSelectWidgetMixin",
    "TomSelectModelWidget",
    "TomSelectModelMultipleWidget",
    "TomSelectIterablesWidget",
    "TomSelectIterablesMultipleWidget",
    # Middleware
    "TomSelectMiddleware",
    "get_current_request",
    # Cache
    "PermissionCache",
    "cache_permission",
    "permission_cache",
]


def __getattr__(name: str):
    """Lazy import public API members to avoid circular imports during app loading."""
    # Configuration
    if name in (
        "TomSelectConfig",
        "FilterSpec",
        "Const",
        "AllowedCSSFrameworks",
        "GLOBAL_DEFAULT_CONFIG",
        "merge_configs",
        "PluginCheckboxOptions",
        "PluginClearButton",
        "PluginDropdownHeader",
        "PluginDropdownFooter",
        "PluginDropdownInput",
        "PluginRemoveButton",
    ):
        from django_tomselect import app_settings

        return getattr(app_settings, name)

    # Autocomplete views
    if name in ("AutocompleteModelView", "AutocompleteIterablesView", "MAX_PAGE_SIZE"):
        from django_tomselect import autocompletes

        return getattr(autocompletes, name)

    # Form fields
    if name in (
        "TomSelectChoiceField",
        "TomSelectMultipleChoiceField",
        "TomSelectModelChoiceField",
        "TomSelectModelMultipleChoiceField",
    ):
        from django_tomselect import forms

        return getattr(forms, name)

    # Widgets
    if name in (
        "TomSelectWidgetMixin",
        "TomSelectModelWidget",
        "TomSelectModelMultipleWidget",
        "TomSelectIterablesWidget",
        "TomSelectIterablesMultipleWidget",
    ):
        from django_tomselect import widgets

        return getattr(widgets, name)

    # Middleware
    if name in ("TomSelectMiddleware", "get_current_request"):
        from django_tomselect import middleware

        return getattr(middleware, name)

    # Cache
    if name in ("PermissionCache", "cache_permission", "permission_cache"):
        from django_tomselect import cache

        return getattr(cache, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
