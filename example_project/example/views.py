"""Views for the example app."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import HttpResponseRedirect, reverse
from django.template.response import TemplateResponse

from .forms import Form, FormHTMX, ModelForm
from .models import ModelFormTestModel


def form_test_view(request: HttpRequest) -> HttpResponse:
    """View for the form test page."""
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


def model_form_test_view(request: HttpRequest) -> HttpResponse:
    """View for the model form test page."""
    template = "base5.html"
    context = {}

    form = ModelForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
            form.save()
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect(reverse("demo_with_model"))

    context["form"] = form

    return TemplateResponse(request, template, context)


def model_form_edit_test_view(request: HttpRequest, pk: int) -> HttpResponse:
    """View for the model form edit test page."""
    template = "base5.html"
    context = {}

    instance = ModelFormTestModel.objects.get(pk=pk)

    form = ModelForm(request.POST or None, instance=instance)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
            form.save()
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect(reverse("demo_with_model"))

    context["form"] = form

    return TemplateResponse(request, template, context)


def listview_view(request: HttpRequest) -> HttpResponse:  # pylint: disable=W0613
    """View for the listview page."""
    return HttpResponse("This is a stub listview page.")


def create_view(request: HttpRequest) -> HttpResponse:  # pylint: disable=W0613
    """View for the create page."""
    return HttpResponse("This is a stub create page.")


def update_view(request: HttpRequest) -> HttpResponse:  # pylint: disable=W0613
    """View for the update page."""
    return HttpResponse("This is a stub update page.")


def htmx_view(request: HttpRequest) -> HttpResponse:
    """View for the htmx page."""
    template = "base5_htmx.html"
    context = {}

    return TemplateResponse(request, template, context)


def htmx_form_fragment_view(request: HttpRequest) -> HttpResponse:
    """View for the htmx form fragment page."""
    template = "base5_htmx_fragment.html"
    context = {}

    form = FormHTMX(request.POST or None)

    if request.POST:
        if form.is_valid():
            print(f"Form valid. Form cleaned_data: {form.cleaned_data}")
        else:
            print(f"Form NOT valid. Form cleaned_data: {form.cleaned_data}")
            print(f"Form NOT valid. Form errors: {form.errors.as_data()}")

        return HttpResponseRedirect("/")

    context["form"] = form

    return TemplateResponse(request, template, context)
