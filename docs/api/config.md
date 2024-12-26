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
    label_field='title',
    create_field='name',

    # Display Settings
    placeholder='Select a book...',
    minimum_query_length=2,
    max_items=5,
    max_options=50,

    # Behavior Settings
    preload='focus',  # Can be 'focus', True, or False
    highlight=True,
    open_on_focus=True,
    close_after_select=True,
    hide_placeholder=True,

    # Performance Settings
    load_throttle=300,
    loading_class='loading',

    # Feature Toggles
    show_list=True,
    show_create=True,
    show_detail=True,
    show_update=True,
    show_delete=True,

    # Framework Settings
    css_framework='bootstrap5',  # 'default', 'bootstrap4', or 'bootstrap5'
    use_minified=True,

    # Plugins (covered in detail below)
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
        title="Clear All",
        class_name="btn-clear"
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
        title="Select Books",
        header_class="dropdown-header bg-light",
        title_row_class="header-row",
        label_class="header-label",
        value_field_label="ID",
        label_field_label="Title",
        show_value_field=True,
        extra_columns={
            'author__name': 'Author',
            'publication_year': 'Year'
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
        title="Options",
        footer_class="dropdown-footer",
        list_view_label="View All",
        list_view_class="btn btn-sm btn-primary",
        create_view_label="Add New",
        create_view_class="btn btn-sm btn-success"
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
        title="Remove",
        label="×",
        class_name="remove-button"
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

Better, you can customize the logging level configuration by updating your Django settings to skip debug messages, but still see more important messages:

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
        if self.max_items and self.max_items < 1:
            raise ValidationError("max_items must be greater than 0")
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
