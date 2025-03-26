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

1. **Search Configuration**

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

2. **Value Fields Configuration**

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
```

⚠️ **Important**: Always include the field specified as `label_field` in your widget configuration. If a field is used as `label_field` but not included in `value_fields`, labels could display as "undefined" in the widget.

For example, if your widget uses:
```python
config=TomSelectConfig(label_field="name")
```
Then your autocomplete view should include "name" in its `value_fields` list.

3. **Queryset Customization**

Use `hook_queryset` to optimize or customize the queryset:

```python
def hook_queryset(self, queryset):
    return queryset.select_related('publisher')\
                  .prefetch_related('categories')\
                  .annotate(book_count=Count('books'))\
                  .filter(is_active=True)
```

4. **Permission Handling**

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

5. **Result Preparation**

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

## Response Format

Both view types return JSON responses in this format:

```python
{
    "results": [
        {
            "id": "1",
            "name": "Example Item",
            "detail_url": "/items/1/",
            "update_url": "/items/1/update/",
            "delete_url": "/items/1/delete/",
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

When creating custom templates and renderers for Tom Select widgets, always ensure proper escaping of user-provided values:

1. Use the `escape()` function for any user data inserted into HTML content
2. For URL attributes (href, src), always escape the URLs using the `escape()` function
3. Avoid using `new Function()` with user-provided content whenever possible
4. When customizing rendering templates, validate and sanitize all input

This is particularly important when using custom rendering templates with `data_template_option` and `data_template_item`.
