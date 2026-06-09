# Quick Start

This section guides you through a simple, end-to-end example of integrating `django_tomselect` into your Django project. By the end, you’ll have a functioning autocomplete-enabled select field that dynamically fetches options from the server as the user types.

## Basic Form Implementation

The simplest approach is to add a `TomSelectModelChoiceField` to a basic form. This field uses a `TomSelectConfig` that specifies where to fetch data from and how to display it.

```python
from django import forms
from django_tomselect import TomSelectConfig, TomSelectModelChoiceField

class SimpleForm(forms.Form):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",  # Name of the URL pattern for your autocomplete view
            value_field="id",             # Field returned as the <option> value
            label_field="name",           # Field displayed as the <option> label
            placeholder="Select a magazine...",
            preload="focus",              # Load options when the field is focused, instead of waiting for a query
            highlight=True                # Highlight query matches in the dropdown
        )
    )
```

In this snippet:

- The `url` parameter points to an autocomplete endpoint you’ll define.
- The `value_field` and `label_field` specify which model fields represent the option’s value and label.
- Additional parameters like `placeholder` and `highlight` enhance the user experience.

## ModelForm Integration

Integrating with a Django `ModelForm` is straightforward-just replace a standard model field with a `TomSelectModelChoiceField`. Suppose you have an `Article` model that references a `Magazine` model via a ForeignKey:

```python
from django import forms
from django_tomselect import TomSelectConfig, TomSelectModelChoiceField
from .models import Article

class ArticleForm(forms.ModelForm):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            placeholder="Select a magazine...",
            minimum_query_length=2,  # Only start searching after 2 chars
            preload="focus"
        )
    )

    class Meta:
        model = Article
        fields = ["title", "magazine"]
```

This form field will automatically integrate with Tom Select, providing an enhanced dropdown with autocomplete and search capabilities.

## Setting Up the Views

### Configure the Autocomplete View

Create a subclass of `AutocompleteModelView` to provide data to the widget. For example, if your `Magazine` model has a `name` field:

```python
from django_tomselect.autocompletes import AutocompleteModelView
from .models import Magazine

class MagazineAutocompleteView(AutocompleteModelView):
    model = Magazine
    search_lookups = ["name__icontains"]  # Fields to search against
    ordering = ["name"]
    page_size = 20
```

This view will respond to requests from the widget, returning JSON data for matching magazines.

### Use the Form in a View

Create a simple view that handles displaying and processing the `ArticleForm`:

```python
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from .forms import ArticleForm

def article_create_view(request):
    template = "article_form.html"
    context = {}

    form = ArticleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("article-list")  # Adjust the redirect as needed

    context["form"] = form
    return TemplateResponse(request, template, context)
```

## Add URL Patterns

Register the URLs for your article creation page and the magazine autocomplete endpoint:

```python
from django.urls import path
from .views import article_create_view, MagazineAutocompleteView

urlpatterns = [
    path("article/create/", article_create_view, name="article-create"),
    path("autocomplete/magazine/", MagazineAutocompleteView.as_view(), name="autocomplete-magazine"),
]
```

## Template Setup

Include the form’s media assets in your template to ensure that Tom Select CSS and JS are properly loaded. Your form template might look like this:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Include form's media -->
    {{ form.media }}
</head>
<body>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Submit</button>
    </form>
</body>
</html>
```

That’s it! With this setup, you have a working autocomplete-enabled select field that:

- Dynamically fetches results as the user types
- Integrates seamlessly with Django ModelForms
- Supports search filtering, pagination, and keyboard navigation out-of-the-box
