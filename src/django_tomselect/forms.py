"""Form fields for the django-tomselect package."""

__all__ = [
    "TomSelectChoiceField",
    "TomSelectMultipleChoiceField",
    "TomSelectModelChoiceField",
    "TomSelectModelMultipleChoiceField",
]

from typing import Any, ClassVar

from django import forms
from django.core.exceptions import FieldError, ValidationError
from django.db.models import QuerySet
from django.forms.widgets import Widget

from django_tomselect.app_settings import (
    GLOBAL_DEFAULT_CONFIG,
    TomSelectConfig,
    merge_configs,
)
from django_tomselect.lazy_utils import LazyView
from django_tomselect.logging import get_logger
from django_tomselect.models import EmptyModel
from django_tomselect.widgets import (
    TomSelectIterablesMultipleWidget,
    TomSelectIterablesWidget,
    TomSelectModelMultipleWidget,
    TomSelectModelWidget,
)

logger = get_logger(__name__)


class BaseTomSelectMixin:
    """Mixin providing common initialization logic for TomSelect fields.

    Extracts TomSelectConfig-related kwargs, sets up widget config and attrs.
    Handles merging of configuration from global defaults and instance-specific
    settings, managing widget attributes, and proper widget initialization.
    """

    field_base_class: ClassVar[type[forms.Field]] = forms.Field
    widget_class: ClassVar[type[Widget] | None] = None  # To be defined by subclasses
    config: TomSelectConfig
    widget: Widget

    def __init__(
        self, *args: Any, choices: Any = None, config: TomSelectConfig | dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """Initialize a TomSelect field with optional configuration."""
        try:
            if choices is not None:
                logger.warning("There is no need to pass choices to a TomSelectField. It will be ignored.")

            # Extract widget-specific arguments for TomSelectConfig
            widget_kwargs: dict[str, Any] = {
                k: v for k, v in kwargs.items() if hasattr(TomSelectConfig, k) and not hasattr(self.field_base_class, k)
            }

            # Pop these arguments out so they don't go into the parent's __init__
            for k in widget_kwargs:
                kwargs.pop(k, None)

            # Merge with GLOBAL_DEFAULT_CONFIG
            base_config: TomSelectConfig = GLOBAL_DEFAULT_CONFIG
            if config is not None:
                if not isinstance(config, TomSelectConfig):
                    try:
                        config = TomSelectConfig(**config)
                    except (TypeError, ValueError) as e:
                        logger.error("Failed to create TomSelectConfig from dict: %s", e, exc_info=True)
                        config = None

            final_config: TomSelectConfig = merge_configs(base_config, config)
            self.config = final_config

            logger.debug("Final config to be passed to widget: %s", final_config)

            # Get attrs from either the config or kwargs, with kwargs taking precedence
            attrs: dict[str, Any] = kwargs.pop("attrs", {}) or {}
            if self.config.attrs:
                attrs = {**self.config.attrs, **attrs}

            logger.debug("Final attrs to be passed to widget: %s", attrs)

            # Initialize the widget with config and attrs
            if not self.widget_class:
                logger.error("Widget class not defined for %s", self.__class__.__name__)
                raise ValueError(f"Widget class not defined for {self.__class__.__name__}")

            self.widget = self.widget_class(config=self.config)
            self.widget.attrs = attrs

            super().__init__(*args, **kwargs)
        except (TypeError, ValueError, AttributeError) as e:
            logger.error("Error initializing %s: %s", self.__class__.__name__, e, exc_info=True)
            raise


class BaseTomSelectModelMixin:
    """Mixin providing common initialization logic for TomSelect model fields.

    Similar to BaseTomSelectMixin but also handles queryset defaults and provides
    specialized validation for model-based selections. Manages configuration merging,
    widget attributes, and proper widget initialization with model querysets.
    """

    field_base_class: ClassVar[type[forms.Field]] = forms.Field
    widget_class: ClassVar[type[Widget] | None] = None  # To be defined by subclasses
    config: TomSelectConfig
    widget: Widget
    queryset: QuerySet
    instance: Any
    _lazy_view: LazyView | None

    def __init__(
        self,
        *args: Any,
        queryset: QuerySet | None = None,
        config: TomSelectConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a TomSelect model field with optional configuration."""
        if queryset is not None:
            logger.warning("There is no need to pass a queryset to a TomSelectModelField. It will be ignored.")
        self.instance: Any = kwargs.get("instance")

        # Extract widget-specific arguments for TomSelectConfig
        widget_kwargs: dict[str, Any] = {
            k: v for k, v in kwargs.items() if hasattr(TomSelectConfig, k) and not hasattr(self.field_base_class, k)
        }

        # Pop these arguments out so they don't go into the parent's __init__
        for k in widget_kwargs:
            kwargs.pop(k, None)

        # Merge with GLOBAL_DEFAULT_CONFIG
        base_config: TomSelectConfig = GLOBAL_DEFAULT_CONFIG
        if config is not None:
            if not isinstance(config, TomSelectConfig):
                try:
                    config = TomSelectConfig(**config)
                except TypeError as e:
                    logger.error("Failed to create TomSelectConfig from dict: %s", e)
                    # Re-raise TypeError for invalid config keys to maintain expected behavior
                    raise TypeError(f"Invalid configuration: {e}") from e
                except ValueError as e:
                    logger.error("Error creating TomSelectConfig: %s", e, exc_info=True)
                    config = None

        final_config: TomSelectConfig = merge_configs(base_config, config)
        self.config = final_config

        logger.debug("Final config to be passed to widget: %s", final_config)

        self._lazy_view = None

        # Get attrs from either the config or kwargs, with kwargs taking precedence
        attrs: dict[str, Any] = kwargs.pop("attrs", {}) or {}
        if self.config.attrs:
            attrs = {**self.config.attrs, **attrs}

        logger.debug("Final attrs to be passed to widget: %s", attrs)

        # Initialize the widget with config and attrs
        if not self.widget_class:
            logger.error("Widget class not defined for %s", self.__class__.__name__)
            raise ValueError(f"Widget class not defined for {self.__class__.__name__}")

        self.widget = self.widget_class(config=self.config)
        self.widget.attrs = attrs

        # Set to_field_name based on value_field configuration to aid ModelChoiceField validation
        if hasattr(self.config, "value_field") and self.config.value_field:
            if self.config.value_field != "pk":
                kwargs["to_field_name"] = self.config.value_field
                logger.debug("Set to_field_name to: %s", self.config.value_field)

        # Use EmptyModel queryset initially - the actual queryset will be resolved lazily
        # when needed (during clean/validation). This avoids circular imports that occur
        # when URL resolution is triggered during form class definition.
        if queryset is None:
            queryset = EmptyModel.objects.none()

        try:
            super().__init__(queryset, *args, **kwargs)
        except (TypeError, ValueError, AttributeError) as e:
            logger.error("Error in parent initialization of %s: %s", self.__class__.__name__, e, exc_info=True)
            raise

    def clean(self, value: Any) -> Any:
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
            widget_queryset = self.widget.get_queryset()
            if widget_queryset is not None and hasattr(widget_queryset, "model"):
                # Only update if it's not EmptyModel
                if widget_queryset.model != EmptyModel:
                    self.queryset = widget_queryset
                    logger.debug("Updated queryset in clean to: %s", widget_queryset.model)
                else:
                    logger.debug(
                        "Widget queryset is EmptyModel, keeping original queryset. "
                        "This may indicate a URL configuration issue or unresolved lazy view."
                    )

            # Make sure to_field_name is set correctly based on value_field
            if hasattr(self.config, "value_field") and self.config.value_field:
                if self.config.value_field != "pk":
                    self.to_field_name = self.config.value_field
                    logger.debug("Set/Updated to_field_name in clean to: %s", self.config.value_field)
                else:
                    # Explicitly set to None if value_field is 'pk'
                    self.to_field_name = None
                    logger.debug("Reset to_field_name to None for pk-based lookup")

            # Clean the value before passing to validation
            cleaned_value = self._clean_value(value)

            return super().clean(cleaned_value)
        except ValidationError:
            raise
        except (AttributeError, TypeError, FieldError) as e:
            logger.error("Error in clean method of %s: %s", self.__class__.__name__, e, exc_info=True)
            raise ValidationError(f"An unexpected error occurred: {str(e)}") from e

    def _clean_value(self, value: Any) -> Any:
        """Clean the input value by removing surrounding quotes if needed."""
        if value is None:
            return value

        # Convert to string for processing
        if not isinstance(value, str):
            return value

        # Remove surrounding quotes if present (e.g.: "'uuid-string'" >> "uuid-string")
        cleaned_value = value.strip()

        # Remove outer quotes if they exist
        if len(cleaned_value) >= 2:
            if (cleaned_value.startswith("'") and cleaned_value.endswith("'")) or (
                cleaned_value.startswith('"') and cleaned_value.endswith('"')
            ):
                cleaned_value = cleaned_value[1:-1]

        return cleaned_value


class TomSelectChoiceField(BaseTomSelectMixin, forms.ChoiceField):
    """Single-select field for Tom Select.

    Provides a form field for selecting a single value from options provided
    by a TomSelect autocomplete source. Validates that the selected value
    is among the allowed choices.
    """

    field_base_class: ClassVar[type[forms.ChoiceField]] = forms.ChoiceField
    widget_class: ClassVar[type[TomSelectIterablesWidget]] = TomSelectIterablesWidget

    def clean(self, value: Any) -> Any:
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
                logger.error("%s: Could not determine autocomplete view", self.__class__.__name__)
                raise ValidationError("Could not determine allowed choices")

            try:
                all_items = autocomplete_view.get_iterable()
                allowed_values = {str(item["value"]) for item in all_items}
            except (AttributeError, TypeError, KeyError) as e:
                logger.error("Error getting choices from autocomplete view: %s", e, exc_info=True)
                raise ValidationError(f"Error determining allowed choices: {str(e)}") from e

            if str_value not in allowed_values:
                logger.debug("Invalid choice in %s: %s", self.__class__.__name__, value)
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": value},
                )

            return value
        except ValidationError:
            raise
        except (AttributeError, TypeError) as e:
            logger.error("Error in clean method of %s: %s", self.__class__.__name__, e, exc_info=True)
            raise ValidationError(f"An unexpected error occurred: {str(e)}") from e


class TomSelectMultipleChoiceField(BaseTomSelectMixin, forms.MultipleChoiceField):
    """Multi-select field for Tom Select.

    Provides a form field for selecting multiple values from options provided
    by a TomSelect autocomplete source. Validates that all selected values
    are among the allowed choices.
    """

    field_base_class: ClassVar[type[forms.MultipleChoiceField]] = forms.MultipleChoiceField
    widget_class: ClassVar[type[TomSelectIterablesMultipleWidget]] = TomSelectIterablesMultipleWidget

    def clean(self, value: Any) -> list[Any]:
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
                logger.error("%s: Could not determine autocomplete view", self.__class__.__name__)
                raise ValidationError("Could not determine allowed choices")

            try:
                all_items = autocomplete_view.get_iterable()
                allowed_values = {str(item["value"]) for item in all_items}
            except (AttributeError, TypeError, KeyError) as e:
                logger.error("Error getting choices from autocomplete view: %s", e, exc_info=True)
                raise ValidationError(f"Error determining allowed choices: {str(e)}") from e

            invalid_values = [val for val in str_values if val not in allowed_values]
            if invalid_values:
                logger.debug("Invalid choice(s) in %s: %s", self.__class__.__name__, invalid_values)
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": invalid_values[0]},
                )

            return value
        except ValidationError:
            raise
        except (AttributeError, TypeError) as e:
            logger.error("Error in clean method of %s: %s", self.__class__.__name__, e, exc_info=True)
            raise ValidationError(f"An unexpected error occurred: {str(e)}") from e


class TomSelectModelChoiceField(BaseTomSelectModelMixin, forms.ModelChoiceField):
    """Wraps the TomSelectModelWidget as a form field.

    Provides a form field for selecting a single model instance from options
    provided by a TomSelect autocomplete source. Leverages Django's built-in
    ModelChoiceField validation with TomSelect UI enhancements.
    """

    field_base_class: ClassVar[type[forms.ModelChoiceField]] = forms.ModelChoiceField
    widget_class: ClassVar[type[TomSelectModelWidget]] = TomSelectModelWidget


class TomSelectModelMultipleChoiceField(BaseTomSelectModelMixin, forms.ModelMultipleChoiceField):
    """Wraps the TomSelectModelMultipleWidget as a form field.

    Provides a form field for selecting multiple model instances from options
    provided by a TomSelect autocomplete source. Leverages Django's built-in
    ModelMultipleChoiceField validation with TomSelect UI enhancements.
    """

    field_base_class: ClassVar[type[forms.ModelMultipleChoiceField]] = forms.ModelMultipleChoiceField
    widget_class: ClassVar[type[TomSelectModelMultipleWidget]] = TomSelectModelMultipleWidget
