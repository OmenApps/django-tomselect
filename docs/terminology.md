# Terminology and Definitions

## Core Concepts

### Tom Select Terms

- **[Tom Select](https://tom-select.js.org/)**: A vanilla JavaScript library that transforms native `<select>` elements into powerful, dynamic selection controls with features like searching, tagging, and remote data loading.

- **Dropdown**: The popup menu that displays available options when the control is clicked or receives focus.

- **Item**: A selected value in the control. In single-select mode, there can only be one item. In multi-select mode, there can be multiple items.

- **Option**: An individual choice in the dropdown that can be selected. Options are rendered from your data source.

### Field and View Types

- **TomSelectModelChoiceField**: A Django form field for single-selection of model instances, replacing Django's standard `ModelChoiceField`.

- **TomSelectModelMultipleChoiceField**: Similar to TomSelectModelChoiceField but allows selection of multiple model instances.

- **TomSelectChoiceField**: A field for single-selection from static choices or iterables (not tied to Django models).

- **TomSelectMultipleChoiceField**: Similar to TomSelectChoiceField but allows multiple selections.

- **Autocomplete View**: A Django view that handles search requests and returns filtered results to Tom Select. Base classes:
  - **AutocompleteModelView**: For Django model-based lookups
  - **AutocompleteIterablesView**: For choices and iterables-based lookups

### Configuration Components

- **Plugin**: A module that adds specific functionality to Tom Select. Our package includes several built-in plugins:
  - **CheckboxOptions**: Adds checkboxes to options in the dropdown
  - **DropdownHeader**: Adds a header to the dropdown, often used for tabular displays
  - **DropdownFooter**: Adds a footer to the dropdown
  - **ClearButton**: Adds a button to clear all selections
  - **RemoveButton**: Adds buttons to remove individual selections
  - **DropdownInput**: Adds an input field in the dropdown for filtering

## Field Configuration

- **value_field**: The model field used for the actual value stored by the form (often 'id')
- **label_field**: The model field used for displaying options to users (often 'name' or 'title')
- **search_lookups**: List of Django field lookups used for filtering results (e.g., ["name__icontains"])

## Common Terms

- **Tabular Display**: A mode where dropdown options are shown in a table format with multiple columns.

- **Dependent/Chained Fields**: Form fields whose available options depend on the value selected in another field.

- **Pagination**: The process of loading results in chunks as the user scrolls, rather than all at once.

- **Search Throttling**: Limiting how frequently search requests are sent to the server while typing.

## Notes

For more detailed information about any of these terms, please refer to:
- [Tom Select Documentation](https://tom-select.js.org/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Django TomSelect Documentation](https://django-tomselect.readthedocs.io/en/latest/usage.html)
