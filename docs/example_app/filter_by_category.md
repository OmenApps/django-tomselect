# Filter by Category

## Example Overview

- **Objective**: This example demonstrates the use of `django_tomselect` to create dependent dropdowns, where selecting a "Main Category" dynamically filters the options available in the "Subcategories" field. It highlights the package's ability to handle hierarchical relationships and improve user input accuracy.
  - **Problem Solved**: By dynamically filtering subcategories based on the selected main category, this example prevents user confusion and ensures meaningful relationships between the fields.
  - **Features Highlighted**:
    - Dynamic filtering of options using the `filter_by` parameter.
    - Integration with metadata-rich dropdowns using plugins like `DropdownHeader`.

- **Use Case**:
  - Categorizing content (e.g., articles, products, or documents) by main and subcategories.
  - Applications that require hierarchical selections, such as taxonomies or multi-level product filters.

- **Visual Elements**:
  *(Placeholders for images or GIFs)*:
  - `![Screenshot: Filter by Category](path-to-image)`
  - `![GIF: Subcategories Dynamic Filtering](path-to-gif)`

## Key Code Segments

### Forms
The form uses `TomSelectModelChoiceField` and `TomSelectModelMultipleChoiceField` for main categories and subcategories, respectively. The `subcategories` field is configured with the `filter_by` parameter.

```python
class FilterByCategoryForm(forms.Form):
    main_category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Category Selection"),
                extra_columns={
                    "parent_name": _("Parent"),
                    "direct_articles": _("Direct Articles"),
                    "total_articles": _("Total Articles"),
                },
            ),
        ),
    )

    subcategories = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="full_path",
            filter_by=("main_category", "parent_id"),
            css_framework="bootstrap5",
            placeholder=_("Select subcategories..."),
            highlight=True,
            plugin_remove_button=PluginRemoveButton(),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )
```

**Explanation**:
- The `filter_by` parameter dynamically restricts the subcategory options to those associated with the selected main category.
- The `DropdownHeader` plugin enriches the UI with additional metadata for categories.

**Repository Link**: [View FilterByCategoryForm Code](#)

### Templates
The template `filter_by_category.html` renders the form and highlights the cascading behavior of the dropdowns.

```html
<form>
    {% csrf_token %}
    {{ form.as_div }}
</form>
```

**Key Elements**:
- Uses Bootstrap 5 for consistent styling.
- Displays dynamic relationships between main categories and subcategories using JavaScript-enhanced dropdowns.

**Repository Link**: [View Template Code](#)

### Autocomplete Views
`autocomplete-category` provides data for both dropdowns. The backend logic ensures that subcategories are filtered based on the selected main category.

```python
class AutocompleteCategory(AutocompleteModelView):
    model = Category
    search_lookups = ["name__icontains"]
```

**Repository Link**: [View Autocomplete Code](#)

### Dependencies
- Models: A `Category` model with a self-referential relationship (e.g., `parent_id`) to enable hierarchy.
- Autocomplete URLs: Ensure `autocomplete-category` is correctly configured in the Django URLs.

## Design and Implementation Notes

- **Key Features**:
  - Use of `filter_by` to dynamically manage hierarchical relationships.
  - Enhanced dropdowns with metadata and UI plugins like `DropdownHeader` and `RemoveButton`.

- **Design Decisions**:
  - Subcategories are implemented as a `TomSelectModelMultipleChoiceField` to allow multi-selection.
  - Dropdowns use metadata like `Parent Name` and `Total Articles` for better context.

- **Alternative Approaches**:
  - Static dropdowns with all subcategories listed (less user-friendly for large datasets).
  - Separate AJAX calls to load subcategories dynamically (requires custom JavaScript).

- **Potential Extensions**:
  - Add a "Select All" option for subcategories.
  - Use an additional field to filter categories by type or level (e.g., root categories only).
