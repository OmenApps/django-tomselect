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
    Handles merging of configuration from global defaults and instance-specific
    settings, managing widget attributes, and proper widget initialization.
    """

    field_base_class = forms.Field
    widget_class = None  # To be defined by subclasses

    def __init__(self, *args, choices=None, config: TomSelectConfig | dict = None, **kwargs):
        try:
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
            if config is not None:
                if not isinstance(config, TomSelectConfig):
                    try:
                        config = TomSelectConfig(**config)
                    except Exception as e:
                        package_logger.error(f"Failed to create TomSelectConfig from dict: {e}")
                        config = None

            final_config = merge_configs(base_config, config)
            self.config = final_config

            package_logger.debug(f"Final config to be passed to widget: {final_config}")

            # Get attrs from either the config or kwargs, with kwargs taking precedence
            attrs = kwargs.pop("attrs", {}) or {}
            if self.config.attrs:
                attrs = {**self.config.attrs, **attrs}

            package_logger.debug(f"Final attrs to be passed to widget: {attrs}")

            # Initialize the widget with config and attrs
            if not self.widget_class:
                package_logger.error(f"Widget class not defined for {self.__class__.__name__}")
                raise ValueError(f"Widget class not defined for {self.__class__.__name__}")

            self.widget = self.widget_class(config=self.config)
            self.widget.attrs = attrs

            super().__init__(*args, **kwargs)
        except Exception as e:
            package_logger.error(f"Error initializing {self.__class__.__name__}: {e}")
            raise


class BaseTomSelectModelMixin:
    """Mixin providing common initialization logic for TomSelect model fields.

    Similar to BaseTomSelectMixin but also handles queryset defaults and provides
    specialized validation for model-based selections. Manages configuration merging,
    widget attributes, and proper widget initialization with model querysets.
    """

    field_base_class = forms.Field
    widget_class = None  # To be defined by subclasses

    def __init__(self, *args, queryset=None, config: TomSelectConfig | dict = None, **kwargs):
        """Initialize a TomSelect model field with optional configuration.

        Sets up the widget with proper configuration and handles the queryset.

        Args:
            args: Positional arguments for the field
            queryset: Optional queryset for the model field (ignored)
            config: TomSelect configuration object or dictionary
            kwargs: Additional field options

        Raises:
            TypeError: If the config is a dict with invalid keys
        """
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
        if config is not None:
            if not isinstance(config, TomSelectConfig):
                try:
                    config = TomSelectConfig(**config)
                except TypeError as e:
                    package_logger.error(f"Failed to create TomSelectConfig from dict: {e}")
                    # Re-raise TypeError for invalid config keys to maintain expected behavior
                    raise TypeError(f"Invalid configuration: {e}") from e
                except Exception as e:
                    package_logger.error(f"Error creating TomSelectConfig: {e}")
                    config = None

        final_config = merge_configs(base_config, config)
        self.config = final_config

        package_logger.debug(f"Final config to be passed to widget: {final_config}")

        # Get attrs from either the config or kwargs, with kwargs taking precedence
        attrs = kwargs.pop("attrs", {}) or {}
        if self.config.attrs:
            attrs = {**self.config.attrs, **attrs}

        package_logger.debug(f"Final attrs to be passed to widget: {attrs}")

        # Initialize the widget with config and attrs
        if not self.widget_class:
            package_logger.error(f"Widget class not defined for {self.__class__.__name__}")
            raise ValueError(f"Widget class not defined for {self.__class__.__name__}")

        self.widget = self.widget_class(config=self.config)
        self.widget.attrs = attrs

        # Default queryset if not provided
        if queryset is None:
            queryset = EmptyModel.objects.none()

        try:
            super().__init__(queryset, *args, **kwargs)
        except Exception as e:
            package_logger.error(f"Error in parent initialization of {self.__class__.__name__}: {e}")
            raise

    def clean(self, value):
        """Validate the selected value(s) against the queryset.

        Updates the field's queryset from the widget before performing validation
        to ensure that validation is performed against the most current data.

        Args:
            value: The value to validate

        Returns:
            The validated value

        Raises:
            ValidationError: If the value cannot be validated
        """
        try:
            # Update queryset from widget before cleaning
            self.queryset = self.widget.get_queryset()
            return super().clean(value)
        except ValidationError:
            raise
        except Exception as e:
            package_logger.error(f"Error in clean method of {self.__class__.__name__}: {e}")
            raise ValidationError(f"An unexpected error occurred: {str(e)}")


class TomSelectChoiceField(BaseTomSelectMixin, forms.ChoiceField):
    """Single-select field for Tom Select.

    Provides a form field for selecting a single value from options provided
    by a TomSelect autocomplete source. Validates that the selected value
    is among the allowed choices.
    """

    field_base_class = forms.ChoiceField
    widget_class = TomSelectIterablesWidget

    def clean(self, value):
        """Validate that the selected value is among the allowed choices.

        Retrieves the autocomplete view and checks that the submitted value
        is in the set of allowed values.

        Args:
            value: The value to validate

        Returns:
            The validated value

        Raises:
            ValidationError: If the value is not among the allowed choices
        """
        if not self.required and not value:
            return None

        try:
            str_value = str(value)
            autocomplete_view = self.widget.get_autocomplete_view()
            if not autocomplete_view:
                package_logger.error(f"{self.__class__.__name__}: Could not determine autocomplete view")
                raise ValidationError("Could not determine allowed choices")

            try:
                all_items = autocomplete_view.get_iterable()
                allowed_values = {str(item["value"]) for item in all_items}
            except Exception as e:
                package_logger.error(f"Error getting choices from autocomplete view: {e}")
                raise ValidationError(f"Error determining allowed choices: {str(e)}")

            if str_value not in allowed_values:
                package_logger.debug(f"Invalid choice in {self.__class__.__name__}: {value}")
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": value},
                )

            return value
        except ValidationError:
            raise
        except Exception as e:
            package_logger.error(f"Error in clean method of {self.__class__.__name__}: {e}")
            raise ValidationError(f"An unexpected error occurred: {str(e)}")


class TomSelectMultipleChoiceField(BaseTomSelectMixin, forms.MultipleChoiceField):
    """Multi-select field for Tom Select.

    Provides a form field for selecting multiple values from options provided
    by a TomSelect autocomplete source. Validates that all selected values
    are among the allowed choices.
    """

    field_base_class = forms.MultipleChoiceField
    widget_class = TomSelectIterablesMultipleWidget

    def clean(self, value):
        """Validate that all selected values are allowed.

        Retrieves the autocomplete view and checks that all submitted values
        are in the set of allowed values.

        Args:
            value: The value or values to validate

        Returns:
            The validated value list

        Raises:
            ValidationError: If any of the values are not among the allowed choices
        """
        if not value:
            if self.required:
                raise ValidationError(self.error_messages["required"], code="required")
            return []

        try:
            # Ensure value is iterable
            if not hasattr(value, "__iter__") or isinstance(value, str):
                value = [value]

            str_values = [str(v) for v in value]
            autocomplete_view = self.widget.get_autocomplete_view()
            if not autocomplete_view:
                package_logger.error(f"{self.__class__.__name__}: Could not determine autocomplete view")
                raise ValidationError("Could not determine allowed choices")

            try:
                all_items = autocomplete_view.get_iterable()
                allowed_values = {str(item["value"]) for item in all_items}
            except Exception as e:
                package_logger.error(f"Error getting choices from autocomplete view: {e}")
                raise ValidationError(f"Error determining allowed choices: {str(e)}")

            invalid_values = [val for val in str_values if val not in allowed_values]
            if invalid_values:
                package_logger.debug(f"Invalid choice(s) in {self.__class__.__name__}: {invalid_values}")
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": invalid_values[0]},
                )

            return value
        except ValidationError:
            raise
        except Exception as e:
            package_logger.error(f"Error in clean method of {self.__class__.__name__}: {e}")
            raise ValidationError(f"An unexpected error occurred: {str(e)}")


class TomSelectModelChoiceField(BaseTomSelectModelMixin, forms.ModelChoiceField):
    """Wraps the TomSelectModelWidget as a form field.

    Provides a form field for selecting a single model instance from options
    provided by a TomSelect autocomplete source. Leverages Django's built-in
    ModelChoiceField validation with TomSelect UI enhancements.
    """

    field_base_class = forms.ModelChoiceField
    widget_class = TomSelectModelWidget


class TomSelectModelMultipleChoiceField(BaseTomSelectModelMixin, forms.ModelMultipleChoiceField):
    """Wraps the TomSelectModelMultipleWidget as a form field.

    Provides a form field for selecting multiple model instances from options
    provided by a TomSelect autocomplete source. Leverages Django's built-in
    ModelMultipleChoiceField validation with TomSelect UI enhancements.
    """

    field_base_class = forms.ModelMultipleChoiceField
    widget_class = TomSelectModelMultipleWidget
