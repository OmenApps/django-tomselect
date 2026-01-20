# Usage Guide

## Installation

`django_tomselect` provides form fields and widgets to integrate [Tom Select](https://tom-select.js.org/) into your Django projects, enabling dynamic and customizable `<select>` elements with advanced features like autocomplete, tagging, and search. Follow the steps below to install and configure the package in your project.

Most of the code samples below are based on the example app provided with the package. You can find the complete example app in the `example_project/example/` directory of the repository.

### Install the Package

You can install `django_tomselect` via pip:

```bash
pip install django_tomselect
```

This installs the latest release of `django_tomselect` and its dependencies.

### Add to `INSTALLED_APPS`

In your Django project's `settings.py`, add `django_tomselect` to the `INSTALLED_APPS` list:

```python
INSTALLED_APPS = [
    ...,
    "django_tomselect",
]
```

### Add the middleware and context processor

The middleware and context processor ensure a request context is provided for each form field (and widget) that requires it.

Add the `django_tomselect.middleware.TomSelectMiddleware` to your middleware list:

```python
MIDDLEWARE = [
    ...,
    "django_tomselect.middleware.TomSelectMiddleware",
]
```

Add the `django_tomselect.context_processors.tomselect` context processor to your template context processors:

```python
TEMPLATES = [
    {
        ...,
        "OPTIONS": {
            "context_processors": [
                ...,
                "django_tomselect.context_processors.tomselect",
            ],
        },
    },
]
```

### Verify Required Dependencies

`django_tomselect` integrates Tom Select with Django forms. Ensure you meet the following minimum requirements:

- **Django**: Version 4.2 or higher is recommended.
- **Tom Select**: Bundled via static files. You don't need to separately install Tom Select.

### Static Files

Confirm your static files setup is correct. Run:

```bash
python manage.py collectstatic
```

This collects the CSS, JavaScript, and related assets from `django_tomselect` (including Tom Select’s bundled files) into your static root.

### Include Tom Select in Your HTML

`django_tomselect` uses Django’s form media mechanism to load Tom Select’s CSS and JS. In any template where you plan to use `django_tomselect` widgets, ensure that you include the form’s media.

```html
<!DOCTYPE html>
<html lang="en">
<head>
</head>
<body>
    {{ form.media }}
</body>
</html>
```

This can also be done in a base template using the provided template tags. It is particularly useful if you will be loading one or more forms with tomselect fields via htmx.

```html
{% load django_tomselect %}
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Other head content -->
    {% csrf_token %}
    {% tomselect_media %}
    <!-- Optionally specify a css_framework: {% tomselect_media css_framework="bootstrap5" %} -->
</head>
<body>
</body>
</html>
```

If you prefer manual control, you can include only CSS or JS separately:

```django
{% tomselect_media_css css_framework="bootstrap4" %}
{% tomselect_media_js %}
```

These tags insert the appropriate `<link>` and `<script>` elements for Tom Select assets.

### When to Use Template Tags Over `form.media`

- **Global Availability**: If your layout loads forms after the page is rendered or conditionally via AJAX, having the Tom Select assets already included in the base template ensures the environment is ready before forms appear.
- **Consistent Theming**: Applying a global CSS framework choice or custom Tom Select styling in the base template means all subsequently loaded forms will follow the same look without needing to repeat configuration.
- **Cleaner Templates**: Keeping the media loading logic in a single place (like the base template) can simplify templates that render forms, making it easier to maintain and update.

While `{{ form.media }}` is suitable for inline, one-off usage, the template tags `{% tomselect_media %}`, `{% tomselect_media_css %}`, and `{% tomselect_media_js %}` give you more control and flexibility in how and where you load Tom Select’s assets.

### Optional: Configure CSS Framework

`django_tomselect` supports multiple CSS frameworks for styling: `default`, `bootstrap4`, and `bootstrap5`. You can choose a default framework in `settings.py`:

```python
TOMSELECT = {
    "DEFAULT_CSS_FRAMEWORK": "bootstrap5",  # Options: "default", "bootstrap4", "bootstrap5"
}
```

You can override this at any point using template tags (e.g., `{% tomselect_media css_framework="bootstrap4" %}`) or by configuring the widget on a per-field basis.

## Quick Start

This section guides you through a simple, end-to-end example of integrating `django_tomselect` into your Django project. By the end, you’ll have a functioning autocomplete-enabled select field that dynamically fetches options from the server as the user types.

### Basic Form Implementation

The simplest approach is to add a `TomSelectModelChoiceField` to a basic form. This field uses a `TomSelectConfig` that specifies where to fetch data from and how to display it.

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.app_settings import TomSelectConfig

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

### ModelForm Integration

Integrating with a Django `ModelForm` is straightforward—just replace a standard model field with a `TomSelectModelChoiceField`. Suppose you have an `Article` model that references a `Magazine` model via a ForeignKey:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.app_settings import TomSelectConfig
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

### Setting Up the Views

#### Configure the Autocomplete View

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

#### Use the Form in a View

Create a simple view that handles displaying and processing the `ArticleForm`:

```python
from django.shortcuts import redirect, TemplateResponse
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

### Add URL Patterns

Register the URLs for your article creation page and the magazine autocomplete endpoint:

```python
from django.urls import path
from .views import article_create_view, MagazineAutocompleteView

urlpatterns = [
    path("article/create/", article_create_view, name="article-create"),
    path("autocomplete/magazine/", MagazineAutocompleteView.as_view(), name="autocomplete-magazine"),
]
```

### Template Setup

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

## Core Components

`django_tomselect` is built around a few key components that work together to provide a seamless autocomplete and selection experience in your Django forms. Understanding these components will help you configure and customize the behavior of Tom Select in your application.

### Autocompletes

Autocompletes are server-side views that respond to requests from the Tom Select widget. They provide the data—often filtered or searched by the user’s query—that populates the dropdown. Implementing an autocomplete view is crucial for any dynamic search functionality.

#### `AutocompleteModelView`

- **Purpose**: Serves as the primary autocomplete endpoint for model-based data.
- **Typical Use Case**: When you want to provide a list of model instances (e.g., `Magazine` objects) to a Tom Select widget, allowing the user to search by name and select one or more items.
- **Key Features**:
  - Configurable `search_lookups` to filter data (e.g., `name__icontains`).
  - Supports pagination, ordering, and filtering by additional parameters.
  - Integrates with Django’s authentication and permission system.
  - Can be subclassed to customize search logic (`search()`, `get_queryset()`), filtering (`apply_filters()`), and result formatting (`prepare_results()`).

#### `AutocompleteIterablesView`

- **Purpose**: Provides autocomplete data for simple iterables (lists, tuples, or Django choices), rather than model querysets.
- **Typical Use Case**: When selecting from a static list of values (e.g., a list of countries) without hitting the database.
- **Key Features**:
  - Offers search capabilities over a static set of values.
  - Pagination and incremental loading for large sets of options.
  - Simpler than `AutocompleteModelView`, since no ORM queries are involved.

:::{note}
Could you manually add Tom Select to your project and supply iterables as context to the template? Absolutely. But `django_tomselect` standardizes the process, providing a consistent API, integration with Django forms, and advanced features like filtering and server-side pagination for large datasets.
:::

### Form Fields

Form fields integrate `django_tomselect` widgets into Django’s form system, making it easy to replace traditional `ModelChoiceField` or `ModelMultipleChoiceField` fields with Tom Select-enabled versions.

- **TomSelectModelChoiceField**:
  - Single-select field, wrapping a `ModelChoiceField`.
  - Ideal when the user must pick exactly one model instance.

- **TomSelectModelMultipleChoiceField**:
  - Multi-select field, wrapping a `ModelMultipleChoiceField`.
  - Enables the user to select multiple model instances.

- **TomSelectChoiceField**:
  - Single-select field for static choices (e.g., tuples, lists, or Django choices).
  - Similar to `TomSelectModelChoiceField`, but for non-model data.

- **TomSelectMultipleChoiceField**:
  - Multi-select field for static choices.
  - Similar to `TomSelectModelMultipleChoiceField`, but for non-model data.

**Key Features**:

- Each field type automatically binds to a corresponding Tom Select widget.
- Configurations (e.g., `url`, `placeholder`, `search_lookups`) are provided through `TomSelectConfig`.
- Behaves like a standard Django model field, making it easy to integrate into `ModelForm`s.
- Ensures validation and data integrity: the chosen options must exist in the referenced queryset.

### Widgets

Widgets handle the front-end presentation and behavior of the fields. They render the `<select>` element, attach the appropriate JavaScript initialization code, and integrate with the autocomplete views.

- **TomSelectModelWidget**:
  - For single-select fields.
  - Renders as a Tom Select-enhanced `<select>` field, loading data from a specified autocomplete endpoint.

- **TomSelectModelMultipleWidget**:
  - For multi-select fields.
  - Similar to `TomSelectModelWidget`, but allows multiple item selection.

- **TomSelectWidget**:
  - For static choice fields.
  - Renders a Tom Select-enhanced `<select>` field for static choices.

- **TomSelectMultipleWidget**:
  - For static multiple choice fields.
  - Similar to `TomSelectWidget`, but for multiple selections.

**Key Features**:

- Customize look, feel, and behavior through `TomSelectConfig` and widget attributes.
- Seamless integration with autocomplete views: the widget automatically fetches data based on user input.
- Supports advanced features like dependent/chained fields, custom templates, plugin configurations, and HTMX integration.
- Works well with different CSS frameworks (e.g., Bootstrap) for styling, as well as custom templates for full UI control.

## Configuration

`django_tomselect` provides a flexible configuration system built around a main `TomSelectConfig` class. This class, along with various plugin and framework configuration options, lets you control the behavior, appearance, and functionality of Tom Select widgets at both a global and per-field level.

### TomSelectConfig Overview

`TomSelectConfig` is the central configuration object that defines how the widget behaves:

- **URL and Data Retrieval**: Specify the `url` to fetch autocomplete results from.
- **Value and Label Fields**: Define which model fields map to the option’s value and label.
- **Search and Loading Behavior**: Control how and when searches are triggered, how options are preloaded, and how results are highlighted.
- **CSS Framework Integration**: Choose a styling framework (e.g., Bootstrap) to apply consistent UI elements.

**Example:**

```python
from django_tomselect.app_settings import TomSelectConfig

config = TomSelectConfig(
    url="author-autocomplete",
    value_field="id",
    label_field="name",
    placeholder="Select an author...",
    preload="focus",
    highlight=True,
)
```

### General Configuration Options

Basic settings for the widget are typically passed as keyword arguments directly into `TomSelectConfig`. These include:

- **Search Behavior**: `minimum_query_length` to determine when to trigger searches.
- **Display Settings**: `placeholder` text, whether to `open_on_focus`, and `highlight` matching terms.
- **Loading and Performance**: `load_throttle` to control how frequently searches occur, and `max_options` to limit how many results appear.
- **Creation and HTMX**: `create` to allow new item creation, and `create_with_htmx` to handle server-driven creation workflows.

**Example:**

```python
config = TomSelectConfig(
    url="author-autocomplete",
    value_field="id",
    label_field="name",
    placeholder="Search authors...",
    minimum_query_length=2,
    open_on_focus=True,
    preload="focus",
    highlight=True,
    load_throttle=300,
    max_options=50,
    create=False,
    create_with_htmx=False,
)
```

### Available Plugins

Plugins enhance the default behavior of Tom Select. `django_tomselect` maps plugin configurations to Python classes that you can pass into `TomSelectConfig`. Common plugins include:

- **Checkbox Options**: Display checkboxes alongside dropdown items.
- **Clear Button**: A button to quickly clear all selections.
- **Dropdown Header/Footer**: Custom headers and footers for grouping data, adding labels, or linking to external pages.
- **Remove Button**: A small “x” icon to quickly remove selected items.
- **Dropdown Input**: Adds a searchable input inside the dropdown itself.

**Example:**

```python
from django_tomselect.app_settings import (
    TomSelectConfig,
    PluginClearButton,
    PluginDropdownHeader
)

config = TomSelectConfig(
    url="author-autocomplete",
    value_field="id",
    label_field="name",
    highlight=True,
    plugin_clear_button=PluginClearButton(
        title="Clear Selection",
        class_name="clear-button"
    ),
    plugin_dropdown_header=PluginDropdownHeader(
        title="Authors",
        show_value_field=False,
        extra_columns={"article_count": "Articles"}
    )
)
```

### CSS Framework Options

`django_tomselect` supports `default`, `bootstrap4`, and `bootstrap5` frameworks:

**Examples:**

```python
TomSelectConfig(css_framework="bootstrap5")  # Use Bootstrap 5 styles
TomSelectConfig(css_framework="bootstrap4")  # Use Bootstrap 4 styles
TomSelectConfig(css_framework="default")     # Use default Tom Select styles
```

You can also set a global default in your `settings.py`:

```python
# settings.py
TOMSELECT = {
    "DEFAULT_CSS_FRAMEWORK": "bootstrap5"
}
```

### Global Settings vs Field-level Settings

**Global Settings**: Define a default configuration that applies to all `django_tomselect` fields. This might go in your `settings.py`, allowing a single source of truth for default behavior:

```python
# settings.py
from django_tomselect.app_settings import TomSelectConfig

GLOBAL_TOMSELECT_CONFIG = TomSelectConfig(
    minimum_query_length=2,
    highlight=True,
    preload="focus"
)
```

**Field-level Overrides**: When you create a form field, you can pass a custom `TomSelectConfig` to override global defaults for that specific field. This ensures local control where needed, without duplicating common settings everywhere.

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.app_settings import TomSelectConfig

class AuthorForm(forms.Form):
    author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="author-autocomplete",
            minimum_query_length=1,  # Overrides the global setting of 2
            highlight=True
        )
    )
```

In this example, the global setting for `minimum_query_length` might be 2, but here it’s reduced to 1 for the `author` field.

### Example Configuration

Bringing it all together, here’s a more complete example:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectModelMultipleChoiceField
from django_tomselect.app_settings import (
    TomSelectConfig,
    PluginRemoveButton,
    PluginDropdownFooter
)

# Single-select field configuration
AUTHOR_CONFIG = TomSelectConfig(
    url="author-autocomplete",
    value_field="id",
    label_field="name",
    placeholder="Select an author...",
    highlight=True,
    open_on_focus=True,
    preload="focus",
    plugin_remove_button=PluginRemoveButton(title="Remove", label="×"),
)

# Multi-select field configuration
CATEGORY_CONFIG = TomSelectConfig(
    url="category-autocomplete",
    value_field="id",
    label_field="name",
    placeholder="Select categories...",
    highlight=True,
    open_on_focus=True,
    plugin_dropdown_footer=PluginDropdownFooter(
        title="Categories Footer",
        footer_class="dropdown-footer"
    ),
    max_items=None,  # Unlimited selections
)

class ArticleForm(forms.Form):
    author = TomSelectModelChoiceField(config=AUTHOR_CONFIG, label="Author")
    categories = TomSelectModelMultipleChoiceField(config=CATEGORY_CONFIG, label="Categories")
```

In this configuration:

- The `author` field uses a single-select setup with a remove button plugin.
- The `categories` field is multi-select with a dropdown footer plugin.
- Both fields have their own configuration objects, ensuring clear and maintainable setup.

## Working with Models

Using `django_tomselect` with Django models involves setting up dedicated autocomplete views that return JSON responses to your TomSelect widgets, customizing querysets for dynamic filtering, and configuring search behavior. This section covers the basic concepts you will need to integrate TomSelect fields into your Django models and forms.

### Setting up Autocomplete Views

To use TomSelect widgets with Django model data, you must create a view that extends `AutocompleteModelView`. This view handles incoming requests from the widget, fetches matching model instances, and returns a JSON response formatted for TomSelect.

```python
# autocompletes.py
from django_tomselect.autocompletes import AutocompleteModelView
from .models import Author

class AuthorAutocompleteView(AutocompleteModelView):
    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]
    ordering = ["name"]
    page_size = 20  # Limit how many results to return per request

# urls.py
from django.urls import path
from .autocompletes import AuthorAutocompleteView

urlpatterns = [
    path("autocomplete/author/", AuthorAutocompleteView.as_view(), name="author-autocomplete"),
]
```

By extending `AutocompleteModelView`, you gain access to built-in pagination, optional permission handling, and straightforward customization points like `search_lookups` and `ordering`.

### Customizing Queryset Filtering

When working with related data or conditional dropdowns, you may need to dynamically filter the options returned by the autocomplete view. `django_tomselect` supports passing filtering parameters from the widget to the view through `filter_by` and `exclude_by`. These parameters allow the view to return only relevant model instances.

For example, you might have a dependent field that filters `Edition` instances based on a selected `Magazine`. In your view, you could implement the logic as follows:

```python
from django.db.models import F, Q
from django_tomselect.autocompletes import AutocompleteModelView
from .models import Edition

class EditionAutocompleteView(AutocompleteModelView):
    model = Edition
    search_lookups = ["name__icontains"]

    def apply_filters(self, queryset):
        # The filter_by parameter will be in the format: "magazine__id=<value>"
        # If the widget sends this parameter, filter editions by the given magazine ID.
        return super().apply_filters(queryset)
```

If the frontend widget includes `filter_by=("magazine", "magazine_id")` in its configuration, the widget will automatically append something like `?f='magazine__id=1'` to the AJAX request once a magazine is selected. The `apply_filters` method will then restrict the queryset accordingly.

Similarly, `exclude_by` works the same way but excludes matching objects. For example, if you want to prevent a primary author from appearing in a list of contributing authors, you can use `exclude_by=("primary_author", "id")` in the widget config. The view will receive `e='primary_author__id=<value>'` and remove that author from the results.

### Handling Related Fields

TomSelect widgets can be chained to handle related fields intuitively. For instance, selecting a `Magazine` can dynamically filter the available `Editions`, and selecting an `Edition` can further filter `Articles`. You configure this by specifying `filter_by` or `exclude_by` parameters at the widget level, ensuring that the view applies those constraints.

For a field that depends on another selection, the widget configuration might look like this:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectModelMultipleChoiceField
from django_tomselect.configs import TomSelectConfig

class ArticleForm(forms.ModelForm):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(url="magazine-autocomplete")
    )
    edition = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="edition-autocomplete",
            filter_by=("magazine", "magazine_id")  # Dynamically filter editions by the selected magazine
        )
    )
    authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(url="author-autocomplete")
    )

    class Meta:
        model = Article
        fields = ["title", "magazine", "edition", "authors", "categories"]
```

### Model Field Relationships

`django_tomselect` can work seamlessly with various model relationship types, such as `ForeignKey`, `ManyToManyField`, and `OneToOneField`. When bound to `ModelChoiceField` or `ModelMultipleChoiceField` subclasses, the widget will handle the standard relational logic:

- **ForeignKey fields:** Single selection of a related instance.
- **ManyToManyField fields:** Multiple selection from a related model.
- **Chained relationships:** Filter results based on the currently selected related object, as shown with `filter_by` and `exclude_by`.

Your autocomplete views should return the relevant model instances, and the widget will ensure the correct options are presented to the user.

### Implementing Search

Searching is a key feature of `AutocompleteModelView`. By setting `search_lookups`, you define which model fields should be searched against the user’s query.

```python
class AuthorAutocompleteView(AutocompleteModelView):
    model = Author
    search_lookups = [
        "name__icontains",
        "bio__icontains"
    ]

    # Optionally override search for more complex queries:
    def search(self, queryset, query):
        if not query:
            return queryset

        # Combine Q lookups to implement multi-field searches
        q_objects = Q()
        for lookup in self.search_lookups:
            q_objects |= Q(**{lookup: query})

        return queryset.filter(q_objects).distinct()
```

By default, `search_lookups` are used directly. If you need more advanced logic—such as searching multiple related fields, adding custom filters, or combining conditions—override the `search()` method.

### Example View Implementation

Below is a sample implementation that ties everything together. This view filters results, applies search logic, orders the queryset, and handles dynamic parameters from the widget:

```python
from django.db.models import Count, Q, F
from django_tomselect.autocompletes import AutocompleteModelView
from .models import Category

class CategoryAutocompleteView(AutocompleteModelView):
    model = Category
    search_lookups = ["name__icontains", "parent__name__icontains"]
    ordering = ["name"]
    page_size = 20

    def hook_queryset(self, queryset):
        # Annotate with counts or other prefetch logic
        return queryset.annotate(article_count=Count("article"))

    def apply_filters(self, queryset):
        # Use built-in filtering logic. If `f='parent__id=<value>'` is provided,
        # this method will apply that filter automatically.
        return super().apply_filters(queryset)

    def search(self, queryset, query):
        # Add custom search conditions in addition to the configured search_lookups
        if query:
            q_objects = Q()
            for lookup in self.search_lookups:
                q_objects |= Q(**{lookup: query})
            # Add custom fields to search:
            q_objects |= Q(articles__title__icontains=query)
            return queryset.filter(q_objects).distinct()
        return queryset

    def prepare_results(self, results):
        # Format results for JSON response
        data = []
        for cat in results:
            data.append({
                "id": cat["id"],
                "name": cat["name"],
                "article_count": cat["article_count"],
            })
        return data
```

This example demonstrates how to integrate all aspects of model-based autocompletes: searching, filtering, ordering, and result preparation. With these fundamentals in place, you can easily incorporate TomSelect widgets into your Django forms and leverage your models’ relationships to provide a responsive, intuitive selection interface for your users.

## Advanced Features

As your project grows, you may need more than just basic autocomplete functionality. `django_tomselect` includes several advanced features that let you dynamically update dropdowns based on user selections, apply exclusion rules, handle large datasets efficiently, integrate with HTMX for seamless server-driven interactions, and customize the search logic to fit your needs. Additionally, you can override core view and widget methods to fine-tune how data is fetched and presented.

### Visualizing Request Flow and Data Processing

```{mermaid}

    sequenceDiagram
        participant Client
        participant Widget
        participant View
        participant Cache
        participant Database

        Client->>Widget: User interacts with select
        Widget->>View: Send autocomplete request

        alt Cache enabled
            View->>Cache: Check permissions
            Cache-->>View: Return cached permissions
        else Cache disabled
            View->>Database: Check permissions
            Database-->>View: Return permissions
        end

        View->>Database: Query filtered data
        Database-->>View: Return results
        View->>View: Process results
        View-->>Widget: Return JSON response
        Widget-->>Client: Update dropdown options

        note over Widget,View: Permissions are cached<br/>if caching is enabled
        note over View,Database: Results are paginated<br/>and filtered based on search
```

### Dependent/Chained Fields

One common pattern is to make the options in one dropdown field depend on the selected value of another field. For example, after a user chooses a `Category`, you might need to restrict available `Subcategories` to those related to that `Category`.

To achieve this, `django_tomselect` supports dependent (chained) fields. When setting up your widget configuration, you can specify a `filter_by` attribute, instructing the field to refresh its options whenever the parent field changes.

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.configs import TomSelectConfig

class CategoryForm(forms.Form):
    category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="category-autocomplete",
            value_field="id",
            label_field="name",
        ),
    )

    subcategory = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="subcategory-autocomplete",
            value_field="id",
            label_field="name",
            # Instructs the subcategory field to dynamically filter by the selected category
            filter_by=("category", "category_id"),
        ),
    )
```

#### Multiple Field Filters

You can filter by multiple fields using a list of tuples. All conditions are combined (aka: AND):

```python
from django_tomselect.app_settings import TomSelectConfig

class ArticleFilterForm(forms.Form):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(url="autocomplete-magazine"),
    )
    status = TomSelectChoiceField(
        config=TomSelectConfig(url="autocomplete-article-status"),
    )
    # Filter articles by BOTH magazine AND status
    articles = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article",
            filter_by=[
                ("magazine", "magazine_id"),  # Filter by selected magazine
                ("status", "status"),         # AND by selected status
            ],
        ),
    )
```

See the [Multiple Filter-By](example_app/multiple_filter_by.md) example for complete demonstration.

#### Constant Value Filters

Use the `Const` helper to filter by a constant value that doesn't come from a form field. This is useful for enforcing business rules in the UI:

```python
from django_tomselect.app_settings import TomSelectConfig, Const

class PublishedArticleForm(forms.Form):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(url="autocomplete-magazine"),
        required=False,
    )
    # Articles always filtered to published status, optionally by magazine
    published_articles = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article",
            filter_by=[
                ("magazine", "magazine_id"),       # Optional magazine filter
                Const("published", "status"),      # Always filter to published
            ],
        ),
    )
```

Common use cases for constant filters:
- Only show published content: `Const("published", "status")`
- Only show active items: `Const("true", "is_active")`
- Filter by current year: `Const("2024", "year")`

See the [Constant Filter-By](example_app/constant_filter_by.md) example for complete demonstration.

### Field Exclusions

Beyond filtering, you might need to exclude certain options dynamically. For example, if you have a form with a `primary_author` field and a `contributing_authors` field, you may want to prevent the primary author from appearing in the contributing authors list.

#### Using `exclude_by`

`django_tomselect` lets you specify `exclude_by` logic similar to how `filter_by` works. In your widget configuration, you can set `exclude_by` to exclude options based on the value of another field in the same form.

```python
class ArticleForm(forms.Form):
    primary_author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="author-autocomplete",
            value_field="id",
            label_field="name",
        )
    )

    contributing_authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="author-autocomplete",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),  # Excludes whoever is chosen as the primary author
        )
    )
```

This ensures that once a primary author is selected, they disappear from the options in the contributing authors field.

### Pagination Handling

For large datasets, loading all results at once can be inefficient. `django_tomselect` implements pagination and supports virtual scrolling to load results incrementally as the user scrolls the dropdown.

In your `AutocompleteModelView`, set `page_size` to determine how many items load per request:

```python
from django_tomselect.autocompletes import AutocompleteModelView
from .models import Author

class AuthorAutocompleteView(AutocompleteModelView):
    model = Author
    search_lookups = ["name__icontains"]
    page_size = 20
```

When the user scrolls through the dropdown, `django_tomselect` will automatically fetch the next page of results. The JSON response should include `has_more` and `next_page` parameters to indicate whether more results are available. The widget will keep loading pages until no more results remain.

### Custom Search Implementation

If your filtering and searching needs extend beyond basic lookups, you can override the `search()` method in your `AutocompleteModelView` to implement custom logic.

```python
from django.db.models import Q
from django_tomselect.autocompletes import AutocompleteModelView
from .models import Category

class CategoryAutocompleteView(AutocompleteModelView):
    model = Category
    search_lookups = ["name__icontains", "description__icontains"]

    def search(self, queryset, query):
        if query:
            # Combine multiple lookups with Q objects
            return queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return queryset
```

By extending `search()`, you gain fine-grained control over how queries are processed, letting you implement complex logic such as multi-field search, fuzzy matching, or multi-level relationship lookups.

### Overriding Methods in Autocomplete Views

`AutocompleteModelView` provides several hook methods that you can override to customize behavior at every stage of processing a request:

- `get_queryset(self)`: Define the base queryset. Add `prefetch_related` or `annotate` calls for efficiency.
- `apply_filters(self, queryset)`: Customize how filters and exclusions are applied based on `filter_by` and `exclude_by`.
- `search(self, queryset, query)`: Implement complex search logic.
- `order_queryset(self, queryset)`: Change the ordering of results.
- `prepare_results(self, results)`: Modify the output dictionary before sending JSON to the frontend.
- `hook_queryset(self, queryset)`: Manipulate the queryset before any filters or searches are applied.
- `hook_prepare_results(self, results)`: Adjust results after all other processing is complete.

For example, to annotate a queryset and then filter by a calculated field:

```python
class CustomAutocompleteView(AutocompleteModelView):
    model = Category

    def hook_queryset(self, queryset):
        return queryset.annotate(is_special=(F('some_field') > 5))

    def apply_filters(self, queryset):
        # Only return "special" categories
        return queryset.filter(is_special=True)
```


## Customization

`django_tomselect` is highly flexible, allowing you to adjust its visual appearance, modify how data is displayed, and fine-tune plugin settings. From selecting different CSS frameworks to defining custom template blocks, you can tailor the user experience to match the style and functionality of your application.

### Styling and Theming

One of the simplest ways to customize the look of your TomSelect widgets is by choosing a supported CSS framework and adding custom CSS classes.

#### CSS Framework Selection

`django_tomselect` supports `default`, `bootstrap4`, and `bootstrap5` frameworks out-of-the-box. You can configure the framework and the use of minified assets in your project’s Django settings:

```python
# settings.py

# Options: "default", "bootstrap4", "bootstrap5"
TOMSELECT_CSS_FRAMEWORK = "bootstrap5"

# Controls whether to use minified JS/CSS; defaults to opposite of DEBUG
TOMSELECT_MINIFIED = True
```

If you choose a bootstrap-based theme, `django_tomselect` will automatically apply framework-specific classes to your dropdowns and items, creating a consistent look and feel with the rest of your UI.

#### Custom CSS Classes

You can further refine the appearance by adding custom CSS classes to the widget’s HTML attributes. For example, you can add your own `form-control` classes, spacing utilities, or brand-specific color classes:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.configs import TomSelectConfig

class CustomStyledForm(forms.Form):
    category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            attrs={
                "class": "form-control custom-select mb-3",
                "placeholder": "Select a category",
            }
        )
    )
```

This approach lets you leverage both the chosen framework’s utility classes and your custom styles.

### Custom Templates

The rendering of items, dropdowns, and other UI elements is handled through templates located in `django_tomselect/templates/django_tomselect/render/`. By overriding these templates in your own project’s template directory, you can gain complete control over the output.

#### Visualizing Template Structure

```{mermaid}

    flowchart TD
        subgraph Template Structure
            A[tomselect.html] -->|includes| B[render/select.html]
            A -->|contains| C[Initialization Script]

            C -->|uses| D[Plugin Templates]

            subgraph Plugin Templates
                E[clear_button.html]
                F[dropdown_header.html]
                G[dropdown_footer.html]
                H[item.html]
                I[loading.html]
                J[no_results.html]
                K[option.html]
                L[option_create.html]
            end

            subgraph Context
                M[Widget Context]
                N[Plugin Context]
                O[URL Context]
                P[Permission Context]
            end

            A -->|renders with| Context
        end

        style A fill:#f9f,stroke:#333
        style B fill:#bbf,stroke:#333
        style C fill:#fbf,stroke:#333
        style D fill:#ddf,stroke:#333
```

#### Adjusting Template Blocks

`django_tomselect` uses template blocks to let you override pieces of the rendering logic. For instance, you could override `option.html` or `item.html` to change how options and selected items appear in the dropdown.

If you want to display additional data, format labels differently, or integrate icons, you can do so by editing these templates. Just ensure that your overridden templates are placed in `templates/django_tomselect/render/` so that Django’s template loading mechanism finds and uses them.

#### Example: Customizing Item Display

Suppose you want to display extra metadata like the number of related articles next to an author’s name. You could override `option.html` to display a more detailed layout:

```html
{# templates/django_tomselect/render/option.html #}
option: function(data, escape) {
    return `<div role="option">
              <strong>${escape(data.name)}</strong><br>
              <small>${escape(data.article_count)} articles</small>
            </div>`;
},
```

By integrating logic directly into the template, you can dynamically show additional attributes returned by your autocomplete view’s `prepare_results()` method.

#### Custom Selected Item Display

You can also tailor how selected items appear in the input field by overriding `item.html`. For example, adding an update button next to the selected item:

```html
{# templates/django_tomselect/render/item.html #}
item: function(data, escape) {
    let item = `<div>${escape(data.name)}`;
    if (data.update_url) {
        item += `<a href="${escape(data.update_url)}" class="ms-1" title="Update" target="_blank">
                    <i class="bi bi-pencil-square text-success"></i>
                 </a>`;
    }
    item += `</div>`;
    return item;
},
```

### Plugin Configuration

`django_tomselect` supports various plugins—such as clear buttons, dropdown headers/footers, remove buttons, and more—that enhance the functionality and appearance of your dropdowns. You can configure these plugins through `TomSelectConfig`:

```python
from django import forms
from django_tomselect.forms import TomSelectModelMultipleChoiceField
from django_tomselect.configs import (
    TomSelectConfig,
    PluginDropdownHeader,
    PluginDropdownFooter,
    PluginClearButton,
    PluginRemoveButton,
)

class CustomPluginForm(forms.Form):
    authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Author Selection",
                header_class="bg-primary text-white p-2"
            ),
            plugin_dropdown_footer=PluginDropdownFooter(
                title="Browse All Authors",
                footer_class="border-top mt-2 px-2"
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

By adjusting the plugin settings, you can control label text, classes, and additional columns displayed in tabular layouts.

### Dropdown Customization

The dropdown can be rendered in a tabular format, show multiple columns, or present custom states while loading or fetching more data.

#### Tabular Layout

If you have additional metadata for each option (e.g., year, pages, publication number), you can create a tabular layout by enabling `plugin_dropdown_header` with extra columns:

```python
from django_tomselect.configs import TomSelectConfig, PluginDropdownHeader

config = TomSelectConfig(
    url="autocomplete-edition",
    value_field="id",
    label_field="name",
    plugin_dropdown_header=PluginDropdownHeader(
        label_field_label="Edition",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        }
    )
)
```

In the template, `option.html` and `dropdown_header.html` work together to display data in columns, giving your users a more structured view of their choices.

#### Custom Rendering Functions

By returning extra data in `prepare_results()` from your `AutocompleteModelView`, you can reference those fields in your templates. Add logic to `prepare_results()` to annotate querysets or perform computations, and then display those computed fields directly in the rendered templates.

```python
def prepare_results(self, results):
    data = []
    for author in results:
        data.append({
            "id": author["id"],
            "name": author["name"],
            "article_count": author["article_count"],
            "formatted_name": f"{author['name']} ({author['article_count']} articles)",
        })
    return data
```

Then reference `formatted_name` in your `option.html` template to display a customized label.

#### Loading States

Enhance the user experience by customizing loading states. Override the `loading.html` and `loading_more.html` templates to provide spinners, animated indicators, or descriptive messages.

```html
{# templates/django_tomselect/render/loading.html #}
loading: function(data, escape) {
    return `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
},
```

This ensures users have visual feedback when the widget is fetching new data.


## Working with Forms

Integrating `django_tomselect` into your forms is straightforward and leverages the familiar patterns of standard Django forms and ModelForms. Whether you’re working with simple stand-alone forms or complex model-backed forms with dynamic fields and validation, `django_tomselect` fits naturally into the Django form ecosystem.

### Basic Form Integration

You can start using `django_tomselect` fields in regular Django forms without any additional configuration beyond defining the widget in the field. For example, to create a form that allows users to filter results based on a selected `Magazine`:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.configs import TomSelectConfig

class MagazineFilterForm(forms.Form):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            placeholder="Select a magazine...",
            preload="focus",
            highlight=True,
        )
    )
```

This form can be used to filter data in a view or dynamically update a portion of a page with JavaScript. The TomSelect widget handles autocompletion, pagination, and other interactive features automatically.

### Working with ModelForms

When dealing with database-backed models, `ModelForm` provides a more integrated solution. By using `TomSelectModelChoiceField` or `TomSelectModelMultipleChoiceField`, you can seamlessly integrate autocompletes into your forms:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectModelMultipleChoiceField
from django_tomselect.configs import TomSelectConfig
from .models import Article

class ArticleForm(forms.ModelForm):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        )
    )
    authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            placeholder="Select authors...",
            max_items=None,  # Allow any number of authors
        )
    )

    class Meta:
        model = Article
        fields = ["title", "magazine", "authors"]
```

ModelForms automatically populate initial values from the provided model instance, and saving the form updates the related database records as normal.

### Handling Initial Values

`django_tomselect` handles initial values just like any other Django form field. For ModelForms, the field will display the current related objects, so if you’re editing an existing `Article`:

```python
from django.shortcuts import get_object_or_404, TemplateResponse, redirect

def article_edit_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    form = ArticleForm(request.POST or None, instance=article)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("article-list")

    return TemplateResponse(request, "article_form.html", {"form": form})
```

When loading this form, the `magazine` and `authors` fields will be pre-filled with the article’s current magazine and authors, allowing users to adjust the selection as needed.

### Dynamic Form Fields

A powerful feature of `django_tomselect` is the ability to dynamically update form fields based on other fields’ values—also known as dependent or chained fields. For example, you might want the `edition` field to show only editions from the currently selected `magazine`.

```python
class DynamicArticleForm(forms.ModelForm):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        )
    )
    edition = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),  # Filter editions by selected magazine
        ),
        required=False,
    )

    class Meta:
        model = Article
        fields = ["title", "magazine", "edition"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set the initial value for 'edition' if the instance already has a related edition
        if self.instance and self.instance.magazine and self.instance.edition:
            self.fields["edition"].initial = self.instance.edition.pk
```

In this scenario, when the `magazine` field changes, the widget triggers the `edition` field to refresh its options via AJAX, ensuring users see only editions relevant to the chosen magazine.

### Form Validation

`django_tomselect` fields integrate with Django’s form validation system. You can write custom clean methods or field-specific validators just like any other form field. The following example ensures the selected `primary_author` is not also chosen as a contributing author:

```python
class AuthorArticleForm(forms.ModelForm):
    primary_author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
        )
    )
    contributing_authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),
        )
    )

    class Meta:
        model = Article
        fields = ["title", "primary_author", "contributing_authors"]

    def clean(self):
        cleaned_data = super().clean()
        primary = cleaned_data.get("primary_author")
        contributors = cleaned_data.get("contributing_authors", [])

        if primary and primary in contributors:
            raise forms.ValidationError(
                "The primary author cannot also be a contributing author."
            )
        return cleaned_data
```

### Form Rendering

Since `django_tomselect` fields are just Django form fields with a special widget, you can render them using all the standard approaches:

```html
<!-- Default rendering with form.as_p, as_ul, or as_table -->
{{ form.as_p }}

<!-- Render an individual field with labels, errors, and help text -->
<div class="mb-3">
    <label for="{{ form.magazine.id_for_label }}" class="form-label">
        {{ form.magazine.label }}
    </label>
    {{ form.magazine }}
    {% if form.magazine.errors %}
        <div class="invalid-feedback d-block">
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

TomSelect’s JavaScript and CSS are automatically included based on your configuration. By combining this rendering flexibility with Django’s robust form ecosystem, you can easily integrate powerful autocomplete and selection features into even the most complex forms.

## Security Considerations

`django_tomselect` is designed to integrate seamlessly with Django’s authentication and authorization frameworks. It provides built-in mechanisms for controlling data visibility, validating permissions, and restricting access to autocomplete endpoints. By configuring permissions, employing authorization hooks, and leveraging caching, you can ensure that your autocomplete fields expose only allowed data to authorized users.

### Visualizing Security

```{mermaid}

    stateDiagram-v2
        [*] --> CheckAuth: Request received

        CheckAuth --> SkipAuth: skip_authorization=True
        CheckAuth --> AllowAnon: allow_anonymous=True
        CheckAuth --> ValidateUser: Regular auth flow

        SkipAuth --> ProcessRequest: Allow
        AllowAnon --> ProcessRequest: Allow

        ValidateUser --> CheckCache: User authenticated
        ValidateUser --> RejectRequest: User not authenticated

        CheckCache --> UseCache: Cache hit
        CheckCache --> CheckPerms: Cache miss

        CheckPerms --> CachePerms: Has permission
        CheckPerms --> RejectRequest: No permission

        CachePerms --> ProcessRequest
        UseCache --> ProcessRequest

        ProcessRequest --> [*]: Complete
        RejectRequest --> [*]: Reject
```

### Permission Handling

Security often begins with permission checks. `django_tomselect` supports permission-based restrictions on Model-type autocomplete views, allowing you to define who can see, search, or create new entries. Iterables-type components, on the other hand, do not benefit from built-in permission checks and rely on your custom logic.

#### Model-type vs. Iterables-type Components

- **Model-type Components:**
  When using `AutocompleteModelView`, permissions are integrated. You can rely on the model’s defined permissions (e.g., `view`, `add`, `change`, `delete`) to restrict access. If a user lacks `view` permission, that user will not see the corresponding model instances.

- **Iterables-type Components:**
  For iterables-based autocomplete (`AutocompleteIterablesView`), there are no out-of-the-box permission checks. You must implement your own filtering or conditional logic in the view to ensure only allowed data is returned.

#### Request Passing for Authentication

`django_tomselect` automatically receives the `request` object through its views, making it possible to check `request.user` and confirm that the user is authenticated and authorized before returning data. Ensure that your URLs or views are protected by `login_required`, `LoginRequiredMixin`, or custom permission checks so that the `request.user` is set and reliable.

### Class Variable Priority and Usage

`AutocompleteModelView` provides several class-level attributes that let you fine-tune authorization logic. These attributes influence how permissions are enforced and in which order:

- **`permission_required`**: Specifies exact permissions needed. This could be a single permission string or a list of permissions required to access the data.
- **`allow_anonymous`**: If set to `True`, anonymous users are allowed access, bypassing normal permission checks. Use with caution.
- **`skip_authorization`**: Setting this to `True` disables all permission checks entirely, allowing unrestricted access to the autocomplete. Use only in trusted or controlled environments.

**Priority**:
`skip_authorization` (highest)
`allow_anonymous`
`permission_required` (lowest)

If `skip_authorization` is `True`, no checks are performed at all. If it’s `False`, but `allow_anonymous` is `True`, then no authentication is required. Otherwise, `permission_required` is evaluated against `request.user`.

### Django’s Built-in Authorization System

`django_tomselect` integrates naturally with Django’s built-in authentication and authorization system. By using standard model permissions (e.g., `app_label.view_modelname`), you can control who can see, create, update, or delete specific objects:

```python
class AuthorAutocompleteView(AutocompleteModelView):
    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]

    permission_required = "myapp.view_author"

    def has_permission(self, request, action="view"):
        # Uses built-in user.has_perms() behind the scenes
        return super().has_permission(request, action)
```

By aligning autocomplete views with Django’s permission model, you ensure consistent enforcement across your application.

### Object-level Permissions

If your application requires more granular, object-level permissions (e.g., user A can see only articles they own, while user B can see all articles), you can override `has_object_permission()`:

```python
class ArticleAutocompleteView(AutocompleteModelView):
    model = Article

    def has_object_permission(self, request, obj, action="view"):
        # Restrict visibility to objects owned by the current user
        return obj.owner == request.user
```

Combine object-level checks with Django’s permission system or third-party packages like `django-guardian` to implement fine-grained access control.

### Custom and Third-party Auth Systems

For more complex scenarios (e.g., OAuth, SSO, or custom backends), subclass `AutocompleteModelView` and integrate with your custom authentication logic. Implement checks in `has_permission()` or `has_object_permission()` to validate tokens, interact with external services, or apply custom roles and policies.

`django_tomselect` does not impose any specific authentication mechanism, allowing you to seamlessly integrate solutions like `django-guardian` for per-object permissions or adapt to enterprise SSO systems.

### Customizing Authorization

If you need complete control over the authorization process, override key methods in `AutocompleteModelView`:

- **`has_permission()`**: Called before processing the request; return `False` to deny access.
- **`has_object_permission()`**: Evaluate permissions on each object returned.

For instance, to apply a custom logic that checks a user’s organization membership before displaying data:

```python
class OrganizationRestrictedAutocompleteView(AutocompleteModelView):
    model = Magazine

    def has_permission(self, request, action="view"):
        # Check if user belongs to the required organization
        return request.user.is_authenticated and request.user.organization_id == 42
```

### User Permission Caching and Invalidation

Checking permissions repeatedly can be costly. `django_tomselect` provides a permission caching mechanism to speed up subsequent checks. When enabled, permissions are cached per user and view for improved performance. If user permissions change, you can invalidate the cache:

- **`invalidate_user(user_id)`**: Clear cached permissions for a specific user.
- **`invalidate_all()`**: Clear all cached permissions globally.

This ensures that changes in user roles or memberships are reflected immediately in the autocomplete results.
