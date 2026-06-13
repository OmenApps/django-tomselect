# Working with Models

Using `django_tomselect` with Django models involves setting up dedicated autocomplete views that return JSON responses to your TomSelect widgets, customizing querysets for dynamic filtering, and configuring search behavior. This section covers the basic concepts you will need to integrate TomSelect fields into your Django models and forms.

## Setting up Autocomplete Views

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

## Customizing Queryset Filtering

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

## Handling Related Fields

TomSelect widgets can be chained to handle related fields intuitively. For instance, selecting a `Magazine` can dynamically filter the available `Editions`, and selecting an `Edition` can further filter `Articles`. You configure this by specifying `filter_by` or `exclude_by` parameters at the widget level, ensuring that the view applies those constraints.

For a field that depends on another selection, the widget configuration might look like this:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectModelMultipleChoiceField
from django_tomselect import TomSelectConfig

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

## Model Field Relationships

`django_tomselect` can work seamlessly with various model relationship types, such as `ForeignKey`, `ManyToManyField`, and `OneToOneField`. When bound to `ModelChoiceField` or `ModelMultipleChoiceField` subclasses, the widget will handle the standard relational logic:

- **ForeignKey fields:** Single selection of a related instance.
- **ManyToManyField fields:** Multiple selection from a related model.
- **Chained relationships:** Filter results based on the currently selected related object, as shown with `filter_by` and `exclude_by`.

Your autocomplete views should return the relevant model instances, and the widget will ensure the correct options are presented to the user.

## Using a UUID `value_field` with a separate integer primary key

Some projects keep an auto-incrementing integer as the real primary key while exposing an opaque, non-sequential `UUIDField` as the public identifier:

```python
# models.py
import uuid
from django.db import models


class Customer(models.Model):
    pkid = models.AutoField(primary_key=True)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
```

Point `value_field` at the UUID column so the rendered option values are the opaque UUIDs rather than the sequential integers:

```python
config = TomSelectConfig(
    url="customer-autocomplete",
    value_field="id",      # the UUID column, not the integer pkid
    label_field="name",
)
```

```{important}
The field named in `value_field` must be **unique**. It identifies a single row when an option is selected, so a non-unique column cannot reliably round-trip a selection.
```

### Preselected values on bound `ModelForm`s

When a `ModelForm` is bound to an existing instance and the field is a `ForeignKey` (or `ManyToManyField`) to a model like the one above, Django renders the field's initial value as the related object's **integer primary key**, not the UUID. This is a consequence of how Django builds form initials: `model_to_dict` reduces a relation to the related object's primary key, and `ModelChoiceField.prepare_value` only applies `to_field_name` to model instances, not to the raw integer it receives.

`django-tomselect` handles this for you. When `value_field` is a `UUIDField` on a model whose primary key is a separate integer column, an incoming integer (or its string form, as submitted by a re-rendered bound form) is resolved by primary key, and the **UUID is always emitted as the option value**. The integer primary key is never exposed in the rendered widget, and no extra configuration is required.

For the `Customer` model above, a form pointing a `ForeignKey` at it needs nothing special - editing an existing instance preselects correctly:

```python
# models.py
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

# forms.py
from django.forms import ModelForm
from django_tomselect.forms import TomSelectModelChoiceField


class OrderForm(ModelForm):
    customer = TomSelectModelChoiceField(
        config=TomSelectConfig(url="customer-autocomplete", value_field="id", label_field="name"),
    )

    class Meta:
        model = Order
        fields = ["customer"]

# views.py - binding to an existing order hands the widget the related Customer's
# integer pkid; the widget resolves it and renders the UUID with no extra config.
form = OrderForm(instance=order)
```

```{note}
Package logging is on by default (`ENABLE_LOGGING` defaults to `True`; set `TOMSELECT = {"ENABLE_LOGGING": False}` to silence it). While enabled, the widget emits a `DEBUG` line each time it resolves a preselected value through this path - handy when verifying the behavior.
```

### Models whose primary key *is* a `UUIDField` are unaffected

This behavior is narrowly scoped to the separate-column case. If your model uses a UUID as its actual primary key - the common pattern below - nothing changes: the incoming value is already a UUID, and the widget resolves it through the normal `value_field` path exactly as it always has.

```python
class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
```

The fallback only ever activates when the model's real primary key is an integer column **and** `value_field` points at a separate `UUIDField`, so existing UUID-primary-key configurations are never rerouted.

## Implementing Search

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

By default, `search_lookups` are used directly. If you need more advanced logic-such as searching multiple related fields, adding custom filters, or combining conditions-override the `search()` method.

## Example View Implementation

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
                "id": cat.id,
                "name": cat.name,
                "article_count": cat.article_count,
            })
        return data
```

This example demonstrates how to integrate all aspects of model-based autocompletes: searching, filtering, ordering, and result preparation. With these fundamentals in place, you can easily incorporate TomSelect widgets into your Django forms and leverage your models’ relationships to provide a responsive, intuitive selection interface for your users.
