import json

from django import forms
from django.urls import reverse


class TomSelectWidget(forms.Select):
    """
    A Tom Select widget with model object choices.

    The Tom Select element will be configured using custom data attributes on
    the select element, which are provided by the widget's `build_attrs` method.
    """

    def __init__(
        self,
        model,
        url="autocomplete",
        value_field="",
        label_field="",
        search_lookups="",
        create_field="",
        multiple=False,
        listview_url="",
        add_url="",
        filter_by=(),
        **kwargs,
    ):
        """
        Instantiate a TomSelectWidget widget.

        Args:
            model: the django model that the choices are derived from
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
            multiple: if True, allow selecting multiple options
            listview_url: URL name of the listview view for this model
            add_url: URL name of the add view for this model
            filter_by: a 2-tuple (form_field_name, field_lookup) to filter the
              results against the value of the form field using the given
              Django field lookup. For example:
               ('foo', 'bar__id') => results.filter(bar__id=data['foo'])
            kwargs: additional keyword arguments passed to forms.Select
        """
        self.model = model
        self.url = url
        self.value_field = value_field or self.model._meta.pk.name
        self.label_field = label_field or getattr(self.model, "name_field", "name")
        self.search_lookups = search_lookups or [
            f"{self.value_field}__icontains",
            f"{self.label_field}__icontains",
        ]
        self.create_field = create_field
        self.multiple = multiple
        self.listview_url = listview_url
        self.add_url = add_url
        self.filter_by = filter_by
        super().__init__(**kwargs)

    def optgroups(self, name, value, attrs=None):
        return []  # Never provide any options; let the view serve the options.

    def get_url(self):
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

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)
        opts = self.model._meta
        attrs.update(
            {
                "is-tomselect": True,
                "is-multiple": self.multiple,
                "data-autocomplete-url": self.get_url(),
                "data-model": f"{opts.app_label}.{opts.model_name}",
                "data-search-lookup": json.dumps(self.search_lookups),
                "data-value-field": self.value_field,
                "data-label-field": self.label_field,
                "data-create-field": self.create_field,
                "data-listview-url": self.get_listview_url() or "",
                "data-add-url": self.get_add_url() or "",
                "data-filter-by": json.dumps(list(self.filter_by)),
            }
        )
        return attrs

    class Media:
        css = {
            "all": [
                "vendor/tom-select/css/tom-select.bootstrap5.css",
                "django_tomselect/css/django-tomselect.css",
            ],
        }
        js = ["django_tomselect/js/django-tomselect.js"]


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
        super().__init__(*args, **kwargs)
        self.value_field_label = value_field_label or self.value_field.title()
        self.label_field_label = label_field_label or self.model._meta.verbose_name or "Object"
        self.show_value_field = show_value_field
        self.extra_columns = extra_columns or {}

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)
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
