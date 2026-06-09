# Autocomplete Views

This module provides the view classes that handle autocomplete requests from TomSelect widgets. These views manage data loading, searching, filtering, and permission checks.

## Model Autocomplete Views

### AutocompleteModelView Processing

```{mermaid}

    sequenceDiagram
        participant User
        participant Widget
        participant AutocompleteView
        participant QuerySet
        participant Paginator

        User->>Widget: Type Search Term
        Widget->>AutocompleteView: GET Request with Query

        activate AutocompleteView
        AutocompleteView->>AutocompleteView: hook_queryset()
        AutocompleteView->>QuerySet: apply_filters()
        QuerySet-->>AutocompleteView: Filtered Results

        AutocompleteView->>QuerySet: search()
        QuerySet-->>AutocompleteView: Search Results

        AutocompleteView->>QuerySet: order_queryset()
        QuerySet-->>AutocompleteView: Ordered Results

        AutocompleteView->>Paginator: paginate_queryset()
        Paginator-->>AutocompleteView: Paginated Results

        AutocompleteView->>AutocompleteView: prepare_results()
        AutocompleteView->>AutocompleteView: hook_prepare_results()

        AutocompleteView-->>Widget: JSON Response
        deactivate AutocompleteView

        Widget-->>User: Update Dropdown

        note over AutocompleteView: Hooks allow customization<br/>at various stages
```

### AutocompleteModelView

```{eval-rst}
.. autoclass:: django_tomselect.autocompletes.AutocompleteModelView
   :members:
   :show-inheritance:
```

The `AutocompleteModelView` is the primary view for handling model-based autocomplete requests. It provides a flexible foundation for creating searchable, paginated, and permission-controlled autocomplete endpoints.

#### Basic Usage

```python
from django_tomselect.autocompletes import AutocompleteModelView
from myapp.models import Book

class BookAutocomplete(AutocompleteModelView):
    model = Book
    search_lookups = ['title__icontains', 'author__name__icontains']
    ordering = 'title'
    page_size = 20
    # Important: Include any fields you'll use as label_field in the widget
    value_fields = ['id', 'title', 'author__name']
    virtual_fields = ['computed_field']  # Fields that should not be queried from the database

    # Optional: Restrict which fields users can filter/order by via request parameters
    allowed_filter_fields = ['category', 'author']
    allowed_ordering_fields = ['title', 'publication_date']
```

#### URL Configuration

```python
# urls.py
from django.urls import path
from .views import BookAutocomplete

urlpatterns = [
    path('book-autocomplete/', BookAutocomplete.as_view(), name='book-autocomplete'),
]
```

#### Advanced Configuration

```python
from django.db.models import Prefetch
from myapp.models import Book, Author

class BookAutocomplete(AutocompleteModelView):
    model = Book
    search_lookups = ['title__icontains', 'author__name__icontains']
    ordering = ['title', 'publication_date']
    page_size = 20
    # Include all fields needed for display and filtering
    value_fields = ['id', 'title', 'author__name', 'publication_date', 'isbn']

    # URLs for CRUD operations
    list_url = 'book-list'
    create_url = 'book-create'
    detail_url = 'book-detail'
    update_url = 'book-update'
    delete_url = 'book-delete'

    # Custom permission settings
    permission_required = ('myapp.view_book', 'myapp.search_book')
    allow_anonymous = False

    def hook_queryset(self, queryset):
        """Customize the base queryset before filtering and searching."""
        return queryset.select_related('author').prefetch_related(
            Prefetch('categories', queryset=Category.objects.only('name'))
        )

    def hook_prepare_results(self, results):
        """Customize the prepared results before sending to the client."""
        for result in results:
            result['author_name'] = result.pop('author__name', '')
            result['category_count'] = len(result.get('categories', []))
        return results
```

#### Key Features

1. **Restricting Filter and Ordering Fields**

By default, users can pass arbitrary field names via `filter_by`, `exclude_by`, and `ordering` request parameters. To restrict which fields are accepted, set `allowed_filter_fields` and `allowed_ordering_fields`:

```python
class BookAutocomplete(AutocompleteModelView):
    model = Book
    search_lookups = ['title__icontains']
    value_fields = ['id', 'title', 'category__name', 'publication_date']

    # Only allow filtering/excluding by these fields
    allowed_filter_fields = ['category', 'author', 'status']

    # Only allow ordering by these fields
    allowed_ordering_fields = ['title', 'publication_date']
```

When `allowed_filter_fields` is set, any `filter_by` or `exclude_by` parameter referencing a field not in the list is silently rejected (the base field name is checked, so `category__id` is allowed when `category` is in the list). When `allowed_ordering_fields` is set, disallowed ordering fields fall back to the view's default `ordering`.

When these attributes are `None` (the default), all valid model fields are accepted.

```{tip}
Setting these attributes is recommended for production deployments to prevent users from probing your model structure through filter/ordering parameters.
```

2. **Search Configuration**

The `search_lookups` attribute defines how searching works:

```python
class AuthorAutocomplete(AutocompleteModelView):
    model = Author
    # Search in multiple fields
    search_lookups = [
        'name__icontains',          # Case-insensitive name search
        'email__istartswith',       # Email starting with query
        'books__title__icontains',  # Search in related books
    ]
```

3. **Value Fields Configuration**

The `value_fields` attribute determines which fields are included in the autocomplete results. This is critical for the widget's functionality:

```python
class AuthorAutocomplete(AutocompleteModelView):
    model = Author
    # Define fields to include in results
    value_fields = [
        'id',                # Primary key (always required)
        'name',              # For use as label_field in widget
        'email',             # Optional additional field
        'profile_picture',   # Optional additional field
        'books__count',      # Can include annotations
    ]
    virtual_fields = [
        'books__count',      # Computed or annotated fields
    ]
```

⚠️ **Important**: The `value_fields` attribute should include all fields you need in your results, but for fields that don't exist in the database (computed properties, annotations added later, etc.), add them to `virtual_fields` to prevent database query errors. The widget will automatically add your `label_field` to `value_fields` and detect if it should be in `virtual_fields`.

For example, if your widget uses:
```python
config=TomSelectConfig(label_field="name")
```
Then your autocomplete view should include "name" in its `value_fields` list.

````{warning}
**Do not use `label_field="__str__"`** (or any Python dunder). django-tomselect
serializes options with `QuerySet.values()`, and `__str__` is not a selectable
column, so option labels would render empty. This now raises `ImproperlyConfigured`
at configuration time.

When you are tempted to reach for the model's `__str__`, use a **real field** or an
**annotation** instead. For a composite/computed label, reproduce it as a queryable
annotation in `hook_queryset()` and point `label_field` at that annotation:

```python
from django.db.models import CharField, Value
from django.db.models.functions import Concat

class SubscriptionAutocomplete(AutocompleteModelView):
    model = Subscription
    value_fields = ["id", "display_name"]
    search_lookups = ["monitor__name__icontains"]

    def hook_queryset(self, queryset):
        # Reproduce the model's __str__ as a queryable annotation. Pass an
        # explicit output_field so Django can resolve the type even when a
        # concatenated part is not itself text (an int/date column otherwise
        # raises FieldError: unknown output_field).
        return queryset.annotate(
            display_name=Concat(
                "monitor__name", Value(" - "), "metric",
                output_field=CharField(),
            ),
        )

# Widget config:
config = TomSelectConfig(url="subscription-autocomplete", label_field="display_name")
```

Because `display_name` is a real annotation it flows through both the AJAX results
(`.values()`) and the pre-selected option rendering, and it stays searchable and
sortable. If a single column already captures the label, just use it directly
(e.g. `label_field="name"`) - no annotation needed. (The annotation's relation
traversal, `monitor__name`, is JOINed automatically; only add `select_related`
in `hook_queryset()` if you also access the related object on the result
instances for other reasons.)
````

4. **Queryset Customization**

Use `hook_queryset` to optimize or customize the queryset:

```python
def hook_queryset(self, queryset):
    """Customize the base queryset before filtering and searching.

    This is the ideal place to add select_related, prefetch_related,
    or annotations that should apply to all results.
    """
    return queryset.select_related('publisher')\
                   .prefetch_related('categories')\
                   .annotate(book_count=Count('books'))\
                   .filter(is_active=True)
```

```{note}
When the widget's `label_field` points to a relation (e.g., `label_field="author"`), the widget automatically adds `select_related()` for that field to prevent N+1 queries when rendering selected options. You do not need to add it manually in `hook_queryset` for this case.
```

5. **Permission Handling**

Multiple ways to configure permissions:

```python
class BookAutocomplete(AutocompleteModelView):
    # Option 1: Specify required permissions
    permission_required = ('myapp.view_book', 'myapp.search_book')

    # Option 2: Allow anonymous access
    allow_anonymous = True

    # Option 3: Skip all permission checks
    skip_authorization = False

    # Option 4: Custom permission checking
    def has_permission(self, request, action="view"):
        if action == "create":
            return request.user.is_staff
        return super().has_permission(request, action)
```

6. **Result Preparation**

Customize the data sent to the client:

```python
def hook_prepare_results(self, results):
    for result in results:
        # Add computed fields
        result['display_label'] = f"{result['title']} ({result['year']})"
        # Transform data
        result['author_info'] = {
            'name': result.pop('author__name'),
            'email': result.pop('author__email')
        }
        # Add custom URLs
        result['preview_url'] = reverse('book-preview', args=[result['id']])
    return results
```

7. **Custom JSON Encoder**

If your model has fields with non-serializable types (e.g., a `PhoneNumber` from the django-phonenumber-field package), you can specify a custom JSON encoder:

```python
import json

class PhoneNumberEncoder(json.JSONEncoder):
    """Encoder that handles PhoneNumber objects."""

    def default(self, obj):
        if hasattr(obj, 'as_e164'):
            return obj.as_e164
        return super().default(obj)

class ContactAutocomplete(AutocompleteModelView):
    model = Contact
    search_lookups = ['name__icontains']
    value_fields = ['id', 'name', 'phone']

    # Use the custom encoder for this view
    json_encoder = PhoneNumberEncoder
```

The encoder can also be specified as a dotted string path:

```python
class ContactAutocomplete(AutocompleteModelView):
    model = Contact
    json_encoder = 'myapp.encoders.PhoneNumberEncoder'
```

See {ref}`Configuration documentation <custom-json-encoder>` for details on setting a global default encoder.

## Iterables Autocomplete Views

### AutocompleteIterablesView Processing

```{mermaid}

    sequenceDiagram
        participant User
        participant Widget
        participant AutocompleteIterablesView
        participant Iterable
        participant Paginator

        User->>Widget: Type Search Term
        Widget->>AutocompleteIterablesView: GET Request with Query

        activate AutocompleteIterablesView
        AutocompleteIterablesView->>AutocompleteIterablesView: get_iterable()

        alt TextChoices/IntegerChoices
            AutocompleteIterablesView->>Iterable: Access choices attribute
            Iterable-->>AutocompleteIterablesView: Return choices list
            AutocompleteIterablesView->>AutocompleteIterablesView: Format as {value, label}
        else Tuple Iterables
            AutocompleteIterablesView->>Iterable: Access tuple items
            Iterable-->>AutocompleteIterablesView: Return tuple list
            AutocompleteIterablesView->>AutocompleteIterablesView: Format as {value, label}
        else Simple Iterables
            AutocompleteIterablesView->>Iterable: Access items
            Iterable-->>AutocompleteIterablesView: Return items
            AutocompleteIterablesView->>AutocompleteIterablesView: Format as {value, label}
        end

        AutocompleteIterablesView->>AutocompleteIterablesView: search()
        Note over AutocompleteIterablesView: Filter items based on query

        AutocompleteIterablesView->>Paginator: paginate_iterable()
        Paginator-->>AutocompleteIterablesView: Paginated Results

        AutocompleteIterablesView-->>Widget: JSON Response
        deactivate AutocompleteIterablesView

        Widget-->>User: Update Dropdown

        note over AutocompleteIterablesView: Handles three types of iterables:<br/>1. Django Choices (Text/Integer)<br/>2. Tuple Iterables<br/>3. Simple Iterables
```

### AutocompleteIterablesView

```{eval-rst}
.. autoclass:: django_tomselect.autocompletes.AutocompleteIterablesView
   :members:
   :show-inheritance:
```

This view handles autocomplete for choices, iterables, and enums.

#### Basic Usage

```python
from django_tomselect.autocompletes import AutocompleteIterablesView
from django.db.models import TextChoices

class Status(TextChoices):
    DRAFT = 'D', 'Draft'
    PUBLISHED = 'P', 'Published'
    ARCHIVED = 'A', 'Archived'

class StatusAutocomplete(AutocompleteIterablesView):
    iterable = Status
    page_size = 10
```

#### Custom Iterables

```python
class YearAutocomplete(AutocompleteIterablesView):
    iterable = [
        2020,
        2021,
        2022,
        2023,
        2024,
        2025,
    ]

class TiersAutocomplete(AutocompleteIterablesView):
    iterable = [
        (1, "Tier 1"),
        (2, "Tier 2"),
        (3, "Tier 3"),
    ]
```

#### With Dictionary

```python
class ClassStandingsAutocomplete(AutocompleteIterablesView):
    iterable = {
        "FR": "Freshman",
        "SO": "Sophomore",
        "JR": "Junior",
        "SR": "Senior",
        "GR": "Graduate",
    }
```

#### Custom Iterable Formatting

Autocompletes can be customized to modify formatting by overriding the `get_iterable` method.

For an example where we use this to display tuples as ranges, see the [autcompletes.py code](https://github.com/OmenApps/django-tomselect/blob/main/example_project/example/autocompletes.py#L66) in the example app.

#### Dependent (filter_by) and exclude_by Filtering

`AutocompleteIterablesView` supports the same `filter_by` and `exclude_by` configuration as
model views, so iterables-backed fields (`TomSelectChoiceField` / `TomSelectMultipleChoiceField`)
can act as dependent dropdowns or exclude already-chosen values.

Because an iterable item is just `{"value", "label"}` with no model behind it, the lookup must
target the `value` or `label` key (not a model field). Configure the lookup accordingly:

```python
# Only show statuses whose value matches the selected parent field's value
filter_by = ("parent_field", "value")          # -> value=<parent value>
filter_by = ("parent_field", "value__in")      # -> value in <comma list>
exclude_by = ("other_field", "value")          # drop the value chosen elsewhere
```

Supported lookups: `exact` (default), `iexact`, `in`, `contains`, `icontains`, `startswith`,
`istartswith`, `endswith`, `iendswith`. Multiple `filter_by` entries are AND-ed; multiple
`exclude_by` entries drop the union. Invalid configuration (a key other than `value`/`label`,
an unsupported lookup, or an empty/whitespace value) fails closed and returns no results,
matching the dependent-dropdown contract.

```{note}
A lookup whose key is a model field name (e.g. `("category", "category_id")`, which works for
model views) targets `category_id` and will not match an iterable item, so it returns an empty
list. For iterables, always target `value` or `label`. Also note that values containing single
quotes cannot be matched exactly, since the URL parser strips quotes.
```

## Response Format

Both view types return JSON responses in this format:

```python
{
    "results": [
        {
            "id": "1",
            "name": "Example Item",
            "can_view": true,    # Permission flags for the current user
            "can_update": true,
            "can_delete": false,
            "detail_url": "/items/1/",
            "update_url": "/items/1/update/",
            # No delete_url since can_delete is false
            # ... additional fields from hook_prepare_results
        }
    ],
    "page": 1,
    "has_more": true,
    "next_page": 2,
    "total_pages": 5
}
```

## Error Handling

The views include built-in error handling:

1. Invalid permissions return 403 Forbidden
2. Unauthenticated users are redirected to login
3. Invalid queries return empty results
4. Database errors return a 200 response with an error message and empty results

## Caching

The views support permission caching to improve performance:

```python
# settings.py
PERMISSION_CACHE = {
    'TIMEOUT': 300,  # Cache permissions for 5 minutes
    'KEY_PREFIX': 'myapp',
    'NAMESPACE': 'permissions'
}
```

To invalidate the cache:

```python
from django_tomselect.autocompletes import AutocompleteModelView

# Invalidate for specific user
AutocompleteModelView.invalidate_permissions(user=request.user)

# Invalidate all cached permissions
AutocompleteModelView.invalidate_permissions()
```

## Security Considerations

The package already includes built-in protections:

1. All user-provided values are automatically escaped using Django's `escape()` function
2. URLs are sanitized through the `safe_url()` utility which prevents unsafe schemes
3. Dictionary values are recursively sanitized via the `sanitize_dict()` utility

These protections work together to prevent XSS vulnerabilities when customizing rendering templates.

When creating custom templates and renderers for Tom Select widgets, always ensure proper escaping of user-provided values:

1. Use the `escape()` function for any user data inserted into HTML content
2. For URL attributes (href, src), always escape the URLs using the `escape()` function
3. Avoid using `new Function()` with user-provided content whenever possible
4. When customizing rendering templates, validate and sanitize all input

This is particularly important when using custom rendering templates with `data_template_option` and `data_template_item`.

## CompositeAutocompleteView (token widget backend)

Multiplexes multiple `AutocompleteModelView` and/or `AutocompleteIterablesView`
subclasses into a single endpoint that powers `TomSelectTokenWidget`. Three
GET routes by `mode=` query param:

- `?mode=operators` - JSON list of registered operator metadata.
- `?mode=value&op=<key>&q=...` - delegates to the operator's bound view.
- `?mode=resolve&op=<k>&id=<v>[...]` - batch label resolution for chip rehydration.

```python
from django_tomselect import CompositeAutocompleteView, Operator


class ArticleTokenQueryView(CompositeAutocompleteView):
    operators = [
        Operator(
            key="author",
            view=AuthorAutocompleteView,         # class ref or "url-name"
            value_field="id",                    # JSON key in prepare_results()
            label_field="name",                  # JSON key in prepare_results()
            filter_lookup="authors__id",         # parent-QS exact-match field path
            label=_("Author"),
            max_count=3,
        ),
        Operator(
            key="status",
            view=ArticleStatusAutocompleteView,  # iterables view
            value_field="value",
            label_field="label",
            filter_lookup="status",
            multi=True,                          # comma-separated: status:a,b
        ),
    ]
    free_text_lookups = ["title__icontains"]
```

### `Operator` contract

- **Required:** `key`, `view`, `value_field`, `label_field`, exactly one of
  `filter_lookup` or `q_translator`.
- **`bound_lookup`:** ORM lookup field for chip resolution. Defaults to
  `value_field`. Override when `prepare_results()` projects renamed/computed keys.
- **`filter_lookup`:** exact-match field path (e.g. `"authors__id"`,
  `"status"`). For `multi=True` the per-token lookup is `field__in=[values]`. For
  non-exact behavior (icontains, gt/lt, custom expressions), use `q_translator`
  instead.
- **`q_translator`:** callable `(operator, [values]) -> Q`. Maximum flexibility
  for custom filtering.
- **`search_lookups`:** `None` inherits the bound view's lookups; `[]`
  deliberately disables search; non-empty list overrides for this operator only
  (instance-scoped per-request, no cross-request leakage).
- **`max_count` / `min_count`:** enforced by `TomSelectTokenField.clean()`.

### `split_search` flag (opt-in)

`AutocompleteModelView` gained a `split_search: bool = False` class attribute.
When `True`, `search()` splits the query on whitespace using a quote-aware
tokenizer; each term is OR'd across `search_lookups`, and per-term Qs are
ANDed together. Quoted phrases stay single terms. Default `False` preserves
existing behavior verbatim.

### Permission caveats

- **Iterables operators have no `has_permission()` hook** - they are
  public-by-default. The composite view emits a one-time logger warning on
  subclass registration. Gate sensitive iterables at the form/view layer.
- **Object-level permissions are NOT enforced row-by-row.** The resolve flow
  honors queryset-level scoping (whatever your `get_queryset()` returns) and
  dispatch-level `has_permission()`, but `has_object_permission()` is not
  applied per-row by `prepare_results()`. Override `get_queryset()` for
  per-row checks.

See {doc}`../example_app/article_token_search` for an end-to-end demo.
