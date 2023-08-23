import copy
import json
from urllib.parse import unquote

from django import forms
from django.urls import resolve, reverse

from .settings import DJANGO_TOMSELECT_BOOTSTRAP_VERSION, ProxyRequest


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
        search_lookups=(),
        create_field="",
        listview_url="",
        add_url="",
        edit_url="",
        filter_by=(),
        bootstrap_version=DJANGO_TOMSELECT_BOOTSTRAP_VERSION,
        format_overrides=None,
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
            search_lookups: a list or tuple of Django field lookups to use with
              the given search term to filter the results
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
        self.model = None
        self.url = url
        self.value_field = value_field
        self.label_field = label_field
        self.search_lookups = search_lookups
        self.create_field = create_field
        self.listview_url = listview_url
        self.add_url = add_url
        self.edit_url = edit_url
        self.filter_by = filter_by
        self.bootstrap_version = bootstrap_version if bootstrap_version in (4, 5) else 5
        self.format_overrides = format_overrides or {}
        super().__init__(**kwargs)

    def optgroups(self, name, value, attrs=None):
        """Only query for selected model objects."""
        print("self.choices.queryset: ", self.choices.queryset)

        # inspired by dal.widgets.WidgetMixin from django-autocomplete-light
        selected_choices = [str(c) for c in value if c]  # Is this right?
        all_choices = copy.copy(self.choices)
        # TODO: empty values in selected_choices will be filtered out twice
        self.choices.queryset = self.choices.queryset.filter(pk__in=[c for c in selected_choices if c])
        results = super().optgroups(name, value, attrs)
        self.choices = all_choices
        return results

    def get_autocomplete_url(self):
        """Hook to specify the autocomplete URL."""
        return reverse(self.url)

    def get_add_url(self):
        """Hook to specify the URL to the model's add page."""
        if self.add_url:
            return reverse(self.add_url)

    def get_listview_url(self):
        """Hook to specify the URL the model's listview."""
        if self.listview_url:
            return reverse(self.listview_url)

    def get_edit_url(self):
        """Hook to specify the URL to the model's 'change' page."""
        if self.edit_url:
            return unquote(reverse(self.edit_url, args=["{pk}"]))

    def get_queryset(self):
        # Get the model from the field's QuerySet
        self.model = self.choices.queryset.model

        # Create a ProxyRequest that we can pass to the view to obtain its queryset
        proxy_request = ProxyRequest(model=self.model)

        autocomplete_view = resolve(self.get_autocomplete_url()).func.view_class()
        autocomplete_view.setup(model=self.model, request=proxy_request)
        return autocomplete_view.get_queryset()

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""

        self.get_queryset()

        self.value_field = self.value_field or self.model._meta.pk.name
        self.label_field = self.label_field or getattr(self.model, "name_field", "name")

        self.search_lookups = self.search_lookups or [
            f"{self.value_field}__icontains",
            f"{self.label_field}__icontains",
        ]

        attrs = super().build_attrs(base_attrs, extra_attrs)
        opts = self.model._meta

        attrs.update(
            {
                "is-tomselect": True,
                "data-autocomplete-url": self.get_autocomplete_url(),
                "data-model": f"{opts.app_label}.{opts.model_name}",
                "data-search-lookup": json.dumps(self.search_lookups),
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
                js=["django_tomselect/js/django-tomselect.js"],
            )
        else:
            return forms.Media(
                css={
                    "all": [
                        "django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.css",
                        "django_tomselect/css/django-tomselect.css",
                    ],
                },
                js=["django_tomselect/js/django-tomselect.js"],
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


class MultipleSelectionMixin:
    """Enable multiple selection with TomSelect."""

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)  # noqa
        attrs["is-multiple"] = True
        return attrs


class TomSelectMultipleWidget(MultipleSelectionMixin, TomSelectWidget, forms.SelectMultiple):
    """A MIZSelect widget that allows multiple selection."""


class TomSelectTabularMultipleWidget(MultipleSelectionMixin, TomSelectTabularWidget, forms.SelectMultiple):
    """A MIZSelectTabular widget that allows multiple selection."""
