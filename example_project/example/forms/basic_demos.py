"""Forms for the example project demonstrating TomSelectConfig usage."""

from django import forms
from django.forms import formset_factory, modelformset_factory

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
from example_project.example.models import Category


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


class MultipleHeavySelectorsForm(forms.Form):
    """Form with multiple TomSelect fields, each with many pre-selected items."""

    editions_group_1 = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,  # Allow unlimited selections
            placeholder="Select editions",
            hide_selected=True,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(),
            plugin_remove_button=PluginRemoveButton(),
        ),
        label="First Group of Editions",
        help_text="Basic configuration with many selected items",
    )

    editions_group_2 = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,
            placeholder="Select editions",
            hide_selected=True,
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
        label="Second Group of Editions",
        help_text="Tabular configuration with many selected items",
    )

    editions_group_3 = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,
            placeholder="Select editions",
            hide_selected=True,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(),
            plugin_remove_button=PluginRemoveButton(),
        ),
        label="Third Group of Editions",
        help_text="Another configuration with many selected items",
    )


class EditionFormsetForm(forms.Form):
    """Form for managing multiple editions with their magazines using TomSelect."""

    name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control mb-3"}),
    )

    year = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control mb-3"}),
    )

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            show_list=True,
            show_create=True,
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a magazine",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection"),
        ),
        attrs={"class": "form-control mb-3"},
        label="Magazine",
        help_text="Select the magazine for this edition",
    )


# A basic formset factory based on the EditionFormsetForm
EditionFormset = formset_factory(EditionFormsetForm, extra=1, can_delete=True)


class CategoryModelForm(forms.ModelForm):
    """ModelForm for managing categories with their parent categories using TomSelect.

    Demonstrates exclude_by in a model formset to prevent circular parent-child relationships.
    """

    # Override the parent field to use TomSelect with tabular display
    parent = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            show_list=True,
            value_field="id",
            label_field="name",
            exclude_by=("id", "id"),  # Exclude current category from parent options (prevents circular references)
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a parent category (optional)",
            plugin_dropdown_header=PluginDropdownHeader(
                show_value_field=False,
                label_field_label="Category",
                extra_columns={
                    "direct_articles": "Direct Articles",
                    "total_articles": "Total Articles",
                },
            ),
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection"),
        ),
        queryset=None,  # Queryset is set by the widget's autocomplete view
        required=False,
        attrs={"class": "form-control mb-3"},
        label="Parent Category",
        help_text="Select a parent category (optional) - current category is excluded to prevent circular references",
    )

    class Meta:
        """Meta options for the CategoryModelForm."""

        model = Category
        fields = ["name", "parent"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control mb-3", "placeholder": "Enter category name"}),
        }


# A model formset factory based on the CategoryModelForm
CategoryModelFormset = modelformset_factory(Category, form=CategoryModelForm, extra=1, can_delete=True)


class EditionWithFilterFormsetForm(forms.Form):
    """Form demonstrating filter_by in formsets.

    This form shows how dependent/chained fields work within a Django formset.
    Each row has a magazine field that controls the available editions in that same row.
    """

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a magazine first",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection"),
        ),
        attrs={"class": "form-control mb-3"},
        label="Magazine",
        help_text="Select a magazine to filter available editions",
    )

    edition = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),  # Key feature: filter editions by selected magazine
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            placeholder="Select an edition (filtered by magazine)",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection"),
            plugin_dropdown_footer=PluginDropdownFooter(),
        ),
        attrs={"class": "form-control mb-3"},
        label="Edition",
        help_text="Editions are filtered based on the selected magazine",
        required=False,
    )


# Formset factory for the EditionWithFilterFormsetForm
EditionWithFilterFormset = formset_factory(EditionWithFilterFormsetForm, extra=2, can_delete=True)
