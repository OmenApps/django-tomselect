"""Form widgets for the django-tomselect package."""

import json
from typing import Any, Callable, cast

from django import forms
from django.db.models import Model, QuerySet
from django.forms.renderers import BaseRenderer
from django.http import HttpRequest
from django.urls import NoReverseMatch, reverse, reverse_lazy
from django.utils.html import escape

from django_tomselect.app_settings import (
    GLOBAL_DEFAULT_CONFIG,
    AllowedCSSFrameworks,
    TomSelectConfig,
    merge_configs,
)
from django_tomselect.autocompletes import (
    AutocompleteIterablesView,
    AutocompleteModelView,
)
from django_tomselect.lazy_utils import LazyView
from django_tomselect.logging import package_logger
from django_tomselect.middleware import get_current_request
from django_tomselect.models import EmptyModel


class TomSelectWidgetMixin:
    """Mixin to provide methods and properties for all TomSelect widgets."""

    template_name: str = "django_tomselect/tomselect.html"

    def __init__(self, config: TomSelectConfig | dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Initialize shared TomSelect configuration.

        Args:
            config: a TomSelectConfig instance that provides all configuration options
            **kwargs: additional keyword arguments that override config values
        """
        # Merge user provided config with global defaults
        base_config: TomSelectConfig = GLOBAL_DEFAULT_CONFIG
        if config is not None:
            if isinstance(config, TomSelectConfig):
                final_config = merge_configs(base_config, config)
            elif isinstance(config, dict):
                final_config = merge_configs(base_config, TomSelectConfig(**config))
            else:
                raise TypeError(f"config must be a TomSelectConfig or a dictionary, not {type(config)}")
        else:
            final_config = base_config

        # Set common configuration attributes
        self.url: str = final_config.url
        self.value_field: str = final_config.value_field
        self.label_field: str = final_config.label_field
        self.filter_by: tuple[str, str] | None = final_config.filter_by
        self.exclude_by: tuple[str, str] | None = final_config.exclude_by
        self.use_htmx: bool = final_config.use_htmx

        self.minimum_query_length: int = final_config.minimum_query_length
        self.preload: bool = final_config.preload
        self.highlight: bool = final_config.highlight
        self.hide_selected: bool = final_config.hide_selected
        self.open_on_focus: bool = final_config.open_on_focus
        self.placeholder: str | None = final_config.placeholder
        self.max_items: int | None = final_config.max_items
        self.max_options: int | None = final_config.max_options
        self.css_framework: str = final_config.css_framework
        self.use_minified: bool = final_config.use_minified
        self.close_after_select: bool = final_config.close_after_select
        self.hide_placeholder: bool = final_config.hide_placeholder
        self.load_throttle: int = final_config.load_throttle
        self.loading_class: str = final_config.loading_class
        self.create: bool = final_config.create

        # Initialize plugin configurations
        self.plugin_checkbox_options: Any = final_config.plugin_checkbox_options
        self.plugin_clear_button: Any = final_config.plugin_clear_button
        self.plugin_dropdown_header: Any = final_config.plugin_dropdown_header
        self.plugin_dropdown_footer: Any = final_config.plugin_dropdown_footer
        self.plugin_dropdown_input: Any = final_config.plugin_dropdown_input
        self.plugin_remove_button: Any = final_config.plugin_remove_button

        # Explicitly set self.attrs from config.attrsto ensure attributes are properly passed to the widget
        if hasattr(final_config, "attrs") and final_config.attrs:
            self.attrs: dict[str, Any] = final_config.attrs.copy()

            # Handle 'render' attribute if present
            if "render" in self.attrs:
                render_data = self.attrs.pop("render")
                if isinstance(render_data, dict):
                    if "option" in render_data:
                        self.attrs["data_template_option"] = render_data["option"]
                    if "item" in render_data:
                        self.attrs["data_template_item"] = render_data["item"]

        # Allow kwargs to override any config values
        for key, value in kwargs.items():
            if hasattr(final_config, key):
                if isinstance(value, dict):
                    setattr(self, key, {**getattr(final_config, key), **value})
                else:
                    setattr(self, key, value)

        super().__init__(**kwargs)
        package_logger.debug("TomSelectWidgetMixin initialized.")

    def render(
        self,
        name: str,
        value: Any,
        attrs: dict[str, str] | None = None,
        renderer: BaseRenderer | None = None,
    ) -> str:
        """Render the widget."""
        context = self.get_context(name, value, attrs)

        package_logger.debug(
            "Rendering TomSelect widget with context: %s and template: %s using %s",
            context,
            self.template_name,
            renderer,
        )
        return self._render(self.template_name, context, renderer)

    def get_plugin_context(self) -> dict[str, Any]:
        """Get context for plugins."""
        plugins: dict[str, Any] = {}

        # Add plugin contexts only if plugin is enabled
        if self.plugin_clear_button:
            plugins["clear_button"] = self.plugin_clear_button.as_dict()

        if self.plugin_remove_button:
            plugins["remove_button"] = self.plugin_remove_button.as_dict()

        if self.plugin_dropdown_header:
            header = self.plugin_dropdown_header
            plugins["dropdown_header"] = {
                "title": str(header.title),
                "header_class": header.header_class,
                "title_row_class": header.title_row_class,
                "label_class": header.label_class,
                "value_field_label": str(header.value_field_label),
                "label_field_label": str(header.label_field_label),
                "label_col_class": header.label_col_class,
                "show_value_field": header.show_value_field,
                "extra_headers": list(header.extra_columns.values()),
                "extra_values": list(header.extra_columns.keys()),
            }

        if self.plugin_dropdown_footer:
            plugins["dropdown_footer"] = self.plugin_dropdown_footer.as_dict()

        # These plugins don't have additional config
        plugins["checkbox_options"] = bool(self.plugin_checkbox_options)
        plugins["dropdown_input"] = bool(self.plugin_dropdown_input)

        package_logger.debug("Plugins in use: %s", ", ".join(plugins.keys() if plugins else ["None"]))
        return plugins

    def get_lazy_view(self) -> LazyView | None:
        """Get lazy-loaded view for the TomSelect widget."""
        if not hasattr(self, "_lazy_view") or self._lazy_view is None:
            # Get current user from request if available
            request = self.get_current_request()
            user = getattr(request, "user", None) if request else None

            # Create LazyView with the URL from config
            self._lazy_view = LazyView(url_name=self.url, model=self.get_model(), user=user)
        return self._lazy_view

    def get_autocomplete_url(self) -> str:
        """Hook to specify the autocomplete URL."""
        # Special case for widgets that have a lazy view
        if hasattr(self, "get_lazy_view") and callable(getattr(self, "get_lazy_view")):
            lazy_view = self.get_lazy_view()
            if lazy_view:
                return lazy_view.get_url()

        # Standard case for direct URL resolution
        if not hasattr(self, "_cached_url"):
            package_logger.debug("Resolving URL for the first time: %s", self.url)
            try:
                self._cached_url = reverse(self.url)
                package_logger.debug("URL resolved in TomSelectWidgetMixin: %s", self._cached_url)
            except NoReverseMatch as e:
                package_logger.error("Could not reverse URL in TomSelectWidgetMixin:%s - %s", self.url, e)
                raise
        return self._cached_url

    def get_autocomplete_params(self) -> str:
        """Hook to specify additional autocomplete parameters."""
        params: list[str] = []
        autocomplete_view = self.get_autocomplete_view()
        if not autocomplete_view:
            return ""

        if params:
            return f"{'&'.join(params)}"
        return ""

    def build_attrs(self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build HTML attributes for the widget."""
        package_logger.debug("Building attrs with base_attrs: %s and extra_attrs: %s", base_attrs, extra_attrs)

        attrs = super().build_attrs(base_attrs, extra_attrs)

        package_logger.debug("attrs after `super` in build_attrs: %s", attrs)

        # Add required data attributes
        if self.url:
            attrs["data-autocomplete-url"] = reverse_lazy(self.url)
        if self.value_field:
            attrs["data-value-field"] = self.value_field
        if self.label_field:
            attrs["data-label-field"] = self.label_field

        if self.placeholder is not None:
            attrs["placeholder"] = self.placeholder

        # Mark as TomSelect widget for dynamic initialization
        attrs["data-tomselect"] = "true"

        # Ensure custom templates are JSON-encoded to prevent script injection
        if "data-template-option" in attrs:
            attrs["data-template-option"] = json.dumps(attrs["data-template-option"])
        if "data-template-item" in attrs:
            attrs["data-template-item"] = json.dumps(attrs["data-template-item"])

        # Handle 'render' attribute if present in the input attributes
        if "render" in attrs:
            render_data = attrs.pop("render")
            if isinstance(render_data, dict):
                if "option" in render_data:
                    attrs["data_template_option"] = render_data["option"]
                if "item" in render_data:
                    attrs["data_template_item"] = render_data["item"]

        package_logger.debug("Returning final attrs: %s and extra_attrs: %s", attrs, extra_attrs)
        return {**attrs, **(extra_attrs or {})}

    def get_url(self, view_name: str, view_type: str = "", **kwargs: Any) -> str:
        """Reverse the given view name and return the path.

        Fail silently with logger warning if the url cannot be reversed.
        """
        if view_name:
            try:
                return cast(str, reverse_lazy(view_name, **kwargs))
            except NoReverseMatch as e:
                package_logger.warning(
                    "TomSelectIterablesWidget requires a resolvable '%s' attribute. Original error: %s",
                    view_type,
                    e,
                )
        package_logger.warning("No URL provided for %s", view_type)
        return ""

    @property
    def media(self) -> forms.Media:
        """Return the media for rendering the widget."""
        if self.css_framework.lower() == AllowedCSSFrameworks.BOOTSTRAP4.value:
            css = {
                "all": [
                    (
                        "django_tomselect/vendor/tom-select/css/tom-select.bootstrap4.min.css"
                        if self.use_minified
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
                        if self.use_minified
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
                        if self.use_minified
                        else "django_tomselect/vendor/tom-select/css/tom-select.default.css"
                    ),
                    "django_tomselect/css/django-tomselect.css",
                ],
            }

        media = forms.Media(
            css=css,
            js=[
                (
                    "django_tomselect/js/django-tomselect.min.js"
                    if self.use_minified
                    else "django_tomselect/js/django-tomselect.js"
                )
            ],
        )
        package_logger.debug("Media loaded for TomSelectWidgetMixin.")
        return media


class TomSelectModelWidget(TomSelectWidgetMixin, forms.Select):
    """A Tom Select widget with model object choices."""

    def __init__(self, config: TomSelectConfig | dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Initialize widget with model-specific attributes."""
        self.model: type[Model] | None = None

        # Auth override settings
        self.allow_anonymous: bool = kwargs.pop("allow_anonymous", False)
        self.skip_authorization: bool = kwargs.pop("skip_authorization", False)

        # Initialize URL-related attributes
        self.show_list: bool = False
        self.show_detail: bool = False
        self.show_create: bool = False
        self.show_update: bool = False
        self.show_delete: bool = False
        self.create_field: str = ""
        self.create_filter: Callable | None = None
        self.create_with_htmx: bool = False

        super().__init__(config=config, **kwargs)

        # Update from config if provided
        if config:
            self.show_list = config.show_list
            self.show_detail = config.show_detail
            self.show_create = config.show_create
            self.show_update = config.show_update
            self.show_delete = config.show_delete
            self.create_field = config.create_field
            self.create_filter = config.create_filter
            self.create_with_htmx = config.create_with_htmx

    def get_current_request(self) -> HttpRequest | None:
        """Get the current request from thread-local storage."""
        return get_current_request()

    def get_autocomplete_context(self) -> dict[str, Any]:
        """Get context for autocomplete functionality."""
        autocomplete_context: dict[str, Any] = {
            "value_field": self.value_field or (self.model._meta.pk.name if self.model else ""),
            "label_field": self.label_field or getattr(self.model, "name_field", "name") if self.model else "",
            "is_tabular": bool(self.plugin_dropdown_header),
            "use_htmx": self.use_htmx,
            "search_lookups": self.get_search_lookups(),
            "autocomplete_url": self.get_autocomplete_url(),
            "autocomplete_params": self.get_autocomplete_params(),
        }
        package_logger.debug("Autocomplete context: %s in widget %s", autocomplete_context, self.__class__.__name__)
        return autocomplete_context

    def get_permissions_context(self, autocomplete_view: AutocompleteModelView) -> dict[str, Any]:
        """Get permission-related context for the widget."""
        request = self.get_current_request()

        context: dict[str, Any] = {
            "can_create": autocomplete_view.has_permission(request, "create"),
            "can_view": autocomplete_view.has_permission(request, "view"),
            "can_update": autocomplete_view.has_permission(request, "update"),
            "can_delete": autocomplete_view.has_permission(request, "delete"),
        }

        # Only show buttons/links for permitted actions
        context.update(
            {
                "show_create": self.show_create and context["can_create"],
                "show_list": self.show_list and context["can_view"],
                "show_detail": self.show_detail and context["can_view"],
                "show_update": self.show_update and context["can_update"],
                "show_delete": self.show_delete and context["can_delete"],
            }
        )

        package_logger.debug(
            "Permissions context: %s for model %s with %s in widget %s",
            context,
            self.model.__class__.__name__ if self.model else None,
            autocomplete_view,
            self.__class__.__name__,
        )
        return context

    def get_model_url_context(self, autocomplete_view: AutocompleteModelView) -> dict[str, Any]:
        """Get URL-related context for a model object.

        We retrieve & store list and create URLs, because they are model-specific, not instance-specific.
        These are used when initializing the widget, not when selecting an option.

        Instance-specific URLs are stored in the selected_options.
        """
        request = self.get_current_request()

        def is_valid_url(view: AutocompleteModelView, url_attr: str, permission: str) -> bool:
            """Check if the URL attribute is valid and if the user has permission."""
            return (
                hasattr(view, url_attr)
                and getattr(view, url_attr) not in ("", None)
                and view.has_permission(request, permission)
            )

        def get_url(view: AutocompleteModelView, url_attr: str, permission: str) -> str | None:
            """Get the URL for the specified attribute."""
            try:
                if is_valid_url(view, url_attr, permission):
                    return reverse(getattr(view, url_attr))
                else:
                    package_logger.warning("No valid %s URL available for model %s", url_attr, self.model)
                    return None
            except NoReverseMatch:
                package_logger.warning("Unable to reverse %s for model %s", url_attr, self.model)
                return None

        context: dict[str, Any] = {
            "view_list_url": get_url(autocomplete_view, "list_url", "view"),
            "view_create_url": get_url(autocomplete_view, "create_url", "create"),
        }
        package_logger.debug("Model URL context: %s", context)
        return context

    def get_instance_url_context(
        self, obj: Model | dict[str, Any], autocomplete_view: AutocompleteModelView
    ) -> dict[str, Any]:
        """Get URL-related context for a selected object."""
        request = self.get_current_request()
        urls: dict[str, str] = {}

        # If obj is a dictionary, it's likely a cleaned_data object
        if isinstance(obj, dict) or not hasattr(obj, "pk") or obj.pk is None:
            return {}

        if self.show_detail and autocomplete_view.detail_url and autocomplete_view.has_permission(request, "view"):
            try:
                urls["detail_url"] = escape(reverse(autocomplete_view.detail_url, args=[obj.pk]))
            except NoReverseMatch:
                package_logger.warning(
                    "Unable to reverse detail_url %s with pk %s",
                    autocomplete_view.detail_url,
                    obj.pk,
                )

        if self.show_update and autocomplete_view.update_url:
            try:
                urls["update_url"] = escape(reverse(autocomplete_view.update_url, args=[obj.pk]))
            except NoReverseMatch:
                package_logger.warning(
                    "Unable to reverse update_url %s with pk %s",
                    autocomplete_view.update_url,
                    obj.pk,
                )

        if self.show_delete and autocomplete_view.delete_url:
            try:
                urls["delete_url"] = escape(reverse(autocomplete_view.delete_url, args=[obj.pk]))
            except NoReverseMatch:
                package_logger.warning(
                    "Unable to reverse delete_url %s with pk %s",
                    autocomplete_view.delete_url,
                    obj.pk,
                )
        package_logger.debug("Instance URL context: %s", urls)
        return urls

    def get_context(self, name: str, value: Any, attrs: dict[str, str] | None = None) -> dict[str, Any]:
        """Get context for rendering the widget."""
        self.get_queryset()  # Ensure we have model info

        # Only include the global setup if it hasn't been rendered yet
        autocomplete_view = self.get_autocomplete_view()

        request = get_current_request()
        if not getattr(request, "_tomselect_global_rendered", False):
            package_logger.debug("Rendering global TomSelect setup.")
            self.template_name = "django_tomselect/tomselect_setup.html"
            if request:
                request._tomselect_global_rendered = True

        # Initial context without autocomplete view
        base_context: dict[str, Any] = {
            "widget": {
                "attrs": attrs or {},
                "close_after_select": self.close_after_select,
                "create": self.create,
                "create_field": self.create_field,
                "create_with_htmx": self.create_with_htmx,
                "hide_placeholder": self.hide_placeholder,
                "hide_selected": self.hide_selected,
                "highlight": self.highlight,
                "is_hidden": self.is_hidden,
                "is_multiple": False,
                "load_throttle": self.load_throttle,
                "loading_class": self.loading_class,
                "max_items": self.max_items,
                "max_options": self.max_options,
                "minimum_query_length": self.minimum_query_length,
                "name": name,
                "open_on_focus": self.open_on_focus,
                "placeholder": self.placeholder,
                "plugins": self.get_plugin_context(),
                "preload": self.preload,
                "required": self.is_required,
                "selected_options": [],
                "template_name": self.template_name,
                "value": value,
                **self.get_autocomplete_context(),
            }
        }

        # Add filter/exclude configuration
        if self.filter_by:
            dependent_field, dependent_field_lookup = self.filter_by
            base_context["widget"].update(
                {
                    "dependent_field": dependent_field,
                    "dependent_field_lookup": dependent_field_lookup,
                }
            )

        if self.exclude_by:
            exclude_field, exclude_field_lookup = self.exclude_by
            base_context["widget"].update(
                {
                    "exclude_field": exclude_field,
                    "exclude_field_lookup": exclude_field_lookup,
                }
            )

        # Handle model instances directly, if they are provided
        if value and hasattr(value, "_meta") and hasattr(value, "pk") and value.pk is not None:
            # Extract just the label field value
            label = getattr(value, self.label_field, None)
            if label is None:
                # Fallback to using get_label_for_object if available
                if autocomplete_view and hasattr(self, "get_label_for_object"):
                    label = self.get_label_for_object(value, autocomplete_view)
                else:
                    # If nothing else, use the model name instead of full string representation
                    label = str(getattr(value, "name", value))
            else:
                label = str(label)

            opt = {
                "value": str(value.pk),
                "label": escape(label),
            }

            # Add URLs if autocomplete_view is available
            if autocomplete_view and request and self.validate_request(request):
                for url_type in ["detail_url", "update_url", "delete_url"]:
                    url = self.get_instance_url_context(value, autocomplete_view).get(url_type)
                    if url:
                        opt[url_type] = escape(url)

            base_context["widget"]["selected_options"] = [opt]
            return base_context

        if not autocomplete_view or not request or not self.validate_request(request):
            package_logger.warning("Autocomplete view or request not available, returning base context")
            return base_context

        # Build full context with autocomplete view
        attrs = self.build_attrs(self.attrs, attrs)
        context: dict[str, Any] = {
            "widget": {
                **base_context["widget"],
                "attrs": attrs,
                **self.get_model_url_context(autocomplete_view),
            }
        }

        # Add permissions context
        context["widget"].update(self.get_permissions_context(autocomplete_view))

        # Add selected options if value is provided
        if value and value != "":
            selected: list[dict[str, Any]] = []

            # Value is an ID or list of IDs
            if self.get_queryset() is not None:
                selected_objects = self.get_queryset().filter(
                    pk__in=[value] if not isinstance(value, (list, tuple)) else value
                )

                for obj in selected_objects:
                    # Handle the case where obj is a dictionary (e.g., cleaned_data)
                    if isinstance(obj, dict):
                        opt: dict[str, str] = {
                            "value": str(obj.get("pk", "")),
                            "label": self.get_label_for_object(obj, autocomplete_view),
                        }
                    else:
                        opt = {
                            "value": str(obj.pk),
                            "label": self.get_label_for_object(obj, autocomplete_view),
                        }

                    # Safely add URLs with proper escaping
                    for url_type in ["detail_url", "update_url", "delete_url"]:
                        url = self.get_instance_url_context(obj, autocomplete_view).get(url_type)
                        if url:
                            opt[url_type] = escape(url)
                    selected.append(opt)

            context["widget"]["selected_options"] = selected

        return context

    def get_label_for_object(self, obj: Model | dict[str, Any], autocomplete_view: AutocompleteModelView) -> str:
        """Get the label for an object using the configured label field."""
        label_field = self.label_field
        try:
            # Handle dictionary case
            if isinstance(obj, dict) and label_field in obj:
                return escape(str(obj[label_field]))

            # Handle model instance - get the field value directly
            if hasattr(obj, label_field):
                label_value = getattr(obj, label_field)
                if label_value is not None:
                    return escape(str(label_value))

            # Check for prepare method on autocomplete view
            prepare_method = getattr(autocomplete_view, f"prepare_{label_field}", None)
            if prepare_method:
                label_value = prepare_method(obj)
                if label_value is not None:
                    return escape(str(label_value))

        except Exception as e:
            package_logger.error("Error getting label for object: %s", e)

        # Fallback to string representation
        return escape(str(obj))

    def get_model(self) -> type[Model] | None:
        """Get model from field's choices or queryset."""
        model = None
        if hasattr(self.choices, "queryset") and hasattr(self.choices.queryset, "model"):
            model = self.choices.queryset.model
        elif hasattr(self.choices, "model"):
            model = self.choices.model
        elif isinstance(self.choices, list) and self.choices:
            model = None
        package_logger.debug(
            "Model retrieved in %s: %s",
            self.__class__.__name__,
            model.__class__.__name__ if model else "None. Returning None",
        )
        return model or None

    def validate_request(self, request: Any) -> bool:
        """Validate that a request object is valid for permission checking."""
        if not request:
            package_logger.warning("Request object is missing.")
            return False

        # Check if request has required attributes and methods
        required_attributes = ["user", "method", "GET"]
        has_required = all(hasattr(request, attr) for attr in required_attributes)

        if not has_required:
            package_logger.warning("Request object is missing required attributes or methods.")
            return False

        # Verify user attribute has required auth methods
        if not hasattr(request, "user") or not hasattr(request.user, "is_authenticated"):
            package_logger.warning("Request object is missing user or is_authenticated method.")
            return False

        # Verify request methods are callable
        if not callable(getattr(request, "get_full_path", None)):
            package_logger.warning("Request object is missing get_full_path method.")
            return False

        package_logger.debug("Request object is valid.")
        return True

    def get_autocomplete_view(self) -> AutocompleteModelView | None:
        """Get instance of autocomplete view for accessing queryset and search_lookups."""
        lazy_view = self.get_lazy_view()
        if lazy_view:
            view = lazy_view.get_view()
            self.model = lazy_view.get_model()
            package_logger.debug("Lazy view model: %s", self.model)
            if not self.model:
                package_logger.warning("Model is not a valid Django model.")
                return None
            if not isinstance(view, AutocompleteModelView):
                package_logger.warning("View is not an instance of AutocompleteModelView.")
                return None

            # Add label_field to value_fields if needed
            if view and self.label_field and self.label_field not in view.value_fields:
                package_logger.warning(
                    "Label field '%s' is not in the autocomplete view's value_fields. "
                    "This may result in 'undefined' labels.",
                    self.label_field,
                )
                view.value_fields.append(self.label_field)

                # Check if it's a model field
                if self.model is not None:
                    try:
                        model_fields = [f.name for f in self.model._meta.fields]
                        is_related_field = "__" in self.label_field  # Allow double-underscore pattern

                        # If it's not a real field or relation, add to virtual_fields
                        if not (self.label_field in model_fields or is_related_field):
                            # Initialize virtual_fields if needed
                            if not hasattr(view, "virtual_fields"):
                                view.virtual_fields = []

                            # Add to virtual_fields
                            if self.label_field not in view.virtual_fields:
                                view.virtual_fields.append(self.label_field)
                                package_logger.info(
                                    "Label field '%s' added to virtual_fields: %s",
                                    self.label_field,
                                    view.virtual_fields,
                                )
                    except (AttributeError, TypeError):
                        # Cases where model is None or doesn't have _meta
                        pass

            return view
        return None

    def get_queryset(self) -> QuerySet | None:
        """Get queryset from autocomplete view."""
        try:
            lazy_view = self.get_lazy_view()
            if lazy_view:
                queryset = lazy_view.get_queryset()
                if queryset is not None:
                    return queryset

            # If we reach here, we need a fallback queryset
            model = self.get_model()

            # Explicitly check if model is a valid Django model with objects manager
            if model and hasattr(model, "_meta") and hasattr(model, "objects"):
                package_logger.warning("Using fallback empty queryset for model %s", model)
                return model.objects.none()

            package_logger.warning("Using EmptyModel.objects.none() as last resort")
            return EmptyModel.objects.none()
        except Exception as e:
            # If anything fails, return an empty EmptyModel queryset
            package_logger.error("Error in get_queryset: %s, falling back to EmptyModel.objects.none()", e)
            return EmptyModel.objects.none()

    def get_search_lookups(self) -> list[str]:
        """Get search lookups from autocomplete view."""
        autocomplete_view = self.get_autocomplete_view()
        if autocomplete_view:
            lookups = autocomplete_view.search_lookups
            package_logger.debug("Search lookups: %s", lookups)
            return lookups
        return []


class TomSelectModelMultipleWidget(TomSelectModelWidget, forms.SelectMultiple):
    """A TomSelect widget that allows multiple model object selection."""

    def get_context(self, name: str, value: Any, attrs: dict[str, str] | None = None) -> dict[str, Any]:
        """Get context for rendering the widget."""
        context = super().get_context(name, value, attrs)
        context["widget"]["is_multiple"] = True
        return context

    def build_attrs(self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["is-multiple"] = True
        return attrs


class TomSelectIterablesWidget(TomSelectWidgetMixin, forms.Select):
    """A Tom Select widget with iterables, TextChoices, or IntegerChoices choices."""

    def set_request(self, request: HttpRequest) -> None:
        """Iterables do not require a request object."""
        package_logger.warning("Request object is not required for iterables-type Tom Select widgets.")

    def get_autocomplete_context(self) -> dict[str, Any]:
        """Get context for autocomplete functionality."""
        autocomplete_context: dict[str, Any] = {
            "value_field": self.value_field,
            "label_field": self.label_field,
            "is_tabular": bool(self.plugin_dropdown_header),
            "use_htmx": self.use_htmx,
            "autocomplete_url": self.get_autocomplete_url(),
        }
        package_logger.debug("Autocomplete context: %s", autocomplete_context)
        return autocomplete_context

    def get_context(self, name: str, value: Any, attrs: dict[str, str] | None = None) -> dict[str, Any]:
        """Get context for rendering the widget."""
        # Only include the global setup if it hasn't been rendered yet
        request = get_current_request()
        if not getattr(request, "_tomselect_global_rendered", False):
            package_logger.debug("Rendering global TomSelect setup.")
            self.template_name = "django_tomselect/tomselect_setup.html"
            if request:
                request._tomselect_global_rendered = True

        attrs = self.build_attrs(self.attrs, attrs)
        context: dict[str, Any] = {
            "widget": {
                "attrs": attrs,
                "close_after_select": self.close_after_select,
                "create": self.create,
                "hide_placeholder": self.hide_placeholder,
                "hide_selected": self.hide_selected,
                "highlight": self.highlight,
                "is_hidden": self.is_hidden,
                "is_multiple": False,
                "load_throttle": self.load_throttle,
                "loading_class": self.loading_class,
                "max_items": self.max_items,
                "max_options": self.max_options,
                "minimum_query_length": self.minimum_query_length,
                "name": name,
                "open_on_focus": self.open_on_focus,
                "placeholder": self.placeholder,
                "plugins": self.get_plugin_context(),
                "preload": self.preload,
                "required": self.is_required,
                "template_name": self.template_name,
                "value": value,
                **self.get_autocomplete_context(),
            }
        }

        if value is not None:
            autocomplete_view = self.get_autocomplete_view()

            if autocomplete_view:
                # Handle different types of iterables
                if isinstance(autocomplete_view.iterable, type) and hasattr(autocomplete_view.iterable, "choices"):
                    # TextChoices/IntegerChoices
                    values = [value] if not isinstance(value, (list, tuple)) else value
                    selected: list[dict[str, str]] = []
                    for val in values:
                        for (
                            choice_value,
                            choice_label,
                        ) in autocomplete_view.iterable.choices:
                            if str(val) == str(choice_value):
                                selected.append({"value": str(val), "label": escape(str(choice_label))})
                                break
                        else:
                            selected.append({"value": str(val), "label": escape(str(val))})

                elif (
                    isinstance(autocomplete_view.iterable, (tuple, list))
                    and autocomplete_view.iterable
                    and isinstance(autocomplete_view.iterable[0], (tuple))
                ):
                    # Tuple iterables
                    values = [value] if not isinstance(value, (list, tuple)) else value
                    selected = []
                    for val in values:
                        for item in autocomplete_view.iterable:
                            if str(item) == str(val):
                                selected.append({"value": str(val), "label": escape(f"{item[0]}-{item[1]}")})
                                break
                        else:
                            selected.append({"value": str(val), "label": escape(str(val))})

                else:
                    # Simple iterables
                    values = [value] if not isinstance(value, (list, tuple)) else value
                    selected = [{"value": str(val), "label": escape(str(val))} for val in values]

                if selected:
                    context["widget"]["selected_options"] = selected

        return context

    def get_lazy_view(self) -> LazyView | None:
        """Get lazy-loaded view for the TomSelect iterables widget."""
        if not hasattr(self, "_lazy_view") or self._lazy_view is None:
            # Create LazyView with the URL from config
            self._lazy_view = LazyView(url_name=self.url)
        return self._lazy_view

    def get_autocomplete_view(self) -> AutocompleteIterablesView | None:
        """Get instance of autocomplete view for accessing iterable."""
        lazy_view = self.get_lazy_view()
        if lazy_view:
            view = lazy_view.get_view()

            # Check if view has get_iterable method
            if view and hasattr(view, "get_iterable"):
                return view

            # If not iterables view but has get_iterable, it's compatible
            if view and not issubclass(view.__class__, AutocompleteIterablesView):
                if not hasattr(view, "get_iterable"):
                    raise ValueError(
                        "The autocomplete view must either be a subclass of "
                        "AutocompleteIterablesView or implement get_iterable()"
                    )
            return view

        return None

    def get_iterable(self) -> list | tuple | type:
        """Get iterable or choices from autocomplete view."""
        autocomplete_view = self.get_autocomplete_view()
        if autocomplete_view:
            iterable = autocomplete_view.get_iterable()
            package_logger.debug("Iterable: %s", iterable)
            return iterable
        return []


class TomSelectIterablesMultipleWidget(TomSelectIterablesWidget, forms.SelectMultiple):
    """A TomSelect widget for multiple selection of iterables, TextChoices, or IntegerChoices."""

    def get_context(self, name: str, value: Any, attrs: dict[str, str] | None = None) -> dict[str, Any]:
        """Get context for rendering the widget."""
        context = super().get_context(name, value, attrs)
        context["widget"]["is_multiple"] = True
        return context

    def build_attrs(self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["is-multiple"] = True
        return attrs
