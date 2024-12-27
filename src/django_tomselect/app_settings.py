"""Settings for the django-tomselect package."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from django_tomselect.request import DefaultProxyRequest

logger = logging.getLogger(__name__)


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
        base_dict['title'] = self._title
        base_dict['value_field_label'] = self._value_field_label
        base_dict['label_field_label'] = self._label_field_label
        base_dict['extra_columns'] = self._extra_columns
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


def validate_proxy_request_class():
    """Validate the ProxyRequest class based on settings.

    Returns:
        A subclass of DefaultProxyRequest.
    """
    proxy_request_class = PROJECT_TOMSELECT.get("PROXY_REQUEST_CLASS", DefaultProxyRequest)
    if proxy_request_class is None:
        return DefaultProxyRequest

    if isinstance(proxy_request_class, str):
        try:
            proxy_request_class = import_string(proxy_request_class)
        except (ModuleNotFoundError, ImportError) as e:
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
        filter_by: tuple of model field and lookup value to filter by.
        exclude_by: tuple of model field and lookup value to exclude by.
        use_htmx: if True, use HTMX for AJAX requests.
        css_framework: CSS framework to use ("default", "bootstrap4", "bootstrap5").
        attrs: additional attributes for the widget.

        close_after_select: if True, close the dropdown after selecting an item.
        hide_placeholder: if True, hide the placeholder when an item is selected.
        highlight: if True, highlight the matching text in the dropdown.
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
    filter_by: tuple = field(default_factory=tuple)
    exclude_by: tuple = field(default_factory=tuple)
    use_htmx: bool = False
    attrs: dict[str, str] = field(default_factory=dict)

    close_after_select: bool | None = None
    hide_placeholder: bool | None = None
    highlight: bool = True
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
    plugin_checkbox_options: Optional["PluginCheckboxOptions"] = None
    plugin_clear_button: Optional["PluginClearButton"] = None
    plugin_dropdown_header: PluginDropdownHeader | None = None
    plugin_dropdown_footer: Optional["PluginDropdownFooter"] = None
    plugin_dropdown_input: Optional["PluginDropdownInput"] = None
    plugin_remove_button: Optional["PluginRemoveButton"] = None

    def validate(self) -> None:
        """Validate the complete configuration."""
        if len(self.filter_by) > 0 and len(self.filter_by) != 2:
            raise ValidationError("filter_by must be either empty or a 2-tuple")

        if len(self.exclude_by) > 0 and len(self.exclude_by) != 2:
            raise ValidationError("exclude_by must be either empty or a 2-tuple")

        if (len(self.filter_by) > 0 or len(self.exclude_by) > 0) and self.filter_by == self.exclude_by:
            raise ValidationError("filter_by and exclude_by cannot refer to the same field")

        if self.load_throttle < 0:
            raise ValidationError("load_throttle must be positive")
        if self.max_items is not None and self.max_items < 1:
            raise ValidationError("max_items must be greater than 0")
        if self.max_options is not None and self.max_options < 1:
            raise ValidationError("max_options must be greater than 0")
        if self.minimum_query_length < 0:
            raise ValidationError("minimum_query_length must be positive")

    def as_dict(self) -> dict:
        """Convert config to dictionary for template rendering."""
        return {k: v.as_dict() if isinstance(v, BaseConfig) else v for k, v in self.__dict__.items()}

    def update(self, **kwargs):
        """Update config with widget-level settings."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def verify_config_types(self):
        """Verify that the configuration types are correct."""
        # Check the plugin config
        if not isinstance(self.plugin_checkbox_options, PluginCheckboxOptions):
            logger.warning("PluginCheckboxOptions is not of type PluginCheckboxOptions")
        if not isinstance(self.plugin_clear_button, PluginClearButton):
            logger.warning("PluginClearButton is not of type PluginClearButton")
        if not isinstance(self.plugin_dropdown_header, PluginDropdownHeader):
            logger.warning("PluginDropdownHeader is not of type PluginDropdownHeader")
        if not isinstance(self.plugin_dropdown_footer, PluginDropdownFooter):
            logger.warning("PluginDropdownFooter is not of type PluginDropdownFooter")
        if not isinstance(self.plugin_dropdown_input, PluginDropdownInput):
            logger.warning("PluginDropdownInput is not of type PluginDropdownInput")
        if not isinstance(self.plugin_remove_button, PluginRemoveButton):
            logger.warning("PluginRemoveButton is not of type PluginRemoveButton")
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
    """Merge a base TomSelectConfig with an override config.

    Args:
        base: The base configuration.
        override: The override configuration.

    Returns:
        The merged configuration.
    """
    if not override:
        return base
    # For each field in TomSelectConfig, if override has a non-default value, use it.
    # If it's None or not provided, keep base value.
    # Since these are dataclasses, we can do something more direct:
    # We'll just manually handle this for clarity
    combined = base.__dict__.copy()
    for field_name in override.__dataclass_fields__:
        val = getattr(override, field_name)
        if val is not None:
            if field_name == 'plugin_dropdown_header' and val:
                # Special handling for dropdown header to preserve translations
                header_dict = val.__dict__.copy()
                if 'extra_columns' in header_dict:
                    header_dict['extra_columns'] = header_dict.pop('extra_columns')
                combined[field_name] = PluginDropdownHeader(**header_dict)
            else:
                combined[field_name] = val
    return TomSelectConfig(**combined)
