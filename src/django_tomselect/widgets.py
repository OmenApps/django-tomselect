import copy
import json
from urllib.parse import unquote

from django import forms
from django.urls import resolve, reverse, reverse_lazy

from .settings import DJANGO_TOMSELECT_BOOTSTRAP_VERSION, ProxyRequest
from .models import EmptyModel


class TomSelectWidget(forms.Select):
    """
    A Tom Select widget with model object choices.

    The Tom Select element will be configured using custom data attributes on
    the select element, which are provided by the widget's `build_attrs` method.
    """

    def __init__(
        self,
        url="autocomplete",
        value_field="",
        label_field="",
        create_field="",
        listview_url="",
        add_url="",
        edit_url="",
        filter_by=(),
        bootstrap_version=DJANGO_TOMSELECT_BOOTSTRAP_VERSION,
        format_overrides=None,
        show_value_field=False,
        **kwargs,
    ):
        """
        Instantiate a TomSelectWidget widget.

        Args:
            url: the URL pattern name of the view that serves the choices and
              handles requests from the Tom Select element
            value_field: the name of the model field that corresponds to the
              choice value of an option (f.ex. 'id'). Defaults to the name of
              the model's primary key field.
            label_field: the name of the model field that corresponds to the
              human-readable value of an option (f.ex. 'name'). Defaults to the
              value of the model's `name_field` attribute. If the model has no
              `name_field` attribute, it defaults to 'name'.
            create_field: the name of the model field used to create new
              model objects with
            listview_url: URL name of the listview view for this model
            add_url: URL name of the add view for this model
            edit_url: URL name of the 'change' view for this model
            filter_by: a 2-tuple (form_field_name, field_lookup) to filter the
              results against the value of the form field using the given
              Django field lookup. For example:
               ('foo', 'bar__id') => results.filter(bar__id=data['foo'])
            bootstrap_version: the Bootstrap version to use for the widget. Can
                be set project-wide via settings.TOMSELECT_BOOTSTRAP_VERSION,
                or per-widget instance. Defaults to 5.
            format_overrides: a dictionary of formatting overrides to pass to
                the widget. See package docs for details.
            kwargs: additional keyword arguments passed to forms.Select
        """
        self.url = url
        self.value_field = value_field
        self.label_field = label_field
        self.create_field = create_field
        self.listview_url = listview_url
        self.add_url = add_url
        self.edit_url = edit_url
        self.filter_by = filter_by
        self.bootstrap_version = (
            bootstrap_version if bootstrap_version in (4, 5) else 5
        )  # ToDo: Rename to something more generic to allow for other frameworks
        self.format_overrides = format_overrides or {}
        self.template_name = "django_tomselect/select.html"
        self.show_value_field = show_value_field

        # print(f"self.url: {self.url}")

        super().__init__(**kwargs)

    def get_context(self, name, value, attrs):
        """Get the context for rendering the widget."""
        context = super().get_context(name, value, attrs)

        context["widget"]["highlight"] = True
        context["widget"]["open_on_focus"] = True
        context["widget"]["max_options"] = 50
        context["widget"]["max_items"] = 50
        context["widget"]["preload"] = 'focus'  # Either 'focus' or True/False

        context["widget"]["show_value_field"] = self.show_value_field
        context["widget"]["is_tabular"] = False

        context["widget"]["plugins"] = {}

        context["widget"]["plugins"]["checkbox_options"] = False

        context["widget"]["plugins"]["clear_button"] = {
            "title": "Clear Selections",
            "class_name": "clear-button",
        }

        context["widget"]["plugins"]["dropdown_header"] = {
            "title": "Autocomplete",
            "headerClass": "container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header",
            "titleRowClass": "row",
            "labelClass": "form-label",
            "valueFieldLabel": "Value",
            "labelFieldLabel": "Label",
            "labelColClass": "col-6",
            "show_value_field": self.show_value_field,
            "extraHeaders": [],
        }

        context["widget"]["plugins"]["dropdown_input"] = True

        context["widget"]["plugins"]["remove_button"] = {
            "label": "&times;",
            "title": "Remove this item",
            "class_name": "remove",
        }

        context["widget"]["plugins"]["virtual_scroll"] = True

        context["widget"]["value_field"] = self.value_field
        context["widget"]["label_field"] = self.label_field
        context["widget"]["search_lookups"] = self.get_search_lookups()
        context["widget"]["autocomplete_url"] = self.get_autocomplete_url()

        # if self.bootstrap_version == 4:
        #     self.template_name = "django_tomselect/select-bs4.html"
        # else:

        return context

    def optgroups(self, name, value, attrs=None):
        """Only query for selected model objects."""
        # print(f"self.choices.queryset: {self.choices.queryset}")
        # print(f"self.get_queryset(): {self.get_queryset()}")

        # inspired by dal.widgets.WidgetMixin from django-autocomplete-light
        selected_choices = [str(c) for c in value if c]  # Is this right?
        all_choices = copy.copy(self.choices)
        # TODO: empty values in selected_choices will be filtered out twice
        # self.choices.queryset = self.choices.queryset.filter(pk__in=[c for c in selected_choices if c])
        self.choices.queryset = self.get_queryset().filter(pk__in=[c for c in selected_choices if c])
        results = super().optgroups(name, value, attrs)
        self.choices = all_choices
        return results

    def get_autocomplete_url(self):
        """Hook to specify the autocomplete URL."""
        # print(f"get_autocomplete_url reverse(self.url): {reverse(self.url)}")
        return reverse_lazy(self.url)

    def get_add_url(self):
        """Hook to specify the URL to the model's add page."""
        if self.add_url:
            return reverse_lazy(self.add_url)

    def get_listview_url(self):
        """Hook to specify the URL the model's listview."""
        if self.listview_url:
            return reverse_lazy(self.listview_url)

    def get_edit_url(self):
        """Hook to specify the URL to the model's 'change' page."""
        if self.edit_url:
            return unquote(reverse_lazy(self.edit_url, args=["{pk}"]))

    def get_model(self):
        """Gets the model from the field's QuerySet"""
        # print(f"get_model self.choices.queryset.model: {self.choices.queryset.model}")
        return self.choices.queryset.model

    def get_autocomplete_view(self):
        """Gets the autocomplete view"""
        self.model = self.get_model()

        # Create a ProxyRequest that we can pass to the view to obtain its queryset
        proxy_request = ProxyRequest(model=self.model)

        autocomplete_view = resolve(self.get_autocomplete_url()).func.view_class()
        autocomplete_view.setup(model=self.model, request=proxy_request)

        # print(f"autocomplete_view: {autocomplete_view}")
        return autocomplete_view

    def get_queryset(self):
        """Gets the queryset from the autocomplete view"""
        autocomplete_view = self.get_autocomplete_view()
        # print(f"get_queryset autocomplete_view.get_queryset(): {autocomplete_view.get_queryset()}")
        return autocomplete_view.get_queryset()

    def get_search_lookups(self):
        """Gets the search lookups from the autocomplete view"""
        autocomplete_view = self.get_autocomplete_view()
        # print(f"get_search_lookups autocomplete_view.search_lookups: {autocomplete_view.search_lookups}")
        return autocomplete_view.search_lookups

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""

        self.get_queryset()
        # print(f"build_attrs self.get_queryset(): {self.get_queryset()}")

        self.value_field = self.value_field or self.model._meta.pk.name
        self.label_field = self.label_field or getattr(self.model, "name_field", "name")

        attrs = super().build_attrs(base_attrs, extra_attrs)
        opts = self.model._meta

        attrs.update(
            {
                "is-tomselect": True,
                "data-autocomplete-url": self.get_autocomplete_url(),
                "data-model": f"{opts.app_label}.{opts.model_name}",
                "data-value-field": self.value_field,
                "data-label-field": self.label_field,
                "data-create-field": self.create_field,
                "data-listview-url": self.get_listview_url() or "",
                "data-add-url": self.get_add_url() or "",
                "data-edit-url": self.get_edit_url() or "",
                "data-filter-by": json.dumps(list(self.filter_by)),
                "data-format-overrides": json.dumps(self.format_overrides),
            }
        )
        return attrs

    @property
    def media(self):
        if self.bootstrap_version == 4:
            return forms.Media(
                css={
                    "all": [
                        "django_tomselect/vendor/tom-select/css/tom-select.bootstrap4.css",
                        "django_tomselect/css/django-tomselect.css",
                    ],
                },
                # js=["django_tomselect/js/django-tomselect.js"],
            )
        else:
            return forms.Media(
                css={
                    "all": [
                        "django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.css",
                        "django_tomselect/css/django-tomselect.css",
                    ],
                },
                # js=["django_tomselect/js/django-tomselect.js"],
            )


class TomSelectTabularWidget(TomSelectWidget):
    """TomSelectWidget widget that displays results in a table with header."""

    def __init__(
        self,
        *args,
        extra_columns=None,
        value_field_label="",
        label_field_label="",
        show_value_field=False,
        **kwargs,
    ):
        """
        Instantiate a TomSelectTabularWidget widget.

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
            args: additional positional arguments passed to TomSelectWidget
            kwargs: additional keyword arguments passed to TomSelectWidget
        """
        super().__init__(**kwargs)
        self.value_field_label = value_field_label or self.value_field.title()
        self.label_field_label = label_field_label
        self.show_value_field = show_value_field
        self.extra_columns = extra_columns or {}

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)
        self.get_queryset()
        self.label_field_label = self.label_field_label or self.model._meta.verbose_name or "Object"

        attrs.update(
            {
                "is-tabular": True,
                "data-value-field-label": self.value_field_label,
                "data-label-field-label": self.label_field_label,
                "data-show-value-field": json.dumps(self.show_value_field),
                "data-extra-headers": json.dumps(list(self.extra_columns.values())),
                "data-extra-columns": json.dumps(list(self.extra_columns.keys())),
            }
        )
        return attrs

    def get_context(self, name, value, attrs):
        """Get the context for rendering the widget."""
        context = super().get_context(name, value, attrs)

        context["widget"]["is_tabular"] = True

        context["widget"]["plugins"]["dropdown_header"]["extraHeaders"] = list(self.extra_columns.values())
        context["widget"]["extra_columns"] = list(self.extra_columns.keys())
        context["widget"]["plugins"]["dropdown_header"]["labelColClass"] = (
            "col-5" if 0 < len(self.extra_columns) < 5 else "col"
        )

        return context


class MultipleSelectionMixin:
    """Enable multiple selection with TomSelect."""

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)  # noqa
        attrs["is-multiple"] = True
        return attrs


class TomSelectMultipleWidget(MultipleSelectionMixin, TomSelectWidget, forms.SelectMultiple):
    """A TomSelect widget that allows multiple selection."""


class TomSelectTabularMultipleWidget(MultipleSelectionMixin, TomSelectTabularWidget, forms.SelectMultiple):
    """A TomSelectTabular widget that allows multiple selection."""


class TomSelectField(forms.ModelChoiceField):
    """Wraps the TomSelectWidget as a form field."""

    def __init__(self, *args, **kwargs):
        """Instantiate a TomSelectField field."""
        self.widget = TomSelectWidget(
            url=kwargs.pop("url", "autocomplete"),
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            create_field=kwargs.pop("create_field", ""),
            listview_url=kwargs.pop("listview_url", ""),
            add_url=kwargs.pop("add_url", ""),
            edit_url=kwargs.pop("edit_url", ""),
            filter_by=kwargs.pop("filter_by", ()),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            format_overrides=kwargs.pop("format_overrides", {}),
            show_value_field=kwargs.pop("show_value_field", False),
            attrs=kwargs.pop("attrs", {}),
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
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            label_field_label=kwargs.pop("label_field_label", ""),
            create_field=kwargs.pop("create_field", ""),
            listview_url=kwargs.pop("listview_url", ""),
            add_url=kwargs.pop("add_url", ""),
            edit_url=kwargs.pop("edit_url", ""),
            filter_by=kwargs.pop("filter_by", ()),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            format_overrides=kwargs.pop("format_overrides", {}),
            show_value_field=kwargs.pop("show_value_field", False),
            extra_columns=kwargs.pop("extra_columns", {}),
            attrs=kwargs.pop("attrs", {}),
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
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            create_field=kwargs.pop("create_field", ""),
            listview_url=kwargs.pop("listview_url", ""),
            add_url=kwargs.pop("add_url", ""),
            edit_url=kwargs.pop("edit_url", ""),
            filter_by=kwargs.pop("filter_by", ()),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            format_overrides=kwargs.pop("format_overrides", {}),
            show_value_field=kwargs.pop("show_value_field", False),
            attrs=kwargs.pop("attrs", {}),
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
            value_field=kwargs.pop("value_field", ""),
            label_field=kwargs.pop("label_field", ""),
            label_field_label=kwargs.pop("label_field_label", ""),
            create_field=kwargs.pop("create_field", ""),
            listview_url=kwargs.pop("listview_url", ""),
            add_url=kwargs.pop("add_url", ""),
            edit_url=kwargs.pop("edit_url", ""),
            filter_by=kwargs.pop("filter_by", ()),
            bootstrap_version=kwargs.pop("bootstrap_version", DJANGO_TOMSELECT_BOOTSTRAP_VERSION),
            format_overrides=kwargs.pop("format_overrides", {}),
            show_value_field=kwargs.pop("show_value_field", False),
            extra_columns=kwargs.pop("extra_columns", {}),
            attrs=kwargs.pop("attrs", {}),
        )
        super().__init__(queryset=EmptyModel.objects.none(), **kwargs)

    def clean(self, value):
        self.queryset = self.widget.get_queryset()
        return super().clean(value)


