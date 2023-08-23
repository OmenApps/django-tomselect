from django import forms

from django_tomselect.widgets import (
    TomSelectMultipleWidget,
    TomSelectTabularMultipleWidget,
    TomSelectTabularWidget,
    TomSelectWidget,
)

from .models import Edition, Magazine


class Form(forms.Form):
    tomselect = forms.ModelChoiceField(
        queryset=Edition.objects.none(),
        widget=TomSelectWidget(create_field="name", listview_url="listview", add_url="add",
                               attrs={"class": "form-control mb-3"}),
        required=False,
    )
    tomselect_tabular = forms.ModelChoiceField(
        queryset=Edition.objects.none(),
        widget=TomSelectTabularWidget(
            extra_columns={"year": "Year", "pages": "Pages", "pub_num": "Publication Number"},
            label_field_label="Edition",
            attrs={"class": "form-control mb-3"},
            listview_url="listview",
            add_url="add",
        ),
        required=False,
    )

    # Multiple selection:
    tomselect_multiple = forms.ModelMultipleChoiceField(
        queryset=Edition.objects.all(),
        widget=TomSelectMultipleWidget(
            attrs={"class": "form-control mb-3"},
            listview_url="listview",
        ),
        required=False,
    )
    tomselect_tabular_multiple_with_value_field = forms.ModelMultipleChoiceField(
        queryset=Edition.objects.all(),
        widget=TomSelectTabularMultipleWidget(
            extra_columns={"year": "Year", "pages": "Pages", "pub_num": "Publication Number"},
            label_field_label="Edition",
            attrs={"class": "form-control mb-3", "placeholder": "Select multiple values"},
            add_url="add",
            create_field="name",
            show_value_field=True,
            search_lookups=["pages__icontains", "year__icontains", "pub_num__icontains"],
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tomselect"].queryset = self.fields["tomselect"].widget.get_queryset()
        self.fields["tomselect_tabular"].queryset = Edition.objects.filter(year__gte=2020)
        # self.fields["tomselect_multiple"].queryset = Edition.objects.filter(year__gte=2020)
        # self.fields["tomselect_tabular_multiple_with_value_field"].queryset = Edition.objects.filter(year__gte=2020)

    def clean(self):
        print(f"Form cleaned_data: {self.cleaned_data}")


class FilteredForm(forms.Form):
    magazine = forms.ModelChoiceField(queryset=Magazine.objects.all(), widget=TomSelectWidget(Magazine))
    edition = forms.ModelChoiceField(
        Edition.objects.all(),
        widget=TomSelectWidget(create_field="name", listview_url="listview", add_url="add",
                               filter_by=("magazine", "magazine_id"), attrs={"class": "form-control mb-3"}),
        required=False,
    )

    def clean(self):
        print(f"FilteredForm cleaned_data: {self.cleaned_data}")
