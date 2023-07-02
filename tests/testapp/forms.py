from django import forms

from django_tomselect.widgets import TomSelectTabularWidget, TomSelectWidget

from .models import Edition, Magazine

kwargs = {"model": Edition, "url": "ac"}


class SimpleForm(forms.Form):
    field = forms.ModelChoiceField(Edition.objects.all(), widget=TomSelectWidget(**kwargs), required=False)


class MultipleForm(forms.Form):
    field = forms.ModelChoiceField(
        Edition.objects.all(), widget=TomSelectWidget(**kwargs, multiple=True), required=False
    )


class TabularForm(forms.Form):
    field = forms.ModelChoiceField(
        Edition.objects.all(),
        widget=TomSelectTabularWidget(
            **kwargs,
            extra_columns={"year": "Year", "pages": "Pages", "pub_num": "Publication Number"},
            label_field_label="Edition",
        ),
        required=False,
    )


class TabularWithValueFieldForm(forms.Form):
    field = forms.ModelChoiceField(
        Edition.objects.all(),
        widget=TomSelectTabularWidget(
            **kwargs,
            extra_columns={"year": "Year", "pages": "Pages", "pub_num": "Publication Number"},
            label_field_label="Edition",
            show_value_field=True,
        ),
        required=False,
    )


class CreateForm(forms.Form):
    field = forms.ModelChoiceField(
        Edition.objects.all(), widget=TomSelectWidget(**kwargs, create_field="name"), required=False
    )


class AddForm(forms.Form):
    """Test form with a widget with a 'add' URL."""

    field = forms.ModelChoiceField(
        Edition.objects.all(), widget=TomSelectWidget(**kwargs, add_url="add_page", create_field="name")
    )


class ListViewForm(forms.Form):
    """Test form with a widget with a 'listview' URL."""

    field = forms.ModelChoiceField(
        Edition.objects.all(), widget=TomSelectWidget(listview_url="listview_page", **kwargs)
    )


class FilteredForm(forms.Form):
    """
    Test form where the results of the 'edition' field are filtered by the value
    of the 'magazine' field.
    """

    magazine = forms.ModelChoiceField(Magazine.objects.all())
    edition = forms.ModelChoiceField(
        Edition.objects.all(), widget=TomSelectWidget(filter_by=("magazine", "magazine_id"), **kwargs)
    )
