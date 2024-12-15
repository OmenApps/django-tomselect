# Bootstrap 5 Styling Demo

## Example Overview

This example demonstrates how to use `django_tomselect` with Bootstrap 5 styling to create modern, accessible, and dynamic dropdowns. The configuration includes single and multiple selection fields and leverages the latest features of Bootstrap 5 for enhanced responsiveness and aesthetics.

### What problem does it solve?
The example simplifies creating visually consistent and functional dropdowns with features such as:
- Autocomplete functionality.
- Placeholder text.
- Clear and remove buttons.
- Enhanced user interactivity with tabular dropdown headers and dynamic filtering.

### Key features highlighted:
- Integration with Bootstrap 5 for form styling.
- Autocomplete-backed single and multiple select dropdowns.
- Plugins for additional interactivity and customization.

### Use Case Scenarios:
- Selecting products or categories in an admin dashboard.
- Managing participants or resources in event management applications.
- Country or city selection in location-based services.

*(Placeholders for screenshots or GIFs)*:
- `![Screenshot: Dropdown with Bootstrap 5 Styling](path-to-image)`
- `![GIF: Dynamic Dropdown with Autocomplete](path-to-gif)`

---

## Key Code Segments

### Forms
The `Bootstrap5StylingForm` in `basic_demos.py` defines fields styled with Bootstrap 5 using `TomSelectConfig`.

```python
class Bootstrap5StylingForm(forms.Form):
    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            css_framework="bootstrap5",
            placeholder="Select a value",
            highlight=True,
            open_on_focus=True,
            plugin_clear_button=PluginClearButton(
                title="Clear Selection", class_name="clear-button"
            ),
        ),
        attrs={"class": "form-control mb-3"},
        label="Single Select",
        help_text="Example of single select with Bootstrap 5 styling.",
    )
    # Additional fields omitted for brevity
```

- **Purpose**: Configures a `TomSelectModelChoiceField` with enhanced styling and behavior for single selections. It highlights the use of Bootstrap 5’s `form-control` class and interactivity plugins.

[See full code in the repository](#).

---

### Template
The `bs5.html` template extends a Bootstrap 5 base layout and ensures required styles and scripts are included.

```html
{% extends 'example/base_with_bootstrap5.html' %}

{% block extra_header %}
    {{ form.media }}
    <style>
        .helptext {
            font-size: 10px;
            color: #757575;
        }
    </style>
{% endblock %}

{% block content %}
    <div class="card">
        <div class="card-header">
            <h2>Bootstrap 5 Styling Demo</h2>
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

- **Purpose**: Renders the form fields with Bootstrap 5 styling, ensuring alignment with modern UI design practices.

[See full code in the repository](#).

---

### Autocomplete View
The backend for this example uses the same `AutocompleteModelView` as in the Bootstrap 4 example, adapted for the specific data model.

```python
class EditionAutocomplete(AutocompleteModelView):
    model = Edition  # Model to query
    search_lookups = ["name__icontains"]
    ordering = "name"
```

- **Purpose**: Handles autocomplete logic, including searching and ordering results for the dropdown.

[See full code in the repository](#).

---

## Design and Implementation Notes

### Key Features
- **Responsive Design**: Fully compatible with Bootstrap 5’s grid and component system, ensuring a seamless experience across devices.
- **Plugins for Usability**: Includes `clear_button`, `remove_button`, and `dropdown_header` plugins for enhanced interactivity.

### Design Decisions
- **Bootstrap 5**: Selected for its lightweight, responsive design and utility classes that simplify CSS management.
- **Customizable Behavior**: Used `TomSelectConfig` to fine-tune behavior, such as `open_on_focus` and `highlight`.

### Alternative Approaches
- Switch to Bootstrap 4 if legacy support is needed.
- Replace default plugins with custom implementations to match unique project requirements.

### Potential Extensions
- Add conditional dropdowns that update based on the selection of another field.
- Introduce headers or additional columns in the dropdown for richer data visualization.
