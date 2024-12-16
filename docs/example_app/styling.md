# Styling Demos

## Example Overview

This example demonstrates the use of `django_tomselect` with Default, Bootstrap 4, and Bootstrap 5 styling to create responsive, dynamic `<select>` fields. The example includes various configurations for single and multiple selections, highlighting the integration with a modern CSS framework.

### What problem does it solve?
This setup simplifies the creation of user-friendly, visually appealing dropdowns with advanced features like:
- Autocomplete.
- Placeholder text.
- Tabular dropdown headers.
- Options for creating and managing items directly from the dropdown.

### Key features highlighted:
- Single and multiple select fields with Bootstrap 4 styling.
- Server-side autocomplete with configurable behavior.

**Visual Examples**

![Screenshot: Single Selection](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/Single.png)
![Screenshot: Multiple Selection with Tabular Display](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/Multiple_Tabular.png)

---

## Key Code Segments

### Forms
The `DefaultStylingForm`, `Bootstrap4StylingForm`, and `Bootstrap5StylingForm` in `forms/basic_demos.py` configures fields using `TomSelectConfig` for the prefered styling.

:::{admonition} Default Styling
:class: dropdown

```python
class Bootstrap4StylingForm(forms.Form):
    tomselect = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            css_framework="bootstrap4",  # <<-- Bootstrap 4 styling
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
:::


- **Purpose**: This sets up a dropdown with an autocomplete endpoint (`url`), styling with preferred style, and a clear button plugin.

---

### Template
The `default.html`. `bs4.html`, and `bs5.html` templates render the form using the specified styling. They extend the base layout and include the necessary CSS and JavaScript assets.

:::{admonition} Template
:class: dropdown

```html
{% extends 'example/base_with_bootstrap4.html' %}

{% block extra_header %}
    {{ form.media }}
    <style>
        .helptext {
            font-size: 10px;
            color: #757575;
        }

        /* Override the default form label color to white */
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
            <div class="pb-5">This page demonstrates four different configurations for the django_tomselect form fields using Bootstrap 4 styling.</div>
            <form>
                {% csrf_token %}
                {{ form.as_div }}
            </form>
        </div>
    </div>
{% endblock %}

```
:::

---

### Autocomplete View
The autocomplete functionality is defined in the `autocompletes.py` file using `AutocompleteModelView`.

- Here, we use `skip_authorization` to bypass the default authorization checks for demonstration purposes.
- Any searches will use the `name` field of the `Edition` model.
- The `page_size` parameter sets the number of results to return per page.
- The `value_fields` parameter specifies the fields to return in the response.
- The `list_url`, `create_url`, `update_url`, and `delete_url` parameters are the url names for the respective views, if available.

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

- **Purpose**: Provides the backend logic for fetching autocomplete results, with filtering and ordering.

---

### Views
We use standard Django views to render the form.

:::{admonition} View for Bootstrap 4 Demo
:class: dropdown

```python
def bootstrap4_demo(request: HttpRequest) -> HttpResponse:
    """View for the Bootstrap 4 demo page."""
    template = "example/basic_demos/bs4.html"
    context = {}

    context["form"] = Bootstrap4StylingForm()
    return TemplateResponse(request, template, context)
```
:::

---

## Design and Implementation Notes

### Key Features
- **Dynamic styling**: Uses the preferred styling.
- **Plugins**: Includes plugins like `clear_button` and `dropdown_footer` to enhance UX.

### Alternative Approaches
- Use the "default" styling if Bootstrap is not integrated into the project.
- Use additional plugins like `dropdown_footer` to add create and list buttons directly in the dropdown.

### Potential Extensions
- Add dependent dropdowns where one field’s options are filtered based on another field’s selection.
