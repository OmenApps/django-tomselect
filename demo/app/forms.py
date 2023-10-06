from django import forms

from django_tomselect.widgets import (
    TomSelectField,
    TomSelectMultipleField,
    TomSelectTabularField,
    TomSelectTabularMultipleField,
    TomSelectWidget,
)

from .models import Edition, Magazine, ModelFormTestModel


class Form(forms.Form):
    tomselect = TomSelectField(
        url="autocomplete-edition",
        create_field="name",
        listview_url="listview",
        add_url="add",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
        },
        required=False,
    )
    tomselect_tabular = TomSelectTabularField(
        url="autocomplete-edition",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        },
        label_field_label="Edition",
        attrs={
            "class": "form-control mb-3",
        },
        listview_url="listview",
        add_url="add",
        required=False,
    )

    # Multiple selection:
    tomselect_multiple = TomSelectMultipleField(
        url="autocomplete-edition",
        attrs={
            "class": "form-control mb-3",
        },
        listview_url="listview",
        required=False,
    )
    tomselect_tabular_multiple_with_value_field = TomSelectTabularMultipleField(
        url="autocomplete-edition",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        },
        label_field_label="Edition",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        add_url="add",
        create_field="name",
        show_value_field=True,
        required=False,
    )

    def clean(self):
        print(f"Form cleaned_data: {self.cleaned_data}")


class ModelForm(forms.ModelForm):
    """This version uses the TomSelectField and TomSelectTabularField fields instead of the default Django fields."""

    tomselect = TomSelectField(
        url="autocomplete-edition",
        create_field="name",
        listview_url="listview",
        add_url="add",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
        },
    )
    tomselect_tabular = TomSelectTabularField(
        url="autocomplete-edition",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        },
        label_field_label="Edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
        add_url="add",
    )

    # Multiple selection:
    tomselect_multiple = TomSelectMultipleField(
        url="autocomplete-edition",
        attrs={"class": "form-control mb-3"},
        listview_url="listview",
    )
    tomselect_tabular_multiple_with_value_field = TomSelectTabularMultipleField(
        url="autocomplete-edition",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        },
        label_field_label="Edition",
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        add_url="add",
        create_field="name",
        show_value_field=True,
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
        create_field="name",
        listview_url="listview",
        add_url="add",
        filter_by=("magazine", "magazine_id"),
        attrs={"class": "form-control mb-3"},
        required=False,
    )

    def clean(self):
        print(f"FilteredForm cleaned_data: {self.cleaned_data}")
