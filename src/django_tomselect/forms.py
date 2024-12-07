"""Forms for the django-tomselect package."""

from django import forms

from .configs import TomSelectConfig
from .models import EmptyModel
from .widgets import TomSelectMultipleWidget, TomSelectWidget


class TomSelectField(forms.ModelChoiceField):
    """Wraps the TomSelectWidget as a form field."""

    def __init__(self, *args, queryset=EmptyModel.objects.none(), config: TomSelectConfig = None, **kwargs):
        """Instantiate a TomSelectField field."""
        self.instance = kwargs.get("instance")
        # Extract widget-specific arguments that would be valid for TomSelectConfig
        widget_kwargs = {
            k: v for k, v in kwargs.items() if hasattr(TomSelectConfig, k) and not hasattr(forms.ModelChoiceField, k)
        }

        # Create config from widget kwargs if no config provided
        self.config = config or TomSelectConfig(**widget_kwargs)

        # Get attrs from either the config or kwargs, with kwargs taking precedence
        attrs = kwargs.pop("attrs", {})
        if self.config.attrs:
            attrs = {**self.config.attrs, **attrs}  # kwargs attrs override config attrs

        # Create the widget with the merged attrs
        self.widget = TomSelectWidget(config=self.config)
        # self.widget.attrs.update(attrs)
        self.widget.attrs = attrs

        # Pass remaining kwargs to parent class
        super().__init__(queryset, *args, **kwargs)

    def clean(self, value):
        """Return the queryset of objects that match the value."""
        # Gets the queryset from the widget, which is set by the view.
        self.queryset = self.widget.get_queryset()
        return super().clean(value)


class TomSelectMultipleField(forms.ModelMultipleChoiceField):
    """Wraps the TomSelectMultipleWidget as a form field."""

    def __init__(self, *args, queryset=EmptyModel.objects.none(), config: TomSelectConfig = None, **kwargs):
        """Instantiate a TomSelectMultipleField field."""
        self.instance = kwargs.get("instance")
        # Extract widget-specific arguments that would be valid for TomSelectConfig
        widget_kwargs = {
            k: v
            for k, v in kwargs.items()
            if hasattr(TomSelectConfig, k) and not hasattr(forms.ModelMultipleChoiceField, k)
        }

        # Create config from widget kwargs if no config provided
        self.config = config or TomSelectConfig(**widget_kwargs)

        # Get attrs from either the config or kwargs, with kwargs taking precedence
        attrs = kwargs.pop("attrs", {})
        if self.config.attrs:
            attrs = {**self.config.attrs, **attrs}  # kwargs attrs override config attrs

        # Create the widget with the merged attrs
        self.widget = TomSelectMultipleWidget(config=self.config)
        self.widget.attrs.update(attrs)

        # Pass remaining kwargs to parent class
        super().__init__(queryset, *args, **kwargs)

    def clean(self, value):
        """Return the queryset of objects that match the value."""
        # Gets the queryset from the widget, which is set by the view.
        self.queryset = self.widget.get_queryset()
        return super().clean(value)
