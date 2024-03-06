from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect, reverse
from django.template.response import TemplateResponse


from .forms import Form, ModelForm, FormHTMX
from .models import ModelFormTestModel


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


def model_form_test_view(request):
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


def model_form_edit_test_view(request, pk):
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


def listview_view(request):
    return HttpResponse("This is a dummy listview page.")


def create_view(request):
    return HttpResponse("This is a dummy create page.")


def update_view(request):
    return HttpResponse("This is a dummy update page.")


def htmx_view(request):
    template = "base5_htmx.html"
    context = {}

    return TemplateResponse(request, template, context)


def htmx_form_fragment_view(request):
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
