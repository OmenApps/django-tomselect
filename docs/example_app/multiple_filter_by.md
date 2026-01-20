# Multiple Filter-By

## Example Overview

- **Objective**: This example demonstrates how to filter options based on **multiple form fields** simultaneously using `django_tomselect`. The goal is to filter available articles by both the selected Magazine AND the selected Status, combining conditions with AND logic.
  - **Problem Solved**: When users need to narrow down options based on multiple criteria, this pattern allows combining several filter conditions seamlessly.
  - **Features Highlighted**:
    - Multiple field filters using a list of tuples in the `filter_by` parameter.
    - AND logic for combining filter conditions.

- **Use Case**:
  - Content management systems where articles are filtered by publication AND status.
  - E-commerce applications filtering products by category AND availability.
  - Any application requiring multi-dimensional filtering in dropdown menus.

## Key Code Segments

### Forms

This example uses the new list format for `filter_by` to specify multiple filter conditions:

:::{admonition} Form Definition
:class: dropdown

```python
from django import forms
from django_tomselect.app_settings import TomSelectConfig, PluginDropdownHeader, PluginClearButton, PluginRemoveButton
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectModelMultipleChoiceField, TomSelectChoiceField


class MultipleFilterByForm(forms.Form):
    """Demonstrates filter_by with multiple field-based filters."""

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            placeholder="Select a magazine...",
            plugin_clear_button=PluginClearButton(title="Clear magazine"),
        ),
        required=False,
    )

    status = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
            placeholder="Select a status...",
            plugin_clear_button=PluginClearButton(title="Clear status"),
        ),
        required=False,
    )

    # Articles filtered by BOTH magazine AND status
    articles = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article",
            value_field="id",
            label_field="title",
            # Multiple field filters - filter by magazine AND status
            filter_by=[
                ("magazine", "magazine_id"),  # Filter by selected magazine
                ("status", "status"),         # AND by selected status
            ],
            placeholder="Select articles (filtered by magazine and status)...",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Articles",
                extra_columns={
                    "status": "Status",
                    "magazine_name": "Magazine",
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
- The `filter_by` parameter accepts a list of 2-tuples: `[("form_field", "lookup_field"), ...]`
- Each tuple specifies: the form field name to get the value from, and the model field to filter by
- All conditions are combined with AND logic
- If a form field has no value, that filter condition is skipped

### How It Works

When both Magazine and Status are selected:

1. The JavaScript reads values from both form fields
2. The autocomplete URL includes multiple `f` parameters:
   ```
   ?q=search&f='magazine__magazine_id=5'&f='status__status=published'
   ```
3. The server applies both filters with AND logic
4. Only articles matching BOTH conditions are returned

### Templates

:::{admonition} Template Code
:class: dropdown

```html
{% extends 'example/base_with_bootstrap5.html' %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h2>Multiple Filter By Demo</h2>
    </div>
    <div class="card-body">
        <p>Select a magazine AND/OR a status to filter the available articles.</p>

        <form method="post">
            {% csrf_token %}
            <div class="mb-3">
                <label for="{{ form.magazine.id_for_label }}" class="form-label">Magazine</label>
                {{ form.magazine }}
            </div>

            <div class="mb-3">
                <label for="{{ form.status.id_for_label }}" class="form-label">Status</label>
                {{ form.status }}
            </div>

            <div class="mb-3">
                <label for="{{ form.articles.id_for_label }}" class="form-label">Articles</label>
                {{ form.articles }}
                <div class="form-text">Articles are filtered by both magazine AND status above.</div>
            </div>
        </form>
    </div>
</div>
{% endblock %}
```
:::

## Design and Implementation Notes

- **Key Features**:
  - Combines multiple `filter_by` conditions with AND logic
  - Each filter is optional - if not selected, that condition is ignored
  - Fully backwards compatible with the single-tuple format

- **Comparison with Single Filter**:

  | Single Filter | Multiple Filters |
  |--------------|------------------|
  | `filter_by=('field', 'lookup')` | `filter_by=[('field1', 'lookup1'), ('field2', 'lookup2')]` |
  | One condition | Multiple AND conditions |
  | Form field value only | Form field values only |

See the [Constant Filter-By](constant_filter_by.md) example for filtering with constant values.
