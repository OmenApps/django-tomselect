from django import forms

from django_tomselect.widgets import (
    TomSelectMultipleWidget,
    TomSelectTabularMultipleWidget,
    TomSelectTabularWidget,
    TomSelectWidget,
    TomSelectField,
    TomSelectTabularField,
    TomSelectMultipleField,
    TomSelectTabularMultipleField,
)
from django_tomselect.models import EmptyModel

from .models import Edition, Magazine, ModelFormTestModel


class Form(forms.Form):
    tomselect = forms.ModelChoiceField(
        queryset=Edition.objects.none(),
        widget=TomSelectWidget(
            url="autocomplete-edition",
            create_field="name",
            listview_url="listview",
            add_url="add",
            attrs={
                "class": "form-control mb-3",
                "placeholder": "Select a value",
            },
        ),
        required=False,
    )
    tomselect_tabular = forms.ModelChoiceField(
        queryset=Edition.objects.none(),
        widget=TomSelectTabularWidget(
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
        ),
        required=False,
    )

    # Multiple selection:
    tomselect_multiple = forms.ModelMultipleChoiceField(
        queryset=Edition.objects.none(),
        widget=TomSelectMultipleWidget(
            url="autocomplete-edition",
            attrs={
                "class": "form-control mb-3",
            },
            listview_url="listview",
        ),
        required=False,
    )
    tomselect_tabular_multiple_with_value_field = forms.ModelMultipleChoiceField(
        queryset=Edition.objects.none(),
        widget=TomSelectTabularMultipleWidget(
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
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            print(f"Field: {field}, widget: {type(field.widget)}")
            if type(field.widget) in (
                TomSelectWidget,
                TomSelectTabularWidget,
                TomSelectMultipleWidget,
                TomSelectTabularMultipleWidget,
            ):
                field.queryset = field.widget.get_queryset()

        # self.fields["tomselect"].queryset = self.fields["tomselect"].widget.get_queryset()
        # self.fields["tomselect_tabular"].queryset = Edition.objects.filter(year__gte=2020)
        # self.fields["tomselect_multiple"].queryset = Edition.objects.filter(year__gte=2020)
        # self.fields["tomselect_tabular_multiple_with_value_field"].queryset = Edition.objects.filter(year__gte=2020)

    def clean(self):
        print(f"Form cleaned_data: {self.cleaned_data}")


# class ModelForm(forms.ModelForm):
#     tomselect = forms.ModelChoiceField(
#         queryset=EmptyModel.objects.none(),
#         widget=TomSelectWidget(
#             url="autocomplete-edition",
#             create_field="name",
#             listview_url="listview",
#             add_url="add",
#             attrs={
#                 "class": "form-control mb-3",
#                 "placeholder": "Select a value",
#             },
#         ),
#         required=False,
#     )
#     tomselect2 = TomSelectField(
#         url="autocomplete-edition",
#         create_field="name",
#         listview_url="listview",
#         add_url="add",
#         attrs={
#             "class": "form-control mb-3",
#             "placeholder": "Select a value",
#         },
#     )
#     tomselect_tabular = forms.ModelChoiceField(
#         queryset=EmptyModel.objects.none(),
#         widget=TomSelectTabularWidget(
#             url="autocomplete-edition",
#             extra_columns={
#                 "year": "Year",
#                 "pages": "Pages",
#                 "pub_num": "Publication Number",
#             },
#             label_field_label="Edition",
#             attrs={"class": "form-control mb-3"},
#             listview_url="listview",
#             add_url="add",
#         ),
#         required=False,
#     )
#
#     # Multiple selection:
#     tomselect_multiple = forms.ModelMultipleChoiceField(
#         queryset=EmptyModel.objects.none(),
#         widget=TomSelectMultipleWidget(
#             url="autocomplete-edition",
#             attrs={"class": "form-control mb-3"},
#             listview_url="listview",
#         ),
#         required=False,
#     )
#     tomselect_tabular_multiple_with_value_field = forms.ModelMultipleChoiceField(
#         queryset=EmptyModel.objects.none(),
#         widget=TomSelectTabularMultipleWidget(
#             url="autocomplete-edition",
#             extra_columns={
#                 "year": "Year",
#                 "pages": "Pages",
#                 "pub_num": "Publication Number",
#             },
#             label_field_label="Edition",
#             attrs={
#                 "class": "form-control mb-3",
#                 "placeholder": "Select multiple values",
#             },
#             add_url="add",
#             create_field="name",
#             show_value_field=True,
#         ),
#         required=False,
#     )
#
#     class Meta:
#         model = ModelFormTestModel
#         fields = "__all__"
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         for field in self.fields.values():
#             print(f"Field: {field}, widget: {type(field.widget)}")
#             if type(field.widget) in (
#                 TomSelectWidget,
#                 TomSelectTabularWidget,
#                 TomSelectMultipleWidget,
#                 TomSelectTabularMultipleWidget,
#             ):
#                 field.queryset = field.widget.get_queryset()


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
    magazine = forms.ModelChoiceField(
        queryset=Magazine.objects.none(),
        widget=TomSelectWidget(
            url="autocomplete-magazine",
        ),
    )
    edition = forms.ModelChoiceField(
        queryset=Edition.objects.none(),
        widget=TomSelectWidget(
            url="autocomplete-edition",
            create_field="name",
            listview_url="listview",
            add_url="add",
            filter_by=("magazine", "magazine_id"),
            attrs={"class": "form-control mb-3"},
        ),
        required=False,
    )

    def clean(self):
        print(f"FilteredForm cleaned_data: {self.cleaned_data}")
