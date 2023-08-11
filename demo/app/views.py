from django.http import HttpResponse
from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.template.response import TemplateResponse

from django_tomselect.views import AutocompleteView

from .forms import FilteredForm, Form


class DemoAutocompleteView(AutocompleteView):
    def has_add_permission(self, request):
        return True  # no auth in this demo app

    def get_queryset(self):
        """Return a queryset of objects that match the search parameters and filters."""
        queryset = super().get_queryset().filter(name__icontains="3")
        return queryset


def form_test_view(request):
    template = "base5.html"
    context = {}

    form = Form(request.POST or None)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect("/")

    context["form"] = form

    return TemplateResponse(request, template, context)


def listview_view(request):
    return HttpResponse("This is a dummy listview page.")


def add_view(request):
    return HttpResponse("This is a dummy add page.")
