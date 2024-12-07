"""Form widgets for the django-tomselect package."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from django import forms
from django.urls import NoReverseMatch, resolve, reverse_lazy

from .app_settings import DJANGO_TOMSELECT_CSS_FRAMEWORK, DJANGO_TOMSELECT_MINIFIED, AllowedCSSFrameworks, ProxyRequest
from .configs import (
    GeneralConfig,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class TomSelectContext:
    """Context manager for TomSelect widget rendering."""

    widget: Any
    name: str
    value: Any
    attrs: Dict[str, str]

    def get_autocomplete_context(self) -> Dict[str, Any]:
        """Get context for autocomplete functionality."""
        return {
            "value_field": self.widget.value_field or self.widget.model._meta.pk.name,
            "label_field": self.widget.label_field or getattr(self.widget.model, "name_field", "name"),
            "is_tabular": bool(self.widget.plugin_dropdown_header),
            "use_htmx": self.widget.use_htmx,
            "search_lookups": self.widget.get_search_lookups(),
            "autocomplete_url": self.widget.get_autocomplete_url(),
            "listview_url": self.widget.get_listview_url(),
            "create_url": self.widget.get_create_url(),
            "update_url": self.widget.get_update_url(),
        }

    def get_plugin_context(self) -> Dict[str, Any]:
        """Get context for plugins."""
        plugins = {}

        # Add plugin contexts only if plugin is enabled
        if self.widget.plugin_clear_button:
            plugins["clear_button"] = self.widget.plugin_clear_button.as_dict()

        if self.widget.plugin_remove_button:
            plugins["remove_button"] = self.widget.plugin_remove_button.as_dict()

        if self.widget.plugin_dropdown_header:
            header_dict = self.widget.plugin_dropdown_header.as_dict()
            if isinstance(self.widget.plugin_dropdown_header.extra_columns, dict):
                header_dict["extra_headers"] = list(self.widget.plugin_dropdown_header.extra_columns.values())
                header_dict["extra_values"] = list(self.widget.plugin_dropdown_header.extra_columns.keys())
            plugins["dropdown_header"] = header_dict

        if self.widget.plugin_dropdown_footer:
            plugins["dropdown_footer"] = self.widget.plugin_dropdown_footer.as_dict()

        # These plugins don't have additional config
        plugins["checkbox_options"] = bool(self.widget.plugin_checkbox_options)
        plugins["dropdown_input"] = bool(self.widget.plugin_dropdown_input)

        return plugins

    def get_context(self) -> Dict[str, Any]:
        """Get the complete context for widget rendering."""
        context = {
            "widget": {
                "name": self.name,
                "value": self.value,
                "attrs": self.attrs,
                "is_multiple": False,
                **self.get_autocomplete_context(),
                "general_config": self.widget.general_config.as_dict(),
                "plugins": self.get_plugin_context(),
            }
        }
        return context


class TomSelectWidget(forms.Select):
    """A Tom Select widget with model object choices."""

    template_name = "django_tomselect/select.html"

    def __init__(  # pylint: disable=R0913
        self,
        config=None,
        **kwargs,
    ):
        """Instantiate a TomSelectWidget widget.

        Args:
            config: a TomSelectConfig instance that provides all configuration options
            **kwargs: additional keyword arguments that override config values
        """
        self.model = None  # Placeholder for the model, which we will get from the queryset

        # If config is provided, use it as base configuration
        if config:
            if not isinstance(config, TomSelectConfig):
                raise ValueError("config must be an instance of TomSelectConfig")

            # Copy configuration from config object
            self.url = config.url
            self.listview_url = config.listview_url
            self.create_url = config.create_url
            self.update_url = config.update_url
            self.value_field = config.value_field
            self.label_field = config.label_field
            self.create_field = config.create_field
            self.filter_by = config.filter_by
            self.exclude_by = config.exclude_by
            self.use_htmx = config.use_htmx
            self.css_framework = config.css_framework

            # Copy plugin configurations
            self.general_config = config.general_config
            self.plugin_checkbox_options = config.plugin_checkbox_options
            self.plugin_clear_button = config.plugin_clear_button
            self.plugin_dropdown_header = config.plugin_dropdown_header
            self.plugin_dropdown_footer = config.plugin_dropdown_footer
            self.plugin_dropdown_input = config.plugin_dropdown_input
            self.plugin_remove_button = config.plugin_remove_button

        else:
            # If no config provided, initialize with defaults or kwargs
            self.url = kwargs.pop("url", "autocomplete")
            self.listview_url = kwargs.pop("listview_url", "")
            self.create_url = kwargs.pop("create_url", "")
            self.update_url = kwargs.pop("update_url", "")
            self.value_field = kwargs.pop("value_field", "")
            self.label_field = kwargs.pop("label_field", "")
            self.create_field = kwargs.pop("create_field", "")
            self.filter_by = kwargs.pop("filter_by", ())
            self.exclude_by = kwargs.pop("exclude_by", ())
            self.use_htmx = kwargs.pop("use_htmx", False)
            self.css_framework = kwargs.pop("css_framework", DJANGO_TOMSELECT_CSS_FRAMEWORK)

            # Initialize plugin configurations with defaults or from kwargs
            self.general_config = kwargs.pop("general_config", GeneralConfig())
            self.plugin_checkbox_options = kwargs.pop("plugin_checkbox_options", PluginCheckboxOptions())
            self.plugin_clear_button = kwargs.pop("plugin_clear_button", PluginClearButton())
            self.plugin_dropdown_header = kwargs.pop("plugin_dropdown_header", PluginDropdownHeader())
            self.plugin_dropdown_footer = kwargs.pop("plugin_dropdown_footer", PluginDropdownFooter())
            self.plugin_dropdown_input = kwargs.pop("plugin_dropdown_input", PluginDropdownInput())
            self.plugin_remove_button = kwargs.pop("plugin_remove_button", PluginRemoveButton())

        # Allow kwargs to override any config values
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.template_name = "django_tomselect/select.html"
        super().__init__(**kwargs)

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None, renderer=None) -> str:
        """Render the widget."""
        context = self.get_context(name, value, attrs)
        return self._render(self.template_name, context, renderer)

    def get_context(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get context for rendering the widget using the context manager."""
        self.get_queryset()  # Ensure we have model info

        attrs = self.build_attrs(self.attrs, attrs)
        context_manager = TomSelectContext(self, name, value, attrs or {})
        context = context_manager.get_context()

        # Add filter_by configuration
        if hasattr(self, "filter_by") and self.filter_by:
            dependent_field, dependent_field_lookup = self.filter_by
            context["widget"]["dependent_field"] = dependent_field
            context["widget"]["dependent_field_lookup"] = dependent_field_lookup

        # Add exclude_by configuration
        if hasattr(self, "exclude_by") and self.exclude_by:
            exclude_field, exclude_field_lookup = self.exclude_by
            context["widget"]["exclude_field"] = exclude_field
            context["widget"]["exclude_field_lookup"] = exclude_field_lookup

        if value:
            # If we have an initial queryset, use it to get the selected options
            if self.get_queryset() is not None:
                selected_objects = self.get_queryset().filter(
                    pk__in=[value] if not isinstance(value, (list, tuple)) else value
                )

                # Add selected options data to context
                context["widget"]["selected_options"] = [
                    {
                        "value": str(obj.pk),
                        "label": str(obj),
                    }
                    for obj in selected_objects
                ]

        return context

    @staticmethod
    def get_url(view_name, view_type: str = "", **kwargs):
        """Reverse the given view name and return the path.

        Fail silently with logger warning if the url cannot be reversed.
        """
        if view_name:
            try:
                return reverse_lazy(view_name, **kwargs)
            except NoReverseMatch as e:
                logger.warning("TomSelectWidget requires a resolvable '%s' attribute. Original error: %s", view_type, e)
        return ""

    def get_autocomplete_url(self):
        """Hook to specify the autocomplete URL."""
        return self.get_url(self.url, "autocomplete URL")

    def get_create_url(self):
        """Hook to specify the URL to the model's 'create' view."""
        return self.get_url(self.create_url, "create URL")

    def get_listview_url(self):
        """Hook to specify the URL the model's listview."""
        return self.get_url(self.listview_url, "listview URL")

    def get_update_url(self):
        """Hook to specify the URL to the model's 'change' view."""
        return self.get_url(self.update_url, "update URL", args=["_pk_"])

    def get_model(self):
        """Gets the model from the field's QuerySet."""
        return self.choices.queryset.model

    def get_autocomplete_view(self):
        """Gets an instance of the autocomplete view, so we can use its queryset and search_lookups."""
        self.model = self.get_model()

        # Create a ProxyRequest that we can pass to the view to obtain its queryset
        proxy_request = ProxyRequest(model=self.model)

        autocomplete_view = resolve(self.get_autocomplete_url()).func.view_class()
        autocomplete_view.setup(model=self.model, request=proxy_request)

        return autocomplete_view

    def get_queryset(self):
        """Gets the queryset from the specified autocomplete view."""
        autocomplete_view = self.get_autocomplete_view()
        return autocomplete_view.get_queryset()

    def get_search_lookups(self):
        """Gets the search lookups from the specified autocomplete view."""
        autocomplete_view = self.get_autocomplete_view()
        return autocomplete_view.search_lookups

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)

        # Add required data attributes
        if self.url:
            attrs["data-autocomplete-url"] = reverse_lazy(self.url)
        if self.value_field:
            attrs["data-value-field"] = self.value_field
        if self.label_field:
            attrs["data-label-field"] = self.label_field
        if self.create_url:
            attrs["data-create-url"] = reverse_lazy(self.create_url)
        if self.listview_url:
            attrs["data-listview-url"] = reverse_lazy(self.listview_url)

        if self.general_config and self.general_config.placeholder is not None:
            attrs["placeholder"] = self.general_config.placeholder

        return {**attrs, **(extra_attrs or {})}

    @property
    def media(self):
        """Return the media for rendering the widget."""

        if self.css_framework.lower() == AllowedCSSFrameworks.BOOTSTRAP4.value:
            css = {
                "all": [
                    (
                        "django_tomselect/vendor/tom-select/css/tom-select.bootstrap4.min.css"
                        if DJANGO_TOMSELECT_MINIFIED
                        else "django_tomselect/vendor/tom-select/css/tom-select.bootstrap4.css"
                    ),
                    "django_tomselect/css/django-tomselect.css",
                ],
            }
        elif self.css_framework.lower() == AllowedCSSFrameworks.BOOTSTRAP5.value:
            css = {
                "all": [
                    (
                        "django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.min.css"
                        if DJANGO_TOMSELECT_MINIFIED
                        else "django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.css"
                    ),
                    "django_tomselect/css/django-tomselect.css",
                ],
            }
        else:
            css = {
                "all": [
                    (
                        "django_tomselect/vendor/tom-select/css/tom-select.default.min.css"
                        if DJANGO_TOMSELECT_MINIFIED
                        else "django_tomselect/vendor/tom-select/css/tom-select.default.css"
                    ),
                    "django_tomselect/css/django-tomselect.css",
                ],
            }

        return forms.Media(
            css=css,
            js=[
                (
                    "django_tomselect/js/django-tomselect.min.js"
                    if DJANGO_TOMSELECT_MINIFIED
                    else "django_tomselect/js/django-tomselect.js"
                )
            ],
        )


class TomSelectMultipleWidget(TomSelectWidget, forms.SelectMultiple):
    """A TomSelect widget that allows multiple selection."""

    def get_context(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get the context for rendering the widget."""
        context = super().get_context(name, value, attrs)

        # Update context to reflect multiple selection
        context["widget"]["is_multiple"] = True
        return context

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)  # noqa
        attrs["is-multiple"] = True
        return attrs
