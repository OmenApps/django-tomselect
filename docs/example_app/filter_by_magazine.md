# Filter-By Magazine

## Example Overview

- **Objective**: This example demonstrates how to create dependent dropdowns using `django_tomselect`. The goal is to filter available options in the "Edition" dropdown based on the selected "Magazine." If not magazine is selected, the "Edition" dropdown remains empty. If a magazine is selected, the "Edition" dropdown will only show editions linked to that magazine.
  - **Problem Solved**: Dynamically linking fields avoids presenting users with irrelevant or overwhelming options.
  - **Features Highlighted**:
    - Dynamic filtering of options using the `filter_by` parameter.

- **Use Case**:
  - Publishing systems where editions are linked to specific magazines.
  - Applications needing cascaded or conditional dropdown menus, such as location selectors or product configurations.
  - User interfaces requiring a clean and intuitive way to manage interdependent fields.

**Visual Examples**

![Screenshot: Filter-By Magazine](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/filter-by-magazine.png)

## Key Code Segments

### Forms
This example uses `TomSelectModelChoiceField` for both `magazine` and `edition` fields in the form. The `edition` field is configured with the `filter_by` parameter to ensure it depends on the `magazine` selection.

:::{admonition} Form Definition
:class: dropdown

```python
class FilterByMagazineForm(forms.Form):
    """Form with dependent fields demonstrating filter_by functionality."""

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
        ),
    )

    edition = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),
            css_framework="bootstrap5",
            plugin_dropdown_footer=PluginDropdownFooter(),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )
```
:::

**Explanation**:
- The `filter_by` parameter in the `edition` field dynamically narrows down options based on the `magazine_id` of the selected magazine.

### Templates
The form is rendered in the `filter_by_magazine.html` template, which extends a base template with Bootstrap 5 integration. The `extra_header` block includes the form media and custom CSS for styling the help text.

:::{admonition} Template Code
:class: dropdown

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
            <h2>Filter-By Magazine Demo</h2>
        </div>
        <div class="card-body">
            <div class="pb-5">
                This page demonstrates how to filter available options based on the selected value of another, related field.
                In this case, the options for Edition are limited to those associated with the selected Magazine.
            </div>
            <form>
                {% csrf_token %}
                {{ form.as_div }}
            </form>
        </div>
    </div>
{% endblock %}
```
:::

**Key Elements**:
- Uses Bootstrap 5 for consistent styling.
- Dynamically displays dropdown options using JavaScript integration with `django_tomselect`.


### Autocomplete Views
`autocomplete-magazine` and `autocomplete-edition` endpoints provide data for the dropdowns. These endpoints are backed by models and use `filter_by` logic to narrow results for the dependent field.

Note that we use `skip_authorization = True` to bypass the default authorization checks for simplicity in this example.

:::{admonition} Autocomplete Views
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


class MagazineAutocompleteView(AutocompleteModelView):
    """Autocomplete that returns all Magazine objects."""

    model = Magazine
    search_lookups = ["name__icontains"]
    value_fields = ["id", "name", "accepts_new_articles"]

    list_url = "magazine-list"
    create_url = "magazine-create"
    update_url = "magazine-update"
    delete_url = "magazine-delete"

    skip_authorization = True
```
:::

### Dependencies
- Models: `Magazine` and `Edition` models must have a foreign key relationship to enable filtering.
- URLs: Autocomplete views must be registered in the URL configuration.

## Design and Implementation Notes

- **Key Features**:
  - Dependency management through `filter_by`.

See the Article List and Create example for a more comprehensive demonstration, which includes this functionality.
