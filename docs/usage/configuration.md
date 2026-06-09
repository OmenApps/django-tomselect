# Configuration

`django_tomselect` provides a flexible configuration system built around a main `TomSelectConfig` class. This class, along with various plugin and framework configuration options, lets you control the behavior, appearance, and functionality of Tom Select widgets at both a global and per-field level.

## TomSelectConfig Overview

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

## General Configuration Options

Basic settings for the widget are typically passed as keyword arguments directly into `TomSelectConfig`. These include:

- **Search Behavior**: `minimum_query_length` to determine when to trigger searches.
- **Display Settings**: `placeholder` text, whether to `open_on_focus`, and `highlight` matching terms.
- **Loading and Performance**: `load_throttle` to control how frequently searches occur, and `max_options` to limit how many results appear.
- **Creation and HTMX**: `create` to allow new item creation, and `create_with_htmx` to handle server-driven creation workflows. See {ref}`Creating New Items <creating-new-items>` for detailed documentation.

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

## Available Plugins

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

## CSS Framework Options

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

## Global Settings vs Field-level Settings

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

## Example Configuration

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
