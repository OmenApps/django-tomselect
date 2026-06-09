# Advanced Features

As your project grows, you may need more than just basic autocomplete functionality. `django_tomselect` includes several advanced features that let you dynamically update dropdowns based on user selections, apply exclusion rules, handle large datasets efficiently, integrate with HTMX for seamless server-driven interactions, and customize the search logic to fit your needs. Additionally, you can override core view and widget methods to fine-tune how data is fetched and presented.

## Visualizing Request Flow and Data Processing

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

## Dependent/Chained Fields

One common pattern is to make the options in one dropdown field depend on the selected value of another field. For example, after a user chooses a `Category`, you might need to restrict available `Subcategories` to those related to that `Category`.

To achieve this, `django_tomselect` supports dependent (chained) fields. When setting up your widget configuration, you can specify a `filter_by` attribute, instructing the field to refresh its options whenever the parent field changes.

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect import TomSelectConfig

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

### Multiple Field Filters

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

See the [Multiple Filter-By](../example_app/multiple_filter_by.md) example for complete demonstration.

### Formset Support

Both `filter_by` and `exclude_by` work within Django formsets. Each formset row operates independently - selecting a value in row 1 only affects dependent fields in row 1, not other rows. The widget automatically handles form prefixes (e.g., `myformset-0-magazine`, `myformset-1-magazine`).

```python
from django.forms import formset_factory

class MagazineEditionForm(forms.Form):
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(url="autocomplete-magazine"),
    )
    edition = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            filter_by=("magazine", "magazine_id"),  # Works per-row in formsets
        ),
    )

MagazineEditionFormset = formset_factory(MagazineEditionForm, extra=2)
```

See the [Formset with filter_by](../example_app/formset_filter_by.md) example for complete demonstration including dynamic row addition.

For **nested formsets**, where an inner row needs to filter by a value on the outer parent row, use `FilterSpec` with `levels_up`:

```python
from django_tomselect.app_settings import TomSelectConfig, FilterSpec

class LineItemForm(forms.Form):
    product = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-product",
            # Inner row, but pull "customer" from the parent Order row
            filter_by=FilterSpec(
                source="customer", lookup="id",
                source_type="field", levels_up=1,
            ),
        ),
    )
```

`levels_up=0` (the default) keeps the same-row behavior. See [FilterSpec](../api/config.md#filterspec) for full details.

### Constant Value Filters

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
- Restrict to specific primary keys via `__in`: `Const([11, 13], "id__in")`
- Restrict to a numeric range via `__range`: `Const([2020, 2024], "year__range")`

`Const` accepts a list or tuple value when the lookup expects an iterable
(`__in`, `__range`); items are comma-joined for transport and split server-side
before the queryset filter is applied. Items must not themselves contain
commas.

See the [Constant Filter-By](../example_app/constant_filter_by.md) example for complete demonstration.

## Field Exclusions

Beyond filtering, you might need to exclude certain options dynamically. For example, if you have a form with a `primary_author` field and a `contributing_authors` field, you may want to prevent the primary author from appearing in the contributing authors list.

### Using `exclude_by`

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

### filter_by / exclude_by with Iterables Fields

`filter_by` and `exclude_by` also work for iterables-backed fields (`TomSelectChoiceField` /
`TomSelectMultipleChoiceField` served by an `AutocompleteIterablesView`), so choice/enum
dropdowns can be dependent or exclude already-chosen values.

The difference: an iterable item is just `{"value", "label"}` with no model behind it, so the
lookup must target the `value` or `label` key rather than a model field.

```python
class ArticleForm(forms.Form):
    # Parent field (its value drives the dependent dropdown below)
    category = TomSelectModelChoiceField(
        config=TomSelectConfig(url="category-autocomplete", value_field="id", label_field="name"),
    )

    # Iterables field whose options are narrowed by the selected category's value
    status = TomSelectChoiceField(
        config=TomSelectConfig(
            url="status-autocomplete",          # an AutocompleteIterablesView
            filter_by=("category", "value"),    # keep items where item value == category's value
        )
    )
```

Supported lookups for iterables: `exact` (default), `iexact`, `in`, `contains`, `icontains`,
`startswith`, `istartswith`, `endswith`, `iendswith` (e.g. `("category", "value__in")` or
`("other_field", "label__icontains")`). Multiple `filter_by` entries are AND-ed and multiple
`exclude_by` entries drop the union, just like model views. Invalid configuration (a key other
than `value`/`label`, an unsupported lookup, or an empty/whitespace value) fails closed and
returns no results.

```{note}
A model-style lookup such as `("category", "category_id")` targets `category_id`, which does not
exist on an iterable item, so it returns an empty list. For iterables, always target `value` or
`label`. See the [AutocompleteIterablesView docs](../api/autocomplete_views.md) for details.
```

## Pagination Handling

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

## Custom Search Implementation

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

## Overriding Methods in Autocomplete Views

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
