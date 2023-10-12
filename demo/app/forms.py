from django import forms

from django_tomselect.configs import (
    GeneralConfig,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
)
from django_tomselect.forms import TomSelectField, TomSelectMultipleField

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


class Form(forms.Form):
    """This version uses the TomSelectField and TomSelectMultipleField fields instead of the default Django fields."""

    tomselect = TomSelectField(
        url="autocomplete-edition",
        # create_field="name",  # ToDo: Move to config
        listview_url="listview",
        create_url="create",
        update_url="update",
        value_field="id",
        label_field="name",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
            "id": "tomselect-custom-id",
        },
        general_config=general_config,
        plugin_dropdown_header=None,
        label="Tomselect Single",
        help_text=(
            "TomSelectField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )
    tomselect_tabular = TomSelectField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        create_url="create",
        value_field="id",
        label_field="name",
        general_config=general_config,
        plugin_dropdown_header=plugin_dropdown_header,
        plugin_checkbox_options=None,
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    # Multiple selection:
    tomselect_multiple = TomSelectMultipleField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        value_field="id",
        label_field="name",
        general_config=general_config,
        plugin_dropdown_header=None,
        plugin_checkbox_options=None,
        plugin_remove_button=None,
        label="Tomselect Multiple",
        help_text=(
            "TomSelectField with multiple select, dropdown input, dropdown "
            "footer, clear, and highlighting"
        ),
    )
    tomselect_tabular_multiple_with_value_field = TomSelectMultipleField(
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
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectField with multiple select, placeholder text, dropdown input, " "remove, clear, and highlighting"
        ),
    )


class FormHTMX(forms.Form):
    """This version uses the TomSelectField and TomSelectMultipleField fields instead of the default Django fields."""

    tomselect = TomSelectField(
        url="autocomplete-edition",
        # create_field="name",  # ToDo: Move to config
        listview_url="listview",
        create_url="create",
        update_url="update",
        value_field="id",
        label_field="name",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
            "id": "tomselect-custom-id",
        },
        use_htmx=True,
        general_config=general_config,
        plugin_dropdown_header=None,
        label="Tomselect Single",
        help_text=(
            "TomSelectField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )
    tomselect_tabular = TomSelectField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        create_url="create",
        value_field="id",
        label_field="name",
        use_htmx=True,
        general_config=general_config,
        plugin_dropdown_header=plugin_dropdown_header,
        plugin_checkbox_options=None,
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    # Multiple selection:
    tomselect_multiple = TomSelectMultipleField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        value_field="id",
        label_field="name",
        use_htmx=True,
        general_config=general_config,
        plugin_dropdown_header=None,
        plugin_checkbox_options=None,
        plugin_remove_button=None,
        label="Tomselect Multiple",
        help_text=(
            "TomSelectField with multiple select, dropdown input, dropdown "
            "footer, clear, and highlighting"
        ),
    )
    tomselect_tabular_multiple_with_value_field = TomSelectMultipleField(
        url="autocomplete-edition",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        create_url="create",
        value_field="id",
        label_field="name",
        # create_field="name",  # ToDo: Move to config
        use_htmx=True,
        general_config=general_config,
        plugin_dropdown_header=plugin_dropdown_header,
        plugin_checkbox_options=None,
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectField with multiple select, placeholder text, dropdown input, " "remove, clear, and highlighting"
        ),
    )


class ModelForm(forms.ModelForm):
    """This version uses the TomSelectField and TomSelectMultipleField fields instead of the default Django fields."""

    tomselect = TomSelectField(
        url="autocomplete-edition",
        # create_field="name",  # ToDo: Move to config
        listview_url="listview",
        create_url="create",
        update_url="update",
        value_field="id",
        label_field="name",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
        },
        general_config=general_config,
        plugin_dropdown_header=None,
        label="Tomselect Single",
        help_text=(
            "TomSelectField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )
    tomselect_tabular = TomSelectField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        create_url="create",
        value_field="id",
        label_field="name",
        general_config=general_config,
        plugin_dropdown_header=plugin_dropdown_header,
        plugin_checkbox_options=None,
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    # Multiple selection:
    tomselect_multiple = TomSelectMultipleField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        value_field="id",
        label_field="name",
        general_config=general_config,
        plugin_dropdown_header=None,
        plugin_checkbox_options=None,
        plugin_remove_button=None,
        label="Tomselect Multiple",
        help_text=(
            "TomSelectField with multiple select, dropdown input, dropdown "
            "footer, clear, and highlighting"
        ),
    )
    tomselect_tabular_multiple_with_value_field = TomSelectMultipleField(
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
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectField with multiple select, placeholder text, dropdown input, " "remove, clear, and highlighting"
        ),
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
