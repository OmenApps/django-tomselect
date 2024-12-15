# View Range-based Data

## Example Overview

- **Objective**: This example demonstrates how to implement dynamic range-based data selection with a live preview visualization. Users can select a range (e.g., word count) and instantly see data distributions, such as the number of articles within the selected range. The integration with `django_tomselect` ensures a smooth user experience with enhanced dropdowns.
  - **Problem Solved**: It enables users to interactively select ranges and see associated data without requiring a page reload, improving data exploration and decision-making workflows.
  - **Features Highlighted**:
    - Dynamic range selection with `TomSelectChoiceField`.
    - Live data preview updates using HTMX.

- **Use Case**:
  - Applications requiring interactive filtering and visualization, such as analytics dashboards or content management systems.
  - Scenarios where users need to select ranges dynamically, such as price filters, date ranges, or statistical data bins.

- **Visual Elements**:
  *(Placeholders for images or GIFs)*:
  - `![Screenshot: Range Selection](path-to-image)`
  - `![GIF: Live Range Preview](path-to-gif)`

## Key Code Segments

### Forms
The form uses `TomSelectChoiceField` to allow users to select a range dynamically.

```python
class RangePreviewForm(forms.Form):
    word_count = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-page-count-range",
            value_field="value",
            label_field="label",
            css_framework="bootstrap5",
            placeholder="Select a word count range...",
            preload="focus",
            highlight=True,
            minimum_query_length=0,
        ),
        help_text="Select a word count range to see distribution visualization",
    )
```

**Explanation**:
- The `word_count` field is configured with a `TomSelectConfig` object that connects to an autocomplete endpoint and allows range selection.
- The `highlight` parameter ensures the selected range is visually prominent.

**Repository Link**: [View RangePreviewForm Code](#)

### Templates
The form is rendered in the `range_preview.html` template, where HTMX is used to update the preview dynamically based on the selected range.

```html
<form>
    {% csrf_token %}
    <div class="mb-4">
        {{ form.word_count }}
        {% if form.word_count.help_text %}
            <div class="helptext">{{ form.word_count.help_text }}</div>
        {% endif %}
    </div>
</form>

<div class="preview-container mt-4"
     id="preview-container"
     hx-get="{% url 'update-range-preview' %}"
     hx-trigger="change from:#id_word_count"
     hx-target="#preview-container"
     hx-include="#id_word_count"
     hx-swap="innerHTML">
</div>
```

**Key Elements**:
- HTMX attributes (`hx-get`, `hx-trigger`, etc.) dynamically update the preview container when a new range is selected.
- Clean Bootstrap 5 styling for consistency and usability.

**Repository Link**: [View Template Code](#)

### HTMX Endpoint for Preview Updates
The `update-range-preview` endpoint processes the selected range and returns the updated data visualization.

```python
from django.template.loader import render_to_string
from django.http import JsonResponse

def update_range_preview(request):
    selected_range = request.GET.get("word_count", None)
    data = generate_preview_data(selected_range)  # Replace with actual logic
    html = render_to_string("example/intermediate_demos/range_preview_bars.html", {"data": data})
    return JsonResponse({"html": html})
```

**Repository Link**: [View HTMX Endpoint Code](#)

### Autocomplete Views
The `autocomplete-page-count-range` endpoint serves the dropdown options for word count ranges.

```python
class AutocompletePageCountRange(AutocompleteModelView):
    model = WordCountRange
    search_lookups = ["label__icontains"]
```

**Repository Link**: [View Autocomplete Code](#)

### Dependencies
- Models: A `WordCountRange` model that defines range bins (e.g., "0-500 words").
- Autocomplete URLs: Ensure `autocomplete-page-count-range` and `update-range-preview` are correctly configured.

## Design and Implementation Notes

- **Key Features**:
  - Integration with HTMX for dynamic, AJAX-based updates.
  - `TomSelectChoiceField` enables a smooth user experience for range selection.

- **Design Decisions**:
  - Using HTMX reduces the complexity of JavaScript for dynamic updates.
  - The `TomSelectConfig` is optimized for minimal query length (`minimum_query_length=0`) to display all available ranges on focus.

- **Alternative Approaches**:
  - Use a custom JavaScript function to update the preview container (less maintainable compared to HTMX).
  - Preload all range data and render the visualization statically (less dynamic and responsive).

- **Potential Extensions**:
  - Add filters for other metrics (e.g., publication date or author popularity).
  - Include summary statistics or additional charts alongside the range preview.
