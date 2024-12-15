# Bootstrap 4 Styling Demo

## Example Overview

This example demonstrates the use of `django_tomselect` with Bootstrap 4 styling to create responsive, dynamic `<select>` fields. The example includes various configurations for single and multiple selections, highlighting the integration with a modern CSS framework.

### What problem does it solve?
This setup simplifies the creation of user-friendly, visually appealing dropdowns with advanced features like:
- Autocomplete.
- Placeholder text.
- Tabular dropdown headers.
- Options for creating and managing items directly from the dropdown.

### Key features highlighted:
- Single and multiple select fields with Bootstrap 4 styling.
- Plugins for clearing selections, adding footers/headers, and enhanced navigation.
- Server-side autocomplete with configurable behavior.

### Use Case Scenarios:
- Tagging systems for blog posts or resources.
- Selecting contacts or participants in an event management application.
- Dynamic selection of countries, products, or categories in e-commerce platforms.

*(Placeholders for screenshots or GIFs)*:
- `![Screenshot: Initial Dropdown State](path-to-image)`
- `![GIF: Autocomplete in Action](path-to-gif)`

---

## Key Code Segments

### Forms
The `Bootstrap4StylingForm` in `basic_demos.py` configures fields using `TomSelectConfig` for Bootstrap 4.

```python
class Bootstrap4StylingForm(forms.Form):
    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            css_framework="bootstrap4",
            placeholder="Select a value",
            highlight=True,
            open_on_focus=True,
            plugin_clear_button=PluginClearButton(
                title="Clear Selection", class_name="clear-button"
            ),
        ),
        attrs={"class": "form-control mb-3"},
        label="Single Select",
        help_text="Example of single select with autocomplete and clear button.",
    )
    # Other fields omitted for brevity
```

- **Purpose**: This sets up a dropdown with an autocomplete endpoint (`url`), styling via Bootstrap 4, and a clear button plugin.

[See full code in the repository](#).

---

### Template
The `bs4.html` template renders the form using Bootstrap 4 components. It extends the base layout and includes the necessary CSS and JavaScript assets.

```html
{% extends 'example/base_with_bootstrap4.html' %}

{% block extra_header %}
    {{ form.media }}
    <style>
        .form-label {
            color: #FFF;
        }
    </style>
{% endblock %}

{% block content %}
    <div class="card">
        <div class="card-header">
            <h2>Bootstrap 4 Styling Demo</h2>
        </div>
        <div class="card-body">
            <form>
                {% csrf_token %}
                {{ form.as_div }}
            </form>
        </div>
    </div>
{% endblock %}
```

- **Purpose**: Demonstrates how to use the Bootstrap 4 styled form, integrating Django’s CSRF protection and dynamic media rendering.

---

### Autocomplete View
The autocomplete functionality is defined in the `autocompletes.py` file using `AutocompleteModelView`.

```python
class EditionAutocomplete(AutocompleteModelView):
    model = Edition  # The model to query
    search_lookups = ["name__icontains"]
    ordering = "name"
```

- **Purpose**: Provides the backend logic for fetching autocomplete results, with filtering and ordering.

[See full code in the repository](#).

---

## Design and Implementation Notes

### Key Features
- **Dynamic styling**: The example leverages Bootstrap 4’s `form-control` classes for consistent styling.
- **Plugins**: Includes plugins like `clear_button` and `dropdown_footer` to enhance UX.

### Design Decisions
- **Bootstrap 4**: Chosen for projects using older but still widely supported CSS frameworks.
- **Clear button plugin**: Simplifies user interaction by allowing quick deselection.

### Alternative Approaches
- Use the "default" styling if Bootstrap is not integrated into the project.
- Swap the clear button plugin for a custom implementation if additional behavior is needed.

### Potential Extensions
- Add dependent dropdowns where one field’s options are filtered based on another field’s selection.
- Integrate custom headers or footers with additional data points like descriptions or icons.
