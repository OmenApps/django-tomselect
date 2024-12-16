"""Views for the example app."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.template.response import TemplateResponse

from example_project.example.forms import (
    Bootstrap4StylingForm,
    Bootstrap5StylingForm,
    Bootstrap5StylingHTMXForm,
    DefaultStylingForm,
)


def default_demo(request: HttpRequest) -> HttpResponse:
    """View for the Default demo page."""
    template = "example/basic_demos/default.html"
    context = {}

    context["form"] = DefaultStylingForm()
    return TemplateResponse(request, template, context)


def bootstrap4_demo(request: HttpRequest) -> HttpResponse:
    """View for the Bootstrap 4 demo page."""
    template = "example/basic_demos/bs4.html"
    context = {}

    context["form"] = Bootstrap4StylingForm()
    return TemplateResponse(request, template, context)


def bootstrap5_demo(request: HttpRequest) -> HttpResponse:
    """View for the Bootstrap 5 demo page."""
    template = "example/basic_demos/bs5.html"
    context = {}

    context["form"] = Bootstrap5StylingForm()
    return TemplateResponse(request, template, context)


def htmx_view(request: HttpRequest) -> HttpResponse:
    """View for the htmx page."""
    template = "example/basic_demos/htmx.html"
    context = {}

    return TemplateResponse(request, template, context)


def htmx_form_fragment_view(request: HttpRequest) -> HttpResponse:
    """View for the htmx form fragment page."""
    template = "example/basic_demos/htmx_fragment.html"
    context = {}

    form = Bootstrap5StylingHTMXForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            messages.success(request, "Form submitted successfully!")
        else:
            messages.error(request, "Please correct the errors in the form before proceeding.")

        return HttpResponseRedirect("/")

    context["form"] = form
    return TemplateResponse(request, template, context)
