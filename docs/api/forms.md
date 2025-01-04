# Forms

This module provides form fields for using Tom Select in Django forms. These fields provide an enhanced selection interface with features like autocomplete, tagging, and remote data loading.

## Model Choice Fields

### TomSelectModelChoiceField

```{eval-rst}
.. autoclass:: django_tomselect.forms.TomSelectModelChoiceField
   :members:
   :show-inheritance:
   :special-members: __init__
```

#### Example Usage

```python
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.app_settings import TomSelectConfig

class AuthorForm(forms.Form):
    author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url='author-autocomplete',
            placeholder='Select an author...',
            minimum_query_length=2
        )
    )
```

### TomSelectModelMultipleChoiceField

```{eval-rst}
.. autoclass:: django_tomselect.forms.TomSelectModelMultipleChoiceField
   :members:
   :show-inheritance:
   :special-members: __init__
```

#### Example Usage

```python
class BookForm(forms.Form):
    authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url='author-autocomplete',
            placeholder='Select authors...',
            plugin_remove_button=PluginRemoveButton()
        )
    )
```

## Choice Fields

### TomSelectChoiceField

```{eval-rst}
.. autoclass:: django_tomselect.forms.TomSelectChoiceField
   :members:
   :show-inheritance:
   :special-members: __init__
```

#### Example Usage

```python
class ColorForm(forms.Form):
    color = TomSelectChoiceField(
        choices=[
            ('red', 'Red'),
            ('blue', 'Blue'),
            ('green', 'Green')
        ],
        config=TomSelectConfig(
            plugin_clear_button=PluginClearButton()
        )
    )
```

### TomSelectMultipleChoiceField

```{eval-rst}
.. autoclass:: django_tomselect.forms.TomSelectMultipleChoiceField
   :members:
   :show-inheritance:
   :special-members: __init__
```

#### Example Usage

```python
from django.db.models import TextChoices

class Sizes(TextChoices):
    SMALL = 'S', 'Small'
    MEDIUM = 'M', 'Medium'
    LARGE = 'L', 'Large'

class ProductForm(forms.Form):
    available_sizes = TomSelectMultipleChoiceField(
        choices=Sizes.choices,
        config=TomSelectConfig(
            plugin_checkbox_options=PluginCheckboxOptions()
        )
    )
```

## Base Mixins

These mixins provide common functionality for TomSelect fields. They're primarily for internal use but may be useful for custom field development.

### BaseTomSelectMixin

```{eval-rst}
.. autoclass:: django_tomselect.forms.BaseTomSelectMixin
   :members:
   :show-inheritance:
   :special-members: __init__
```

### BaseTomSelectModelMixin

```{eval-rst}
.. autoclass:: django_tomselect.forms.BaseTomSelectModelMixin
   :members:
   :show-inheritance:
   :special-members: __init__
```

## Integration with Django Forms

All TomSelect fields can be used in Django forms just like standard form fields. They support all the usual field options like `required`, `label`, `help_text`, etc.

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.app_settings import TomSelectConfig

class MyForm(forms.Form):
    user = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url='user-autocomplete',
            show_detail=True,
            show_update=True
        ),
        required=True,
        label='Select User',
        help_text='Search and select a user'
    )
```

The fields handle form validation, cleaning, and initial data automatically. They also properly integrate with Django's form media system to include required JavaScript and CSS files.

```{note}
All TomSelect fields require a corresponding autocomplete view to handle the data loading. See the Views documentation for details on setting up autocomplete views.
```
