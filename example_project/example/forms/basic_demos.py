"""Forms for the example project demonstrating TomSelectConfig usage."""

from django import forms
from django.utils.translation import gettext_lazy as _

from django_tomselect.app_settings import (
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.forms import (
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)


class DefaultStylingForm(forms.Form):
    """Uses TomSelectModelChoiceField and TomSelectModelMultipleChoiceField fields with TomSelectConfig."""

    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            show_update=True,
            value_field="id",
            label_field="name",
            css_framework="default",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a value",
            minimum_query_length=2,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection", class_name="clear-button"),
        ),
        attrs={
            "id": "tomselect-custom-id",
        },
        label="Tomselect Single",
        help_text=(
            "TomSelectModelChoiceField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )

    tomselect_tabular = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            value_field="id",
            label_field="name",
            css_framework="default",
            highlight=True,
            open_on_focus=True,
            preload="focus",
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
        ),
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectModelChoiceField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    tomselect_multiple = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            value_field="id",
            label_field="name",
            css_framework="default",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,  # Allow unlimited selections
            placeholder="Select multiple values",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(),
            plugin_remove_button=PluginRemoveButton(),
        ),
        label="Tomselect Multiple",
        help_text=(
            "TomSelectModelChoiceField with multiple select, dropdown input, dropdown footer, clear, and highlighting"
        ),
    )

    tomselect_tabular_multiple_with_value_field = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_create=True,
            value_field="id",
            label_field="name",
            css_framework="default",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,
            placeholder="Select multiple values",
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
        ),
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectModelChoiceField with multiple select, placeholder text, dropdown input, "
            "remove, clear, and highlighting"
        ),
    )


class Bootstrap4StylingForm(forms.Form):
    """Uses TomSelectModelChoiceField and TomSelectModelMultipleChoiceField fields with TomSelectConfig."""

    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            show_update=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap4",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a value",
            minimum_query_length=2,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection", class_name="clear-button"),
        ),
        attrs={
            "class": "form-control mb-3",
            "id": "tomselect-custom-id",
        },
        label="Tomselect Single",
        help_text=(
            "TomSelectModelChoiceField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )

    tomselect_tabular = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap4",
            highlight=True,
            open_on_focus=True,
            preload="focus",
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
        ),
        attrs={"class": "form-control mb-3"},
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectModelChoiceField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    tomselect_multiple = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap4",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,  # Allow unlimited selections
            placeholder="Select multiple values",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(),
            plugin_remove_button=PluginRemoveButton(),
        ),
        attrs={"class": "form-control mb-3"},
        label="Tomselect Multiple",
        help_text=(
            "TomSelectModelChoiceField with multiple select, dropdown input, dropdown footer, "
            "clear, and highlighting"
        ),
    )

    tomselect_tabular_multiple_with_value_field = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_create=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap4",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,
            placeholder="Select multiple values",
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
        ),
        attrs={
            "class": "form-control mb-3",
        },
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectModelChoiceField with multiple select, placeholder text, dropdown input, "
            "remove, clear, and highlighting"
        ),
    )


class Bootstrap5StylingForm(forms.Form):
    """Uses TomSelectModelChoiceField and TomSelectModelMultipleChoiceField fields with TomSelectConfig."""

    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            show_update=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a value",
            minimum_query_length=2,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection", class_name="clear-button"),
        ),
        attrs={
            "class": "form-control mb-3",
            "id": "tomselect-custom-id",
        },
        label="Tomselect Single",
        help_text=(
            "TomSelectModelChoiceField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )

    tomselect_tabular = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
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
        ),
        attrs={"class": "form-control mb-3"},
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectModelChoiceField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    tomselect_multiple = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,  # Allow unlimited selections
            placeholder="Select multiple values",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(),
            plugin_remove_button=PluginRemoveButton(),
        ),
        attrs={"class": "form-control mb-3"},
        label="Tomselect Multiple",
        help_text=(
            "TomSelectModelChoiceField with multiple select, dropdown input, dropdown footer, "
            "clear, and highlighting"
        ),
    )

    tomselect_tabular_multiple_with_value_field = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_create=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,
            placeholder="Select multiple values",
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
        ),
        attrs={
            "class": "form-control mb-3",
        },
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectModelChoiceField with multiple select, placeholder text, dropdown input, "
            "remove, clear, and highlighting"
        ),
    )


class Bootstrap5StylingHTMXForm(Bootstrap5StylingForm):
    """Same as Form but with HTMX enabled."""

    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            show_update=True,
            value_field="id",
            label_field="name",
            use_htmx=True,
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a value",
            minimum_query_length=2,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection", class_name="clear-button"),
        ),
        attrs={
            "class": "form-control mb-3",
            "id": "tomselect-custom-id",
        },
        label="Tomselect Single",
        help_text=(
            "TomSelectModelChoiceField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )

    tomselect_tabular = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            value_field="id",
            label_field="name",
            use_htmx=True,
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
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
        ),
        attrs={"class": "form-control mb-3"},
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectModelChoiceField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    tomselect_multiple = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            value_field="id",
            label_field="name",
            use_htmx=True,
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,  # Allow unlimited selections
            placeholder="Select multiple values",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(),
            plugin_remove_button=PluginRemoveButton(),
        ),
        attrs={"class": "form-control mb-3"},
        label="Tomselect Multiple",
        help_text=(
            "TomSelectModelChoiceField with multiple select, dropdown input, dropdown footer, "
            "clear, and highlighting"
        ),
    )

    tomselect_tabular_multiple_with_value_field = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_create=True,
            value_field="id",
            label_field="name",
            use_htmx=True,
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,
            placeholder="Select multiple values",
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
        ),
        attrs={
            "class": "form-control mb-3",
        },
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectModelChoiceField with multiple select, placeholder text, dropdown input, "
            "remove, clear, and highlighting"
        ),
    )
