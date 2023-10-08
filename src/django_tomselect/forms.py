import logging

from django import forms

from .app_settings import DJANGO_TOMSELECT_BOOTSTRAP_VERSION
from .configs import (
    GeneralConfig,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    PluginVirtualScroll,
)
from .models import EmptyModel
from .widgets import (
    TomSelectMultipleWidget,
    TomSelectTabularMultipleWidget,
    TomSelectTabularWidget,
    TomSelectWidget,
)

logger = logging.getLogger(__name__)


class TomSelectField(forms.ModelChoiceField):
    """Wraps the TomSelectWidget as a form field."""

    def __init__(self, *args, **kwargs):
        """Instantiate a TomSelectField field."""
        self.widget = TomSelectWidget(
            url=kwargs.pop("url", "autocomplete"),
            listview_url=kwargs.pop("listview_url", ""),
            create_url=kwargs.pop("create_url", ""),
            edit_url=kwargs.pop("edit_url", ""),
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            filter_by=kwargs.pop("filter_by", ()),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            attrs=kwargs.pop("attrs", {}),
            general_config=kwargs.pop("general_config", GeneralConfig()),
            plugin_checkbox_options=kwargs.pop("plugin_checkbox_options", PluginCheckboxOptions()),
            plugin_clear_button=kwargs.pop("plugin_clear_button", PluginClearButton()),
            plugin_dropdown_header=kwargs.pop("plugin_dropdown_header", PluginDropdownHeader()),
            plugin_dropdown_input=kwargs.pop("plugin_dropdown_input", PluginDropdownInput()),
            plugin_remove_button=kwargs.pop("plugin_remove_button", PluginRemoveButton()),
            plugin_virtual_scroll=kwargs.pop("plugin_virtual_scroll", PluginVirtualScroll()),
        )
        super().__init__(queryset=EmptyModel.objects.none(), *args, **kwargs)

    def clean(self, value):
        self.queryset = self.widget.get_queryset()
        return super().clean(value)


class TomSelectTabularField(forms.ModelChoiceField):
    """Wraps the TomSelectTabularWidget as a form field."""

    def __init__(self, *args, **kwargs):
        """Instantiate a TomSelectTabularField field."""
        self.widget = TomSelectTabularWidget(
            url=kwargs.pop("url", "autocomplete"),
            listview_url=kwargs.pop("listview_url", ""),
            create_url=kwargs.pop("create_url", ""),
            edit_url=kwargs.pop("edit_url", ""),
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            filter_by=kwargs.pop("filter_by", ()),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            attrs=kwargs.pop("attrs", {}),
            general_config=kwargs.pop("general_config", GeneralConfig()),
            plugin_checkbox_options=kwargs.pop("plugin_checkbox_options", PluginCheckboxOptions()),
            plugin_clear_button=kwargs.pop("plugin_clear_button", PluginClearButton()),
            plugin_dropdown_header=kwargs.pop("plugin_dropdown_header", PluginDropdownHeader()),
            plugin_dropdown_input=kwargs.pop("plugin_dropdown_input", PluginDropdownInput()),
            plugin_remove_button=kwargs.pop("plugin_remove_button", PluginRemoveButton()),
            plugin_virtual_scroll=kwargs.pop("plugin_virtual_scroll", PluginVirtualScroll()),
        )
        super().__init__(queryset=EmptyModel.objects.none(), *args, **kwargs)

    def clean(self, value):
        self.queryset = self.widget.get_queryset()
        return super().clean(value)


class TomSelectMultipleField(forms.ModelMultipleChoiceField):
    """Wraps the TomSelectMultipleWidget as a form field."""

    def __init__(self, queryset=EmptyModel.objects.none(), **kwargs):
        """Instantiate a TomSelectMultipleField field."""
        self.widget = TomSelectMultipleWidget(
            url=kwargs.pop("url", "autocomplete"),
            listview_url=kwargs.pop("listview_url", ""),
            create_url=kwargs.pop("create_url", ""),
            edit_url=kwargs.pop("edit_url", ""),
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            filter_by=kwargs.pop("filter_by", ()),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            attrs=kwargs.pop("attrs", {}),
            general_config=kwargs.pop("general_config", GeneralConfig()),
            plugin_checkbox_options=kwargs.pop("plugin_checkbox_options", PluginCheckboxOptions()),
            plugin_clear_button=kwargs.pop("plugin_clear_button", PluginClearButton()),
            plugin_dropdown_header=kwargs.pop("plugin_dropdown_header", PluginDropdownHeader()),
            plugin_dropdown_input=kwargs.pop("plugin_dropdown_input", PluginDropdownInput()),
            plugin_remove_button=kwargs.pop("plugin_remove_button", PluginRemoveButton()),
            plugin_virtual_scroll=kwargs.pop("plugin_virtual_scroll", PluginVirtualScroll()),
        )
        super().__init__(queryset, **kwargs)

    def clean(self, value):
        self.queryset = self.widget.get_queryset()
        return super().clean(value)


class TomSelectTabularMultipleField(forms.ModelMultipleChoiceField):
    """Wraps the TomSelectTabularMultipleWidget as a form field."""

    def __init__(self, *args, **kwargs):
        """Instantiate a TomSelectTabularMultipleField field."""
        self.widget = TomSelectTabularMultipleWidget(
            url=kwargs.pop("url", "autocomplete"),
            listview_url=kwargs.pop("listview_url", ""),
            create_url=kwargs.pop("create_url", ""),
            edit_url=kwargs.pop("edit_url", ""),
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            filter_by=kwargs.pop("filter_by", ()),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            attrs=kwargs.pop("attrs", {}),
            general_config=kwargs.pop("general_config", GeneralConfig()),
            plugin_checkbox_options=kwargs.pop("plugin_checkbox_options", PluginCheckboxOptions()),
            plugin_clear_button=kwargs.pop("plugin_clear_button", PluginClearButton()),
            plugin_dropdown_header=kwargs.pop("plugin_dropdown_header", PluginDropdownHeader()),
            plugin_dropdown_input=kwargs.pop("plugin_dropdown_input", PluginDropdownInput()),
            plugin_remove_button=kwargs.pop("plugin_remove_button", PluginRemoveButton()),
            plugin_virtual_scroll=kwargs.pop("plugin_virtual_scroll", PluginVirtualScroll()),
        )
        super().__init__(queryset=EmptyModel.objects.none(), **kwargs)

    def clean(self, value):
        self.queryset = self.widget.get_queryset()
        return super().clean(value)
