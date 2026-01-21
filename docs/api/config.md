# Configuration

This module provides configuration classes for customizing TomSelect widgets and their plugins. The configuration system is based on dataclasses, providing type safety and validation.

## Core Configuration

### TomSelectConfig

```{eval-rst}
.. autoclass:: django_tomselect.app_settings.TomSelectConfig
   :members:
   :show-inheritance:
```

The `TomSelectConfig` class is the main configuration class for TomSelect widgets. It controls both the widget's behavior and which plugins are enabled.

```{mermaid}

    graph TD
        A[Project Settings] -->|Override| B[GLOBAL_DEFAULT_CONFIG]
        C[Field Config] -->|Override| D[Widget Config]
        B -->|Base| D

        D --> E{Config Type}
        E -->|Model| F[TomSelectModelWidget]
        E -->|Iterables| G[TomSelectIterablesWidget]

        F --> H[Build Context]
        G --> H

        H --> I[Render Template]

        subgraph Plugins
            J[Checkbox Options]
            K[Clear Button]
            L[Dropdown Header]
            M[Dropdown Footer]
            N[Dropdown Input]
            O[Remove Button]
        end

        D -.->|Configure| Plugins
```

#### Basic Usage

```python
from django_tomselect.app_settings import TomSelectConfig

config = TomSelectConfig(
    url='book-autocomplete',
    value_field='id',
    label_field='title',
    placeholder='Select a book...',
    minimum_query_length=2
)
```

#### Complete Configuration Example

```python
from django_tomselect.app_settings import TomSelectConfig, Const

config = TomSelectConfig(
    # Core Settings
    url='book-autocomplete',
    value_field='id',
    label_field='name',
    create_field='',

    # Filtering - supports multiple formats (see "Dependent Fields" section below)
    filter_by=('category', 'category_id'),  # Simple: filter by category form field
    # Or for multiple filters:
    # filter_by=[
    #     ('category', 'category_id'),
    #     Const('published', 'status'),  # Always filter to published status
    # ],
    exclude_by=(),  # No excludes (default)
    use_htmx=False,  # Enable HTMX integration
    attrs={},  # Additional HTML attributes

    # Display Settings
    placeholder='Select a value',
    minimum_query_length=2,
    max_items=None,
    max_options=None,

    # Behavior Settings
    preload='focus',  # Can be 'focus', True, or False
    highlight=True,
    open_on_focus=True,
    close_after_select=None,
    hide_selected=True,
    hide_placeholder=None,
    create=False,  # Enable item creation
    create_filter=None,  # Filter for new items
    create_with_htmx=False,  # Use HTMX for item creation

    # Performance Settings
    load_throttle=300,
    loading_class='loading',

    # Feature Toggles (all default to False)
    show_list=False,
    show_create=False,
    show_detail=False,
    show_update=False,
    show_delete=False,

    # Framework Settings
    css_framework='bootstrap5',
    use_minified=True,

    # Plugins
    plugin_checkbox_options=PluginCheckboxOptions(),
    plugin_clear_button=PluginClearButton(),
    plugin_dropdown_header=PluginDropdownHeader(),
    plugin_dropdown_footer=PluginDropdownFooter(),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_remove_button=PluginRemoveButton()
)
```

## Filter Specification Classes

### FilterSpec

```{eval-rst}
.. autoclass:: django_tomselect.app_settings.FilterSpec
   :members:
   :show-inheritance:
```

The `FilterSpec` dataclass represents a single filter or exclude condition. It supports both field-based filtering (where the value comes from another form field) and constant filtering (where the value is a static constant).

```python
from django_tomselect.app_settings import FilterSpec

# Field-based filter (value from form field)
spec = FilterSpec(source='category', lookup='category_id', source_type='field')

# Constant filter (static value)
spec = FilterSpec(source='published', lookup='status', source_type='const')
```

### Const Helper

```{eval-rst}
.. autofunction:: django_tomselect.app_settings.Const
```

The `Const` function is a convenience helper for creating constant filter specs:

```python
from django_tomselect.app_settings import Const

# These are equivalent:
Const('published', 'status')
FilterSpec(source='published', lookup='status', source_type='const')
```

## Plugin Configurations

### PluginCheckboxOptions

```{eval-rst}
.. autoclass:: django_tomselect.app_settings.PluginCheckboxOptions
   :members:
   :show-inheritance:
```

Enables checkbox selection in the dropdown. No additional configuration required.

```python
config = TomSelectConfig(
    plugin_checkbox_options=PluginCheckboxOptions()
)
```

### PluginClearButton

```{eval-rst}
.. autoclass:: django_tomselect.app_settings.PluginClearButton
   :members:
   :show-inheritance:
```

Adds a button to clear all selections.

```python
config = TomSelectConfig(
    plugin_clear_button=PluginClearButton(
        title="Clear Selections",
        class_name="clear-button",
    )
)
```

### PluginDropdownHeader

```{eval-rst}
.. autoclass:: django_tomselect.app_settings.PluginDropdownHeader
   :members:
   :show-inheritance:
```

Configures the dropdown header display.

```python
config = TomSelectConfig(
    plugin_dropdown_header=PluginDropdownHeader(
        title="Autocomplete",
        header_class="container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header",
        title_row_class="row",
        label_class="form-label",
        value_field_label="Value",
        label_field_label="Label",
        label_col_class="col-6",
        show_value_field=False,
        extra_columns={
            'author__name': 'Author',
            'publication_year': 'Year',
        }
    )
)
```

### PluginDropdownFooter

```{eval-rst}
.. autoclass:: django_tomselect.app_settings.PluginDropdownFooter
   :members:
   :show-inheritance:
```

Configures the dropdown footer display.

```python
config = TomSelectConfig(
    plugin_dropdown_footer=PluginDropdownFooter(
        title="Autocomplete Footer",
        footer_class="container-fluid mt-1 px-2 border-top dropdown-footer",
        list_view_label="List View",
        list_view_class="btn btn-primary btn-sm m-2 p-1 float-end float-right",
        create_view_label="Create New",
        create_view_class="btn btn-primary btn-sm m-2 p-1 float-end float-right",
    )
)
```

### PluginDropdownInput

```{eval-rst}
.. autoclass:: django_tomselect.app_settings.PluginDropdownInput
   :members:
   :show-inheritance:
```

Enables an input field in the dropdown. No additional configuration required.

```python
config = TomSelectConfig(
    plugin_dropdown_input=PluginDropdownInput()
)
```

### PluginRemoveButton

```{eval-rst}
.. autoclass:: django_tomselect.app_settings.PluginRemoveButton
   :members:
   :show-inheritance:
```

Adds a remove button to selected items.

```python
config = TomSelectConfig(
    plugin_remove_button=PluginRemoveButton(
        title="Remove this item",
        label="&times;",
        class_name="remove",
    )
)
```

## Global Configuration

You can set global defaults in your Django settings:

```python
# settings.py

TOMSELECT = {
    # Default CSS framework for all widgets
    'DEFAULT_CSS_FRAMEWORK': 'bootstrap5',

    # Use minified files by default
    'DEFAULT_USE_MINIFIED': True,

    # Default configuration for all widgets
    'DEFAULT_CONFIG': {
        'minimum_query_length': 2,
        'load_throttle': 300,
        'preload': 'focus'
    },

    # Default plugin configurations
    'PLUGINS': {
        'checkbox_options': True,
        'clear_button': {
            'title': 'Clear Selection',
            'class_name': 'clear-btn'
        },
        'dropdown_header': {
            'title': 'Select an Option',
            'show_value_field': False
        },
        'dropdown_footer': {
            'title': 'Options',
            'footer_class': 'footer'
        },
        'remove_button': {
            'title': 'Remove',
            'label': '×'
        }
    },

    # Logging configuration
    'ENABLE_LOGGING': True,  # Set to False to disable logging

    # Custom proxy request class
    'PROXY_REQUEST_CLASS': 'path.to.CustomProxyRequest',

    # Permission cache settings (optional)
    'PERMISSION_CACHE': {
        'TIMEOUT': 3600,  # Cache timeout in seconds
        'KEY_PREFIX': 'myapp',  # Prefix for cache keys
        'NAMESPACE': 'tomselect'  # Namespace for cache keys
    },

    # Custom JSON encoder for autocomplete responses (optional)
    'DEFAULT_JSON_ENCODER': 'path.to.CustomJSONEncoder',
}
```

## Advanced Usage

### Dependent Fields (filter_by / exclude_by)

The `filter_by` and `exclude_by` options allow you to create dependent fields that filter based on other form field values or constant values.

#### Basic Usage (Legacy Format)

The simplest format is a 2-tuple of `(form_field_name, lookup_field)`:

```python
config = TomSelectConfig(
    filter_by=('category', 'category_id'),  # Filter where category_id = value of 'category' form field
    exclude_by=('author', 'author_id')      # Exclude where author_id = value of 'author' form field
)
```

#### Multiple Field Filters

You can filter by multiple fields using a list of tuples. All conditions are combined (AND):

```python
config = TomSelectConfig(
    filter_by=[
        ('magazine', 'magazine_id'),  # Filter by selected magazine
        ('status', 'status'),         # AND by selected status
    ]
)
```

#### Constant Value Filters

Use the `Const` helper to filter by a constant value that doesn't come from a form field:

```python
from django_tomselect.app_settings import TomSelectConfig, Const

config = TomSelectConfig(
    filter_by=[
        ('magazine', 'magazine_id'),       # Filter by selected magazine
        Const('published', 'status'),      # Always filter to published only
    ]
)
```

This is useful for:
- Always showing only active/published items
- Filtering by the current user's organization
- Enforcing business rules in the UI

#### FilterSpec Objects

For advanced use cases, you can use `FilterSpec` objects directly:

```python
from django_tomselect.app_settings import TomSelectConfig, FilterSpec

config = TomSelectConfig(
    filter_by=[
        FilterSpec(source='category', lookup='category_id', source_type='field'),
        FilterSpec(source='active', lookup='is_active', source_type='const'),
    ]
)
```

#### Accepted Formats Summary

| Format | Example | Description |
|--------|---------|-------------|
| Empty tuple | `()` | No filtering (default) |
| 2-tuple | `('field', 'lookup')` | Single field filter |
| FilterSpec | `FilterSpec(...)` | Single spec object |
| Const | `Const('value', 'lookup')` | Constant value filter |
| List | `[('f1', 'l1'), Const(...)]` | Multiple filters (AND logic) |

#### URL Parameter Format

When using multiple filters, the autocomplete URL will include multiple `f` (filter) or `e` (exclude) parameters:

- Field filters: `?f='fieldname__lookup=value'`
- Constant filters: `?f='__const__lookup=value'`
- Multiple: `?f='...'&f='...'&f='...'`

### Creating New Items

Django TomSelect provides two different mechanisms for creating new items:

1. **Dropdown Footer Link** (`show_create`) - Adds a "Create New" link in the dropdown footer that navigates to a create view
2. **Inline Creation** (`create`) - Enables Tom Select's native feature where users can type a new value and create it directly

#### Understanding the Parameters

| Parameter | Location | Purpose |
|-----------|----------|---------|
| `show_create` | `TomSelectConfig` | Shows a "Create New" link in the dropdown footer (requires `PluginDropdownFooter`) |
| `create` | `TomSelectConfig` | Enables Tom Select's inline item creation when typing non-matching values |
| `create_field` | `TomSelectConfig` | Specifies which field receives the new value when creating inline |
| `create_with_htmx` | `TomSelectConfig` | When `True`, inline creation POSTs to a URL via HTMX instead of client-side handling |
| `create_url` | Autocomplete view | URL name for the create view (used by both dropdown footer link and HTMX creation) |

#### Dropdown Footer "Create New" Link

To add a "Create New" link in the dropdown that opens a separate create view:

```python
from django_tomselect.app_settings import TomSelectConfig, PluginDropdownFooter

class ArticleForm(forms.Form):
    author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url='author-autocomplete',
            show_create=True,  # Enable the create link
            plugin_dropdown_footer=PluginDropdownFooter(
                create_view_label="Add New Author",
            ),
        )
    )
```

You must also define `create_url` on your autocomplete view:

```python
from django_tomselect.autocompletes import AutocompleteModelView

class AuthorAutocompleteView(AutocompleteModelView):
    model = Author
    search_lookups = ['name__icontains']
    create_url = 'author-create'  # URL name for the create view
```

The link will only appear if the user has the appropriate `add` permission for the model.

#### Inline Item Creation

Tom Select's native create feature allows users to type a value that doesn't exist and create it:

```python
config = TomSelectConfig(
    url='tag-autocomplete',
    create=True,           # Enable inline creation
    create_field='name',   # Field to populate with the typed value
)
```

#### HTMX-Based Inline Creation

For server-side validation and creation, use HTMX:

```python
from django_tomselect.app_settings import TomSelectConfig

class ArticleForm(forms.Form):
    category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url='category-autocomplete',
            create=True,              # Enable inline creation UI
            create_field='name',      # Field for the new value
            create_with_htmx=True,    # POST to server via HTMX
        )
    )
```

When `create_with_htmx=True`, clicking the create option will POST to the `create_url` defined on your autocomplete view. Your autocomplete view must have `create_url` set:

```python
class CategoryAutocompleteView(AutocompleteModelView):
    model = Category
    search_lookups = ['name__icontains']
    create_url = 'category-create'  # Required for HTMX creation
```

```{note}
The HTMX creation feature requires:
1. `create=True` in the config
2. `create_with_htmx=True` in the config
3. `create_url` defined on the autocomplete view
4. User must have `add` permission for the model
```

#### Complete Example

Here's a complete example combining both dropdown footer and inline HTMX creation:

```python
# autocompletes.py
class CategoryAutocompleteView(AutocompleteModelView):
    model = Category
    search_lookups = ['name__icontains']
    create_url = 'category-create'
    list_url = 'category-list'

# forms.py
class ArticleForm(forms.Form):
    category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url='category-autocomplete',
            # Dropdown footer link
            show_create=True,
            plugin_dropdown_footer=PluginDropdownFooter(
                create_view_label="Open Create Form",
            ),
            # Inline HTMX creation
            create=True,
            create_field='name',
            create_with_htmx=True,
        )
    )

# urls.py
urlpatterns = [
    path('autocomplete/category/', CategoryAutocompleteView.as_view(), name='category-autocomplete'),
    path('category/create/', CategoryCreateView.as_view(), name='category-create'),
    path('category/', CategoryListView.as_view(), name='category-list'),
]
```

### Logging

By default, logging is enabled. To disable logging or configure per-module log levels, see the [Logging section in Utilities](utilities.md#logging).

Quick disable:

```python
TOMSELECT = {
    "ENABLE_LOGGING": False
}
```

### Proxy Request

To automate the interaction between a widget and its associated autocomplete view, we must pass a request. Normally this is very straightforward, but in some cases, you may need to pass a request that has been modified to include additional information. In these cases, you can subclass `django_tomselect.request.DefaultProxyRequest` and override the `__init__` method to add the necessary data.

```python
from django_tomselect.request import DefaultProxyRequest

class CustomProxyRequest(DefaultProxyRequest):
    def __init__(self, request, extra_data):
        super().__init__(request)
        self.extra_data = extra_data
```

Then, use the custom proxy request in your configuration:

```python
TOMSELECT = {
    # Other settings...

    # Custom proxy request
    'PROXY_REQUEST_CLASS': 'path.to.CustomProxyRequest',
}
```

### Custom JSON Encoder

If your models contain fields with non-serializable types (e.g.: using `PhoneNumber` from django-phonenumber-field, custom objects, etc), you can specify a custom JSON encoder to handle serialization in autocomplete responses.

#### Global Configuration

Set a default JSON encoder for all autocomplete views:

```python
# settings.py
import json

class CustomJSONEncoder(json.JSONEncoder):
    """Custom encoder that handles otherwise non-serializable types."""

    def default(self, obj):
        # Handle PhoneNumber objects
        if hasattr(obj, 'as_e164'):
            return obj.as_e164
        # Handle other custom types
        if hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)

TOMSELECT = {
    # Other settings...

    # Custom JSON encoder (can be a class or dotted string path)
    'DEFAULT_JSON_ENCODER': CustomJSONEncoder,
    # Or as a string:
    # 'DEFAULT_JSON_ENCODER': 'myapp.encoders.CustomJSONEncoder',
}
```

#### Per-View Configuration

You can also set a custom encoder on individual autocomplete views, which takes precedence over global setting:

```python
from django_tomselect.autocompletes import AutocompleteModelView
from myapp.encoders import CustomJSONEncoder

class ContactAutocomplete(AutocompleteModelView):
    model = Contact
    search_lookups = ['name__icontains', 'phone__icontains']
    value_fields = ['id', 'name', 'phone']

    # Custom JSON encoder for this view
    json_encoder = CustomJSONEncoder
    # Or as dotted string path:
    # json_encoder = 'myapp.encoders.CustomJSONEncoder'
```

#### Precedence

The JSON encoder is resolved in this order:

1. View-level `json_encoder` attribute (if set)
2. Global `DEFAULT_JSON_ENCODER` setting
3. Django's default `DjangoJSONEncoder` (when neither is set)

### Custom Validation

Add custom validation to configuration:

```python
from django.core.exceptions import ValidationError
from django_tomselect.app_settings import TomSelectConfig

class CustomConfig(TomSelectConfig):
    def validate(self):
        super().validate()
        # Add custom validation logic
        if self.placeholder and len(self.placeholder) > 100:
            raise ValidationError("Placeholder text is too long")
        if self.show_create and not self.create_field:
            raise ValidationError("create_field must be set when show_create is enabled")
```

### Dynamic Configuration

Create configuration based on runtime conditions:

```python
def get_config(user):
    return TomSelectConfig(
        show_create=user.is_staff,
        show_delete=user.is_superuser,
        max_items=10 if user.is_premium else 5,
        plugin_dropdown_header=PluginDropdownHeader(
            title="Select" if user.is_anonymous else f"Welcome {user.username}"
        )
    )
```
