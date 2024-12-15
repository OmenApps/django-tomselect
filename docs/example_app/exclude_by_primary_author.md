# Exclude by Primary Author

## Example Overview

- **Objective**: This example showcases how to dynamically exclude certain options in one field based on the selection in another field using `django_tomselect`. Specifically, the "Contributing Authors" field excludes the "Primary Author" selection to prevent redundant choices.
  - **Problem Solved**: It ensures that users cannot accidentally select the same person as both a primary and contributing author, maintaining data integrity and logical consistency.
  - **Features Highlighted**:
    - Dynamic exclusion of options using the `exclude_by` parameter.
    - Seamless integration with backend autocomplete views.

- **Use Case**:
  - Assigning roles to users where overlapping responsibilities are invalid (e.g., primary and secondary roles in a project).
  - Preventing duplicate selections in multi-step forms or hierarchical data inputs.

- **Visual Elements**:
  *(Placeholders for images or GIFs)*:
  - `![Screenshot: Exclude by Primary Author](path-to-image)`
  - `![GIF: Dynamic Exclusion in Action](path-to-gif)`

## Key Code Segments

### Forms
The form uses `TomSelectModelChoiceField` for the "Primary Author" and `TomSelectModelMultipleChoiceField` for "Contributing Authors". The `exclude_by` parameter ensures contributing authors exclude the selected primary author.

```python
class ExcludeByPrimaryAuthorForm(forms.Form):
    primary_author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
        ),
    )

    contributing_authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),
            css_framework="bootstrap5",
            placeholder=_("Select contributing authors..."),
            highlight=True,
            plugin_remove_button=PluginRemoveButton(),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )
```

**Explanation**:
- The `exclude_by` parameter in the `contributing_authors` field ensures that any selected "Primary Author" is removed from the available options in the "Contributing Authors" field.
- The `RemoveButton` plugin improves user interaction by enabling quick removal of selected contributing authors.

**Repository Link**: [View ExcludeByPrimaryAuthorForm Code](#)

### Templates
The form is rendered in the `exclude_by.html` template, highlighting the exclusion mechanism between the two fields.

```html
<form>
    {% csrf_token %}
    {{ form.as_div }}
</form>
```

**Key Elements**:
- Bootstrap 5 for clean and modern styling.
- The exclusion logic is visually reflected in the dropdowns as selections are made.

**Repository Link**: [View Template Code](#)

### Autocomplete Views
The `autocomplete-author` endpoint serves data for both fields, ensuring proper exclusion logic based on the `exclude_by` parameter.

```python
class AutocompleteAuthor(AutocompleteModelView):
    model = Author
    search_lookups = ["name__icontains"]
```

**Repository Link**: [View Autocomplete Code](#)

### Dependencies
- Models: An `Author` model is required for the autocomplete functionality.
- Autocomplete URLs: Ensure `autocomplete-author` is correctly defined in your URLs.

## Design and Implementation Notes

- **Key Features**:
  - Dynamic exclusion using `exclude_by`.
  - Multi-select functionality for the "Contributing Authors" field with the `RemoveButton` plugin.

- **Design Decisions**:
  - Chose `TomSelectModelMultipleChoiceField` for contributing authors to allow multi-selection.
  - The `exclude_by` parameter ensures clean and efficient backend filtering without additional custom JavaScript.

- **Alternative Approaches**:
  - Implement exclusion logic entirely in JavaScript (requires more maintenance and testing).
  - Use a dedicated autocomplete view to pre-filter contributing authors server-side.

- **Potential Extensions**:
  - Add metadata to the dropdown options, such as the number of articles authored.
  - Extend the exclusion logic to handle multiple fields (e.g., exclude all team leads from a team member selection).
