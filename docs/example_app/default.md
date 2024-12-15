# Default Styling Demo

## Example Overview

This example showcases how to use `django_tomselect` without relying on any external CSS frameworks. It focuses on the native styling provided by the browser, ensuring lightweight and straightforward integration. The example highlights the flexibility of `django_tomselect` in environments where custom or minimal styling is preferred.

### What problem does it solve?
This setup is ideal for projects that:
- Do not require Bootstrap or other CSS frameworks.
- Prioritize a clean, simple, and framework-agnostic approach.
- Need a lightweight alternative for dropdown and autocomplete functionalities.

### Key features highlighted:
- Single and multiple select fields with default browser styling.
- Plugins for enhanced interactivity, such as dropdown headers and clear buttons.

### Use Case Scenarios:
- Internal tools or admin panels without custom UI requirements.
- Projects aiming for performance optimization by avoiding CSS frameworks.
- Minimalist applications where the UI relies on native browser styles.

*(Placeholders for screenshots or GIFs)*:
- `![Screenshot: Default Dropdown Styling](path-to-image)`
- `![GIF: Default Autocomplete Behavior](path-to-gif)`

---

## Key Code Segments

### Forms
The `DefaultStylingForm` in `basic_demos.py` defines fields styled with the default configuration.

```python
class DefaultStylingForm(forms.Form):
    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            css_framework="default",
            placeholder="Select a value",
            highlight=True,
            open_on_focus=True,
            plugin_clear_button=PluginClearButton(
                title="Clear Selection", class_name="clear-button"
            ),
        ),
        attrs={"id": "tomselect-custom-id"},
        label="Single Select",
        help_text="Example of single select with default styling.",
    )
    # Additional fields omitted for brevity
```

- **Purpose**: Defines a `TomSelectModelChoiceField` with default styling, demonstrating the flexibility of `django_tomselect`.

[See full code in the repository](#).

---

### Template
The `default.html` template extends a base layout and renders the form using the default CSS framework.

```html
{% extends 'example/base_with_default.html' %}

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
    <h2>Default Styling Demo</h2>
    <div>This page demonstrates four different configurations for the `django_tomselect` form fields with default styling.</div>
    <br>
    <form>
        {% csrf_token %}
        {{ form.as_div }}
    </form>
{% endblock %}
```

- **Purpose**: Illustrates how to render the form and media with minimal dependencies.

[See full code in the repository](#).

---

### Autocomplete View
The autocomplete logic is implemented similarly to the Bootstrap examples, ensuring consistent functionality across styling options.

```python
class EditionAutocomplete(AutocompleteModelView):
    model = Edition  # Model to query
    search_lookups = ["name__icontains"]
    ordering = "name"
```

- **Purpose**: Provides backend logic for fetching and filtering dropdown options dynamically.

[See full code in the repository](#).

---

## Design and Implementation Notes

### Key Features
- **Lightweight**: Uses native browser styling, eliminating dependency on external frameworks.
- **Plugins**: Enhances usability with plugins like `clear_button` and `dropdown_footer`.

### Design Decisions
- **Framework-agnostic**: Default styling is perfect for projects without a dedicated CSS framework.
- **Customizable**: Developers can add custom CSS rules as needed for their specific requirements.

### Alternative Approaches
- Introduce a lightweight CSS library if some additional styling is required.
- Transition to Bootstrap 4 or 5 styling for projects that need more robust design frameworks.

### Potential Extensions
- Add custom dropdown headers to display metadata alongside options.
- Implement dependent dropdowns where one field’s options depend on another field’s selection.
