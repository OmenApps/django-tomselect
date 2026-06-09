# Formset with filter_by/exclude_by

## Example Overview

This example demonstrates `filter_by` and `exclude_by` inside Django formsets, where each row needs its own independent dependent-field relationships - a selection in row 1 should only affect row 1's dependent fields. It covers automatic form-prefix handling, dynamically added rows, and using `exclude_by` to prevent circular references in model formsets (such as a category becoming its own parent). Use it for bulk data-entry forms or any formset interface that needs cascading dropdown behavior per row.

## Key Code Segments

### Forms with filter_by in Formsets

This example uses `TomSelectModelChoiceField` for both `magazine` and `edition` fields. The `edition` field is configured with the `filter_by` parameter, and the formset handles each row independently.

:::{admonition} Form Definition
:class: dropdown

```python
from django import forms
from django.forms import formset_factory
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.app_settings import (
    TomSelectConfig,
    PluginDropdownInput,
    PluginDropdownFooter,
    PluginClearButton,
)


class EditionWithFilterFormsetForm(forms.Form):
    """Form demonstrating filter_by in formsets."""

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a magazine first",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection"),
        ),
        attrs={"class": "form-control mb-3"},
        label="Magazine",
        help_text="Select a magazine to filter available editions",
    )

    edition = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),  # Key feature!
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            placeholder="Select an edition (filtered by magazine)",
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection"),
            plugin_dropdown_footer=PluginDropdownFooter(),
        ),
        attrs={"class": "form-control mb-3"},
        label="Edition",
        help_text="Editions are filtered based on the selected magazine",
        required=False,
    )


# Create the formset factory
EditionWithFilterFormset = formset_factory(
    EditionWithFilterFormsetForm, extra=2, can_delete=True
)
```
:::

**Explanation**:
- The `filter_by=("magazine", "magazine_id")` parameter tells the edition field to watch the magazine field in the same form row
- When a magazine is selected, the edition field will query the autocomplete endpoint with `?f='magazine__magazine_id=<selected_value>'`
- Form prefixes (e.g., `myformset-0-magazine`, `myformset-1-magazine`) are automatically handled by the JavaScript

### Using exclude_by in Model Formsets

For model formsets, you can use `exclude_by` to prevent invalid selections. A common use case is preventing a category from being selected as its own parent:

:::{admonition} Model Form with exclude_by
:class: dropdown

```python
from django import forms
from django.forms import modelformset_factory
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect.app_settings import (
    TomSelectConfig,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginClearButton,
)
from .models import Category


class CategoryModelForm(forms.ModelForm):
    """ModelForm for managing categories with their parent categories using TomSelect.

    Demonstrates exclude_by in a model formset to prevent circular parent-child relationships.
    """

    # Override the parent field to use TomSelect with tabular display
    parent = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            show_list=True,
            value_field="id",
            label_field="name",
            exclude_by=("id", "id"),  # Exclude current category from parent options (prevents circular references)
            css_framework="bootstrap5",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            placeholder="Select a parent category (optional)",
            plugin_dropdown_header=PluginDropdownHeader(
                show_value_field=False,
                label_field_label="Category",
                extra_columns={
                    "direct_articles": "Direct Articles",
                    "total_articles": "Total Articles",
                },
            ),
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title="Clear Selection"),
        ),
        queryset=None,  # Queryset is set by the widget's autocomplete view
        required=False,
        attrs={"class": "form-control mb-3"},
        label="Parent Category",
        help_text="Select a parent category (optional) - current category is excluded to prevent circular references",
    )

    class Meta:
        model = Category
        fields = ["name", "parent"]


# Create the model formset factory
CategoryModelFormset = modelformset_factory(
    Category, form=CategoryModelForm, extra=1, can_delete=True
)
```
:::

**Explanation**:
- The `exclude_by=("id", "id")` parameter tells the parent field to exclude the category with the same ID as the hidden `id` field in the form row
- This prevents users from selecting a category as its own parent
- For existing records, this automatically excludes the current record from the dropdown

:::{note}
**Why prevent circular references?**

In hierarchical data models (like categories with parent-child relationships), allowing a record to reference itself as its parent creates a circular reference that can cause:
- Infinite loops when traversing the hierarchy
- Database integrity issues
- UI rendering problems (infinite nesting)

The `exclude_by` parameter provides a clean, declarative way to prevent this at the UI level. You can see this in action in the **Model Formset Demo** page of the example app, where editing existing categories automatically hides the current category from the parent dropdown.
:::

### View Implementation

:::{admonition} View Code
:class: dropdown

```python
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

from .forms import EditionWithFilterFormset


def formset_filter_demo(request: HttpRequest) -> HttpResponse:
    """View for demonstrating filter_by with formsets."""
    template = "example/basic_demos/formset_filter.html"

    # Using a prefix helps avoid conflicts with other forms
    formset = EditionWithFilterFormset(
        request.POST or None, prefix="edition_filter"
    )

    if request.method == "POST":
        if formset.is_valid():
            processed_count = 0
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    magazine = form.cleaned_data.get("magazine")
                    edition = form.cleaned_data.get("edition")
                    if magazine and edition:
                        processed_count += 1
                        # Process the data here
            messages.success(
                request,
                f"Successfully processed {processed_count} magazine-edition selections!"
            )
            return HttpResponseRedirect(request.path)
        messages.error(request, "Please correct the errors below.")

    context = {"formset": formset}
    return TemplateResponse(request, template, context)
```
:::

### Template with Dynamic Row Addition

:::{admonition} Template Code
:class: dropdown

```html
{% extends 'example/base_with_bootstrap5.html' %}

{% block content %}
    {{ formset.media }}

    <form method="post">
        {% csrf_token %}
        {{ formset.management_form }}

        <div id="form-container">
            {% for form in formset %}
                <div class="filter-form">
                    <div class="row">
                        <div class="col-md-5">
                            <label>Magazine (Parent)</label>
                            {{ form.magazine }}
                        </div>
                        <div class="col-md-5">
                            <label>Edition (Filtered)</label>
                            {{ form.edition }}
                        </div>
                        <div class="col-md-2">
                            {{ form.DELETE }}
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>

        <button type="button" id="add-form">Add Row</button>
        <button type="submit">Submit</button>
    </form>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const addButton = document.getElementById('add-form');
            const formContainer = document.getElementById('form-container');
            const totalForms = document.getElementById('id_edition_filter-TOTAL_FORMS');

            // Store references to TomSelect configs from the first form
            const magazineSelect = document.querySelector('select[name$="-magazine"][data-tomselect]');
            const editionSelect = document.querySelector('select[name$="-edition"][data-tomselect]');
            const magazineConfig = magazineSelect ? window.djangoTomSelect.configs.get(magazineSelect.id) : null;
            const editionConfig = editionSelect ? window.djangoTomSelect.configs.get(editionSelect.id) : null;

            addButton.addEventListener('click', function() {
                const formCount = parseInt(totalForms.value);
                const firstForm = formContainer.children[0];

                // Create a new div to hold our cloned form
                const container = document.createElement('div');
                container.classList.add('filter-form');

                // Clone only the form structure, excluding scripts
                const formStructure = firstForm.querySelector('.row').cloneNode(true);
                container.appendChild(formStructure);

                // Update form indices and row number
                container.innerHTML = container.innerHTML
                    .replace(/form-(\d+)/g, `form-${formCount}`)
                    .replace(/id_edition_filter-(\d+)/g, `id_edition_filter-${formCount}`)
                    .replace(/edition_filter-(\d+)/g, `edition_filter-${formCount}`)
                    .replace(/Row \d+/g, `Row ${formCount + 1}`);

                // Clean up TomSelect elements and prepare new selects
                const selectElements = container.querySelectorAll('select[data-tomselect]');
                selectElements.forEach((selectElement, index) => {
                    // Remove any ts-wrapper divs that might have been cloned
                    const parentElement = selectElement.parentElement;
                    while (parentElement.querySelector('.ts-wrapper')) {
                        parentElement.querySelector('.ts-wrapper').remove();
                    }

                    // Clean the select element
                    selectElement.className = selectElement.className
                        .replace(/\btomselected\b/g, '')
                        .replace(/\bts-hidden-accessible\b/g, '');
                    selectElement.style.display = '';
                    selectElement.removeAttribute('tabindex');
                    selectElement.removeAttribute('data-ts-hidden');

                    // Clear existing options (keeping only empty option if present)
                    while (selectElement.options.length > 1) {
                        selectElement.remove(1);
                    }
                    if (selectElement.options.length > 0) {
                        selectElement.options[0].selected = true;
                    }
                });

                // Remove any existing script tags
                container.querySelectorAll('script').forEach(script => script.remove());

                // Append the clean container
                formContainer.appendChild(container);

                // Initialize TomSelect on the new selects
                const newMagazineSelect = container.querySelector('select[name$="-magazine"]');
                const newEditionSelect = container.querySelector('select[name$="-edition"]');

                if (newMagazineSelect && magazineConfig) {
                    const newMagazineConfig = window.djangoTomSelect.cloneConfig(magazineConfig);
                    delete newMagazineConfig.items;
                    delete newMagazineConfig.renderCache;
                    window.djangoTomSelect.initialize(newMagazineSelect, newMagazineConfig);
                }

                if (newEditionSelect && editionConfig) {
                    const newEditionConfig = window.djangoTomSelect.cloneConfig(editionConfig);
                    delete newEditionConfig.items;
                    delete newEditionConfig.renderCache;
                    // Update the filter_by reference to point to the new magazine field
                    if (newEditionConfig.filterByFieldId) {
                        newEditionConfig.filterByFieldId = newMagazineSelect.id;
                    }
                    window.djangoTomSelect.initialize(newEditionSelect, newEditionConfig);
                }

                // Update the total forms count
                totalForms.value = formCount + 1;
            });
        });
    </script>
{% endblock %}
```
:::

## How Form Prefix Handling Works

When using `filter_by` or `exclude_by` in formsets, the widget automatically handles form prefixes:

1. **Standard form**: A field named `magazine` has ID `id_magazine`
2. **Formset row 0**: The same field has ID `id_myprefix-0-magazine`
3. **Formset row 1**: The same field has ID `id_myprefix-1-magazine`

The JavaScript automatically:
- Detects when a field is part of a formset by looking at the field name pattern
- Extracts the prefix and index from the field name
- Updates `filter_by` references to point to the correct field in the same row

## Implementation Notes

- **Technical Details**:
  - The widget's JavaScript listens for changes on the parent field
  - When the parent field changes, it updates the autocomplete URL with the filter parameter
  - Each row's filter relationship is independent of other rows

- **Best Practices**:
  - Always use a prefix when instantiating formsets to avoid ID conflicts
  - When dynamically adding rows, clone the TomSelect configuration and reinitialize
  - For model formsets with `exclude_by`, ensure the hidden `id` field is present in the form

See the [Filter-By Magazine](filter_by_magazine.md) example for basic `filter_by` usage, and the [Exclude-By Primary Author](exclude_by_primary_author.md) example for basic `exclude_by` usage.
