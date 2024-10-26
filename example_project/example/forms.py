"""Forms for the example project demonstrating TomSelectConfig usage."""

from django import forms

from django_tomselect.configs import (
    GeneralConfig,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.forms import TomSelectField, TomSelectMultipleField

from .models import ModelFormTestModel

# Define reusable configurations
SINGLE_SELECT_CONFIG = TomSelectConfig(
    url="autocomplete-edition",
    listview_url="listview",
    create_url="create",
    update_url="update",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
        placeholder="Select a value",
        minimum_query_length=2,
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_clear_button=PluginClearButton(
        title="Clear Selection",
        class_name="clear-button"
    ),
)

SINGLE_SELECT_TABULAR_CONFIG = TomSelectConfig(
    url="autocomplete-edition",
    listview_url="listview",
    create_url="create",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
    ),
    plugin_dropdown_header=PluginDropdownHeader(
        show_value_field=False,
        label_field_label="Edition",
        value_field_label="Value",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        },
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_dropdown_footer=PluginDropdownFooter(),
)

MULTIPLE_SELECT_CONFIG = TomSelectConfig(
    url="autocomplete-edition",
    listview_url="listview",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
        max_items=None,  # Allow unlimited selections
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_clear_button=PluginClearButton(),
    plugin_remove_button=PluginRemoveButton(),
)

MULTIPLE_SELECT_TABULAR_CONFIG = TomSelectConfig(
    url="autocomplete-edition",
    create_url="create",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
        max_items=None,
        placeholder="Select multiple values",
    ),
    plugin_dropdown_header=PluginDropdownHeader(
        show_value_field=False,
        label_field_label="Edition",
        value_field_label="Value",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        },
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_clear_button=PluginClearButton(),
    plugin_remove_button=PluginRemoveButton(),
)


class Form(forms.Form):
    """Uses TomSelectField and TomSelectMultipleField fields with TomSelectConfig."""

    tomselect = TomSelectField(
        config=SINGLE_SELECT_CONFIG,
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
            "id": "tomselect-custom-id",
        },
        label="Tomselect Single",
        help_text=(
            "TomSelectField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )

    tomselect_tabular = TomSelectField(
        config=SINGLE_SELECT_TABULAR_CONFIG,
        attrs={"class": "form-control mb-3"},
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    tomselect_multiple = TomSelectMultipleField(
        config=MULTIPLE_SELECT_CONFIG,
        attrs={"class": "form-control mb-3"},
        label="Tomselect Multiple",
        help_text=(
            "TomSelectField with multiple select, dropdown input, dropdown footer, "
            "clear, and highlighting"
        ),
    )

    tomselect_tabular_multiple_with_value_field = TomSelectMultipleField(
        config=MULTIPLE_SELECT_TABULAR_CONFIG,
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectField with multiple select, placeholder text, dropdown input, "
            "remove, clear, and highlighting"
        ),
    )


class FormHTMX(Form):
    """Same as Form but with HTMX enabled."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enable HTMX for all fields
        for field_name, field in self.fields.items():
            if hasattr(field, 'config'):
                field.config.use_htmx = True


class DependentForm(forms.Form):
    """Form with dependent fields demonstrating filter_by functionality."""

    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        ),
    )

    edition = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            listview_url="listview",
            create_url="create",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )


class ModelForm(forms.ModelForm):
    """ModelForm using TomSelectField and TomSelectMultipleField with TomSelectConfig."""

    tomselect = TomSelectField(
        config=SINGLE_SELECT_CONFIG,
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
        },
        label="Tomselect Single",
        help_text=(
            "TomSelectField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )

    tomselect_tabular = TomSelectField(
        config=SINGLE_SELECT_TABULAR_CONFIG,
        attrs={"class": "form-control mb-3"},
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    tomselect_multiple = TomSelectMultipleField(
        config=MULTIPLE_SELECT_CONFIG,
        attrs={"class": "form-control mb-3"},
        label="Tomselect Multiple",
        help_text=(
            "TomSelectField with multiple select, dropdown input, dropdown footer, "
            "clear, and highlighting"
        ),
    )

    tomselect_tabular_multiple_with_value_field = TomSelectMultipleField(
        config=MULTIPLE_SELECT_TABULAR_CONFIG,
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectField with multiple select, placeholder text, dropdown input, "
            "remove, clear, and highlighting"
        ),
    )

    class Meta:
        model = ModelFormTestModel
        fields = "__all__"
