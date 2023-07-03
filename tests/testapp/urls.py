from django.http import HttpResponse
from django.urls import path
from django.views.generic import FormView

from django_tomselect.views import AutocompleteView

from .forms import (
    AddForm,
    CreateForm,
    FilteredForm,
    ListViewForm,
    MultipleForm,
    SimpleForm,
    TabularForm,
    TabularWithValueFieldForm,
)


def listview_view(request):
    return HttpResponse("This is a dummy listview page.")


def add_view(request):
    return HttpResponse("This is a dummy add page.")


urlpatterns = [
    path("simple/", FormView.as_view(form_class=SimpleForm, template_name="base5.html"), name="simple"),
    path("multiple/", FormView.as_view(form_class=MultipleForm, template_name="base5.html"), name="multiple"),
    path("tabular/", FormView.as_view(form_class=TabularForm, template_name="base5.html"), name="tabular"),
    path(
        "tabular-with-value-field/",
        FormView.as_view(form_class=TabularWithValueFieldForm, template_name="base5.html"),
        name="tabular-with-value-field",
    ),
    path("create/", FormView.as_view(form_class=CreateForm, template_name="base5.html"), name="create"),
    path("with_add/", FormView.as_view(form_class=AddForm, template_name="base5.html"), name="add"),
    path("with_listview/", FormView.as_view(form_class=ListViewForm, template_name="base5.html"), name="listview"),
    path("filtered/", FormView.as_view(form_class=FilteredForm, template_name="base5.html"), name="filtered"),
    path("ac/", AutocompleteView.as_view(), name="ac"),
    path("add/", add_view, name="add_page"),
    path("listview/", listview_view, name="listview_page"),
]
