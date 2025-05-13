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
config = TomSelectConfig(
    # Core Settings
    url='book-autocomplete',
    value_field='id',
    label_field='name',
    create_field='',

    # Additional Core Settings
    filter_by=('category__id', 'id'),  # Filter by category.id = id
    exclude_by=('author__id', 'id'),    # Exclude where author.id = id
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
    }
}
```

## Advanced Usage

### Dependent Fields

Configure fields that depend on other field values:

```python
config = TomSelectConfig(
    filter_by=('category__id', 'id'),  # Filter by category.id = id
    exclude_by=('author__id', 'id')    # Exclude where author.id = id
)
```

### Logging

`django_tomselect` uses a custom weapper with the built-in Python logging module to make it easier to turn logging on and off. By default, logging is enabled, and the package emits many debug-level logging entries. In rare cases, you may wish to disable logging completely. To do so, add the following to your Django settings:

```python
TOMSELECT = {
    # Other settings...

    # Disable logging
    "ENABLE_LOGGING": False
}
```

You can customize the logging level configuration by updating your Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django_tomselect': {
            'handlers': ['console'],
            'level': 'INFO',  # <-- Change to 'DEBUG' to see *all* messages
            'propagate': True,
        },
    },
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
