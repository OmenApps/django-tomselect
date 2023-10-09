from django import forms

from django_tomselect.configs import (
    GeneralConfig,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    PluginVirtualScroll,
)
from django_tomselect.forms import (
    TomSelectField,
    TomSelectMultipleField,
    TomSelectTabularField,
    TomSelectTabularMultipleField,
)

from .models import Edition, Magazine, ModelFormTestModel

general_config = GeneralConfig()
plugin_checkbox_options = PluginCheckboxOptions()
plugin_clear_button = PluginClearButton()
plugin_dropdown_header = PluginDropdownHeader(
    show_value_field=False,
    label_field_label="Edition",
    value_field_label="Value",
    extra_columns={
        "year": "Year",
        "pages": "Pages",
        "pub_num": "Publication Number",
    },
)
plugin_dropdown_input = PluginDropdownInput()
plugin_remove_button = PluginRemoveButton()
plugin_virtual_scroll = PluginVirtualScroll()


class Form(forms.Form):
    tomselect = TomSelectField(
        url="autocomplete-edition",
        # create_field="name",  # ToDo: Move to config
        listview_url="listview",
        create_url="create",
        value_field="id",
        label_field="name",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
        },
        required=False,
        general_config=general_config,
    )
    tomselect_tabular = TomSelectTabularField(
        url="autocomplete-edition",
        attrs={
            "class": "form-control mb-3",
        },
        listview_url="listview",
        create_url="create",
        value_field="id",
        label_field="name",
        required=False,
        general_config=general_config,
        plugin_dropdown_header=plugin_dropdown_header,
    )

    # Multiple selection:
    tomselect_multiple = TomSelectMultipleField(
        url="autocomplete-edition",
        attrs={
            "class": "form-control mb-3",
        },
        listview_url="listview",
        value_field="id",
        label_field="name",
        required=False,
        general_config=general_config,
    )
    tomselect_tabular_multiple_with_value_field = TomSelectTabularMultipleField(
        url="autocomplete-edition",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        create_url="create",
        value_field="id",
        label_field="name",
        # create_field="name",  # ToDo: Move to config
        required=False,
        general_config=general_config,
        plugin_dropdown_header=plugin_dropdown_header,
    )


class ModelForm(forms.ModelForm):
    """This version uses the TomSelectField and TomSelectTabularField fields instead of the default Django fields."""

    tomselect = TomSelectField(
        url="autocomplete-edition",
        # create_field="name",  # ToDo: Move to config
        listview_url="listview",
        create_url="create",
        value_field="id",
        label_field="name",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
        },
        general_config=general_config,
    )
    tomselect_tabular = TomSelectTabularField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        create_url="create",
        value_field="id",
        label_field="name",
        general_config=general_config,
        plugin_dropdown_header=plugin_dropdown_header,
        plugin_checkbox_options=None,
    )

    # Multiple selection:
    tomselect_multiple = TomSelectMultipleField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        value_field="id",
        label_field="name",
        general_config=general_config,
    )
    tomselect_tabular_multiple_with_value_field = TomSelectTabularMultipleField(
        url="autocomplete-edition",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        create_url="create",
        value_field="id",
        label_field="name",
        # create_field="name",  # ToDo: Move to config
        general_config=general_config,
        plugin_dropdown_header=plugin_dropdown_header,
        plugin_checkbox_options=None,
    )

    class Meta:
        model = ModelFormTestModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FilteredForm(forms.Form):
    magazine = TomSelectField(
        url="autocomplete-magazine",
    )
    edition = TomSelectField(
        url="autocomplete-edition",
        # create_field="name",  # ToDo: Move to config
        listview_url="listview",
        create_url="create",
        value_field="id",
        label_field="name",
        filter_by=("magazine", "magazine_id"),
        attrs={"class": "form-control mb-3"},
        required=False,
    )
