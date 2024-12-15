# Filter by Magazine

## Example Overview

- **Objective**: This example demonstrates how to create dependent dropdowns using `django_tomselect`. The goal is to filter available options in the "Edition" dropdown based on the selected "Magazine." This functionality ensures that users only see relevant data for their selection, streamlining workflows and minimizing input errors.
  - **Problem Solved**: Dynamically linking fields avoids presenting users with irrelevant or overwhelming options.
  - **Features Highlighted**:
    - Dynamic filtering of options using the `filter_by` parameter.
    - Integration with autocomplete backends for seamless user experience.

- **Use Case**:
  - Publishing systems where editions are linked to specific magazines.
  - Applications needing cascaded or conditional dropdown menus, such as location selectors or product configurations.

- **Visual Elements**:
  *(Placeholders for images or GIFs)*:
  - `![Screenshot: Filter by Magazine](path-to-image)`
  - `![GIF: Dynamic Filtering in Action](path-to-gif)`

## Key Code Segments

### Forms
This example uses `TomSelectModelChoiceField` for both `magazine` and `edition` fields in the form. The `edition` field is configured with the `filter_by` parameter to ensure it depends on the `magazine` selection.

```python
class FilterByMagazineForm(forms.Form):
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
            filter_by=("magazine", "magazine_id"),
            value_field="id",
            label_field="name",
            show_create=True,
            css_framework="bootstrap5",
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )
```
**Explanation**:
- The `filter_by` parameter in the `edition` field dynamically narrows down options based on the `magazine_id` of the selected magazine.

**Repository Link**: [View FilterByMagazineForm Code](#)

### Templates
The form is rendered in the `filter_by_magazine.html` template, ensuring the cascading effect is visually clear to users.

```html
<form>
    {% csrf_token %}
    {{ form.as_div }}
</form>
```

**Key Elements**:
- Uses Bootstrap 5 for consistent styling.
- Dynamically displays dropdown options using JavaScript integration with `django_tomselect`.

**Repository Link**: [View Template Code](#)

### Autocomplete Views
`autocomplete-magazine` and `autocomplete-edition` endpoints provide data for the dropdowns. These endpoints are backed by models and use `filter_by` logic to narrow results for the dependent field.

```python
class AutocompleteMagazine(AutocompleteModelView):
    model = Magazine
    search_lookups = ["name__icontains"]

class AutocompleteEdition(AutocompleteModelView):
    model = Edition
    search_lookups = ["name__icontains"]
```

**Repository Link**: [View Autocomplete Code](#)

### Dependencies
- Models: `Magazine` and `Edition` models must have a foreign key relationship to enable filtering.
- Autocomplete URLs: Ensure `autocomplete-magazine` and `autocomplete-edition` are correctly configured in the Django URLs.

## Design and Implementation Notes

- **Key Features**:
  - Dependency management through `filter_by`.
  - Smooth user experience with Tom Select’s enhanced dropdowns.
  - Ability to add new editions dynamically via the `show_create` plugin.

- **Design Decisions**:
  - Bootstrap 5 was chosen for styling due to its widespread adoption and simplicity.
  - Autocomplete views ensure scalability, even for large datasets.

- **Alternative Approaches**:
  - Manual JavaScript for filtering (less maintainable compared to `django_tomselect`).
  - Using preloaded dropdowns for small datasets.

- **Potential Extensions**:
  - Implement `exclude_by` for further refinements.
  - Add more metadata to options (e.g., publication dates or editors).
