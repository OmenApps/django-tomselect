"""Configuration classes for the django-tomselect package."""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class BaseConfig:
    """Base configuration class for the django-tomselect widgets."""

    def as_dict(self):
        """Return the configuration as a dictionary."""
        return self.__dict__


@dataclass(kw_only=True)
class GeneralConfig(BaseConfig):  # pylint: disable=R0902
    """General configuration for the django-tomselect widgets."""

    close_after_select: Optional[bool] = None
    hide_placeholder: Optional[bool] = None
    highlight: bool = True
    load_throttle: int = 300
    loading_class: str = "loading"
    max_items: Optional[int] = 50
    max_options: Optional[int] = None
    open_on_focus: bool = True
    placeholder: Optional[str] = "Select a value"
    preload: Union[bool, str] = "focus"  # Either 'focus' or True/False
    minimum_query_length: int = 2

    create: bool = False  # Needs rework. If we supply a 'create' url, we should allow creation.
    create_filter: Optional[str] = None
    create_with_htmx: bool = False


@dataclass(kw_only=True)
class PluginCheckboxOptions(BaseConfig):
    """Plugin configuration for the checkbox_options plugin. No additional settings are required."""


@dataclass(kw_only=True)
class PluginDropdownInput(BaseConfig):
    """Plugin configuration for the dropdown_input plugin. No additional settings are required."""


@dataclass(kw_only=True)
class PluginClearButton(BaseConfig):
    """Plugin configuration for the clear_button plugin."""

    title: str = "Clear Selections"
    class_name: str = "clear-button"


@dataclass(kw_only=True)
class PluginDropdownHeader(BaseConfig):  # pylint: disable=R0902
    """Plugin configuration for the dropdown_header plugin.

    Args:
        extra_columns: a mapping of <model field names> to <column labels>
          for additional columns. The field name tells Tom Select what
          values to look up on a model object result for a given column.
          The label is the table header label for a given column.
        value_field_label: table header label for the value field column.
          Defaults to value_field.title().
        label_field_label: table header label for the label field column.
          Defaults to the verbose_name of the model.
        show_value_field: if True, show the value field column in the table.
    """

    title: str = "Autocomplete"
    header_class: str = "container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header"
    title_row_class: str = "row"
    label_class: str = "form-label"
    value_field_label: str = "Value"
    label_field_label: str = "Label"
    label_col_class: str = "col-6"  # Not currently used
    show_value_field: bool = False
    extra_columns: Optional[Dict] = None


@dataclass(kw_only=True)
class PluginDropdownFooter(BaseConfig):
    """Plugin configuration for the dropdown_footer plugin.

    Args:
        footer_class: CSS class for the footer container.
    """

    title: str = "Autocomplete Footer"
    footer_class: str = "container-fluid mt-1 px-2 border-top dropdown-footer"


@dataclass(kw_only=True)
class PluginRemoveButton(BaseConfig):
    """Plugin configuration for the remove_button plugin."""

    title: str = "Remove this item"
    label: str = "&times;"
    class_name: str = "remove"


class TomSelectConfig:
    """Configuration class for the TomSelect widget."""

    def __init__(self, **kwargs):
        """Set global defaults."""
        self.url = kwargs.get("url", "autocomplete")
        self.listview_url = kwargs.get("listview_url", "")
        self.create_url = kwargs.get("create_url", "")
        self.update_url = kwargs.get("update_url", "")
        self.value_field = kwargs.get("value_field", "id")
        self.label_field = kwargs.get("label_field", "name")
        self.create_field = kwargs.get("create_field", "")
        self.filter_by = kwargs.get("filter_by", ())
        self.use_htmx = kwargs.get("use_htmx", False)
        self.css_framework = kwargs.get("css_framework", "bootstrap")
        self.css_framework_version = kwargs.get("css_framework_version", 5)
        self.attrs = kwargs.get("attrs", {})
        # Config objects
        self.general_config = kwargs.get("general_config", GeneralConfig())
        self.plugin_checkbox_options = kwargs.get("plugin_checkbox_options", PluginCheckboxOptions())
        self.plugin_clear_button = kwargs.get("plugin_clear_button", PluginClearButton())
        self.plugin_dropdown_header = kwargs.get("plugin_dropdown_header", PluginDropdownHeader())
        self.plugin_dropdown_footer = kwargs.get("plugin_dropdown_footer", PluginDropdownFooter())
        self.plugin_dropdown_input = kwargs.get("plugin_dropdown_input", PluginDropdownInput())
        self.plugin_remove_button = kwargs.get("plugin_remove_button", PluginRemoveButton())
        self.verify_config_types()


    def update(self, **kwargs):
        """Update config with widget-level settings."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def as_dict(self):
        """Return the configuration as a dictionary."""
        return self.__dict__

    def verify_config_types(self):
        """Verify that the configuration types are correct."""
        # Check the general config
        if not isinstance(self.general_config, GeneralConfig):
            logger.warning("GeneralConfig is not of type GeneralConfig")
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
