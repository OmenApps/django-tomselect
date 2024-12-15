# HTMX Demo

## Example Overview

This example illustrates how to use `django_tomselect` with **HTMX** to load dropdown content dynamically. HTMX is a powerful library that simplifies creating dynamic, server-driven user interfaces. By combining it with `django_tomselect`, you can achieve advanced interactions such as dynamically loaded forms or dependent dropdowns without requiring full-page reloads.

### What problem does it solve?
This setup addresses scenarios where:
- Dropdown options need to be updated based on server-side logic without reloading the page.
- HTMX simplifies the process of fetching or updating parts of the form dynamically.

### Key features highlighted:
- Dynamic form rendering with HTMX.
- Integration with `django_tomselect` for autocomplete and enhanced dropdown functionality.
- Seamless updates without page reloads.

### Use Case Scenarios:
- Filtering dropdown options based on user input or selections in other fields.
- Dynamic form rendering for creating or updating related models.
- Inline editing or form embedding in modal dialogs.

*(Placeholders for screenshots or GIFs)*:
- `![GIF: Dynamic Form Rendering with HTMX](path-to-gif)`
- `![Screenshot: Dropdown with HTMX Interaction](path-to-image)`

---

## Key Code Segments

### Forms
The `Bootstrap5StylingHTMXForm` extends `Bootstrap4StylingForm`, enabling HTMX integration.

```python
class Bootstrap5StylingHTMXForm(Bootstrap4StylingForm):
    """HTMX-enabled form using TomSelectModelChoiceField."""
    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            use_htmx=True,
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

- **Purpose**: Configures a field to dynamically load options via HTMX, enhancing the interactivity of the dropdown.

[See full code in the repository](#).

---

### HTMX Fragment Template
The `htmx_fragment.html` template defines the dynamic content that will be loaded into the page.

```html
{{ form.media }}

<div class="card">
    <div class="card-header">
        <h2>Loading content via HTMX Demo</h2>
    </div>
    <div class="card-body">
        <div class="pb-5">This page demonstrates loading the form using HTMX.</div>
        <form>
            {% csrf_token %}
            {{ form.as_div }}
        </form>
    </div>
</div>
```

- **Purpose**: Specifies the form structure that will be dynamically inserted into the page using HTMX.

[See full code in the repository](#).

---

### Main HTMX Template
The `htmx.html` template renders the page and loads the dynamic fragment via HTMX.

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
    <div class="card" hx-get="{% url 'demo-htmx-form-fragment' %}" hx-trigger="load" hx-swap="innerHTML">
    </div>
{% endblock %}
```

- **Purpose**: Dynamically loads the form fragment via the `hx-get` attribute, triggered on page load.

[See full code in the repository](#).

---

### Autocomplete View
The backend for autocomplete remains consistent, but HTMX makes the interaction seamless.

```python
class EditionAutocomplete(AutocompleteModelView):
    model = Edition  # The model to query
    search_lookups = ["name__icontains"]
    ordering = "name"
```

- **Purpose**: Fetches options dynamically as the user interacts with the dropdown.

[See full code in the repository](#).

---

## Design and Implementation Notes

### Key Features
- **Dynamic Content Loading**: Leverages HTMX to dynamically load or update form sections.
- **Framework Integration**: Works seamlessly with `django_tomselect` and Bootstrap 5.
- **Enhanced User Experience**: Eliminates full-page reloads, making interactions faster and smoother.

### Design Decisions
- **HTMX**: Chosen for its simplicity and compatibility with server-rendered Django views.
- **Reusable Templates**: Separates the dynamically loaded form (`htmx_fragment.html`) from the main template for modularity.

### Alternative Approaches
- Use JavaScript libraries like jQuery or Vue.js for dynamic updates if more complex interactions are required.
- Avoid HTMX for projects with limited interactivity to reduce dependencies.

### Potential Extensions
- Add dependent dropdowns where one field’s options are filtered based on another field’s value.
- Implement inline editing for dropdown options using HTMX and modal dialogs.
