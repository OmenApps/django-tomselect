import logging

from django import forms

from .app_settings import (
    DJANGO_TOMSELECT_BOOTSTRAP_VERSION,
    DJANGO_TOMSELECT_GENERAL_CONFIG,
    DJANGO_TOMSELECT_PLUGIN_CHECKBOX_OPTIONS,
    DJANGO_TOMSELECT_PLUGIN_CLEAR_BUTTON,
    DJANGO_TOMSELECT_PLUGIN_DROPDOWN_HEADER,
    DJANGO_TOMSELECT_PLUGIN_DROPDOWN_INPUT,
    DJANGO_TOMSELECT_PLUGIN_REMOVE_BUTTON,
    DJANGO_TOMSELECT_PLUGIN_VIRTUAL_SCROLL,
)
from .models import EmptyModel
from .widgets import TomSelectMultipleWidget, TomSelectWidget

logger = logging.getLogger(__name__)


class TomSelectField(forms.ModelChoiceField):
    """Wraps the TomSelectWidget as a form field."""

    def __init__(self, *args, **kwargs):
        """Instantiate a TomSelectField field."""
        self.widget = TomSelectWidget(
            url=kwargs.pop("url", "autocomplete"),
            listview_url=kwargs.pop("listview_url", ""),
            create_url=kwargs.pop("create_url", ""),
            update_url=kwargs.pop("update_url", ""),
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            filter_by=kwargs.pop("filter_by", ()),
            attrs=kwargs.pop("attrs", {}),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            general_config=kwargs.pop("general_config", DJANGO_TOMSELECT_GENERAL_CONFIG),
            plugin_checkbox_options=kwargs.pop("plugin_checkbox_options", DJANGO_TOMSELECT_PLUGIN_CHECKBOX_OPTIONS),
            plugin_clear_button=kwargs.pop("plugin_clear_button", DJANGO_TOMSELECT_PLUGIN_CLEAR_BUTTON),
            plugin_dropdown_header=kwargs.pop("plugin_dropdown_header", DJANGO_TOMSELECT_PLUGIN_DROPDOWN_HEADER),
            plugin_dropdown_input=kwargs.pop("plugin_dropdown_input", DJANGO_TOMSELECT_PLUGIN_DROPDOWN_INPUT),
            plugin_remove_button=kwargs.pop("plugin_remove_button", DJANGO_TOMSELECT_PLUGIN_REMOVE_BUTTON),
            plugin_virtual_scroll=kwargs.pop("plugin_virtual_scroll", DJANGO_TOMSELECT_PLUGIN_VIRTUAL_SCROLL),
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
            update_url=kwargs.pop("update_url", ""),
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            filter_by=kwargs.pop("filter_by", ()),
            attrs=kwargs.pop("attrs", {}),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            general_config=kwargs.pop("general_config", DJANGO_TOMSELECT_GENERAL_CONFIG),
            plugin_checkbox_options=kwargs.pop("plugin_checkbox_options", DJANGO_TOMSELECT_PLUGIN_CHECKBOX_OPTIONS),
            plugin_clear_button=kwargs.pop("plugin_clear_button", DJANGO_TOMSELECT_PLUGIN_CLEAR_BUTTON),
            plugin_dropdown_header=kwargs.pop("plugin_dropdown_header", DJANGO_TOMSELECT_PLUGIN_DROPDOWN_HEADER),
            plugin_dropdown_input=kwargs.pop("plugin_dropdown_input", DJANGO_TOMSELECT_PLUGIN_DROPDOWN_INPUT),
            plugin_remove_button=kwargs.pop("plugin_remove_button", DJANGO_TOMSELECT_PLUGIN_REMOVE_BUTTON),
            plugin_virtual_scroll=kwargs.pop("plugin_virtual_scroll", DJANGO_TOMSELECT_PLUGIN_VIRTUAL_SCROLL),
        )
        super().__init__(queryset, **kwargs)

    def clean(self, value):
        self.queryset = self.widget.get_queryset()
        return super().clean(value)
