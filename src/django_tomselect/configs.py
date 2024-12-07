"""Configuration classes for the django-tomselect package."""

import logging
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, Union

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BaseConfig:
    """Base configuration class for django-tomselect widgets with validation."""

    def validate(self) -> None:
        """Validate configuration values. Override in subclasses."""
        pass

    def __post_init__(self):
        """Validate config after initialization."""
        self.validate()

    def as_dict(self):
        """Return the configuration as a dictionary."""
        return self.__dict__


@dataclass(frozen=True)
class GeneralConfig(BaseConfig):
    """General configuration for TomSelect widgets."""

    close_after_select: Optional[bool] = None
    hide_placeholder: Optional[bool] = None
    highlight: bool = True
    load_throttle: int = 300
    loading_class: str = "loading"
    max_items: Optional[int] = 50
    max_options: Optional[int] = None
    open_on_focus: bool = True
    placeholder: Optional[str] = "Select a value"
    preload: Union[Literal["focus"], bool] = "focus"  # Either 'focus' or True/False
    create: bool = False  # ToDo: Needs rework. If we supply a 'create' url, we should allow creation.
    create_filter: Optional[str] = None
    create_with_htmx: bool = False
    minimum_query_length: int = 2

    def validate(self) -> None:
        """Validate general config values."""
        if self.load_throttle < 0:
            raise ValidationError("load_throttle must be positive")
        if self.max_items is not None and self.max_items < 1:
            raise ValidationError("max_items must be greater than 0")
        if self.max_options is not None and self.max_options < 1:
            raise ValidationError("max_options must be greater than 0")
        if self.minimum_query_length < 0:
            raise ValidationError("minimum_query_length must be positive")


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
class PluginDropdownHeader(BaseConfig):  # pylint: disable=R0902
    """Plugin configuration for the dropdown_header plugin.

    Args:
        title: title for the dropdown header.
        header_class: CSS class for the header container.
        title_row_class: CSS class for the title row.
        label_class: CSS class for the label.
        value_field_label: table header label for the value field column.
          Defaults to value_field.title().
        label_field_label: table header label for the label field column.
          Defaults to the verbose_name of the model.
        label_col_class: CSS class for the label column.
        show_value_field: if True, show the value field column in the table.
        extra_columns: a mapping of <model field names> to <column labels>
          for additional columns. The field name tells Tom Select what
          values to look up on a model object result for a given column.
          The label is the table header label for a given column.
    """

    title: str = "Autocomplete"
    header_class: str = "container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header"
    title_row_class: str = "row"
    label_class: str = "form-label"
    value_field_label: str = "Value"
    label_field_label: str = "Label"
    label_col_class: str = "col-6"  # ToDo: Not currently used
    show_value_field: bool = False
    extra_columns: Dict[str, str] = field(default_factory=dict)

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


@dataclass(frozen=True)
class PluginRemoveButton(BaseConfig):
    """Plugin configuration for the remove_button plugin.

    Args:
        title: title for the remove button.
        label: label for the remove button.
        class_name: CSS class for the remove button.
    """

    title: str = "Remove this item"
    label: str = "&times;"
    class_name: str = "remove"


@dataclass(frozen=True)
class TomSelectConfig(BaseConfig):
    """Main configuration class for TomSelect widgets.

    Args:
        url: URL for the autocomplete view.
        listview_url: URL for the listview view.
        create_url: URL for the create view.
        update_url: URL for the update view.
        value_field: field name for the value field.
        label_field: field name for the label field.
        create_field: field name for the create field.
        filter_by: tuple of model field and lookup value to filter by.
        exclude_by: tuple of model field and lookup value to exclude by.
        use_htmx: if True, use HTMX for AJAX requests.
        css_framework: CSS framework to use ("default", "bootstrap4", "bootstrap5").
        attrs: additional attributes for the widget.

        general_config: GeneralConfig instance.
        plugin_checkbox_options: PluginCheckboxOptions instance.
        plugin_clear_button: PluginClearButton instance.
        plugin_dropdown_header: PluginDropdownHeader instance.
        plugin_dropdown_footer: PluginDropdownFooter instance.
        plugin_dropdown_input: PluginDropdownInput instance.
        plugin_remove_button: PluginRemoveButton instance.
    """

    url: str = "autocomplete"
    listview_url: str = ""
    create_url: str = ""
    update_url: str = ""
    value_field: str = "id"
    label_field: str = "name"
    create_field: str = ""
    filter_by: tuple = field(default_factory=tuple)
    exclude_by: tuple = field(default_factory=tuple)
    use_htmx: bool = False
    css_framework: Literal["default"] = "default"
    attrs: Dict[str, str] = field(default_factory=dict)

    # Plugin configurations
    general_config: GeneralConfig = field(default_factory=GeneralConfig)
    plugin_checkbox_options: Optional["PluginCheckboxOptions"] = None
    plugin_clear_button: Optional["PluginClearButton"] = None
    plugin_dropdown_header: Optional[PluginDropdownHeader] = None
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

    def as_dict(self) -> Dict:
        """Convert config to dictionary for template rendering."""
        return {k: v.as_dict() if isinstance(v, BaseConfig) else v for k, v in self.__dict__.items()}

    def update(self, **kwargs):
        """Update config with widget-level settings."""
        for key, value in kwargs.items():
            setattr(self, key, value)

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
