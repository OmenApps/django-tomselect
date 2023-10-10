import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class BaseConfig:
    def as_dict(self):
        return self.__dict__


@dataclass(kw_only=True)
class GeneralConfig(BaseConfig):
    """
    General configuration for the TomSelect widget.
    """

    close_after_select: Optional[bool] = None
    hide_placeholder: Optional[bool] = None
    highlight: bool = True
    load_throttle: int = 300
    loading_class: str = "loading"
    max_items: int = 50
    max_options: int = 50
    open_on_focus: bool = True
    placeholder: Optional[str] = "Select a value"
    preload: Union[bool, str] = "focus"  # Either 'focus' or True/False

    create: bool = False  # Needs rework. If we supply a 'create' url, we should allow creation.
    create_filter: Optional[str] = None
    create_with_htmx: bool = False


@dataclass(kw_only=True)
class PluginCheckboxOptions(BaseConfig):
    pass


@dataclass(kw_only=True)
class PluginDropdownInput(BaseConfig):
    pass


@dataclass(kw_only=True)
class PluginVirtualScroll(BaseConfig):
    pass


@dataclass(kw_only=True)
class PluginClearButton(BaseConfig):
    title: str = "Clear Selections"
    class_name: str = "clear-button"


@dataclass(kw_only=True)
class PluginDropdownHeader(BaseConfig):
    """
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
    """
    Args:
        footer_class: CSS class for the footer container.
    """

    title: str = "Autocomplete Footer"
    footer_class: str = "container-fluid mt-1 px-2 border-top dropdown-footer"


@dataclass(kw_only=True)
class PluginRemoveButton(BaseConfig):
    title: str = "Remove this item"
    label: str = "&times;"
    class_name: str = "remove"
