# Custom Content Display

## Example Overview

- **Objective**: This example showcases how to customize the display of content in dropdown options and selected items using `django_tomselect`. It leverages custom rendering to present rich information, such as icons, metadata, and descriptions, making dropdowns more intuitive and visually engaging.
  - **Problem Solved**: Traditional dropdowns with plain text options can be limiting for complex applications. Custom content display enables a richer user experience by showing additional context for each option.
  - **Features Highlighted**:
    - Custom rendering of dropdown options and selected items.
    - Enhanced display with metadata, icons, and structured layouts.

- **Use Case**:
  - Applications that need dropdowns with detailed context, such as product selectors, user roles, or hierarchical data.
  - Scenarios requiring visual differentiation of options, like tags with usage counts or categories with icons.

- **Visual Elements**:
  *(Placeholders for images or GIFs)*:
  - `![Screenshot: Custom Option Display](path-to-image)`
  - `![GIF: Enhanced Dropdown Interaction](path-to-gif)`

## Key Code Segments

### Forms
Custom rendering is achieved using the `TomSelectConfig` attributes, such as `data_template_option` and `data_template_item`, to define how options and selected items should appear.

```python
class CustomContentForm(forms.Form):
    enriched_field = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-enriched-content",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            data_template_option="""
                <div class="custom-option">
                    <span class="option-icon" style="background-color: {{ color }};">●</span>
                    <span class="option-name">{{ name }}</span>
                    <span class="option-metadata">{{ metadata }}</span>
                </div>
            """,
            data_template_item="""
                <div class="custom-item">
                    <span class="item-icon" style="background-color: {{ color }};">●</span>
                    <span class="item-name">{{ name }}</span>
                </div>
            """,
            highlight=True,
        ),
        attrs={"class": "form-control mb-3"},
    )
```

**Explanation**:
- `data_template_option`: Defines how each dropdown option is rendered. For instance, it can include an icon and metadata.
- `data_template_item`: Defines how selected items are displayed after selection.
- Inline styling can be dynamically populated with values (e.g., `color`, `metadata`).

**Repository Link**: [View CustomContentForm Code](#)

### Templates
The dropdown rendering is handled seamlessly by the form widget, requiring no custom template changes.

For added styling, CSS classes and inline styles can be defined in the main template:

```html
<style>
    .custom-option {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .option-icon, .item-icon {
        display: inline-block;
        width: 16px;
        height: 16px;
        border-radius: 50%;
    }
    .option-metadata {
        font-size: 0.875rem;
        color: #6c757d;
    }
</style>

<form>
    {% csrf_token %}
    <div class="mb-3">
        {{ form.enriched_field }}
    </div>
    <button type="submit" class="btn btn-primary">Submit</button>
</form>
```

**Key Elements**:
- CSS classes like `.custom-option` are used to structure and style the dropdown options.
- Inline styles for dynamic customization, such as coloring icons based on `color` values from the backend.

**Repository Link**: [View Template Code](#)

### Autocomplete Views
The `autocomplete-enriched-content` endpoint provides the necessary data for the custom display.

```python
class AutocompleteEnrichedContent(AutocompleteModelView):
    model = EnrichedItem
    search_lookups = ["name__icontains"]
    value_fields = ["id", "name", "color", "metadata"]
```

**Explanation**:
- The `value_fields` attribute ensures that additional data (e.g., `color` and `metadata`) is included in the response for custom rendering.
- The endpoint dynamically generates JSON objects that populate the dropdown.

**Repository Link**: [View Autocomplete Code](#)

### Dependencies
- Models: An `EnrichedItem` model with fields like `name`, `color`, and `metadata`.
- Autocomplete URLs: Ensure `autocomplete-enriched-content` is correctly set up in your Django project.

## Design and Implementation Notes

- **Key Features**:
  - Flexible customization of dropdowns with metadata and icons.
  - Separation of concerns by defining rendering logic directly in the `TomSelectConfig`.

- **Design Decisions**:
  - Custom templates for options and items ensure a better user experience for complex data types.
  - Metadata like `color` and `metadata` enriches the visual presentation without impacting functionality.

- **Alternative Approaches**:
  - Use custom JavaScript templates for rendering (adds complexity but allows for greater control).
  - Implement static dropdowns with predefined options (less dynamic).

- **Potential Extensions**:
  - Add group headers to the dropdown using the `optgroup` feature in `TomSelect`.
  - Enable filtering based on metadata (e.g., only show items with a specific `metadata` value).
