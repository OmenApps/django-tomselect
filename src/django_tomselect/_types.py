"""Type definitions for django-tomselect."""

from typing import Any, Protocol, TypedDict


class SelectedOption(TypedDict, total=False):
    """A selected option in a TomSelect widget.

    Attributes:
        value: The option value (typically the primary key).
        label: The display label for the option.
        detail_url: URL to view the item details.
        update_url: URL to update the item.
        delete_url: URL to delete the item.
    """

    value: str
    label: str
    detail_url: str
    update_url: str
    delete_url: str


class PaginatedResponse(TypedDict):
    """Response from paginate_queryset().

    Attributes:
        results: List of result dictionaries.
        page: Current page number.
        has_more: Whether there are more pages.
        next_page: Next page number, or None if no more pages.
        total_pages: Total number of pages.
    """

    results: list[dict[str, Any]]
    page: int
    has_more: bool
    next_page: int | None
    total_pages: int


class PluginClearButton(TypedDict, total=False):
    """Clear button plugin configuration."""

    title: str
    class_name: str


class PluginRemoveButton(TypedDict, total=False):
    """Remove button plugin configuration."""

    title: str
    class_name: str


class PluginDropdownHeader(TypedDict, total=False):
    """Dropdown header plugin configuration."""

    title: str
    header_class: str
    title_row_class: str
    label_class: str
    value_field_label: str
    label_field_label: str
    label_col_class: str
    show_value_field: bool
    extra_headers: list[str]
    extra_values: list[str]


class PluginDropdownFooter(TypedDict, total=False):
    """Dropdown footer plugin configuration."""

    title: str
    footer_class: str


class PluginContext(TypedDict, total=False):
    """Plugin configuration context returned by get_plugin_context().

    Attributes:
        clear_button: Clear button plugin configuration.
        remove_button: Remove button plugin configuration.
        dropdown_header: Dropdown header plugin configuration.
        dropdown_footer: Dropdown footer plugin configuration.
        checkbox_options: Whether checkbox options plugin is enabled.
        dropdown_input: Whether dropdown input plugin is enabled.
    """

    clear_button: PluginClearButton
    remove_button: PluginRemoveButton
    dropdown_header: PluginDropdownHeader
    dropdown_footer: PluginDropdownFooter
    checkbox_options: bool
    dropdown_input: bool


class RequestLike(Protocol):
    """Protocol for request-like objects used in permission checking.

    This protocol defines the minimum interface required for objects
    passed to permission checking methods.
    """

    user: Any
    method: str
    GET: dict[str, Any]

    def get_full_path(self) -> str:
        """Return the full path of the request."""
        ...
