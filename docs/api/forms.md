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

Assuming an autocomplete view is set up to return choices for the field, you can use `TomSelectChoiceField` like this:

```python
class ColorForm(forms.Form):
    """Form demonstrating the use of TomSelectChoiceField with a color selection."""
    color = TomSelectChoiceField(
        config=TomSelectConfig(
            url='autocomplete-colors',
            value_field='value',
            label_field='label',
            placeholder='Select a color...',
        ),
        help_text="Select a color from the list"
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

Example usage for `TomSelectMultipleChoiceField`, assuming you have an autocomplete view set up to return choices:

```python
class ProductForm(forms.Form):
    """Form demonstrating the use of TomSelectMultipleChoiceField for selecting product sizes."""
    available_sizes = TomSelectMultipleChoiceField(
        config=TomSelectConfig(
            url='autocomplete-sizes',
            placeholder='Select sizes...',
            value_field='value',
            label_field='label',
            placeholder='Select sizes...',
        ),
        help_text="Select one or more sizes for the product"
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

## TomSelectTokenField

A `CharField` that parses and validates a token-style query string, paired with
`TomSelectTokenWidget`. The form value is one canonical token string like
`author:42 category:5 some free text`.

```python
from django_tomselect import TomSelectTokenField

class ArticleFilterForm(forms.Form):
    q = TomSelectTokenField(
        composite_view="autocomplete-article-token",  # URL name of CompositeAutocompleteView
        required=False,
        allow_free_text=True,
        max_query_length=4096,   # utf-8 byte cap
        max_tokens=32,
        max_values_per_operator=16,
    )
```

`clean()` enforces:

- Parser-level errors (unknown operators, unterminated quotes, cap overflows)
  → `ValidationError`. Unknown operators are NEVER silently re-routed as free text.
- `Operator.max_count` / `Operator.min_count` → field-level error.
- `allow_free_text=False` → un-prefixed input is rejected.
- Empty operator values (e.g. `author:`) → field-level error.

ORM coercion errors (`category:tech` against an id-based `filter_lookup`) are
caught at apply-time, not in `clean()` - the field has no parent queryset.
Surface them via `form.add_error("q", e)` in your view; see the
{doc}`../example_app/article_token_search` demo for the canonical pattern.

For cross-operator rules in `Form.clean()`:

```python
def clean(self):
    cleaned = super().clean()
    parsed = self.fields["q"].parse(cleaned.get("q", "") or "")
    if parsed.has("author") and not parsed.has("category"):
        raise ValidationError("If you specify author:, you must also specify category:.")
    return cleaned
```
