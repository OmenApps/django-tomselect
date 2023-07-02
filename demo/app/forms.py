from django import forms

from django_tomselect.widgets import TomSelectTabularWidget, TomSelectWidget

from .models import Edition, Magazine


class Form(forms.Form):
    tomselect = forms.ModelChoiceField(
        Edition.objects.all(),
        widget=TomSelectWidget(
            Edition,
            attrs={"class": "form-control mb-3"},
            listview_url="listview",
            add_url="add",
            create_field="name",
        ),
        required=False,
    )
    tomselect_tabular = forms.ModelChoiceField(
        Edition.objects.all(),
        widget=TomSelectTabularWidget(
            Edition,
            extra_columns={"year": "Year", "pages": "Pages", "pub_num": "Publication Number"},
            label_field_label="Edition",
            attrs={"class": "form-control mb-3"},
            listview_url="listview",
            add_url="add",
        ),
        required=False,
    )

    # Multiple selection:
    tomselect_multiple = forms.ModelChoiceField(
        Edition.objects.all(),
        widget=TomSelectWidget(
            Edition,
            attrs={"class": "form-control mb-3"},
            multiple=True,
            listview_url="listview",
        ),
        required=False,
    )
    tomselect_tabular_multiple_with_value_field = forms.ModelChoiceField(
        Edition.objects.all(),
        widget=TomSelectTabularWidget(
            Edition,
            extra_columns={"year": "Year", "pages": "Pages", "pub_num": "Publication Number"},
            label_field_label="Edition",
            multiple=True,
            attrs={"class": "form-control mb-3"},
            add_url="add",
            create_field="name",
            show_value_field=True,
            search_lookups=["pages__icontains", "year__icontains", "pub_num__icontains"],
        ),
        required=False,
    )


class FilteredForm(forms.Form):
    magazine = forms.ModelChoiceField(queryset=Magazine.objects.all(), widget=TomSelectWidget(Magazine))
    edition = forms.ModelChoiceField(
        Edition.objects.all(),
        widget=TomSelectWidget(
            Edition,
            attrs={"class": "form-control mb-3"},
            listview_url="listview",
            add_url="add",
            create_field="name",
            filter_by=("magazine", "magazine_id"),
        ),
        required=False,
    )
