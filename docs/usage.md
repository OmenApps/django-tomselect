# Installation

`django_tomselect` provides form fields and widgets to integrate [Tom Select](https://tom-select.js.org/) into your Django projects, enabling dynamic and customizable `<select>` elements with advanced features like autocomplete, tagging, and search. Follow the steps below to install and configure the package in your project.

Most of the code samples below are based on the example app provided with the package. You can find the complete example app in the `example_project/example/` directory of the repository.

## Install the Package

You can install `django_tomselect` via pip:

```bash
pip install django_tomselect
```

## Add to `INSTALLED_APPS`

Ensure that `django_tomselect` is included in your `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = [
    ...,
    "django_tomselect",
]
```

## Verify Required Dependencies

`django_tomselect` requires the following dependencies:

- **Django**: Version 4.2 or higher is recommended.
- **Tom Select**: The JavaScript library is included via the form media.

## Static Files

Ensure that Django’s static files setup is correctly configured. Run the following command to collect the necessary static files for `django_tomselect`:

```bash
python manage.py collectstatic
```

## Include Tom Select in Your HTML

`django_tomselect` relies on the Tom Select JavaScript and CSS. Add the required assets in your base HTML template or the templates where the widgets are used:

```html
<head>
    {% form.media %}
</head>
```

## Optional: Configure CSS Framework

`django_tomselect` supports different CSS frameworks for styling the widgets. Set the desired framework in your `settings.py` file:

```python
TOMSELECT_CSS_FRAMEWORK = "bootstrap5"  # Options: "default", "bootstrap4", "bootstrap5"
```

# Quick Start

This guide will help you quickly implement django_tomselect in your Django project.

## Basic Form Implementation

The simplest way to use django_tomselect is with a basic form field:

```python
from django_tomselect.forms import TomSelectField
from django_tomselect.configs import TomSelectConfig

class SimpleForm(forms.Form):
    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",  # URL pattern name for autocomplete view
            value_field="id",
            label_field="name",
        )
    )
```

## ModelForm Integration

Here's a complete example using ModelForm:

```python
from django import forms
from django_tomselect.forms import TomSelectField
from django_tomselect.configs import TomSelectConfig, GeneralConfig

class ArticleForm(forms.ModelForm):
    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            general_config=GeneralConfig(
                placeholder="Select a magazine...",
                preload="focus",
                highlight=True,
            )
        )
    )

    class Meta:
        model = Article
        fields = ["title", "magazine"]
```

## Setting Up the Views

1. Create an autocomplete view:

```python
from django_tomselect.views import AutocompleteView

class MagazineAutocompleteView(AutocompleteView):
    model = Magazine
    search_lookups = ["name__icontains"]  # Fields to search
    ordering = ["name"]
    page_size = 20
```

2. Set up a form view:

```python
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponseRedirect, reverse

def article_create_view(request):
    template = "article_form.html"

    form = ArticleForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse("article-list"))

    context = {"form": form}
    return TemplateResponse(request, template, context)
```

3. Add URL patterns:

```python
from django.urls import path

urlpatterns = [
    path("article/create/", article_create_view, name="article-create"),
    path("autocomplete/magazine/", MagazineAutocompleteView.as_view(), name="autocomplete-magazine"),
]
```

## Template Setup

Include the form media in your template:

```html
<!DOCTYPE html>
<html>
<head>
    {{ form.media }}  <!-- This includes required CSS and JavaScript -->
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

That's it! You now have a working autocomplete select field that:

- Loads options dynamically as the user types
- Supports keyboard navigation
- Includes built-in pagination
- Provides a smooth user experience

# Core Components

`django_tomselect` provides two main field types and corresponding widgets for handling single and multiple selections.

## Form Fields (TomSelectField/TomSelectMultipleField)

- TomSelectField is used for single-selection scenarios. It extends Django's ModelChoiceField and integrates with Tom Select's features.
- TomSelectMultipleField allows multiple selections and extends Django's ModelMultipleChoiceField.

Each field uses a corresponding widget: TomSelectWidget and TomSelectMultipleWidget. These widgets handle the rendering and JavaScript initialization of Tom Select.

### Widgets (TomSelectWidget/TomSelectMultipleWidget)
- Handle rendering of the form element
- Manage JavaScript initialization
- Control the visual presentation
- Handle AJAX requests for data
- Manage user interactions

## Form Media

Both fields and widgets make use of included CSS and JavaScript, which is handled through Django's form media system:

```html
<!DOCTYPE html>
<html>
<head>
    {{ form.media }}  <!-- Includes all required CSS and JavaScript -->
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

This system ensures:
- The appropriate Tom Select CSS is included
- Required JavaScript is loaded
- Dependencies are handled correctly
- Framework-specific styling (Bootstrap 4/5) is applied when configured

# Configuration

## TomSelectConfig Overview

`TomSelectConfig` is the main configuration class that controls how `django_tomselect` fields behave. It provides a centralized way to configure both general behavior and plugin-specific settings.

Basic usage:

```python
from django_tomselect.configs import TomSelectConfig, GeneralConfig

config = TomSelectConfig(
    url="author-autocomplete",
    listview_url="author-list",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
    )
)
```

## General Configuration Options

The `GeneralConfig` class provides core settings for `django_tomselect` behavior:

```python
from django_tomselect.configs import GeneralConfig

general_config = GeneralConfig(
    # Core behavior
    highlight=True,                  # Highlight matching search terms
    open_on_focus=True,              # Open dropdown when field gets focus
    preload="focus",                 # Load options on focus (can be True/False/"focus")

    # Search and display
    minimum_query_length=2,          # Minimum characters before search triggers
    placeholder="Select a value",    # Placeholder text

    # Item limits
    max_items=None,                  # Maximum number of items (for multiple select)
    max_options=50,                  # Maximum number of options to display

    # Loading behavior
    load_throttle=300,               # Milliseconds to wait between searches
    loading_class="loading",         # CSS class applied during loading

    # Creation options
    create=False,                    # Allow creating new items
    create_filter=None,              # Function to filter creatable values
    create_with_htmx=False           # Use HTMX for item creation
)
```

## Available Plugins

`django_tomselect` includes several plugins that enhance functionality. These correspond with their equivalent [Tom Select Plugins](https://tom-select.js.org/plugins/). Each plugin has its own configuration class:

```python
from django_tomselect.configs import (
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownHeader,
    PluginDropdownFooter,
    PluginDropdownInput,
    PluginRemoveButton,
)

config = TomSelectConfig(
    # ... basic config ...
    plugin_checkbox_options=PluginCheckboxOptions(),  # Checkbox options plugin
    plugin_clear_button=PluginClearButton(
        title="Clear Selection",                      # Button text
        class_name="clear-button"                     # CSS class
    ),
    plugin_dropdown_header=PluginDropdownHeader(
        title="Select an Option",                     # Header text
        show_value_field=False,                       # Show value field
        extra_columns={                               # Additional columns
            "count": "Count",
            "category": "Category"
        }
    ),
    plugin_dropdown_footer=PluginDropdownFooter(
        title="Footer",                               # Footer text
        footer_class="dropdown-footer"                # CSS class
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_remove_button=PluginRemoveButton(
        title="Remove",                               # Button text
        label="×",                                    # Button label
        class_name="remove"                           # CSS class
    )
)
```

## CSS Framework Options

`django_tomselect` supports multiple CSS frameworks through the `css_framework` setting:

```python
from django_tomselect.configs import TomSelectConfig

# Bootstrap 5
config = TomSelectConfig(
    css_framework="bootstrap5",
    # ... other config options
)

# Bootstrap 4
config = TomSelectConfig(
    css_framework="bootstrap4",
    # ... other config options
)

# Default styling
config = TomSelectConfig(
    css_framework="default",
    # ... other config options
)
```

You can set the default framework globally in your Django settings:

```python
# settings.py
TOMSELECT_CSS_FRAMEWORK = "bootstrap5"  # or "bootstrap4" or "default"
```

## Global Settings vs Field-level Settings

Settings can be defined globally in your Django settings or per-field:

```python
# settings.py
from django_tomselect.configs import GeneralConfig, PluginDropdownHeader

TOMSELECT_GENERAL_CONFIG = GeneralConfig(
    highlight=True,
    open_on_focus=True,
    minimum_query_length=2
)

TOMSELECT_PLUGIN_DROPDOWN_HEADER = PluginDropdownHeader(
    show_value_field=True,
    label_field_label="Name"
)
```

Field-level configuration overrides global settings:

```python
from django import forms
from django_tomselect.forms import TomSelectField
from django_tomselect.configs import TomSelectConfig, GeneralConfig

class AuthorForm(forms.Form):
    # Field-specific configuration
    author = TomSelectField(
        config=TomSelectConfig(
            url="author-autocomplete",
            general_config=GeneralConfig(
                highlight=True,
                minimum_query_length=1  # Overrides global setting
            )
        )
    )
```

## Example Configuration

Here's a complete example showing how to configure a form with different field types:

```python
from django import forms
from django_tomselect.forms import TomSelectField, TomSelectMultipleField
from django_tomselect.configs import (
    TomSelectConfig,
    GeneralConfig,
    PluginDropdownHeader,
    PluginRemoveButton,
)

# Reusable configurations
SINGLE_SELECT_CONFIG = TomSelectConfig(
    url="author-autocomplete",
    listview_url="author-list",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
        placeholder="Select an author"
    ),
    plugin_dropdown_header=PluginDropdownHeader(
        show_value_field=False,
        label_field_label="Author",
        extra_columns={
            "article_count": "Articles",
            "category": "Category"
        }
    )
)

MULTIPLE_SELECT_CONFIG = TomSelectConfig(
    url="category-autocomplete",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        max_items=None,  # Allow unlimited selections
        placeholder="Select categories"
    ),
    plugin_remove_button=PluginRemoveButton(),
)

class ArticleForm(forms.Form):
    author = TomSelectField(
        config=SINGLE_SELECT_CONFIG,
        label="Author",
        required=True
    )

    categories = TomSelectMultipleField(
        config=MULTIPLE_SELECT_CONFIG,
        label="Categories",
        help_text="Select one or more categories"
    )
```

# Working with Models

## Setting up Autocomplete Views

To use TomSelect with Django models, you'll need to create an autocomplete view that inherits from `AutocompleteView`:

```python
from django_tomselect.views import AutocompleteView
from .models import Author

class AuthorAutocompleteView(AutocompleteView):
    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]
    ordering = ["name"]
    page_size = 20

# urls.py
from django.urls import path
from .views import AuthorAutocompleteView

urlpatterns = [
    path("autocomplete/author/", AuthorAutocompleteView.as_view(), name="author-autocomplete"),
]
```

## Customizing Queryset Filtering

The `AutocompleteView` provides several methods for customizing queryset behavior:

```python
from django.db.models import Count, Q
from django_tomselect.views import AutocompleteView

class CategoryAutocompleteView(AutocompleteView):
    model = Category
    search_lookups = ["name__icontains", "parent__name__icontains"]

    def hook_queryset(self, queryset):
        """You can add annotations or modify queryset before filtering."""
        return queryset.annotate(
            article_count=Count("article"),
            total_articles=Count(
                "article",
                filter=Q(article__categories=F("id")) |
                       Q(article__categories__parent=F("id"))
            )
        )

    def get_queryset(self):
        """You can override the base queryset method."""
        queryset = super().get_queryset()

        # Additional filtering based on request parameters
        parent_id = self.request.GET.get("parent")
        if parent_id:
            if parent_id == "root":
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)

        return queryset
```

## Handling Related Fields

When working with related fields, you can use `filter_by` and `exclude_by` to create dependent fields:

```python
from django import forms
from django_tomselect.forms import TomSelectField
from django_tomselect.configs import TomSelectConfig

class ArticleForm(forms.Form):
    magazine = TomSelectField(
        config=TomSelectConfig(
            url="magazine-autocomplete",
            value_field="id",
            label_field="name"
        )
    )

    edition = TomSelectField(
        config=TomSelectConfig(
            url="edition-autocomplete",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id")  # Filter editions by selected magazine
        )
    )

    primary_author = TomSelectField(
        config=TomSelectConfig(
            url="author-autocomplete",
            value_field="id",
            label_field="name"
        )
    )

    contributing_authors = TomSelectMultipleField(
        config=TomSelectConfig(
            url="author-autocomplete",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id")  # Exclude primary author from options
        )
    )
```

## Model Field Relationships

`django_tomselect` works with different types of model relationships:

```python
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    magazine = models.ForeignKey("Magazine", on_delete=models.CASCADE)
    edition = models.ForeignKey("Edition", on_delete=models.CASCADE)
    authors = models.ManyToManyField("Author")
    categories = models.ManyToManyField("Category")

    class Meta:
        ordering = ["title"]

# Forms with model relationships
from django.forms import ModelForm
from django_tomselect.forms import TomSelectField, TomSelectMultipleField

class ArticleForm(ModelForm):
    magazine = TomSelectField(
        config=TomSelectConfig(url="magazine-autocomplete")
    )
    edition = TomSelectField(
        config=TomSelectConfig(
            url="edition-autocomplete",
            filter_by=("magazine", "magazine_id")
        )
    )
    authors = TomSelectMultipleField(
        config=TomSelectConfig(url="author-autocomplete")
    )

    class Meta:
        model = Article
        fields = ["title", "magazine", "edition", "authors", "categories"]
```

## Implementing Search

The `AutocompleteView` provides search capabilities through the `search_lookups` attribute and customizable search method:

```python
class AuthorAutocompleteView(AutocompleteView):
    model = Author
    search_lookups = [
        "name__icontains",
        "bio__icontains"
    ]

    def search(self, queryset, query):
        """You can override to add custom search implementations."""
        if not query:
            return queryset

        q_objects = Q()
        for lookup in self.search_lookups:
            q_objects |= Q(**{lookup: query})

        # Add custom search conditions
        q_objects |= Q(articles__title__icontains=query)

        return queryset.filter(q_objects).distinct()

    def prepare_results(self, results):
        """Format results for JSON response."""
        data = []
        for author in results:
            author_data = {
                "id": author.id,
                "name": author.name,
                "article_count": author.article_count,
                "formatted_name": f"{author.name} ({author.article_count} articles)"
            }
            data.append(author_data)
        return data
```

## Example View Implementation

Here's a complete example of a view using `django_tomselect` fields:

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

def article_create_view(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save()
            return redirect(reverse("article-list"))
    else:
        form = ArticleForm()

    return render(
        request,
        "article_form.html",
        {"form": form}
    )

def article_update_view(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            article = form.save()
            return redirect(reverse("article-list"))
    else:
        form = ArticleForm(instance=article)

    return render(
        request,
        "article_form.html",
        {"form": form}
    )
```

# Advanced Features

## Dependent/Chained Fields

`django_tomselect` supports dependent (chained) fields where the options in one field depend on the selection in another field. This is particularly useful for related data like Magazine/Edition selections or Category/Subcategory relationships.

### Example with Magazine and Edition:

```python
from django import forms
from django_tomselect.forms import TomSelectField
from django_tomselect.configs import TomSelectConfig

class DependentForm(forms.Form):
    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        ),
    )

    edition = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),  # Links to magazine field
        ),
        required=False,
    )
```

The corresponding autocomplete views:

```python
from django_tomselect.views import AutocompleteView
from .models import Edition, Magazine

class MagazineAutocompleteView(AutocompleteView):
    model = Magazine
    search_lookups = ["name__icontains"]

class EditionAutocompleteView(AutocompleteView):
    model = Edition
    search_lookups = ["name__icontains"]

    """Providing `filter_by` in the form config links the fields equivalent to the following queryset:
    def get_queryset(self):
        queryset = super().get_queryset()
        magazine_id = self.request.GET.get("magazine_id")
        if magazine_id:
            queryset = queryset.filter(magazine_id=magazine_id)
        return queryset
    """
```

## Field Exclusions

You can exclude options from one field based on selections in another field. This is useful when you want to prevent duplicate selections, like excluding a primary author from contributing authors.

```python
from django_tomselect.forms import TomSelectField, TomSelectMultipleField

class ArticleForm(forms.ModelForm):
    primary_author = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
        ),
    )

    contributing_authors = TomSelectMultipleField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),  # Excludes an existing primary author
        ),
    )
```

## Pagination Handling

`django_tomselect` automatically handles pagination for large datasets. You can customize the page size and implement infinite scrolling:

```python
class AuthorAutocompleteView(AutocompleteView):
    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]
    page_size = 20  # Results per page

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                article_count=Count("article"),
                active_articles=Count("article", filter=Q(article__status="active")),
            )
            .distinct()
        )
        return queryset
```

## HTMX Integration

`django_tomselect` supports HTMX for enhanced interactivity. Enable HTMX integration in your forms:

```python
from django_tomselect.configs import TomSelectConfig

class HTMXEnabledForm(forms.Form):
    category = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            use_htmx=True,
            general_config=GeneralConfig(
                create=True,
                create_with_htmx=True
            )
        )
    )
```

And an example corresponding template:

```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/htmx.org@2.0.3"></script>
    {{ form.media }}
</head>
<body>
    <div class="container mt-5"
         hx-get="{% url 'htmx-form-fragment' %}"
         hx-trigger="load"
         hx-swap="innerHTML">
    </div>
</body>
</html>
```

## Custom Search Implementation

You can implement sophisticated search functionality by customizing the AutocompleteView:

```python
class CategoryAutocompleteView(AutocompleteView):
    model = Category
    search_lookups = [
        "name__icontains",
        "parent__name__icontains",
    ]

    def search(self, queryset, query):
        """Enhanced search through full hierarchy"""
        if not query:
            return queryset

        q_objects = Q()
        for lookup in self.search_lookups:
            q_objects |= Q(**{lookup: query})

        # Add search in full path
        q_objects |= Q(full_path__icontains=query)

        return queryset.filter(q_objects)

    def hook_queryset(self, queryset):
        """Add annotations for better search results"""
        return queryset.annotate(
            full_path=Concat(
                "parent__name",
                Value(" → "),
                "name",
            )
        )
```

# Customization

## Styling and Theming

As mentioned before, `django_tomselect` supports multiple CSS frameworks and allows you to customize the appearance of your select fields.

### CSS Framework Selection

Configure the CSS framework in your Django settings:

```python
# settings.py

# Available options: "default", "bootstrap4", "bootstrap5"
TOMSELECT_CSS_FRAMEWORK = "bootstrap5"

# Control whether to use minified assets
TOMSELECT_MINIFIED = True  # Defaults to the opposite of DEBUG
```

### Custom CSS Classes

You can add custom CSS classes to your fields (see settings for available classes):

```python
from django_tomselect.forms import TomSelectField
from django_tomselect.configs import TomSelectConfig

class CustomStyledForm(forms.Form):
    category = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-category",
            attrs={
                "class": "form-control custom-select mb-3",
                "placeholder": "Select a category",
            }
        )
    )
```

## Custom Templates

`django_tomselect` allows you to customize various rendering aspects.

### Customizing Item Display

You can customize how items are displayed in the dropdown by overriding the render templates:

```html
{# templates/django_tomselect/render/option.html #}
{% if widget.is_tabular %}
    <div class="row">
        <div class="col">{{ data[this.settings.labelField] }}</div>
        {% for item in widget.plugins.dropdown_header.extra_values %}
            <div class="col">{{ data[item] }}</div>
        {% endfor %}
    </div>
{% else %}
    <div>{{ data[widget.label_field] }}</div>
{% endif %}
```

### Custom Selected Item Display

Customize how selected items appear:

```html
{# templates/django_tomselect/render/item.html #}
item: function(data, escape) {
    let item = '<div>' + escape(data.{{ widget.label_field }});

    {% if not widget.update_url == "" %}
        let update_url = "{{ widget.update_url }}".replace("_pk_", escape(data.id));
        item += `
            <a href="${update_url}" class="update ms-1" title="Update" target="_blank">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                     fill="none" stroke="currentColor" stroke-width="2"
                     class="feather feather-edit-3 text-success">
                    <path d="M12 20h9"></path>
                    <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                </svg>
            </a>`;
    {% endif %}

    item += '</div>';
    return item;
}
```

## Plugin Configuration

Each plugin can be customized through its configuration:

```python
from django_tomselect.configs import (
    TomSelectConfig,
    PluginDropdownHeader,
    PluginDropdownFooter,
    PluginClearButton,
    PluginRemoveButton,
)

class CustomPluginForm(forms.Form):
    authors = TomSelectMultipleField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Author Selection",
                header_class="bg-primary text-white p-2",
                show_value_field=False,
                extra_columns={
                    "article_count": "Articles",
                    "active_articles": "Active Articles",
                }
            ),
            plugin_dropdown_footer=PluginDropdownFooter(
                title="Browse all authors",
                footer_class="mt-2 px-2 border-top"
            ),
            plugin_clear_button=PluginClearButton(
                title="Clear Selection",
                class_name="clear-button btn-sm"
            ),
            plugin_remove_button=PluginRemoveButton(
                title="Remove this author",
                class_name="remove-item"
            )
        )
    )
```

## Dropdown Customization

### Tabular Layout

Create a tabular dropdown layout with additional columns:

```python
from django_tomselect.configs import TomSelectConfig, PluginDropdownHeader

config = TomSelectConfig(
    url="autocomplete-edition",
    value_field="id",
    label_field="name",
    plugin_dropdown_header=PluginDropdownHeader(
        show_value_field=False,
        label_field_label="Edition",
        extra_columns={
            "year": "Year",                   # `year` is a field in the model or annotation
            "pages": "Pages",                 # `pages` is a field in the model or annotation
            "pub_num": "Publication Number",  # `pub_num` is a field in the model or annotation
        }
    )
)
```

### Custom Rendering Functions

Customize the dropdown content by providing additional data in your autocomplete view:

```python
from django_tomselect.views import AutocompleteView

def author_autocomplete_view(AutocompleteView):
    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]

    def prepare_results(self, results):
        """Customize the data sent to the frontend"""
        data = []
        for author in results:
            author_data = {
                "id": author.id,
                "name": author.name,
                "bio": author.bio,
                "article_count": author.article_count,
                "active_articles": author.active_articles,
                "formatted_name": f"{author.name} ({author.article_count} articles)",
            }
            data.append(author_data)
        return data
```

### Loading States

Customize loading state displays:

```html
{# templates/django_tomselect/render/loading.html #}
loading: function(data, escape) {
    return '<div class="spinner-border spinner-border-sm" role="status">' +
           '<span class="visually-hidden">Loading...</span></div>';
}

{# templates/django_tomselect/render/loading_more.html #}
loading_more: function(data, escape) {
    return '<div class="loading-more-results py-2 d-flex align-items-center">' +
           '<div class="spinner-border spinner-border-sm me-2"></div>' +
           'Loading more results...</div>';
}
```

# Working with Forms

## Basic Form Integration

The simplest way to use `django_tomselect` is with standard Django forms. Here's a basic example:

```python
from django import forms
from django_tomselect.forms import TomSelectField
from django_tomselect.configs import TomSelectConfig

class ArticleForm(forms.Form):
    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            general_config=GeneralConfig(
                placeholder="Select a magazine...",
                preload="focus",
                highlight=True,
            ),
        ),
    )
```

This is useful for things like filtering datatables in JavaScript based on the value of the widget, where you don't need to save the form data.

## Working with ModelForms

ModelForms provide a more integrated approach, especially when working with related models:

```python
from django import forms
from django_tomselect.forms import TomSelectField, TomSelectMultipleField

class ArticleModelForm(forms.ModelForm):
    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        ),
    )

    authors = TomSelectMultipleField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            general_config=GeneralConfig(
                placeholder="Select authors...",
                max_items=None,  # Allow any number of selections
            ),
        ),
    )

    class Meta:
        model = Article
        fields = ["title", "magazine", "authors"]
```

## Handling Initial Values

`django_tomselect` automatically handles initial values in both forms and modelforms. For ModelForms, it will automatically populate the field with the current value(s) from the model instance:

```python
def article_edit_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    form = ArticleModelForm(request.POST or None, instance=article)

    if request.POST and form.is_valid():
        form.save()
        return redirect("article-list")

    return render(request, "article_form.html", {"form": form})
```

## Dynamic Form Fields

You can create forms with fields that update based on other field selections. Here's an example with dependent fields based on the example app:

```python
class DynamicArticleForm(forms.ModelForm):
    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        ),
    )

    edition = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),  # Filter editions by selected magazine
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically add edition field if magazine exists
        if self.instance.magazine:
            self.fields["edition"].initial = (
                self.instance.edition.pk if hasattr(self.instance, "edition") else None
            )
```

## Form Validation

`django_tomselect` fields support Django's form validation system. You can add custom validation:

```python
class AuthorArticleForm(forms.ModelForm):
    primary_author = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
        ),
    )

    contributing_authors = TomSelectMultipleField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),  # Exclude existing primary author value from options
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        primary_author = cleaned_data.get("primary_author")
        contributing_authors = cleaned_data.get("contributing_authors", [])

        if primary_author and primary_author in contributing_authors:
            raise forms.ValidationError(
                "Primary author cannot also be a contributing author"
            )

        return cleaned_data
```

## Form Rendering

Just like with any other form field, `django_tomselect` fields can be rendered in various ways:

```html
<!-- Default rendering -->
{{ form.as_div }}

<!-- Individual field rendering -->
<div class="mb-3">
    <label for="{{ form.magazine.id_for_label }}" class="form-label">
        {{ form.magazine.label }}
    </label>
    {{ form.magazine }}
    {% if form.magazine.errors %}
        <div class="alert alert-danger">
            {{ form.magazine.errors }}
        </div>
    {% endif %}
    {% if form.magazine.help_text %}
        <small class="form-text text-muted">
            {{ form.magazine.help_text }}
        </small>
    {% endif %}
</div>
```

# Security Considerations

When implementing `django_tomselect` in your project, it's important to consider various security aspects.

## Permission Handling

`django_tomselect` provides built-in permission handling through the `has_add_permission` method in autocomplete views. Here's how to implement proper permission checks:

```python
from django_tomselect.views import AutocompleteView

class AuthorAutocompleteView(AutocompleteView):
    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]

    def has_add_permission(self, request):
        """Control who can add new authors through the autocomplete."""
        if not request.user.is_authenticated:
            return False

        # Check specific model permissions
        return request.user.has_perm("myapp.add_author")
```

## User Authentication

Secure your URL patterns by decorating views with django's `login_required`, either in the URL configuration or in the view itself:

```python
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path(
        "autocomplete/author/",
        login_required(AuthorAutocompleteView.as_view()),
        name="autocomplete-author",
    ),
    path(
        "autocomplete/private/magazine/",
        login_required(MagazineAutocompleteView.as_view()),
        name="autocomplete-magazine",
    ),
]
```

Or using or `LoginRequiredMixin` for class-based views

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tomselect.views import AutocompleteView

class SecureAutocompleteView(LoginRequiredMixin, AutocompleteView):
    login_url = "/login/"
    redirect_field_name = "next"

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Only show records the user has permission to see
        if not self.request.user.is_staff:
            queryset = queryset.filter(organization=self.request.user.organization)

        return queryset
```

## CSRF Protection

`django_tomselect` works with Django's CSRF protection. Ensure your templates include the CSRF token:

```html
<form method="post">
    {% csrf_token %}
    {{ form.as_div }}
    <button type="submit">Save</button>
</form>
```

For AJAX requests in custom implementations:

```python
def create_via_ajax(request):
    if not request.headers.get("X-CSRFToken"):
        return JsonResponse({"error": "CSRF token missing"}, status=403)

    if request.method == "POST":
        # Process the request
        pass
```

## Query Filtering

Override AutocompleteView methods to implement proper query filtering, if needed, to prevent data leakage:

```python
class MagazineAutocompleteView(AutocompleteView):
    model = Magazine

    def apply_filters(self, queryset):
        """Apply security filters to queryset."""
        queryset = super().apply_filters(queryset)

        # Filter based on user permissions
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(public=True) | Q(organization=self.request.user.organization)
            )

        return queryset

    def prepare_results(self, results):
        """Sanitize data before sending to client."""
        return [{
            "id": obj.id,
            "name": obj.name,
            # Only include safe fields
            "public": obj.public,
        } for obj in results]
```
