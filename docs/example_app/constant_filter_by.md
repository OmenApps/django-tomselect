# Constant Filter-By

## Example Overview

- **Objective**: This example demonstrates how to filter options using **constant values** that don't come from form fields. The goal is to always filter articles to only show published ones, while optionally allowing additional filtering by magazine.
  - **Problem Solved**: When you need to enforce business rules in the UI (e.g., only show active items, only show published content), constant filters allow you to bake these rules into the widget configuration.
  - **Features Highlighted**:
    - The `Const` helper function for creating constant filter values.
    - Mixing constant and field-based filters in a single configuration.

- **Use Case**:
  - Content management: Only show published articles to editors.
  - E-commerce: Only show in-stock products.
  - Multi-tenant applications: Always filter by current organization.
  - User management: Only show active users.

## Key Code Segments

### Forms

This example uses the `Const` helper to create a filter that always applies:

:::{admonition} Form Definition
:class: dropdown

```python
from django import forms
from django_tomselect.app_settings import TomSelectConfig, Const, PluginDropdownHeader, PluginClearButton, PluginRemoveButton
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectModelMultipleChoiceField


class ConstantFilterByForm(forms.Form):
    """Demonstrates filter_by with constant values."""

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            placeholder="Optionally select a magazine...",
            plugin_clear_button=PluginClearButton(title="Clear magazine"),
        ),
        required=False,
    )

    # Articles always filtered to "published" status, optionally by magazine
    published_articles = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article",
            value_field="id",
            label_field="title",
            # Mixed filters - field-based AND constant
            filter_by=[
                ("magazine", "magazine_id"),       # Optional magazine filter
                Const("published", "status"),      # Always filter to published
            ],
            placeholder="Select published articles...",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Published Articles",
                extra_columns={
                    "magazine_name": "Magazine",
                    "word_count": "Words",
                },
            ),
            plugin_clear_button=PluginClearButton(title="Clear articles"),
            plugin_remove_button=PluginRemoveButton(),
        ),
        required=False,
    )
```
:::

**Explanation**:
- `Const("published", "status")` creates a filter that always applies `status=published`
- The constant value is sent to the server regardless of any form field
- This can be combined with regular field-based filters
- When the magazine is selected, articles are filtered by BOTH the magazine AND the constant status

### The Const Helper

The `Const` function is a convenience helper for creating constant filter specifications:

```python
from django_tomselect.app_settings import Const, FilterSpec

# These are equivalent:
Const("published", "status")
FilterSpec(source="published", lookup="status", source_type="const")
```

**Parameters**:
- `value`: The constant value to filter by (will be converted to string)
- `lookup`: The Django ORM lookup field (e.g., "status", "is_active", "category_id")

### How It Works

When the form loads and the user searches for articles:

1. The JavaScript always includes the constant filter in the URL:
   ```
   ?q=search&f='__const__status=published'
   ```
2. If a magazine is also selected, both filters are included:
   ```
   ?q=search&f='magazine__magazine_id=5'&f='__const__status=published'
   ```
3. The server recognizes the `__const__` prefix and applies the filter directly
4. Only published articles (optionally filtered by magazine) are returned

### Templates

:::{admonition} Template Code
:class: dropdown

```html
{% extends 'example/base_with_bootstrap5.html' %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h2>Constant Filter By Demo</h2>
    </div>
    <div class="card-body">
        <p>The articles dropdown <strong>always</strong> shows only published articles.</p>
        <p>Optionally select a magazine to further filter the results.</p>

        <form method="post">
            {% csrf_token %}
            <div class="mb-3">
                <label for="{{ form.magazine.id_for_label }}" class="form-label">Magazine (Optional)</label>
                {{ form.magazine }}
            </div>

            <div class="mb-3">
                <label for="{{ form.published_articles.id_for_label }}" class="form-label">Published Articles Only</label>
                {{ form.published_articles }}
                <div class="form-text">Only published articles are shown.</div>
            </div>
        </form>
    </div>
</div>
{% endblock %}
```
:::

## Design and Implementation Notes

- **Key Features**:
  - Constant filters are always applied, regardless of form state
  - Can be mixed with field-based filters
  - Useful for enforcing business rules in the UI

- **Common Use Cases**:

  | Use Case | Const Example |
  |----------|---------------|
  | Only published content | `Const("published", "status")` |
  | Only active items | `Const("true", "is_active")` |
  | Specific category | `Const("5", "category_id")` |
  | Current year | `Const("2024", "year")` |

- **Security Note**: While constant filters help enforce UI-level rules, always validate on the server side as well. Users could potentially modify the URL parameters.

See the [Multiple Filter-By](multiple_filter_by.md) example for filtering by multiple form fields.
