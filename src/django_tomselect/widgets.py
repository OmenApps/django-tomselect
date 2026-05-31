"""Form widgets for the django-tomselect package."""

__all__ = [
    "TomSelectWidgetMixin",
    "TomSelectModelWidget",
    "TomSelectModelMultipleWidget",
    "TomSelectIterablesWidget",
    "TomSelectIterablesMultipleWidget",
    "TomSelectTokenWidget",
]

import html
import json
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, cast

from django import forms
from django.db.models import Model, Q, QuerySet
from django.forms.renderers import BaseRenderer
from django.http import HttpRequest
from django.urls import NoReverseMatch
from django.utils.html import escape

from django_tomselect.app_settings import (
    GLOBAL_DEFAULT_CONFIG,
    AllowedCSSFrameworks,
    FilterSpec,
    StrOrPromise,
    TomSelectConfig,
    merge_configs,
)
from django_tomselect.autocompletes import (
    AutocompleteIterablesView,
    AutocompleteModelView,
)
from django_tomselect.constants import EXCLUDEBY_VAR, FILTERBY_VAR, PAGE_VAR, SEARCH_VAR
from django_tomselect.lazy_utils import LazyView
from django_tomselect.logging import get_logger
from django_tomselect.middleware import get_current_request
from django_tomselect.models import EmptyModel
from django_tomselect.utils import safe_reverse, safe_reverse_lazy

logger = get_logger(__name__)

if TYPE_CHECKING:
    _MixinBase = forms.Select
else:
    _MixinBase = object


class TomSelectWidgetMixin(_MixinBase):
    """Mixin to provide methods and properties for all TomSelect widgets."""

    template_name: str = "django_tomselect/tomselect.html"

    @staticmethod
    def _resolve_widget_config(config: TomSelectConfig | dict[str, Any] | None) -> TomSelectConfig:
        """Resolve config input to a merged TomSelectConfig for the widget.

        Args:
            config: The config input - None, TomSelectConfig, or dict.

        Returns:
            A fully merged TomSelectConfig.

        Raises:
            TypeError: If config is not a recognized type.
        """
        base_config: TomSelectConfig = GLOBAL_DEFAULT_CONFIG
        if config is None:
            return base_config
        if isinstance(config, TomSelectConfig):
            return merge_configs(base_config, config)
        if isinstance(config, dict):
            return merge_configs(base_config, TomSelectConfig(**config))
        raise TypeError(f"config must be a TomSelectConfig or a dictionary, not {type(config)}")

    @staticmethod
    def _process_render_attrs(attrs: dict[str, Any]) -> None:
        """Extract render option/item templates from an attrs dict, in place.

        Pops the 'render' key if present and converts to data_template_option
        and data_template_item keys.
        """
        if "render" in attrs:
            render_data = attrs.pop("render")
            if isinstance(render_data, dict):
                if "option" in render_data:
                    attrs["data_template_option"] = render_data["option"]
                if "item" in render_data:
                    attrs["data_template_item"] = render_data["item"]

    def __init__(self, config: TomSelectConfig | dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Initialize shared TomSelect configuration."""
        final_config = self._resolve_widget_config(config)

        # URL and field config
        self.url: str = final_config.url
        self.value_field: str = final_config.value_field
        self.label_field: str = final_config.label_field
        # Store normalized filter lists
        self.filters: list[FilterSpec] = final_config.get_normalized_filters()
        self.excludes: list[FilterSpec] = final_config.get_normalized_excludes()
        # Keep for backwards compatibility
        self.filter_by = final_config.filter_by
        self.exclude_by = final_config.exclude_by
        self.use_htmx: bool = final_config.use_htmx

        # Behavior config
        self.minimum_query_length: int = final_config.minimum_query_length
        self.preload: Literal["focus"] | bool = final_config.preload
        self.highlight: bool = final_config.highlight
        self.hide_selected: bool = final_config.hide_selected
        self.open_on_focus: bool = final_config.open_on_focus
        self.placeholder: StrOrPromise | None = final_config.placeholder
        self.max_items: int | None = final_config.max_items
        self.max_options: int | None = final_config.max_options
        self.css_framework: str | AllowedCSSFrameworks = final_config.css_framework
        self.use_minified: bool = final_config.use_minified
        self.close_after_select: bool | None = final_config.close_after_select
        self.hide_placeholder: bool | None = final_config.hide_placeholder
        self.load_throttle: int = final_config.load_throttle
        self.loading_class: str = final_config.loading_class
        self.create: bool = final_config.create

        # Plugin configurations
        self.plugin_checkbox_options: Any = final_config.plugin_checkbox_options
        self.plugin_clear_button: Any = final_config.plugin_clear_button
        self.plugin_dropdown_header: Any = final_config.plugin_dropdown_header
        self.plugin_dropdown_footer: Any = final_config.plugin_dropdown_footer
        self.plugin_dropdown_input: Any = final_config.plugin_dropdown_input
        self.plugin_remove_button: Any = final_config.plugin_remove_button

        # Explicitly set self.attrs from config.attrs to ensure attributes are properly passed to the widget
        if hasattr(final_config, "attrs") and final_config.attrs:
            self.attrs: dict[str, Any] = final_config.attrs.copy()
            self._process_render_attrs(self.attrs)

        # Allow kwargs to override any config values
        for key, value in kwargs.items():
            if hasattr(final_config, key):
                if isinstance(value, dict) and isinstance(getattr(final_config, key), dict):
                    setattr(self, key, {**getattr(final_config, key), **value})
                else:
                    setattr(self, key, value)

        super().__init__(**kwargs)
        logger.debug("TomSelectWidgetMixin initialized.")

    def render(
        self,
        name: str,
        value: Any,
        attrs: dict[str, str] | None = None,
        renderer: BaseRenderer | None = None,
    ) -> str:
        """Render the widget."""
        context = self.get_context(name, value, attrs)

        logger.debug(
            "Rendering TomSelect widget with context: %s and template: %s using %s",
            context,
            self.template_name,
            renderer,
        )
        return str(self._render(self.template_name, context, renderer))

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

        logger.debug("Plugins in use: %s", ", ".join(plugins.keys() if plugins else ["None"]))
        return plugins

    def get_model(self) -> "type[Model] | None":
        """Get the model class. Overridden in subclasses."""
        return None

    def get_autocomplete_view(self) -> Any:
        """Get the autocomplete view. Overridden in subclasses."""
        return None

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
        if hasattr(self, "get_lazy_view") and callable(self.get_lazy_view):
            lazy_view = self.get_lazy_view()
            if lazy_view:
                return lazy_view.get_url()

        # Standard case for direct URL resolution
        if not hasattr(self, "_cached_url"):
            logger.debug("Resolving URL for the first time: %s", self.url)
            try:
                self._cached_url = safe_reverse(self.url)
                logger.debug("URL resolved in TomSelectWidgetMixin: %s", self._cached_url)
            except NoReverseMatch as e:
                logger.error("Could not reverse URL in TomSelectWidgetMixin: %s - %s", self.url, e)
                raise
        return self._cached_url

    def get_autocomplete_params(self) -> str:
        """Hook for subclasses to specify additional autocomplete query parameters.

        Override and return a URL-safe `&`-joined string (no leading `&`).
        """
        return ""

    def build_attrs(self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build HTML attributes for the widget."""
        logger.debug("Building attrs with base_attrs: %s and extra_attrs: %s", base_attrs, extra_attrs)

        attrs = super().build_attrs(base_attrs, extra_attrs)

        logger.debug("attrs after `super` in build_attrs: %s", attrs)

        # Add required data attributes
        if self.url:
            attrs["data-autocomplete-url"] = safe_reverse_lazy(self.url)
        if self.value_field:
            attrs["data-value-field"] = self.value_field
        if self.label_field:
            attrs["data-label-field"] = self.label_field

        if self.placeholder is not None:
            attrs["placeholder"] = self.placeholder

        # Auto-set aria-describedby for help text association
        if "aria-describedby" not in attrs:
            widget_id = attrs.get("id", "")
            if widget_id:
                attrs["aria-describedby"] = f"{widget_id}_helptext"

        # Mark as TomSelect widget for dynamic initialization
        attrs["data-tomselect"] = "true"

        # Ensure custom templates are JSON-encoded to prevent script injection
        if "data-template-option" in attrs:
            attrs["data-template-option"] = json.dumps(attrs["data-template-option"])
        if "data-template-item" in attrs:
            attrs["data-template-item"] = json.dumps(attrs["data-template-item"])

        # Handle 'render' attribute if present in the input attributes
        self._process_render_attrs(attrs)

        logger.debug("Returning final attrs: %s and extra_attrs: %s", attrs, extra_attrs)
        return {**attrs, **(extra_attrs or {})}

    def get_url(self, view_name: str, view_type: str = "", **kwargs: Any) -> str:
        """Reverse the given view name and return the path."""
        if not view_name:
            logger.warning("No URL provided for %s", view_type)
            return ""

        try:
            return cast(str, safe_reverse_lazy(view_name, **kwargs))
        except NoReverseMatch as e:
            logger.warning(
                "TomSelectWidget requires a resolvable '%s' attribute. Original error: %s",
                view_type,
                e,
            )
            return ""

    def get_current_request(self) -> HttpRequest | None:
        """Get the current request from thread-local storage."""
        return get_current_request()

    @property
    def media(self) -> forms.Media:
        """Return the media for rendering the widget."""
        css_paths = self._get_css_paths()
        js_path = (
            "django_tomselect/js/django-tomselect.min.js"
            if self.use_minified
            else "django_tomselect/js/django-tomselect.js"
        )

        media = forms.Media(
            css={"all": css_paths},
            js=[js_path],
        )
        logger.debug("Media loaded for TomSelectWidgetMixin.")
        return media

    def get_url_param_constants(self) -> dict[str, str]:
        """Get URL parameter constants for use in templates.

        Returns a dictionary of URL parameter names that can be used
        in JavaScript for building autocomplete request URLs.
        """
        return {
            "search_param": SEARCH_VAR,
            "filter_param": FILTERBY_VAR,
            "exclude_param": EXCLUDEBY_VAR,
            "page_param": PAGE_VAR,
        }

    def get_csp_nonce(self) -> str | None:
        """Get CSP nonce from the current request, if available.

        Supports django-csp (request.csp_nonce) and any middleware that sets
        request._csp_nonce or request.csp_nonce.
        """
        request = self.get_current_request()
        if not request:
            return None
        # django-csp >= 4.0 uses request.csp_nonce
        nonce = getattr(request, "csp_nonce", None)
        if not nonce:
            # Some setups use _csp_nonce
            nonce = getattr(request, "_csp_nonce", None)
        return nonce

    def _get_css_paths(self) -> list[str]:
        """Get CSS paths based on framework."""
        # Framework-specific paths
        framework = (
            self.css_framework.value
            if isinstance(self.css_framework, AllowedCSSFrameworks)
            else str(self.css_framework)
        )
        if framework.lower() == AllowedCSSFrameworks.BOOTSTRAP4.value:
            css = (
                "django_tomselect/vendor/tom-select/css/tom-select.bootstrap4.min.css"
                if self.use_minified
                else "django_tomselect/vendor/tom-select/css/tom-select.bootstrap4.css"
            )
        elif framework.lower() == AllowedCSSFrameworks.BOOTSTRAP5.value:
            css = (
                "django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.min.css"
                if self.use_minified
                else "django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.css"
            )
        else:
            css = (
                "django_tomselect/vendor/tom-select/css/tom-select.default.min.css"
                if self.use_minified
                else "django_tomselect/vendor/tom-select/css/tom-select.default.css"
            )

        paths = [css, "django_tomselect/css/django-tomselect.css"]
        # Append token-widget chrome only when this widget is a token widget.
        # Keeps _get_css_paths generic for the existing widgets.
        if getattr(self, "_token_widget", False):
            paths.append("django_tomselect/css/django-tomselect-token.css")
        return paths


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
        self.create_filter: str | Callable | None = None
        self.create_with_htmx: bool = False

        super().__init__(config=config, **kwargs)

        # Update from config if provided
        if config:
            config = config if isinstance(config, TomSelectConfig) else TomSelectConfig(**config)

            self.show_list = config.show_list
            self.show_detail = config.show_detail
            self.show_create = config.show_create
            self.show_update = config.show_update
            self.show_delete = config.show_delete
            self.create_field = config.create_field
            self.create_filter = config.create_filter
            self.create_with_htmx = config.create_with_htmx

    def get_autocomplete_context(self) -> dict[str, Any]:
        """Get context for autocomplete functionality."""
        model_pk_name = self.model._meta.pk.name if self.model else ""  # type: ignore[union-attr]
        model_label_field = getattr(self.model, "name_field", "name") if self.model else ""

        autocomplete_context: dict[str, Any] = {
            "value_field": self.value_field or model_pk_name,
            "label_field": self.label_field or model_label_field,
            "is_tabular": bool(self.plugin_dropdown_header),
            "use_htmx": self.use_htmx,
            "search_lookups": self.get_search_lookups(),
            "autocomplete_url": self.get_autocomplete_url(),
            "autocomplete_params": self.get_autocomplete_params(),
        }
        logger.debug("Autocomplete context: %s in widget %s", autocomplete_context, self.__class__.__name__)
        return autocomplete_context

    def get_permissions_context(self, autocomplete_view: AutocompleteModelView) -> dict[str, Any]:
        """Get permission-related context for the widget."""
        request = self.get_current_request()

        # Base permissions
        permissions = {
            "can_create": autocomplete_view.has_permission(request, "create"),
            "can_view": autocomplete_view.has_permission(request, "view"),
            "can_update": autocomplete_view.has_permission(request, "update"),
            "can_delete": autocomplete_view.has_permission(request, "delete"),
        }

        # Derived permissions for UI elements
        ui_permissions = {
            "show_create": self.show_create and permissions["can_create"],
            "show_list": self.show_list and permissions["can_view"],
            "show_detail": self.show_detail and permissions["can_view"],
            "show_update": self.show_update and permissions["can_update"],
            "show_delete": self.show_delete and permissions["can_delete"],
        }

        # Combine permissions
        context = {**permissions, **ui_permissions}

        logger.debug(
            "Permissions context: %s for model %s with %s in widget %s",
            context,
            self.model.__name__ if self.model else None,
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
        context: dict[str, Any] = {}

        # Only try to resolve list_url if show_list is True
        if self.show_list:
            context["view_list_url"] = self._get_model_url(autocomplete_view, "list_url", "view")
        else:
            context["view_list_url"] = None

        # Only try to resolve create_url if show_create is True
        if self.show_create:
            context["view_create_url"] = self._get_model_url(autocomplete_view, "create_url", "create")
        else:
            context["view_create_url"] = None

        logger.debug("Model URL context: %s", context)
        return context

    def _get_model_url(self, view: AutocompleteModelView, url_attr: str, permission: str) -> str | None:
        """Get model URL if available and permitted."""
        request = self.get_current_request()

        if not hasattr(view, url_attr) or getattr(view, url_attr) in ("", None):
            logger.warning("No valid %s URL available for model %s", url_attr, self.model)
            return None

        if not view.has_permission(request, permission):
            return None

        try:
            return safe_reverse(getattr(view, url_attr))
        except NoReverseMatch:
            logger.warning("Unable to reverse %s for model %s", url_attr, self.model)
            return None

    def get_instance_url_context(
        self, obj: Model | dict[str, Any], autocomplete_view: AutocompleteModelView
    ) -> dict[str, Any]:
        """Get URL-related context for a selected object.

        Public subclass-override hook. Returns a dict mapping `detail_url` /
        `update_url` / `delete_url` to fully built URL strings, omitting keys
        that are not configured or not permitted. Dicts and instances with no
        pk return an empty mapping.
        """
        return self._compute_instance_url_context(obj, autocomplete_view, cached_permissions=None)

    def _compute_instance_url_context(
        self,
        obj: Model | dict[str, Any],
        autocomplete_view: AutocompleteModelView,
        cached_permissions: dict[str, bool] | None,
    ) -> dict[str, Any]:
        """Shared implementation behind `get_instance_url_context`.

        When `cached_permissions` is `None`, permissions are looked up once via
        `get_current_request()`, preserving the original behavior of only
        calling `has_permission` when both the corresponding `show_*` flag and
        `*_url` attribute are truthy. When pre-computed permissions are passed
        in (loop-rendering hot path), the lookup is skipped entirely.
        """
        urls: dict[str, str] = {}

        if isinstance(obj, dict) or not hasattr(obj, "pk") or obj.pk is None:
            return urls

        if cached_permissions is None:
            # Match the original gating: only call has_permission when BOTH
            # show_X and the *_url attr are truthy. has_permission has potential
            # side effects (logging, cache fills), so we preserve when calls happen.
            request = self.get_current_request()
            cached_permissions = {
                "view": (
                    autocomplete_view.has_permission(request, "view")
                    if self.show_detail and autocomplete_view.detail_url
                    else False
                ),
                "update": (
                    autocomplete_view.has_permission(request, "update")
                    if self.show_update and autocomplete_view.update_url
                    else False
                ),
                "delete": (
                    autocomplete_view.has_permission(request, "delete")
                    if self.show_delete and autocomplete_view.delete_url
                    else False
                ),
            }

        if self.show_detail and autocomplete_view.detail_url and cached_permissions.get("view"):
            self._add_url_to_context(urls, "detail_url", autocomplete_view.detail_url, obj.pk)

        if self.show_update and autocomplete_view.update_url and cached_permissions.get("update"):
            self._add_url_to_context(urls, "update_url", autocomplete_view.update_url, obj.pk)

        if self.show_delete and autocomplete_view.delete_url and cached_permissions.get("delete"):
            self._add_url_to_context(urls, "delete_url", autocomplete_view.delete_url, obj.pk)

        logger.debug("Instance URL context: %s", urls)
        return urls

    def _add_url_to_context(self, context: dict[str, str], key: str, url_pattern: str, pk: Any) -> None:
        """Add URL to context dict if reversible."""
        try:
            context[key] = escape(safe_reverse(url_pattern, args=[pk]))
        except NoReverseMatch:
            logger.warning(
                "Unable to reverse %s %s with pk %s",
                key,
                url_pattern,
                pk,
            )

    def get_context(self, name: str, value: Any, attrs: dict[str, str] | None = None) -> dict[str, Any]:
        """Get context for rendering the widget."""
        self.get_queryset()  # Ensure we have model info

        # Extract configuration
        value_field = self.value_field or "id"
        label_field = self.label_field or "name"

        # Handle possible string representations of model instances
        value = self._process_string_value(value, value_field, label_field)

        # Setup global TomSelect if not already done
        request = get_current_request()
        if request and not getattr(request, "_tomselect_global_rendered", False):
            logger.debug("Rendering global TomSelect setup.")
            self.template_name = "django_tomselect/tomselect_setup.html"
            request._tomselect_global_rendered = True

        # Create base context without autocomplete view
        base_context = self._create_base_context(name, value, attrs, value_field)

        # Handle selected options without autocomplete view
        if isinstance(value, dict) and (value.get(value_field) or value.get("id") or value.get("pk")):
            return self._add_extracted_selected_option(base_context, value, value_field, label_field)

        # Get autocomplete view and request
        autocomplete_view = self.get_autocomplete_view()

        # Return base context if we can't get more info
        if not autocomplete_view or not request or not self.validate_request(request):
            logger.warning("Autocomplete view or request not available, returning base context")
            return base_context

        # Build full context with autocomplete view
        context = self._build_full_context(base_context, attrs, autocomplete_view)

        # Add selected options if value is provided
        if value and value != "":
            context["widget"]["selected_options"] = self._get_selected_options(value, autocomplete_view)

        return context

    @staticmethod
    def _safely_decode_html(value: str) -> str:
        """Iteratively unescape HTML entities with a ReDoS-safe iteration limit.

        Args:
            value: The HTML-encoded string.

        Returns:
            The fully decoded string.
        """
        decoded_value = value
        max_decode_iterations = 10
        prev_value = ""
        iteration_count = 0
        while prev_value != decoded_value and "&" in decoded_value and iteration_count < max_decode_iterations:
            prev_value = decoded_value
            decoded_value = html.unescape(decoded_value)
            iteration_count += 1

        if iteration_count >= max_decode_iterations:
            logger.warning(
                "HTML decoding reached maximum iterations (%d), possible malicious input", max_decode_iterations
            )

        if decoded_value != value:
            logger.debug("Decoded value after %d iterations: %s", iteration_count, decoded_value)

        return decoded_value

    @staticmethod
    def _extract_field_values(decoded_value: str, value_field: str, label_field: str) -> dict[str, str]:
        """Extract field values from a decoded dict-like string using regex patterns.

        Args:
            decoded_value: The decoded string to extract values from.
            value_field: The configured value field name.
            label_field: The configured label field name.

        Returns:
            Dictionary mapping field names to extracted string values.
        """
        extracted_values: dict[str, str] = {}
        for field_name in [value_field, "id", "pk", "pkid", "name", label_field]:
            if field_name in extracted_values:
                continue

            patterns = [
                rf"['\"]({field_name})['\"]\s*:\s*['\"]([^'\"]+)['\"]",
                rf"['\"]({field_name})['\"]\s*:\s*(\d+)",
                rf"['\"]({field_name})['\"]\s*:\s*UUID\(['\"]([^'\"]+)['\"]",
            ]

            for pattern in patterns:
                match = re.search(pattern, decoded_value)
                if match:
                    matched_value = match.group(2).strip()
                    logger.debug("Extracted %s: %s", field_name, matched_value)
                    extracted_values[field_name] = matched_value
                    break
        return extracted_values

    def _resolve_model_instance(self, extracted_values: dict[str, str], value_field: str) -> Any:
        """Look up a model instance from extracted field values, with fallback to the dict.

        Args:
            extracted_values: Dictionary of extracted field values.
            value_field: The configured value field name.

        Returns:
            A model instance if found, the extracted_values dict as fallback, or None.
        """
        lookup_field = value_field
        lookup_value = extracted_values.get(value_field)

        if not lookup_value:
            for field in ["id", "pk", "pkid"]:
                if field in extracted_values:
                    lookup_field = field
                    lookup_value = extracted_values[field]
                    break

        if not lookup_value:
            return extracted_values

        qs = self.get_queryset()
        if qs is None:
            return extracted_values

        try:
            instance = qs.filter(**{lookup_field: lookup_value}).first()
            return instance if instance else extracted_values
        except Exception as e:
            logger.debug("Error looking up with extracted values: %s", e)
            return extracted_values

    def _process_string_value(self, value: Any, value_field: str, label_field: str) -> Any:
        """Process string value that may represent a model instance.

        This method attempts to get the model instance or its attributes from a string representation, so we do not end
        up with weird strings in the widget's selected options.
        """
        if not isinstance(value, str) or ("{" not in value and "&" not in value):
            return value

        try:
            decoded_value = self._safely_decode_html(value)
            extracted_values = self._extract_field_values(decoded_value, value_field, label_field)

            has_identifier = any(extracted_values.get(k) for k in [value_field, "id", "pk", "pkid"])
            if has_identifier:
                return self._resolve_model_instance(extracted_values, value_field)
        except Exception as e:
            logger.error("Error parsing string representation: %s", e)

        return value

    def _create_base_context(
        self, name: str, value: Any, attrs: dict[str, Any] | None, value_field: str
    ) -> dict[str, Any]:
        """Create base context without autocomplete view."""
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
                "aria_label": (attrs or {}).get("aria-label", name.replace("_", " ").replace("-", " ").title()),
                "open_on_focus": self.open_on_focus,
                "placeholder": self.placeholder,
                "plugins": self.get_plugin_context(),
                "preload": self.preload,
                "required": self.is_required,
                "selected_options": [],
                "template_name": self.template_name,
                "value": value,
                **self.get_autocomplete_context(),
                **self.get_url_param_constants(),
            },
            "csp_nonce": self.get_csp_nonce(),
        }

        # Add filter/exclude configuration - pass normalized lists
        if self.filters:
            # Convert FilterSpec objects to dicts for template use
            base_context["widget"]["filters"] = [
                {
                    "source": f.source,
                    "lookup": f.lookup,
                    "source_type": f.source_type,
                    "levels_up": f.levels_up,
                }
                for f in self.filters
            ]
            # Keep for backwards compatibility with custom templates
            # Uses first field-type filter for legacy dependent_field
            field_filters = [f for f in self.filters if f.source_type == "field"]
            if field_filters:
                base_context["widget"].update(
                    {
                        "dependent_field": field_filters[0].source,
                        "dependent_field_lookup": field_filters[0].lookup,
                    }
                )

        if self.excludes:
            # Convert FilterSpec objects to dicts for template use
            base_context["widget"]["excludes"] = [
                {
                    "source": e.source,
                    "lookup": e.lookup,
                    "source_type": e.source_type,
                    "levels_up": e.levels_up,
                }
                for e in self.excludes
            ]
            # Keep for backwards compatibility with custom templates
            # Uses first field-type exclude for legacy exclude_field
            field_excludes = [e for e in self.excludes if e.source_type == "field"]
            if field_excludes:
                base_context["widget"].update(
                    {
                        "exclude_field": field_excludes[0].source,
                        "exclude_field_lookup": field_excludes[0].lookup,
                    }
                )

        # Handle model instances directly, if they are provided
        if value and hasattr(value, "_meta") and hasattr(value, "pk") and value.pk is not None:
            base_context["widget"]["selected_options"] = [self._get_option_from_instance(value, value_field)]

        return base_context

    def _get_option_from_instance(self, instance: Model, value_field: str) -> dict[str, str]:
        """Get option dict from model instance."""
        label_field = self.label_field or "name"

        # Extract fields based on configuration
        val = getattr(instance, value_field, instance.pk)
        label = getattr(instance, label_field, getattr(instance, "name", str(instance)))

        opt = {
            "value": str(val),
            "label": escape(str(label)),
        }

        # Add URLs if autocomplete_view is available
        autocomplete_view = self.get_autocomplete_view()
        request = self.get_current_request()

        if autocomplete_view and request and self.validate_request(request):
            urls = self.get_instance_url_context(instance, autocomplete_view)
            for url_type, url in urls.items():
                if url:
                    opt[url_type] = escape(url)

        return opt

    def _add_extracted_selected_option(
        self, context: dict[str, Any], value: dict[str, Any], value_field: str, label_field: str
    ) -> dict[str, Any]:
        """Add selected option from extracted values."""
        val = value.get(value_field) or value.get("id") or value.get("pk") or value.get("pkid")
        label = value.get(label_field) or value.get("name") or str(val)

        opt = {
            "value": str(val),
            "label": escape(str(label)),
        }
        context["widget"]["selected_options"] = [opt]
        return context

    def _build_full_context(
        self, base_context: dict[str, Any], attrs: dict[str, Any] | None, autocomplete_view: AutocompleteModelView
    ) -> dict[str, Any]:
        """Build full context with autocomplete view."""
        attrs = self.build_attrs(self.attrs, attrs)
        context: dict[str, Any] = {
            "widget": {
                **base_context["widget"],
                "attrs": attrs,
                **self.get_model_url_context(autocomplete_view),
            },
            "csp_nonce": base_context.get("csp_nonce", ""),
        }

        # Add permissions context
        context["widget"].update(self.get_permissions_context(autocomplete_view))

        return context

    def _get_selected_options(self, value: Any, autocomplete_view: AutocompleteModelView) -> list[dict[str, Any]]:
        """Get selected options from value."""
        selected: list[dict[str, Any]] = []
        value_field = self.value_field or "id"

        # Value is an ID or list of IDs
        queryset = self.get_queryset()
        if queryset is None:
            return []

        selected_values = [value] if not isinstance(value, (list, tuple)) else value

        if value_field == "pk":
            final_filter = Q(pk__in=selected_values)  # type: ignore[misc]
        else:
            # Filter on the value_field
            final_filter = Q(**{f"{value_field}__in": selected_values})  # type: ignore[misc]

        selected_objects = queryset.filter(final_filter)

        # Detect if label_field is a relation and add select_related to prevent N+1 queries
        label_field = self.label_field or "name"
        from django.core.exceptions import FieldDoesNotExist

        try:
            field_obj = selected_objects.model._meta.get_field(label_field)  # type: ignore[union-attr]
            if field_obj.is_relation:
                selected_objects = selected_objects.select_related(label_field)
        except (FieldDoesNotExist, AttributeError):
            pass

        # Pre-compute permissions once before the loop to avoid N+1 queries
        # Permissions are model-level, not object-level, so they're the same for all objects
        request = self.get_current_request()
        cached_permissions = {
            "view": autocomplete_view.has_permission(request, "view") if self.show_detail else False,
            "update": autocomplete_view.has_permission(request, "update") if self.show_update else False,
            "delete": autocomplete_view.has_permission(request, "delete") if self.show_delete else False,
        }

        for obj in selected_objects:
            # Handle the case where obj is a dictionary (e.g., cleaned_data)
            if isinstance(obj, dict):
                val = obj.get(value_field) or obj.get("pk", "")
                opt: dict[str, str] = {
                    "value": str(val),
                    "label": self.get_label_for_object(obj, autocomplete_view),
                }
            else:
                val = getattr(obj, value_field, obj.pk)
                opt = {
                    "value": str(val),
                    "label": self.get_label_for_object(obj, autocomplete_view),
                }

            # Safely add URLs with proper escaping, using pre-computed permissions.
            # Bypasses get_instance_url_context() to avoid breaking subclass overrides
            # that use the documented 2-arg signature; the override path is preserved
            # for single-instance rendering at _get_option_from_instance.
            urls = self._compute_instance_url_context(obj, autocomplete_view, cached_permissions)
            for url_type, url in urls.items():
                if url:
                    opt[url_type] = escape(url)
            selected.append(opt)

        return selected

    def get_label_for_object(self, obj: Model | dict[str, Any], autocomplete_view: AutocompleteModelView) -> str:
        """Get the label for an object using the configured label field."""
        label_field = self.label_field or "name"

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
            if prepare_method and callable(prepare_method):
                label_value = prepare_method(obj)
                if label_value is not None:
                    return escape(str(label_value))

        except Exception as e:
            logger.error("Error getting label for object: %s", e)

        # Fallback to string representation
        return escape(str(obj))

    def get_model(self) -> type[Model] | None:
        """Get model from field's choices or queryset."""
        if self.model:
            logger.debug("Model already set in %s: %s", self.__class__.__name__, self.model)
            return self.model

        model = None

        # Try to get model from choices queryset
        choices = self.choices
        if hasattr(choices, "queryset") and hasattr(getattr(choices, "queryset", None), "model"):
            model = choices.queryset.model
        # Try to get model directly from choices
        elif hasattr(choices, "model"):
            model = choices.model
        # If choices is a list, we can't determine model
        elif isinstance(choices, list) and choices:
            model = None

        logger.debug(
            "Model retrieved in %s: %s",
            self.__class__.__name__,
            model.__name__ if model else "None",
        )
        return model

    def validate_request(self, request: Any) -> bool:
        """Validate that a request object is valid for permission checking."""
        if not request:
            logger.warning("Request object is missing.")
            return False

        # Check if request has required attributes and methods
        required_attributes = ["user", "method", "GET"]
        if not all(hasattr(request, attr) for attr in required_attributes):
            logger.warning("Request object is missing required attributes or methods.")
            return False

        # Verify user attribute has required auth methods
        if not hasattr(request, "user") or not hasattr(request.user, "is_authenticated"):
            logger.warning("Request object is missing user or is_authenticated method.")
            return False

        # Verify request methods are callable
        if not callable(getattr(request, "get_full_path", None)):
            logger.warning("Request object is missing get_full_path method.")
            return False

        logger.debug("Request object is valid.")
        return True

    def get_autocomplete_view(self) -> AutocompleteModelView | None:
        """Get instance of autocomplete view for accessing queryset and search_lookups."""
        lazy_view = self.get_lazy_view()
        if not lazy_view:
            return None

        view = lazy_view.get_view()
        self.model = lazy_view.get_model()

        logger.debug("Lazy view model: %s", self.model)

        if not self.model:
            logger.warning("Model is not a valid Django model.")
            return None

        if not isinstance(view, AutocompleteModelView):
            logger.warning("View is not an instance of AutocompleteModelView.")
            return None

        # Add label_field to value_fields if needed
        self._ensure_label_field_in_view(view)

        return view

    def _ensure_label_field_in_view(self, view: AutocompleteModelView) -> None:
        """Ensure the label field is exposed by the view's serialized values."""
        if not self.label_field or self.label_field in view.value_fields:
            return

        logger.warning(
            "Label field '%s' is not in the autocomplete view's value_fields. This may result in 'undefined' labels.",
            self.label_field,
        )
        # Rebind rather than append: never mutate the shared class-level list.
        view.value_fields = [*view.value_fields, self.label_field]

        # Check if it's a model field
        if self.model is None:
            return

        try:
            model_fields = [f.name for f in self.model._meta.fields]  # type: ignore[union-attr]
            # A real ORM relation lookup separates field names with "__" in the
            # middle (e.g. "field__name"). A Python dunder such as "__str__" has
            # leading/trailing "__" and is NOT a queryable relation, so strip those
            # before testing, otherwise the dunder is wrongly kept in value_fields
            # and .values("__str__") raises a FieldError.
            is_related_field = "__" in self.label_field.strip("_")

            # If it's not a real field or relation, add to virtual_fields so it is
            # excluded from the .values() query. The view is responsible for
            # supplying the value in prepare_results()/hook_prepare_results().
            if not (self.label_field in model_fields or is_related_field):
                current_virtual = list(getattr(view, "virtual_fields", None) or [])
                if self.label_field not in current_virtual:
                    current_virtual.append(self.label_field)
                    # Rebind rather than append: never mutate the shared class list.
                    view.virtual_fields = current_virtual
                    logger.info(
                        "Label field '%s' added to virtual_fields: %s",
                        self.label_field,
                        view.virtual_fields,
                    )
        except (AttributeError, TypeError):
            # Cases where model is None or doesn't have _meta
            pass

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
                logger.warning("Using fallback empty queryset for model %s", model)
                return model.objects.none()  # type: ignore[union-attr]

            logger.warning("Using EmptyModel.objects.none() as last resort")
            return EmptyModel.objects.none()
        except Exception as e:
            # If anything fails, return an empty EmptyModel queryset
            logger.warning("Error in get_queryset: %s, falling back to EmptyModel.objects.none()", e)
            return EmptyModel.objects.none()

    def get_search_lookups(self) -> list[str]:
        """Get search lookups from autocomplete view."""
        autocomplete_view = self.get_autocomplete_view()
        if autocomplete_view:
            lookups = autocomplete_view.search_lookups
            logger.debug("Search lookups: %s", lookups)
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
        logger.warning("Request object is not required for iterables-type Tom Select widgets.")

    def get_autocomplete_context(self) -> dict[str, Any]:
        """Get context for autocomplete functionality."""
        autocomplete_context: dict[str, Any] = {
            "value_field": self.value_field,
            "label_field": self.label_field,
            "is_tabular": bool(self.plugin_dropdown_header),
            "use_htmx": self.use_htmx,
            "autocomplete_url": self.get_autocomplete_url(),
        }
        logger.debug("Autocomplete context: %s", autocomplete_context)
        return autocomplete_context

    def get_context(self, name: str, value: Any, attrs: dict[str, str] | None = None) -> dict[str, Any]:
        """Get context for rendering the widget."""
        # Only include the global setup if it hasn't been rendered yet
        request = get_current_request()
        if request and not getattr(request, "_tomselect_global_rendered", False):
            logger.debug("Rendering global TomSelect setup.")
            self.template_name = "django_tomselect/tomselect_setup.html"
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
                "aria_label": (attrs or {}).get("aria-label", name.replace("_", " ").replace("-", " ").title()),
                "open_on_focus": self.open_on_focus,
                "placeholder": self.placeholder,
                "plugins": self.get_plugin_context(),
                "preload": self.preload,
                "required": self.is_required,
                "template_name": self.template_name,
                "value": value,
                **self.get_autocomplete_context(),
                **self.get_url_param_constants(),
            },
            "csp_nonce": self.get_csp_nonce(),
        }

        if value is not None:
            context["widget"]["selected_options"] = self._get_selected_options(value)

        return context

    def _get_selected_options(self, value: Any) -> list[dict[str, Any]]:
        """Get selected options based on value."""
        try:
            autocomplete_view = self.get_autocomplete_view()
            if not autocomplete_view or not hasattr(autocomplete_view, "iterable"):
                return []

            # Handle different types of iterables
            if self._is_enum_choices(autocomplete_view):
                return self._get_enum_choices_options(value, autocomplete_view)
            elif self._is_tuple_iterable(autocomplete_view):
                return self._get_tuple_iterable_options(value, autocomplete_view)
            else:
                # Simple iterables
                values = [value] if not isinstance(value, (list, tuple)) else value
                return [{"value": str(val), "label": escape(str(val))} for val in values]
        except Exception as e:
            logger.error("Error getting selected options: %s", e, exc_info=True)
            # Fallback to just returning the value as both value and label
            values = [value] if not isinstance(value, (list, tuple)) else value
            return [{"value": str(val), "label": escape(str(val))} for val in values]

    def _is_enum_choices(self, view: AutocompleteIterablesView) -> bool:
        """Check if view's iterable is an enum choices class."""
        try:
            return hasattr(view, "iterable") and isinstance(view.iterable, type) and hasattr(view.iterable, "choices")
        except (AttributeError, TypeError):
            logger.warning("Error checking enum choices format", exc_info=True)
            return False

    def _is_tuple_iterable(self, view: AutocompleteIterablesView) -> bool:
        """Check if view's iterable is a tuple-based iterable."""
        try:
            return (
                isinstance(view.iterable, (tuple, list))
                and len(view.iterable) > 0
                and isinstance(view.iterable[0], tuple)
            )
        except (AttributeError, IndexError, TypeError):
            logger.warning("Error checking tuple iterable format", exc_info=True)
            return False

    def _get_enum_choices_options(self, value: Any, view: AutocompleteIterablesView) -> list[dict[str, Any]]:
        """Get options from enum choices."""
        values = [value] if not isinstance(value, (list, tuple)) else value
        selected: list[dict[str, Any]] = []

        iterable = view.iterable
        if iterable is None or not isinstance(iterable, type) or not hasattr(iterable, "choices"):
            return selected

        for val in values:
            for choice_value, choice_label in iterable.choices:
                if str(val) == str(choice_value):
                    selected.append({"value": str(val), "label": escape(str(choice_label))})
                    break
            else:
                selected.append({"value": str(val), "label": escape(str(val))})

        return selected

    def _get_tuple_iterable_options(self, value: Any, view: AutocompleteIterablesView) -> list[dict[str, Any]]:
        """Get options from tuple-based iterable."""
        values = [value] if not isinstance(value, (list, tuple)) else value
        selected: list[dict[str, Any]] = []

        iterable = view.iterable
        if not isinstance(iterable, (list, tuple)):
            return selected

        for val in values:
            for item in iterable:
                try:
                    if str(item[0]) == str(val):
                        # Handle tuples of different lengths properly
                        if len(item) > 1:
                            label = f"{item[0]}-{item[1]}"
                        else:
                            label = str(item[0])
                        selected.append({"value": str(val), "label": escape(label)})
                        break
                except (IndexError, TypeError):
                    # Skip malformed tuple items
                    logger.warning("Malformed tuple in iterable: %s", item)
                    continue
            else:
                selected.append({"value": str(val), "label": escape(str(val))})

        return selected

    def get_lazy_view(self) -> LazyView | None:
        """Get lazy-loaded view for the TomSelect iterables widget."""
        if not hasattr(self, "_lazy_view") or self._lazy_view is None:
            # Create LazyView with the URL from config
            self._lazy_view = LazyView(url_name=self.url)
        return self._lazy_view

    def get_autocomplete_view(self) -> AutocompleteIterablesView | None:
        """Get instance of autocomplete view for accessing iterable."""
        lazy_view = self.get_lazy_view()
        if not lazy_view:
            return None

        view = lazy_view.get_view()

        # Check if view has get_iterable method
        if view and hasattr(view, "get_iterable") and callable(view.get_iterable):
            return view

        # If not iterables view but has get_iterable, it's compatible
        if view and not issubclass(view.__class__, AutocompleteIterablesView):
            if not hasattr(view, "get_iterable"):
                raise ValueError(
                    "The autocomplete view must either be a subclass of "
                    "AutocompleteIterablesView or implement get_iterable()"
                )
        return view

    def get_iterable(self) -> list | tuple | type:
        """Get iterable or choices from autocomplete view."""
        autocomplete_view = self.get_autocomplete_view()
        if autocomplete_view:
            iterable = autocomplete_view.get_iterable()
            logger.debug("Iterable: %s", iterable)
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


class TomSelectTokenWidget(TomSelectWidgetMixin, forms.TextInput):
    """A token-style input that multiplexes multiple autocomplete views.

    Pairs with :class:`~django_tomselect.autocompletes.CompositeAutocompleteView`
    on the server. The serialized form value is a single canonical token string
    (e.g. ``author:42 category:5 some free text``) stored in a ``CharField``.

    Validation lives on :class:`~django_tomselect.forms.TomSelectTokenField`,
    not here - Django widgets do not run ``clean()``.
    """

    template_name = "django_tomselect/tomselect_token.html"
    _token_widget = True

    def __init__(
        self,
        composite_view: str,
        *,
        placeholder: str = "",
        allow_free_text: bool = True,
        max_query_length: int = 4096,
        max_tokens: int = 32,
        css_framework: str | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the token widget.

        Args:
            composite_view: A URL name (``"app:url-name"``) for the composite
                autocomplete endpoint. **Must be a URL name, not a class
                reference** - the browser plugin needs a URL to call. Use a
                URL name even when you have a class reference handy; the
                example app demonstrates the convention.
            placeholder: Text shown before any tokens are entered.
            allow_free_text: When False, un-prefixed input is treated as an
                error by the field's clean() and the JS plugin disables the
                free-text affordance.
            max_query_length: utf-8 byte length cap for the serialized value.
            max_tokens: maximum number of tokens (operator + free-text).
            css_framework: explicit "default" / "bootstrap4" / "bootstrap5"
                override for the CSS framework. Otherwise inherited from the
                project-level ``TOMSELECT.DEFAULT_CSS_FRAMEWORK`` setting.
            attrs: HTML attributes to set on the underlying ``<input>``.

        Raises:
            ImproperlyConfigured: If ``composite_view`` is not a string. The
                browser plugin needs a URL to call; class references would
                emit dead markup the JS cannot bootstrap.
        """
        if not isinstance(composite_view, str):
            from django.core.exceptions import ImproperlyConfigured

            raise ImproperlyConfigured(
                "TomSelectTokenWidget requires composite_view to be a URL name "
                "(string), not a class reference - the browser plugin needs a "
                "URL to call. Pass the URL name registered for "
                "CompositeAutocompleteView.as_view()."
            )
        self.composite_view = composite_view
        self.allow_free_text = allow_free_text
        self.max_query_length = max_query_length
        self.max_tokens = max_tokens

        # Thread placeholder into attrs so forms.TextInput renders it natively.
        merged_attrs: dict[str, Any] = dict(attrs or {})
        if placeholder and "placeholder" not in merged_attrs:
            merged_attrs["placeholder"] = placeholder

        # Skip TomSelectWidgetMixin.__init__: it merges in TomSelectConfig defaults
        # designed for model autocomplete widgets (autocomplete URL, value/label
        # fields, plugin configs) which would pollute the token widget's attrs
        # and shape. Initialize the underlying TextInput directly, then assign
        # just the asset-loading attributes the mixin's _get_css_paths and media
        # property need.
        forms.TextInput.__init__(self, attrs=merged_attrs)

        self.css_framework = css_framework or GLOBAL_DEFAULT_CONFIG.css_framework
        self.use_minified = GLOBAL_DEFAULT_CONFIG.use_minified
        # Plugin context is empty for token widget - no dropdown_header etc.
        self.plugin_clear_button = None
        self.plugin_remove_button = None
        self.plugin_dropdown_header = None
        self.plugin_dropdown_footer = None
        self.plugin_checkbox_options = None
        self.plugin_dropdown_input = None

    def build_attrs(
        self,
        base_attrs: dict[str, Any],
        extra_attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build HTML attributes - bypasses the mixin's model-autocomplete attrs.

        The mixin's ``build_attrs`` injects ``data-autocomplete-url`` and other
        attrs that don't apply to the token widget (which reads from a separate
        JSON config blob). Use the plain TextInput build_attrs.
        """
        return forms.TextInput.build_attrs(self, base_attrs, extra_attrs)

    def get_context(
        self,
        name: str,
        value: Any,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the widget render context.

        Bypasses :class:`TomSelectWidgetMixin`'s autocomplete-URL plumbing
        (``get_lazy_view`` / ``get_autocomplete_url`` are designed for
        single-endpoint model autocomplete views, not the composite view's
        ``mode=…`` envelope). The token plugin reads our JSON config blob
        instead.

        ``token_config`` is JSON-serialized here (not as a raw dict) - Django's
        default template rendering would emit Python ``repr()`` syntax (single
        quotes, ``True``/``None``) which JSON.parse() cannot consume.
        """
        ctx = forms.TextInput.get_context(self, name, value, attrs)
        ctx["widget"]["composite_view_url"] = self._resolve_composite_url()
        ctx["widget"]["token_config"] = json.dumps(self._build_token_config())
        ctx["widget"]["css_framework"] = (
            self.css_framework.value
            if isinstance(self.css_framework, AllowedCSSFrameworks)
            else str(self.css_framework)
        )
        # CSP nonce is referenced at top-level by the inline init script.
        ctx["csp_nonce"] = self.get_csp_nonce() or ""
        return ctx

    def _resolve_composite_url(self) -> str:
        """Resolve the composite_view URL name. Raises ImproperlyConfigured.

        ``composite_view`` is a string per __init__'s ImproperlyConfigured
        check. If the URL doesn't reverse, fail fast at render time rather
        than emit an inert widget - silently rendering markup the JS can't
        bootstrap is the same dead-widget failure mode that class refs were
        rejected to prevent.
        """
        from django.core.exceptions import ImproperlyConfigured

        try:
            return safe_reverse(self.composite_view)
        except NoReverseMatch as exc:
            raise ImproperlyConfigured(
                f"TomSelectTokenWidget: cannot reverse composite_view URL "
                f"{self.composite_view!r}. Make sure the URL is registered "
                "before the form is rendered."
            ) from exc

    def _build_token_config(self) -> dict[str, Any]:
        """Serialize widget settings the JS plugin needs."""
        return {
            "allow_free_text": self.allow_free_text,
            "max_query_length": self.max_query_length,
            "max_tokens": self.max_tokens,
        }

    @property
    def media(self) -> forms.Media:
        """Return media - same JS bundle as the standard widgets, plus token CSS."""
        css_paths = self._get_css_paths()
        js_path = (
            "django_tomselect/js/django-tomselect.min.js"
            if self.use_minified
            else "django_tomselect/js/django-tomselect.js"
        )
        return forms.Media(css={"all": css_paths}, js=[js_path])
