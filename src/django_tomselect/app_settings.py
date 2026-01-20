"""Settings for the django-tomselect package."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Literal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FilterSpec:
    """Specification for a single filter/exclude condition.

    This class represents a single filter or exclude condition that can be applied
    to an autocomplete queryset. It supports both field-based filtering (where the
    value comes from another form field) and constant filtering (where the value
    is a static constant).

    Attributes:
        source: Form field name (for field-based filters) OR constant value (for const filters).
        lookup: Django ORM lookup field (e.g., "category_id", "status").
        source_type: Either "field" (value from form field) or "const" (static value).

    Example:
        # Field-based filter (filter by value from another form field)
        FilterSpec(source="category", lookup="category_id", source_type="field")

        # Constant filter (always filter to a specific value)
        FilterSpec(source="published", lookup="status", source_type="const")
    """

    source: str  # Form field name OR constant value
    lookup: str  # Django ORM lookup (e.g., "category_id")
    source_type: Literal["field", "const"] = "field"

    @classmethod
    def from_tuple(cls, t: tuple[str, str]) -> "FilterSpec":
        """Create a FilterSpec from a legacy 2-tuple format.

        Args:
            t: A tuple of (field_name, lookup_field).

        Returns:
            A FilterSpec with source_type="field".
        """
        return cls(source=t[0], lookup=t[1], source_type="field")


def Const(value: str, lookup: str) -> FilterSpec:  # noqa: N802
    """Helper to create constant filter specs.

    Creates a FilterSpec that always filters by a constant value rather than
    getting the value from another form field.

    Args:
        value: The constant value to filter by.
        lookup: The Django ORM lookup field.

    Returns:
        A FilterSpec with source_type="const".

    Example:
        # Always filter to only published items
        Const("published", "status")

        # Filter by a specific category ID
        Const("5", "category_id")
    """
    return FilterSpec(source=str(value), lookup=lookup, source_type="const")


# Type alias for filter_by/exclude_by input formats
FilterByInput = tuple[()] | tuple[str, str] | FilterSpec | Sequence[tuple[str, str] | FilterSpec]


class AllowedCSSFrameworks(Enum):
    """Enum for allowed CSS frameworks."""

    DEFAULT = "default"
    BOOTSTRAP4 = "bootstrap4"
    BOOTSTRAP5 = "bootstrap5"


def bool_or_callable(value):
    """Return the value if it's a boolean, or call it if it's a callable."""
    if callable(value):
        return value()
    return bool(value)


def currently_in_production_mode():
    """Default method to determine whether to use minified files or not by checking the DEBUG setting."""
    return settings.DEBUG is False


@dataclass(frozen=True)
class BaseConfig:
    """Base configuration class for django-tomselect widgets with validation."""

    def validate(self) -> None:
        """Validate configuration values. Override in subclasses."""

    def __post_init__(self):
        """Validate config after initialization."""
        self.validate()

    def as_dict(self):
        """Return the configuration as a dictionary."""
        return self.__dict__


@dataclass(frozen=True)
class PluginCheckboxOptions(BaseConfig):
    """Plugin configuration for the checkbox_options plugin.

    No additional settings are required. If this plugin is enabled, the widget will display checkboxes.
    """


@dataclass(frozen=True)
class PluginDropdownInput(BaseConfig):
    """Plugin configuration for the dropdown_input plugin.

    No additional settings are required. If this plugin is enabled, the widget will display an input field.
    """


@dataclass(frozen=True)
class PluginClearButton(BaseConfig):
    """Plugin configuration for the clear_button plugin."""

    title: str = "Clear Selections"
    class_name: str = "clear-button"


@dataclass(frozen=True)
class PluginDropdownHeader(BaseConfig):
    """Plugin configuration for the dropdown_header plugin."""

    title: str = "Autocomplete"
    header_class: str = "container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header"
    title_row_class: str = "row"
    label_class: str = "form-label"
    value_field_label: str = "Value"
    label_field_label: str = "Label"
    label_col_class: str = "col-6"
    show_value_field: bool = False
    extra_columns: dict[str, str] = field(default_factory=dict)

    @property
    def _title(self):
        """Return the title with translations."""
        return str(self.title)

    @property
    def _value_field_label(self):
        """Return the value field label with translations."""
        return str(self.value_field_label)

    @property
    def _label_field_label(self):
        """Return the label field label with translations."""
        return str(self.label_field_label)

    @property
    def _extra_columns(self):
        """Return the extra columns with translations."""
        return {k: str(v) for k, v in self.extra_columns.items()}

    def as_dict(self):
        """Return the configuration as a dictionary with evaluated translations."""
        base_dict = super().as_dict()
        # Replace _private fields with their property values
        base_dict["title"] = self._title
        base_dict["value_field_label"] = self._value_field_label
        base_dict["label_field_label"] = self._label_field_label
        base_dict["extra_columns"] = self._extra_columns
        return base_dict

    def validate(self) -> None:
        """Validate dropdown header config."""
        if not isinstance(self.extra_columns, dict):
            raise ValidationError("extra_columns must be a dictionary")


@dataclass(frozen=True)
class PluginDropdownFooter(BaseConfig):
    """Plugin configuration for the dropdown_footer plugin.

    Args:
        title: title for the footer.
        footer_class: CSS class for the footer container.
    """

    title: str = "Autocomplete Footer"
    footer_class: str = "container-fluid mt-1 px-2 border-top dropdown-footer"
    list_view_label: str = "List View"
    list_view_class: str = "btn btn-primary btn-sm m-2 p-1 float-end float-right"
    create_view_label: str = "Create New"
    create_view_class: str = "btn btn-primary btn-sm m-2 p-1 float-end float-right"


@dataclass(frozen=True)
class PluginRemoveButton(BaseConfig):
    """Plugin configuration for the remove_button plugin, which removed an item from the list of selected items.

    Args:
        title: title for the remove button.
        label: label for the remove button.
        class_name: CSS class for the remove button.
    """

    title: str = "Remove this item"
    label: str = "&times;"
    class_name: str = "remove"


PROJECT_TOMSELECT = getattr(settings, "TOMSELECT", {})

DEFAULT_CSS_FRAMEWORK = PROJECT_TOMSELECT.get("DEFAULT_CSS_FRAMEWORK", AllowedCSSFrameworks.DEFAULT.value)
DEFAULT_USE_MINIFIED = PROJECT_TOMSELECT.get("DEFAULT_USE_MINIFIED", currently_in_production_mode())

PROJECT_DEFAULT_CONFIG = PROJECT_TOMSELECT.get("DEFAULT_CONFIG", {})
PROJECT_PLUGINS = PROJECT_TOMSELECT.get("PLUGINS", {})

PERMISSION_CACHE = getattr(settings, "PERMISSION_CACHE", {})
PERMISSION_CACHE_TIMEOUT = PERMISSION_CACHE.get("TIMEOUT", None)
PERMISSION_CACHE_KEY_PREFIX = PERMISSION_CACHE.get("KEY_PREFIX", "")
PERMISSION_CACHE_NAMESPACE = PERMISSION_CACHE.get("NAMESPACE", "")

LOGGING_ENABLED = PROJECT_TOMSELECT.get("ENABLE_LOGGING", True)


def validate_json_encoder_class():
    """Validate and return the JSON encoder class from settings.

    Returns:
        A JSONEncoder subclass or None (to use Django's default DjangoJSONEncoder).

    Raises:
        ImportError: If the DEFAULT_JSON_ENCODER string cannot be imported.
        TypeError: If the class is not a subclass of json.JSONEncoder.
    """
    import json

    json_encoder_class = PROJECT_TOMSELECT.get("DEFAULT_JSON_ENCODER", None)
    if json_encoder_class is None:
        return None

    if isinstance(json_encoder_class, str):
        try:
            json_encoder_class = import_string(json_encoder_class)
        except ImportError as e:
            logger.exception(
                "Could not import %s. Please check your DEFAULT_JSON_ENCODER setting. %s",
                json_encoder_class,
                e,
            )
            raise ImportError(f"Failed to import DEFAULT_JSON_ENCODER: {e}") from e

    if not (isinstance(json_encoder_class, type) and issubclass(json_encoder_class, json.JSONEncoder)):
        raise TypeError(
            "DEFAULT_JSON_ENCODER must be a subclass of json.JSONEncoder "
            "or an importable string pointing to such a subclass."
        )

    return json_encoder_class


DEFAULT_JSON_ENCODER = validate_json_encoder_class()


def validate_proxy_request_class():
    """Validate the ProxyRequest class based on settings.

    Returns:
        A subclass of DefaultProxyRequest.

    Raises:
        ImportError: If the PROXY_REQUEST_CLASS string cannot be imported.
        TypeError: If the class is not a subclass of DefaultProxyRequest.
    """
    from django_tomselect.request import DefaultProxyRequest

    proxy_request_class = PROJECT_TOMSELECT.get("PROXY_REQUEST_CLASS", DefaultProxyRequest)
    if proxy_request_class is None:
        return DefaultProxyRequest

    if isinstance(proxy_request_class, str):
        try:
            proxy_request_class = import_string(proxy_request_class)
        except ImportError as e:
            logger.exception(
                "Could not import %s. Please check your PROXY_REQUEST_CLASS setting. %s",
                proxy_request_class,
                e,
            )
            raise ImportError(f"Failed to import PROXY_REQUEST_CLASS: {e}") from e

    if not issubclass(proxy_request_class, DefaultProxyRequest):
        raise TypeError(
            "PROXY_REQUEST_CLASS must be a subclass of DefaultProxyRequest "
            "or an importable string pointing to such a subclass."
        )

    return proxy_request_class


PROXY_REQUEST_CLASS = validate_proxy_request_class()


@dataclass(frozen=True)
class TomSelectConfig(BaseConfig):
    """Main configuration class for TomSelect widgets, supplied as a `config` argument to the form field.

    This class contains settings specific to a particular TomSelect widget.

    Args:
        url: URL for the autocomplete view.
        show_list: if True, show the list button.
        show_create: if True, show the create button.
        show_detail: if True, show the detail button.
        show_update: if True, show the update button.
        show_delete: if True, show the delete button.
        value_field: field name for the value field.
        label_field: field name for the label field.
        create_field: field name for the create field.
        filter_by: Filter conditions to apply. Accepts:
            - Empty tuple () for no filtering (default)
            - 2-tuple ("field", "lookup") for legacy single field filter
            - FilterSpec object for a single condition
            - List of FilterSpec or 2-tuples for multiple conditions
            - Use Const("value", "lookup") for constant filters.

        exclude_by: Exclude conditions to apply. Same format as filter_by.
        use_htmx: if True, use HTMX for AJAX requests.
        css_framework: CSS framework to use ("default", "bootstrap4", "bootstrap5").
        attrs: additional attributes for the widget.

        close_after_select: if True, close the dropdown after selecting an item.
        hide_placeholder: if True, hide the placeholder when an item is selected.
        highlight: if True, highlight the matching text in the dropdown.
        hide_selected: if True, hide the selected item in the dropdown.
        load_throttle: throttle time in milliseconds for loading items.
        loading_class: CSS class for the loading indicator.
        max_items: maximum number of items to display in the dropdown.
        max_options: maximum number of options to display in the dropdown.
        open_on_focus: if True, open the dropdown when the input is focused.
        placeholder: placeholder text for the input field.
        preload: if True, preload the dropdown on focus.
        create: if True, allow creating new items.
        create_filter: filter for creating new items.
        create_with_htmx: if True, use HTMX for creating new items.
        minimum_query_length: minimum number of characters to trigger a search.
        css_framework: CSS framework to use ("default", "bootstrap4", "bootstrap5").
        use_minified: if True, use minified JS and CSS files.

        plugin_checkbox_options: PluginCheckboxOptions instance.
        plugin_clear_button: PluginClearButton instance.
        plugin_dropdown_header: PluginDropdownHeader instance.
        plugin_dropdown_footer: PluginDropdownFooter instance.
        plugin_dropdown_input: PluginDropdownInput instance.
        plugin_remove_button: PluginRemoveButton instance.
    """

    url: str = "autocomplete"
    show_list: bool = False
    show_create: bool = False
    show_detail: bool = False
    show_update: bool = False
    show_delete: bool = False
    value_field: str = "id"
    label_field: str = "name"
    create_field: str = ""
    filter_by: tuple | FilterSpec | list = field(default_factory=tuple)
    exclude_by: tuple | FilterSpec | list = field(default_factory=tuple)
    use_htmx: bool = False
    attrs: dict[str, str] = field(default_factory=dict)

    close_after_select: bool | None = None
    hide_placeholder: bool | None = None
    highlight: bool = True
    hide_selected: bool = True
    load_throttle: int = 300
    loading_class: str = "loading"
    max_items: int | None = None
    max_options: int | None = None
    open_on_focus: bool = True
    placeholder: str | None = "Select a value"
    preload: Literal["focus"] | bool = "focus"  # Either 'focus' or True/False
    create: bool = False
    create_filter: str | None = None
    create_with_htmx: bool = False
    minimum_query_length: int = 2
    css_framework: AllowedCSSFrameworks = DEFAULT_CSS_FRAMEWORK
    use_minified: bool = DEFAULT_USE_MINIFIED

    # Plugin configurations
    plugin_checkbox_options: PluginCheckboxOptions | None = None
    plugin_clear_button: PluginClearButton | None = None
    plugin_dropdown_header: PluginDropdownHeader | None = None
    plugin_dropdown_footer: PluginDropdownFooter | None = None
    plugin_dropdown_input: PluginDropdownInput | None = None
    plugin_remove_button: PluginRemoveButton | None = None

    def _is_filterspec(self, obj: object) -> bool:
        """Check if an object is a FilterSpec."""
        if isinstance(obj, FilterSpec):
            return True
        # Handle module reload case where class identity differs
        return type(obj).__name__ == "FilterSpec" and hasattr(obj, "source") and hasattr(obj, "lookup")

    def _validate_filter_input(self, value: FilterByInput, field_name: str) -> None:
        """Validate a filter_by or exclude_by input value."""
        # Empty tuple is valid
        if isinstance(value, tuple) and len(value) == 0:
            return

        # Single FilterSpec is valid
        if self._is_filterspec(value):
            return

        # Legacy 2-tuple is valid
        if isinstance(value, tuple) and len(value) == 2:
            if not all(isinstance(v, str) for v in value):
                raise ValidationError(f"{field_name} 2-tuple must contain only strings")
            return

        # List of specs/tuples is valid
        if isinstance(value, list):
            for i, item in enumerate(value):
                if self._is_filterspec(item):
                    continue
                if isinstance(item, tuple) and len(item) == 2:
                    if not all(isinstance(v, str) for v in item):
                        raise ValidationError(
                            f"{field_name}[{i}] 2-tuple must contain only strings"
                        )
                    continue
                raise ValidationError(
                    f"{field_name}[{i}] must be a FilterSpec or a 2-tuple, got {type(item).__name__}"
                )
            return

        # Invalid format
        raise ValidationError(
            f"{field_name} must be an empty tuple, a 2-tuple (field, lookup), "
            f"a FilterSpec, or a list of FilterSpec/tuples"
        )

    def validate(self) -> None:
        """Validate the complete configuration."""
        # Validate filter_by and exclude_by formats
        self._validate_filter_input(self.filter_by, "filter_by")
        self._validate_filter_input(self.exclude_by, "exclude_by")

        # Check for identical filter_by and exclude_by (when non-empty)
        filters = self.get_normalized_filters()
        excludes = self.get_normalized_excludes()
        if filters and excludes:
            # Check if any filter matches any exclude exactly
            for f in filters:
                for e in excludes:
                    if f.source == e.source and f.lookup == e.lookup and f.source_type == e.source_type:
                        raise ValidationError(
                            f"filter_by and exclude_by cannot contain identical conditions: "
                            f"source={f.source!r}, lookup={f.lookup!r}"
                        )

        if self.load_throttle < 0:
            raise ValidationError("load_throttle must be positive")
        if self.max_items is not None and self.max_items < 1:
            raise ValidationError("max_items must be greater than 0")
        if self.max_options is not None and self.max_options < 1:
            raise ValidationError("max_options must be greater than 0")
        if self.minimum_query_length < 0:
            raise ValidationError("minimum_query_length must be positive")

        # Validate css_framework - check against allowed values (None is allowed for inheritance)
        if self.css_framework is not None:
            allowed_frameworks = {f.value for f in AllowedCSSFrameworks}
            if self.css_framework not in allowed_frameworks:
                raise ValidationError(
                    f"css_framework must be one of {sorted(allowed_frameworks)}, got {self.css_framework!r}"
                )

    def _normalize_filter_input(self, value: FilterByInput) -> list[FilterSpec]:
        """Normalize filter_by or exclude_by input to a list of FilterSpec objects."""
        # Empty tuple
        if isinstance(value, tuple) and len(value) == 0:
            return []

        # Single FilterSpec (handle module reload case)
        if self._is_filterspec(value):
            # Convert to ensure it's the current FilterSpec class
            return [FilterSpec(source=value.source, lookup=value.lookup, source_type=value.source_type)]

        # Legacy 2-tuple
        if isinstance(value, tuple) and len(value) == 2:
            return [FilterSpec.from_tuple(value)]

        # List of specs/tuples
        if isinstance(value, list):
            result = []
            for item in value:
                if self._is_filterspec(item):
                    # Convert to ensure it's the current FilterSpec class
                    result.append(FilterSpec(source=item.source, lookup=item.lookup, source_type=item.source_type))
                elif isinstance(item, tuple) and len(item) == 2:
                    result.append(FilterSpec.from_tuple(item))
            return result

        return []

    def get_normalized_filters(self) -> list[FilterSpec]:
        """Get filter_by as a normalized list of FilterSpec objects."""
        return self._normalize_filter_input(self.filter_by)

    def get_normalized_excludes(self) -> list[FilterSpec]:
        """Get exclude_by as a normalized list of FilterSpec objects."""
        return self._normalize_filter_input(self.exclude_by)

    def as_dict(self) -> dict:
        """Convert config to dictionary for template rendering."""
        return {k: v.as_dict() if isinstance(v, BaseConfig) else v for k, v in self.__dict__.items()}

    def update(self, **kwargs) -> "TomSelectConfig":
        """Return a new config with updated values.

        Note: Since TomSelectConfig is a frozen dataclass, this method returns a new
        instance with the specified fields updated rather than modifying in place.
        """
        return replace(self, **kwargs)

    def verify_config_types(self) -> bool:
        """Verify that the configuration types are correct.

        Raises:
            TypeError: If any plugin configuration has an invalid type.

        Returns:
            True if all configurations are valid.
        """
        errors = []

        # Check each plugin config - None is allowed as it means the plugin is disabled
        plugin_checks = [
            (self.plugin_checkbox_options, PluginCheckboxOptions, "plugin_checkbox_options"),
            (self.plugin_clear_button, PluginClearButton, "plugin_clear_button"),
            (self.plugin_dropdown_header, PluginDropdownHeader, "plugin_dropdown_header"),
            (self.plugin_dropdown_footer, PluginDropdownFooter, "plugin_dropdown_footer"),
            (self.plugin_dropdown_input, PluginDropdownInput, "plugin_dropdown_input"),
            (self.plugin_remove_button, PluginRemoveButton, "plugin_remove_button"),
        ]

        for value, expected_type, field_name in plugin_checks:
            if value is not None and not isinstance(value, expected_type):
                errors.append(
                    f"{field_name} must be {expected_type.__name__} or None, "
                    f"got {type(value).__name__}"
                )

        if errors:
            error_msg = "Invalid TomSelectConfig: " + "; ".join(errors)
            logger.error(error_msg)
            raise TypeError(error_msg)

        return True


def get_plugin_config(plugin_class: type[BaseConfig], plugin_key: str, defaults: BaseConfig) -> BaseConfig:
    """Retrieve a plugin configuration from the project settings.

    The plugin config might be defined as a dict or as an instance of the config class.
    If it's not found, return the default config.
    """
    plugin_data = PROJECT_PLUGINS.get(plugin_key, None)
    if plugin_data is None:
        return defaults
    if isinstance(plugin_data, plugin_class):
        return plugin_data
    if isinstance(plugin_data, dict):
        return plugin_class(**plugin_data)
    return defaults  # Fallback if something unexpected


# Create a base "global default" TomSelectConfig from project settings and package defaults
GLOBAL_DEFAULT_CONFIG = TomSelectConfig(
    plugin_checkbox_options=get_plugin_config(PluginCheckboxOptions, "checkbox_options", None),
    plugin_clear_button=get_plugin_config(PluginClearButton, "clear_button", None),
    plugin_dropdown_header=get_plugin_config(PluginDropdownHeader, "dropdown_header", None),
    plugin_dropdown_footer=get_plugin_config(PluginDropdownFooter, "dropdown_footer", None),
    plugin_dropdown_input=get_plugin_config(PluginDropdownInput, "dropdown_input", None),
    plugin_remove_button=get_plugin_config(PluginRemoveButton, "remove_button", None),
    # Merge DEFAULT_CONFIG fields if needed:
    **{k: v for k, v in PROJECT_DEFAULT_CONFIG.items()},
)


def merge_configs(base: TomSelectConfig, override: TomSelectConfig | None = None) -> TomSelectConfig:
    """Merge a base TomSelectConfig with an overriding config.

    1. Starts with all fields from the base config
    2. Overrides only fields explicitly set in overriding config (different from default)
    3. Never overrides using `None` values
    4. For plugin fields, applies the same strategy in a nested manner

    Args:
        base: The base configuration.
        override: The overriding configuration.

    Returns:
        Merged configuration.
    """
    if not override:
        return base

    # Make a copy of the base config's values
    merged_dict = base.__dict__.copy()

    # Get a clean default config for comparison
    default_config = TomSelectConfig()

    # For each field in the override
    for field_name in override.__dataclass_fields__:
        # Skip if we're trying to override with None
        if getattr(override, field_name) is None:
            continue

        # Check if the override has a non-default value (explicitly set)
        if getattr(override, field_name) != getattr(default_config, field_name):
            # The field was explicitly set in the override

            # Special handling for plugin fields
            if (
                field_name.startswith("plugin_")
                and getattr(override, field_name) is not None
                and getattr(base, field_name) is not None
            ):
                # For plugins, we need to merge field by field
                base_plugin = getattr(base, field_name)
                override_plugin = getattr(override, field_name)

                # Create a default plugin instance for comparison
                default_plugin_class = type(override_plugin)
                default_plugin = default_plugin_class()

                # Copy all fields from base plugin
                merged_plugin_dict = base_plugin.__dict__.copy()

                # Override only explicitly set fields in the override plugin
                for plugin_field in override_plugin.__dataclass_fields__:
                    override_value = getattr(override_plugin, plugin_field)
                    if override_value is not None and override_value != getattr(default_plugin, plugin_field):
                        merged_plugin_dict[plugin_field] = override_value

                # Create a new plugin instance with merged values
                merged_dict[field_name] = type(base_plugin)(**merged_plugin_dict)
            else:
                # For regular fields, just override with the explicit value
                merged_dict[field_name] = getattr(override, field_name)

    # Create a new config with the merged values
    return TomSelectConfig(**merged_dict)
