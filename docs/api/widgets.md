# Widgets

This module provides the widget classes that render Tom Select elements in Django forms. These widgets handle both the HTML rendering and JavaScript initialization of Tom Select controls.

## Model Widgets

### Class Hierarchy

```{mermaid}

    classDiagram
        class TomSelectWidgetMixin {
            +template_name: str
            +render()
            +get_plugin_context()
            +get_autocomplete_url()
            +build_attrs()
            +media
        }

        class TomSelectModelWidget {
            +get_context()
            +get_queryset()
            +get_autocomplete_view()
            +validate_request()
        }

        class TomSelectModelMultipleWidget {
            +get_context()
            +build_attrs()
        }

        class TomSelectIterablesWidget {
            +get_context()
            +get_autocomplete_view()
            +get_iterable()
        }

        class TomSelectIterablesMultipleWidget {
            +get_context()
            +build_attrs()
        }

        TomSelectWidgetMixin <-- TomSelectModelWidget
        TomSelectWidgetMixin <-- TomSelectIterablesWidget
        TomSelectModelWidget <-- TomSelectModelMultipleWidget
        TomSelectIterablesWidget <-- TomSelectIterablesMultipleWidget
```

### TomSelectModelWidget

```{eval-rst}
.. autoclass:: django_tomselect.widgets.TomSelectModelWidget
   :members:
   :show-inheritance:
   :special-members: __init__
```

#### Example Usage

```python
from django import forms
from django_tomselect.widgets import TomSelectModelWidget
from django_tomselect.app_settings import TomSelectConfig

class BookForm(forms.ModelForm):
    author = forms.ModelChoiceField(
        widget=TomSelectModelWidget(
            config=TomSelectConfig(
                url='author-autocomplete',
                show_detail=True,
                show_update=True
            )
        )
    )
```

### TomSelectModelMultipleWidget

```{eval-rst}
.. autoclass:: django_tomselect.widgets.TomSelectModelMultipleWidget
   :members:
   :show-inheritance:
   :special-members: __init__
```

#### Example Usage

```python
from django_tomselect.app_settings import TomSelectConfig, PluginCheckboxOptions

class BookForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        widget=TomSelectModelMultipleWidget(
            config=TomSelectConfig(
                url='category-autocomplete',
                plugin_checkbox_options=PluginCheckboxOptions()
            )
        )
    )
```

## Iterables Widgets

### TomSelectIterablesWidget

```{eval-rst}
.. autoclass:: django_tomselect.widgets.TomSelectIterablesWidget
   :members:
   :show-inheritance:
   :special-members: __init__
```

#### Example Usage

```python
from django.db.models import TextChoices

class Status(TextChoices):
    DRAFT = 'D', 'Draft'
    PUBLISHED = 'P', 'Published'
    ARCHIVED = 'A', 'Archived'

class ArticleForm(forms.Form):
    status = forms.ChoiceField(
        choices=Status.choices,
        widget=TomSelectIterablesWidget(
            config=TomSelectConfig(
                plugin_dropdown_header=PluginDropdownHeader(
                    title="Select Status"
                )
            )
        )
    )
```

### TomSelectIterablesMultipleWidget

```{eval-rst}
.. autoclass:: django_tomselect.widgets.TomSelectIterablesMultipleWidget
   :members:
   :show-inheritance:
   :special-members: __init__
```

#### Example Usage

```python
from django_tomselect.app_settings import TomSelectConfig, PluginRemoveButton

class ArticleForm(forms.Form):
    tags = forms.MultipleChoiceField(
        choices=[('python', 'Python'), ('django', 'Django'), ('web', 'Web Development')],
        widget=TomSelectIterablesMultipleWidget(
            config=TomSelectConfig(
                plugin_remove_button=PluginRemoveButton()
            )
        )
    )
```

## Base Mixin

### TomSelectWidgetMixin

```{eval-rst}
.. autoclass:: django_tomselect.widgets.TomSelectWidgetMixin
   :members:
   :show-inheritance:
```

This mixin provides the core functionality for all TomSelect widgets, including:
- Media handling (CSS/JS)
- Template rendering
- Configuration processing
- Plugin support

## Customization

### Custom Rendering Templates

You can override the default rendering templates by creating your own templates in your project's template directory under `django_tomselect/render/`. The available templates are:

- `clear_button.html`: Renders the clear button plugin HTML
- `dropdown_footer.html`: Renders the dropdown footer plugin HTML
- `dropdown_header.html`: Renders the dropdown header plugin HTML
- `item.html`: Renders selected items
- `loading_more.html`: Renders the "Loading more results..." message
- `loading.html`: Renders the loading spinner/indicator
- `no_more_results.html`: Renders the message when no more results are available
- `no_results.html`: Renders the message when no search results are found
- `not_loading.html`: Renders content when not loading
- `optgroup_header.html`: Renders the header for an option group
- `optgroup.html`: Renders an option group container
- `option_create.html`: Renders the "Create new option" element
- `option.html`: Renders dropdown options
- `select.html`: Renders the underlying select element

### Custom Attributes

Widgets accept custom HTML attributes through the `attrs` parameter:

```python
widget = TomSelectModelWidget(
    config=config,
    attrs={
        'class': 'custom-select',
        'data-custom': 'value',
        'data_template_option': '`<div>${data.name} (${data.id})</div>`',
        'data_template_item': '`<div>${data.name}</div>`'
    }
)
```

### Media Configuration

The widgets automatically include the required CSS and JavaScript files. You can configure the CSS framework and whether to use minified files:

```python
widget = TomSelectModelWidget(
    config=TomSelectConfig(
        css_framework='bootstrap5',  # 'default', 'bootstrap4', or 'bootstrap5'
        use_minified=True
    )
)
```

```{note}
Remember to include `{{ form.media }}` in your templates to include the required CSS and JavaScript files.
```
