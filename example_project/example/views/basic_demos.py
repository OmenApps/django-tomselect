"""Views for the example app."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import HttpResponseRedirect, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from example_project.example.forms import (
    Bootstrap4StylingForm,
    Bootstrap5StylingForm,
    Bootstrap5StylingHTMXForm,
    CategoryModelFormset,
    DefaultStylingForm,
    EditionFormset,
)
from example_project.example.models import Category, Edition


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


def formset_demo(request: HttpRequest) -> HttpResponse:
    """View for demonstrating TomSelect with formsets."""
    template = "example/basic_demos/formset.html"
    context = {}

    if request.method == "POST":
        formset = EditionFormset(request.POST)
        if formset.is_valid():
            # Process the valid formset data
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    # Create new Edition instance
                    Edition.objects.create(
                        name=form.cleaned_data["name"],
                        year=form.cleaned_data["year"],
                        magazine=form.cleaned_data["magazine"],
                    )
            messages.success(request, "Editions saved successfully!")
            return HttpResponseRedirect(request.path)
        messages.error(request, "Please correct the errors below.")
    else:
        formset = EditionFormset()

    context["formset"] = formset
    return TemplateResponse(request, template, context)


def model_formset_demo(request: HttpRequest) -> HttpResponse:
    """View for demonstrating TomSelect with model formsets."""
    template = "example/basic_demos/model_formset.html"

    # Only load root categories (ones with no parent) for initial display
    # This keeps the initial load light while still allowing selection of any category
    initial_queryset = Category.objects.filter(parent__isnull=True)

    if request.method == "POST":
        formset = CategoryModelFormset(request.POST, queryset=initial_queryset)
        if formset.is_valid():
            instances = formset.save()
            formset.save()
            messages.success(
                request,
                f"Successfully saved {len(instances)} new or updated categories. "
                f"{len(formset.deleted_forms)} categories were deleted.",
            )
            return redirect(reverse("demo-model-formset"))

        messages.error(request, "Please correct the errors below.")
    else:
        formset = CategoryModelFormset(queryset=initial_queryset)

    context = {
        "formset": formset,
        "total_count": Category.objects.count(),
        "root_count": initial_queryset.count(),
    }

    return TemplateResponse(request, template, context)
