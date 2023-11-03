import logging

from django import forms
from django.db.models.base import Model

from .app_settings import (
    DJANGO_TOMSELECT_BOOTSTRAP_VERSION,
    DJANGO_TOMSELECT_GENERAL_CONFIG,
    DJANGO_TOMSELECT_PLUGIN_CHECKBOX_OPTIONS,
    DJANGO_TOMSELECT_PLUGIN_CLEAR_BUTTON,
    DJANGO_TOMSELECT_PLUGIN_DROPDOWN_HEADER,
    DJANGO_TOMSELECT_PLUGIN_DROPDOWN_INPUT,
    DJANGO_TOMSELECT_PLUGIN_REMOVE_BUTTON,
)
from .models import EmptyModel
from .widgets import TomSelectMultipleWidget, TomSelectWidget

logger = logging.getLogger(__name__)


class TomSelectField(forms.ModelChoiceField):
    """Wraps the TomSelectWidget as a form field."""

    def __init__(self, queryset=EmptyModel.objects.none(), *args, **kwargs):
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
            use_htmx=kwargs.pop("use_htmx", False),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            general_config=kwargs.pop("general_config", DJANGO_TOMSELECT_GENERAL_CONFIG),
            plugin_checkbox_options=kwargs.pop("plugin_checkbox_options", DJANGO_TOMSELECT_PLUGIN_CHECKBOX_OPTIONS),
            plugin_clear_button=kwargs.pop("plugin_clear_button", DJANGO_TOMSELECT_PLUGIN_CLEAR_BUTTON),
            plugin_dropdown_header=kwargs.pop("plugin_dropdown_header", DJANGO_TOMSELECT_PLUGIN_DROPDOWN_HEADER),
            plugin_dropdown_input=kwargs.pop("plugin_dropdown_input", DJANGO_TOMSELECT_PLUGIN_DROPDOWN_INPUT),
            plugin_remove_button=kwargs.pop("plugin_remove_button", DJANGO_TOMSELECT_PLUGIN_REMOVE_BUTTON),
        )
        super().__init__(queryset, *args, **kwargs)        

    def clean(self, value):
        logger.debug(f"clean {value=}")
        self.queryset = self.widget.get_queryset()
        logger.debug(f"clean {self.queryset=}")
        return super().clean(value)
    
    def _set_queryset(self, queryset):
        logger.debug(f"_set_queryset {queryset=}")
        return super()._set_queryset(queryset)
    
    def to_python(self, value):
        logger.debug(f"to_python {value=}")
        logger.debug(f"to_python {self.to_field_name=}")
        return super().to_python(value)
    
    def validate(self, value: Model | None) -> None:
        logger.debug(f"validate {value=}")
        return super().validate(value)
    
    def prepare_value(self, value):
        logger.debug(f"prepare_value {self.__class__} {value=}")
        return super().prepare_value(value)


class TomSelectMultipleField(forms.ModelMultipleChoiceField):
    """Wraps the TomSelectMultipleWidget as a form field."""

    def __init__(self, queryset=EmptyModel.objects.none(), *args, **kwargs):
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
            use_htmx=kwargs.pop("use_htmx", False),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            general_config=kwargs.pop("general_config", DJANGO_TOMSELECT_GENERAL_CONFIG),
            plugin_checkbox_options=kwargs.pop("plugin_checkbox_options", DJANGO_TOMSELECT_PLUGIN_CHECKBOX_OPTIONS),
            plugin_clear_button=kwargs.pop("plugin_clear_button", DJANGO_TOMSELECT_PLUGIN_CLEAR_BUTTON),
            plugin_dropdown_header=kwargs.pop("plugin_dropdown_header", DJANGO_TOMSELECT_PLUGIN_DROPDOWN_HEADER),
            plugin_dropdown_input=kwargs.pop("plugin_dropdown_input", DJANGO_TOMSELECT_PLUGIN_DROPDOWN_INPUT),
            plugin_remove_button=kwargs.pop("plugin_remove_button", DJANGO_TOMSELECT_PLUGIN_REMOVE_BUTTON),
        )
        super().__init__(queryset, *args, **kwargs)

    def clean(self, value):
        logger.debug(f"clean {value=}")
        self.queryset = self.widget.get_queryset()
        logger.debug(f"clean {self.queryset=}")
        return super().clean(value)
    
    def _check_values(self, value):
        logger.debug(f"_check_values {value=}")
        qs = super()._check_values(value)
        logger.debug(f"_check_values {qs=}")
        return qs
    
    def _set_queryset(self, queryset):
        logger.debug(f"_set_queryset {queryset=}")
        return super()._set_queryset(queryset)
    
    def to_python(self, value):
        logger.debug(f"to_python {value=}")
        logger.debug(f"to_python {self.to_field_name=}")
        return super().to_python(value)
    
    def validate(self, value: Model | None) -> None:
        logger.debug(f"validate {value=}")
        return super().validate(value)
    
    def prepare_value(self, value):
        logger.debug(f"prepare_value {self.__class__} {value=}")
        return super().prepare_value(value)
