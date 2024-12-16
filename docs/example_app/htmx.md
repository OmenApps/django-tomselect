# HTMX Demo

## Example Overview

This example is very similar to the BS5 styling example, and illustrates how to use `django_tomselect` with **[HTMX](https://htmx.org/)** to load dropdown content dynamically on page load. By combining htmx with `django_tomselect`, you can achieve advanced interactions such as dynamically loaded content without full page reloads. See the bulk actions example for a more advanced htmx use case.

### Key features highlighted:
- Dynamic form rendering with HTMX.
- Integration with `django_tomselect` for autocomplete and enhanced dropdown functionality.

### Use Case Scenarios:
- Filtering dropdown options based on user input or selections in other fields.
- Dynamic form rendering for creating or updating related models.
- Inline editing or form embedding in modal dialogs.

---

## Key Code Segments

### Forms
The `Bootstrap5StylingHTMXForm` extends `Bootstrap5StylingForm`, enabling HTMX integration.

:::{admonition} Bootstrap 5 Styling with HTMX
:class: dropdown

```python
class Bootstrap5StylingHTMXForm(Bootstrap5StylingForm):
    """HTMX-enabled form using TomSelectModelChoiceField."""
    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            use_htmx=True,  # <<-- Adjusts JavaScript to work with HTMX
            css_framework="bootstrap5",
            placeholder="Select a value",
            highlight=True,
            open_on_focus=True,
            plugin_clear_button=PluginClearButton(
                title="Clear Selection", class_name="clear-button"
            ),
        ),
        attrs={
            "class": "form-control mb-3",
            "id": "tomselect-custom-id",
        },
        label="Single Select",
        help_text="HTMX-enabled dropdown with dynamic content loading.",
    )
    # Additional fields omitted for brevity
```
:::

- **Purpose**: Configures a field to work with HTMX, enabling dynamic content loading.

---

### HTMX Fragment Template
The `htmx_fragment.html` template defines the dynamic content that will be loaded into the page.

:::{admonition} HTMX Fragment Template
:class: dropdown

```html
{% load static %}

{{ form.media }}

<div class="card">
    <div class="card-header">
        <h2>Loading content via htmx Demo</h2>
    </div>
    <div class="card-body">
        <div class="pb-5">This page demonstrates loading the form using htmx.</div>
        <form>
            {% csrf_token %}
            {{ form.as_div }}
        </form>
    </div>
</div>
```
:::

---

### Main HTMX Template
The `htmx.html` template renders the page and loads the dynamic fragment via HTMX.

:::{admonition} Main HTMX Template
:class: dropdown

```html
{% extends 'example/base_with_bootstrap5.html' %}
{% load django_tomselect %}

{% block extra_header %}
    {% tomselect_media css_framework="bootstrap5" %}
    <style>
        .helptext {
            font-size: 10px;
            color: #757575;
        }
    </style>
{% endblock %}

{% block content %}
    <div class="card" hx-get="{%  url 'demo-htmx-form-fragment' %}" hx-trigger="load" hx-swap="innerHTML">
{% endblock %}
```
:::


---

### Autocomplete View
The backend for autocomplete remains consistent with thr styling examples, but HTMX makes the interaction seamless.

:::{admonition} Autocomplete View
:class: dropdown

```python
class EditionAutocompleteView(AutocompleteModelView):
    """Autocomplete that returns all Edition objects."""

    model = Edition
    search_lookups = ["name__icontains"]
    page_size = 20
    value_fields = ["id", "name", "year", "pages", "pub_num"]

    list_url = "edition-list"
    create_url = "edition-create"
    update_url = "edition-update"
    delete_url = "edition-delete"

    skip_authorization = True
```
:::

---

## Design and Implementation Notes

### Key Features
- **Dynamic Content Loading**: Leverages HTMX to dynamically load the form content on page load.
- **Framework Integration**: Works seamlessly with `django_tomselect` and Bootstrap 5.

### Design Decisions
- **Reusable Templates**: Separates the dynamically loaded form (`htmx_fragment.html`) from the main template for modularity.
