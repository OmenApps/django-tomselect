"""Form widgets for the django-tomselect package."""
import copy
import logging

from django import forms
from django.core.cache import cache
from django.urls import NoReverseMatch, resolve, reverse_lazy

from .app_settings import (
    DJANGO_TOMSELECT_CSS_FRAMEWORK,
    DJANGO_TOMSELECT_CSS_FRAMEWORK_VERSION,
    DJANGO_TOMSELECT_MINIFIED,
    ProxyRequest,
)
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


class TomSelectWidget(forms.Select):
    """A Tom Select widget with model object choices."""

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

        # If config is provided, use it as the base configuration
        if config:
            if not isinstance(config, TomSelectConfig):
                raise ValueError("config must be an instance of TomSelectConfig")

            # Copy configuration from the config object
            self.url = config.url
            self.listview_url = config.listview_url
            self.create_url = config.create_url
            self.update_url = config.update_url
            self.value_field = config.value_field
            self.label_field = config.label_field
            self.create_field = config.create_field
            self.filter_by = config.filter_by
            self.use_htmx = config.use_htmx
            self.css_framework = config.css_framework
            self.css_framework_version = config.css_framework_version

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
            self.url = kwargs.pop('url', 'autocomplete')
            self.listview_url = kwargs.pop('listview_url', '')
            self.create_url = kwargs.pop('create_url', '')
            self.update_url = kwargs.pop('update_url', '')
            self.value_field = kwargs.pop('value_field', '')
            self.label_field = kwargs.pop('label_field', '')
            self.create_field = kwargs.pop('create_field', '')
            self.filter_by = kwargs.pop('filter_by', ())
            self.use_htmx = kwargs.pop('use_htmx', False)
            self.css_framework = kwargs.pop('css_framework', DJANGO_TOMSELECT_CSS_FRAMEWORK)
            self.css_framework_version = kwargs.pop('css_framework_version', DJANGO_TOMSELECT_CSS_FRAMEWORK_VERSION)

            # Initialize plugin configurations with defaults or from kwargs
            self.general_config = kwargs.pop('general_config', GeneralConfig())
            self.plugin_checkbox_options = kwargs.pop('plugin_checkbox_options', PluginCheckboxOptions())
            self.plugin_clear_button = kwargs.pop('plugin_clear_button', PluginClearButton())
            self.plugin_dropdown_header = kwargs.pop('plugin_dropdown_header', PluginDropdownHeader())
            self.plugin_dropdown_footer = kwargs.pop('plugin_dropdown_footer', PluginDropdownFooter())
            self.plugin_dropdown_input = kwargs.pop('plugin_dropdown_input', PluginDropdownInput())
            self.plugin_remove_button = kwargs.pop('plugin_remove_button', PluginRemoveButton())

        # Allow kwargs to override any config values
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.template_name = "django_tomselect/select.html"
        super().__init__(**kwargs)

    def get_context(self, name, value, attrs):
        """Get the context for rendering the widget."""
        self.get_queryset()

        context = super().get_context(name, value, attrs)

        self.value_field = self.value_field or self.model._meta.pk.name  # pylint: disable=W0212
        self.label_field = self.label_field or getattr(self.model, "name_field", "name")

        context["widget"]["value_field"] = self.value_field
        context["widget"]["label_field"] = self.label_field

        context["widget"]["is_tabular"] = False
        context["widget"]["use_htmx"] = self.use_htmx

        context["widget"]["search_lookups"] = self.get_search_lookups()
        context["widget"]["autocomplete_url"] = self.get_autocomplete_url()
        context["widget"]["listview_url"] = self.get_listview_url()
        context["widget"]["create_url"] = self.get_create_url()
        context["widget"]["update_url"] = self.get_update_url()

        context["widget"]["general_config"] = self.general_config.as_dict()
        context["widget"]["plugins"] = {}
        context["widget"]["plugins"]["clear_button"] = (
            self.plugin_clear_button.as_dict() if self.plugin_clear_button else None
        )
        context["widget"]["plugins"]["remove_button"] = (
            self.plugin_remove_button.as_dict() if self.plugin_remove_button else None
        )

        if self.plugin_dropdown_header:
            context["widget"]["is_tabular"] = True
            context["widget"]["plugins"]["dropdown_header"] = self.plugin_dropdown_header.as_dict()

            # Update context with the headers and values for the extra columns
            if isinstance(self.plugin_dropdown_header.extra_columns, dict):
                context["widget"]["plugins"]["dropdown_header"]["extra_headers"] = [
                    *self.plugin_dropdown_header.extra_columns.values()
                ]
                context["widget"]["plugins"]["dropdown_header"]["extra_values"] = [
                    *self.plugin_dropdown_header.extra_columns.keys()
                ]

        if self.plugin_dropdown_footer:
            context["widget"]["plugins"]["dropdown_footer"] = self.plugin_dropdown_footer.as_dict()

        # These context objects have no attributes, so we set them to True or False
        #   depending on whether they are provided or not
        context["widget"]["plugins"]["checkbox_options"] = True if self.plugin_checkbox_options else False
        context["widget"]["plugins"]["dropdown_input"] = True if self.plugin_dropdown_input else False

        return context

    def optgroups(self, name, value, attrs=None):
        """Return a list of optgroups for this widget, only querying for selected model objects."""
        selected_choices = [str(c) for c in value if c]
        all_choices = copy.copy(self.choices)

        if not selected_choices:
            # If there are no selected choices, skip querying and return empty groups
            return super().optgroups(name, value, attrs)

        # Cache key based on the widget's unique characteristics
        cache_key = f"{self.model._meta.label_lower}_selected_choices_{hash(frozenset(selected_choices))}"  # pylint: disable=W0212

        # Try to retrieve the queryset from the cache
        cached_queryset = cache.get(cache_key)

        if cached_queryset is None:
            # Fetch all selected objects in a single query if not in cache
            try:
                queryset = self.get_queryset().filter(pk__in=selected_choices)
                cache.set(cache_key, list(queryset), timeout=300)  # Cache the queryset for 5 minutes
            except ValueError:
                logger.info("ValueError in optgroups for selected_choices: %s", selected_choices)
                queryset = self.get_queryset().none()  # Return an empty queryset on error
        else:
            queryset = cached_queryset

        # Only include the filtered queryset in the choices
        self.choices.queryset = queryset

        # Generate the optgroups using the filtered queryset
        results = super().optgroups(name, value, attrs)

        # Restore all choices to avoid side effects on other widgets
        self.choices = all_choices

        return results

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

    def get_bootstrap_media(self):
        """Return the media for rendering the widget with Bootstrap."""
        if self.css_framework_version == 4:
            return forms.Media(
                css={
                    "all": [
                        "django_tomselect/vendor/tom-select/css/tom-select.bootstrap4.css",
                        "django_tomselect/css/django-tomselect.css",
                    ],
                },
                js=[
                    (
                        "django_tomselect/js/django-tomselect.min.js"
                        if DJANGO_TOMSELECT_MINIFIED
                        else "django_tomselect/js/django-tomselect.js"
                    )
                ],
            )
        return forms.Media(
            css={
                "all": [
                    "django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.css",
                    "django_tomselect/css/django-tomselect.css",
                ],
            },
            js=[
                (
                    "django_tomselect/js/django-tomselect.min.js"
                    if DJANGO_TOMSELECT_MINIFIED
                    else "django_tomselect/js/django-tomselect.js"
                )
            ],
        )

    @property
    def media(self):
        """Return the media for rendering the widget."""
        if self.css_framework.lower() == "bootstrap":
            return self.get_bootstrap_media()

        return forms.Media(
            css={
                "all": [
                    "django_tomselect/vendor/tom-select/css/tom-select.css",
                    "django_tomselect/css/django-tomselect.css",
                ],
            },
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

    def get_context(self, name, value, attrs):
        """Get the context for rendering the widget."""
        context = super().get_context(name, value, attrs)

        # Update context to ensure the max_items matches user-provided value
        context["widget"]["is_multiple"] = True
        return context

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)  # noqa
        attrs["is-multiple"] = True
        return attrs
