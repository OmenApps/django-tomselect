import copy
import logging
from typing import Optional
from urllib.parse import unquote

from django import forms
from django.urls import NoReverseMatch, resolve, reverse_lazy

from .app_settings import (
    DJANGO_TOMSELECT_BOOTSTRAP_VERSION,
    DJANGO_TOMSELECT_MINIFIED,
    ProxyRequest,
)
from .configs import (
    GeneralConfig,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    PluginVirtualScroll,
)

logger = logging.getLogger(__name__)


class TomSelectWidget(forms.Select):
    """
    A Tom Select widget with model object choices.
    """

    def __init__(
        self,
        url: str = "autocomplete",
        listview_url: str = "",
        create_url: str = "",
        edit_url: str = "",
        value_field="",
        label_field="",
        create_field="",
        filter_by=(),
        bootstrap_version=DJANGO_TOMSELECT_BOOTSTRAP_VERSION,
        general_config: Optional[GeneralConfig] = GeneralConfig(),
        plugin_checkbox_options: Optional[PluginCheckboxOptions] = PluginCheckboxOptions(),
        plugin_clear_button: Optional[PluginClearButton] = PluginClearButton(),
        plugin_dropdown_header: Optional[PluginDropdownHeader] = PluginDropdownHeader(),
        plugin_dropdown_input: Optional[PluginDropdownInput] = PluginDropdownInput(),
        plugin_remove_button: Optional[PluginRemoveButton] = PluginRemoveButton(),
        plugin_virtual_scroll: Optional[PluginVirtualScroll] = PluginVirtualScroll(),
        **kwargs,
    ):
        """
        Instantiate a TomSelectWidget widget.

        Args:
            url: the URL pattern name of the view that serves the choices and
              handles requests from the Tom Select element
            listview_url: URL name of the listview view for this model
            create_url: URL name of the add view for this model
            edit_url: URL name of the 'change' view for this model
            value_field: the name of the model field that corresponds to the
              choice value of an option (f.ex. 'id'). Defaults to the name of
              the model's primary key field.
            label_field: the name of the model field that corresponds to the
              human-readable value of an option (f.ex. 'name'). Defaults to the
              value of the model's `name_field` attribute. If the model has no
              `name_field` attribute, it defaults to 'name'.
            create_field: the name of the model field used to create new
              model objects with
            filter_by: a 2-tuple (form_field_name, field_lookup) to filter the
              results against the value of the form field using the given
              Django field lookup. For example:
               ('foo', 'bar__id') => results.filter(bar__id=data['foo'])
            bootstrap_version: the Bootstrap version to use for the widget. Can
                be set project-wide via settings.TOMSELECT_BOOTSTRAP_VERSION,
                or per-widget instance. Defaults to 5.
            general_config: a GeneralConfig instance
            plugin_checkbox_options: a PluginCheckboxOptions instance
            plugin_clear_button: a PluginClearButton instance
            plugin_dropdown_header: a PluginDropdownHeader instance
            plugin_dropdown_input: a PluginDropdownInput instance
            plugin_remove_button: a PluginRemoveButton instance
            plugin_virtual_scroll: a PluginVirtualScroll instance
            kwargs: additional keyword arguments passed to forms.Select
        """
        self.url = url
        self.listview_url = listview_url
        self.create_url = create_url
        self.edit_url = edit_url

        self.value_field = value_field
        self.label_field = label_field

        self.create_field = create_field
        self.filter_by = filter_by
        self.bootstrap_version = (
            bootstrap_version if bootstrap_version in (4, 5) else 5
        )  # ToDo: Rename to something more generic to allow for other frameworks

        self.template_name = "django_tomselect/select.html"

        self.general_config = general_config if isinstance(general_config, GeneralConfig) or None else GeneralConfig()

        self.plugin_checkbox_options = (
            plugin_checkbox_options
            if any(
                [
                    isinstance(plugin_checkbox_options, PluginCheckboxOptions),
                    plugin_checkbox_options is None,
                ]
            )
            else PluginCheckboxOptions()
        )
        self.plugin_clear_button = (
            plugin_clear_button
            if any(
                [
                    isinstance(plugin_clear_button, PluginClearButton),
                    plugin_clear_button is None,
                ]
            )
            else PluginClearButton()
        )
        self.plugin_dropdown_header = (
            plugin_dropdown_header
            if any(
                [
                    isinstance(plugin_dropdown_header, PluginDropdownHeader),
                    plugin_dropdown_header is None,
                ]
            )
            else PluginDropdownHeader()
        )
        self.plugin_dropdown_input = (
            plugin_dropdown_input
            if any(
                [
                    isinstance(plugin_dropdown_input, PluginDropdownInput),
                    plugin_dropdown_input is None,
                ]
            )
            else PluginDropdownInput()
        )
        self.plugin_remove_button = (
            plugin_remove_button
            if any(
                [
                    isinstance(plugin_remove_button, PluginRemoveButton),
                    plugin_remove_button is None,
                ]
            )
            else PluginRemoveButton()
        )
        self.plugin_virtual_scroll = (
            plugin_virtual_scroll
            if any(
                [
                    isinstance(plugin_virtual_scroll, PluginVirtualScroll),
                    plugin_virtual_scroll is None,
                ]
            )
            else PluginVirtualScroll()
        )

        super().__init__(**kwargs)

    def get_context(self, name, value, attrs):
        """Get the context for rendering the widget."""
        context = super().get_context(name, value, attrs)

        context["widget"]["value_field"] = self.value_field
        context["widget"]["label_field"] = self.label_field

        context["widget"]["is_tabular"] = False

        context["widget"]["search_lookups"] = self.get_search_lookups()
        context["widget"]["autocomplete_url"] = self.get_autocomplete_url()

        context["widget"]["general_config"] = self.general_config.as_dict()
        context["widget"]["plugins"] = {}
        context["widget"]["plugins"]["clear_button"] = (
            self.plugin_clear_button.as_dict() if self.plugin_clear_button else None
        )
        context["widget"]["plugins"]["remove_button"] = (
            self.plugin_remove_button.as_dict() if self.plugin_remove_button else None
        )
        context["widget"]["plugins"]["dropdown_header"] = (
            self.plugin_dropdown_header.as_dict() if self.plugin_dropdown_header else None
        )

        context["widget"]["plugins"]["checkbox_options"] = True if self.plugin_checkbox_options else False
        context["widget"]["plugins"]["dropdown_input"] = True if self.plugin_dropdown_input else False
        context["widget"]["plugins"]["virtual_scroll"] = True if self.plugin_virtual_scroll else False

        return context

    def optgroups(self, name, value, attrs=None):
        """Only query for selected model objects."""

        # inspired by dal.widgets.WidgetMixin from django-autocomplete-light
        selected_choices = [str(c) for c in value if c]  # Is this right?
        all_choices = copy.copy(self.choices)
        # TODO: empty values in selected_choices will be filtered out twice
        self.choices.queryset = self.get_queryset().filter(pk__in=[c for c in selected_choices if c])
        results = super().optgroups(name, value, attrs)
        self.choices = all_choices
        return results

    def get_autocomplete_url(self):
        """Hook to specify the autocomplete URL."""
        try:
            return reverse_lazy(self.url)
        except NoReverseMatch as e:
            logger.exception("Error resolving autocomplete URL")
            raise NoReverseMatch("TomSelectWidget requires a resolvable 'url' attribute. Original error: %s" % e) from e

    def get_create_url(self):
        """Hook to specify the URL to the model's 'create' page."""
        if self.create_url:
            try:
                return reverse_lazy(self.create_url)
            except NoReverseMatch as e:
                logger.exception("Error resolving create URL")
                raise NoReverseMatch(
                    "TomSelectWidget requires a resolvable 'create_url' attribute. Original error: %s" % e
                ) from e

    def get_listview_url(self):
        """Hook to specify the URL the model's listview."""
        if self.listview_url:
            try:
                return reverse_lazy(self.listview_url)
            except NoReverseMatch as e:
                logger.exception("Error resolving listview URL")
                raise NoReverseMatch(
                    "TomSelectWidget requires a resolvable 'listview_url' attribute. Original error: %s" % e
                ) from e

    def get_edit_url(self):
        """Hook to specify the URL to the model's 'change' page."""
        if self.edit_url:
            try:
                return unquote(reverse_lazy(self.edit_url, args=["{pk}"]))
            except NoReverseMatch as e:
                logger.exception("Error resolving edit URL")
                raise NoReverseMatch(
                    "TomSelectWidget requires a resolvable 'edit_url' attribute. Original error: %s" % e
                ) from e

    def get_model(self):
        """Gets the model from the field's QuerySet"""
        return self.choices.queryset.model

    def get_autocomplete_view(self):
        """Gets the autocomplete view"""
        self.model = self.get_model()

        # Create a ProxyRequest that we can pass to the view to obtain its queryset
        proxy_request = ProxyRequest(model=self.model)

        autocomplete_view = resolve(self.get_autocomplete_url()).func.view_class()
        autocomplete_view.setup(model=self.model, request=proxy_request)

        return autocomplete_view

    def get_queryset(self):
        """Gets the queryset from the autocomplete view"""
        autocomplete_view = self.get_autocomplete_view()
        return autocomplete_view.get_queryset()

    def get_search_lookups(self):
        """Gets the search lookups from the autocomplete view"""
        autocomplete_view = self.get_autocomplete_view()
        return autocomplete_view.search_lookups

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build HTML attributes for the widget."""

        self.get_queryset()

        self.value_field = self.value_field or self.model._meta.pk.name
        self.label_field = self.label_field or getattr(self.model, "name_field", "name")

        attrs = super().build_attrs(base_attrs, extra_attrs)

        attrs.update(
            {
                "is-tomselect": True,
                "data-listview-url": self.get_listview_url() or "",
                "data-create-url": self.get_create_url() or "",
                "data-edit-url": self.get_edit_url() or "",
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
                js=[
                    "django_tomselect/js/django-tomselect.min.js"
                    if DJANGO_TOMSELECT_MINIFIED
                    else "django_tomselect/js/django-tomselect.js"
                ],
            )
        else:
            return forms.Media(
                css={
                    "all": [
                        "django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.css",
                        "django_tomselect/css/django-tomselect.css",
                    ],
                },
                js=[
                    "django_tomselect/js/django-tomselect.min.js"
                    if DJANGO_TOMSELECT_MINIFIED
                    else "django_tomselect/js/django-tomselect.js"
                ],
            )


class TomSelectTabularWidget(TomSelectWidget):
    """TomSelectWidget widget that displays results in a table with header."""

    def __init__(
        self,
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
        # self.value_field_label = value_field_label or self.value_field.title()
        # self.label_field_label = label_field_label or self.model._meta.verbose_name or "Object"

    def get_context(self, name, value, attrs):
        """Get the context for rendering the widget."""
        context = super().get_context(name, value, attrs)

        context["widget"]["is_tabular"] = True

        keys = [*self.plugin_dropdown_header.extra_columns.keys()]
        vals = [*self.plugin_dropdown_header.extra_columns.values()]
        context["widget"]["plugins"]["dropdown_header"]["extra_headers"] = vals
        context["widget"]["plugins"]["dropdown_header"]["extra_values"] = keys

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
