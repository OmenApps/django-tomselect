"""Form fields for the django-tomselect package."""

from django import forms
from django.core.exceptions import ValidationError

from django_tomselect.app_settings import (
    GLOBAL_DEFAULT_CONFIG,
    TomSelectConfig,
    merge_configs,
)
from django_tomselect.logging import package_logger
from django_tomselect.models import EmptyModel
from django_tomselect.widgets import (
    TomSelectIterablesMultipleWidget,
    TomSelectIterablesWidget,
    TomSelectModelMultipleWidget,
    TomSelectModelWidget,
)


class BaseTomSelectMixin:
    """Mixin providing common initialization logic for TomSelect fields.

    Extracts TomSelectConfig-related kwargs, sets up widget config and attrs.
    """

    field_base_class = forms.Field
    widget_class = None  # To be defined by subclasses

    def __init__(self, *args, choices=None, config: TomSelectConfig = None, **kwargs):
        if choices is not None:
            package_logger.warning("There is no need to pass choices to a TomSelectField. It will be ignored.")
        self.instance = kwargs.get("instance")

        # Extract widget-specific arguments for TomSelectConfig
        widget_kwargs = {
            k: v for k, v in kwargs.items() if hasattr(TomSelectConfig, k) and not hasattr(self.field_base_class, k)
        }

        # Pop these arguments out so they don't go into the parent's __init__
        for k in widget_kwargs:
            kwargs.pop(k, None)

        # Merge with GLOBAL_DEFAULT_CONFIG
        base_config = GLOBAL_DEFAULT_CONFIG
        if config and not isinstance(config, TomSelectConfig):
            config = TomSelectConfig(**config)
        final_config = merge_configs(base_config, config)
        self.config = final_config

        package_logger.debug(f"Final config to be passed to widget: {final_config}")

        # Get attrs from either the config or kwargs, with kwargs taking precedence
        attrs = kwargs.pop("attrs", {})
        if self.config.attrs:
            attrs = {**self.config.attrs, **attrs}

        package_logger.debug(f"Final attrs to be passed to widget: {attrs}")

        # Initialize the widget with config and attrs
        self.widget = self.widget_class(config=self.config)
        self.widget.attrs = attrs

        super().__init__(*args, **kwargs)


class BaseTomSelectModelMixin:
    """Mixin providing common initialization logic for TomSelect model fields.

    Similar to BaseTomSelectMixin but also handles queryset defaults.
    """

    field_base_class = forms.Field
    widget_class = None  # To be defined by subclasses

    def __init__(self, *args, queryset=None, config: TomSelectConfig = None, **kwargs):
        if queryset is not None:
            package_logger.warning("There is no need to pass a queryset to a TomSelectModelField. It will be ignored.")
        self.instance = kwargs.get("instance")

        # Extract widget-specific arguments for TomSelectConfig
        widget_kwargs = {
            k: v for k, v in kwargs.items() if hasattr(TomSelectConfig, k) and not hasattr(self.field_base_class, k)
        }

        # Pop these arguments out so they don't go into the parent's __init__
        for k in widget_kwargs:
            kwargs.pop(k, None)

        # Merge with GLOBAL_DEFAULT_CONFIG
        base_config = GLOBAL_DEFAULT_CONFIG
        if config and not isinstance(config, TomSelectConfig):
            config = TomSelectConfig(**config)
        final_config = merge_configs(base_config, config)
        self.config = final_config

        package_logger.debug(f"Final config to be passed to widget: {final_config}")

        # Get attrs from either the config or kwargs, with kwargs taking precedence
        attrs = kwargs.pop("attrs", {})
        if self.config.attrs:
            attrs = {**self.config.attrs, **attrs}

        package_logger.debug(f"Final attrs to be passed to widget: {attrs}")

        # Initialize the widget with config and attrs
        self.widget = self.widget_class(config=self.config)
        self.widget.attrs = attrs

        # Default queryset if not provided
        if queryset is None:
            queryset = EmptyModel.objects.none()

        super().__init__(queryset, *args, **kwargs)

    def clean(self, value):
        """Validate the selected value(s) against the queryset."""
        # Update queryset from widget before cleaning
        self.queryset = self.widget.get_queryset()
        return super().clean(value)


class TomSelectChoiceField(BaseTomSelectMixin, forms.ChoiceField):
    """Single-select field for Tom Select."""

    field_base_class = forms.ChoiceField
    widget_class = TomSelectIterablesWidget

    def clean(self, value):
        """Validate that the selected value is among the allowed choices."""
        if not self.required and not value:
            return None

        str_value = str(value)
        autocomplete_view = self.widget.get_autocomplete_view()
        if not autocomplete_view:
            raise ValidationError("Could not determine allowed choices")

        all_items = autocomplete_view.get_iterable()
        allowed_values = {str(item["value"]) for item in all_items}

        if str_value not in allowed_values:
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

        return value


class TomSelectMultipleChoiceField(BaseTomSelectMixin, forms.MultipleChoiceField):
    """Multi-select field for Tom Select."""

    field_base_class = forms.MultipleChoiceField
    widget_class = TomSelectIterablesMultipleWidget

    def clean(self, value):
        """Validate that all selected values are allowed."""
        if not value:
            if self.required:
                raise ValidationError(self.error_messages["required"], code="required")
            return []

        str_values = [str(v) for v in value]
        autocomplete_view = self.widget.get_autocomplete_view()
        if not autocomplete_view:
            raise ValidationError("Could not determine allowed choices")

        all_items = autocomplete_view.get_iterable()
        allowed_values = {str(item["value"]) for item in all_items}

        invalid_values = [val for val in str_values if val not in allowed_values]
        if invalid_values:
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": invalid_values[0]},
            )

        return value


class TomSelectModelChoiceField(BaseTomSelectModelMixin, forms.ModelChoiceField):
    """Wraps the TomSelectModelWidget as a form field."""

    field_base_class = forms.ModelChoiceField
    widget_class = TomSelectModelWidget


class TomSelectModelMultipleChoiceField(BaseTomSelectModelMixin, forms.ModelMultipleChoiceField):
    """Wraps the TomSelectModelMultipleWidget as a form field."""

    field_base_class = forms.ModelMultipleChoiceField
    widget_class = TomSelectModelMultipleWidget
