# 3-Level Filter-By Example

## Example Overview

The "3-Level Filter-By" example demonstrates how to use `django_tomselect` to implement a hierarchical selection process, where options at one level depend on the user's choice in the previous level. This is ideal for use cases like selecting regions, countries, and local markets, where each level dynamically filters based on the prior selection.

**Objective**:
- To showcase a multi-tiered filtering process in forms using `TomSelectModelChoiceField`.
- Demonstrates the power of `django_tomselect` plugins like `PluginDropdownHeader` for organizing data.

**Use Case**:
- Content publishing platforms selecting publishing regions, countries, and local markets.
- Applications that require dependent dropdowns like car make → model → trim selection.

**Visual Examples** *(Placeholders)*:
- `![Screenshot: 3-Level Filter-By Dropdown](path-to-image)`
- `![GIF: 3-Level Filtering in Action](path-to-gif)`

---

## Key Code Segments

### Forms
The form leverages `TomSelectModelChoiceField` to define hierarchical filtering.

```python
class MarketSelectionForm(forms.Form):
    region = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-region",
            value_field="id",
            label_field="name",
            placeholder="Select region...",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Publishing Regions",
                extra_columns={
                    "total_markets": "Markets",
                    "aggregated_readers": "Potential Readers (M)",
                },
            ),
        ),
        required=True,
    )

    country = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-country",
            filter_by=("region", "parent_id"),
            placeholder="Select country...",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Countries",
                extra_columns={"total_local_markets": "Markets"},
            ),
        ),
        required=False,
    )

    local_market = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-local-market",
            filter_by=("country", "parent_id"),
            placeholder="Select local market...",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Local Markets",
                extra_columns={"market_size": "Size (M)"},
            ),
        ),
        required=False,
    )
```
[View Full Code in Repository](#)

---

### Templates
The form fields are rendered dynamically in the template.

```html
<form method="post">
    {% csrf_token %}
    <div>
        <label for="{{ form.region.id_for_label }}">{{ form.region.label }}</label>
        {{ form.region }}
    </div>
    <div>
        <label for="{{ form.country.id_for_label }}">{{ form.country.label }}</label>
        {{ form.country }}
    </div>
    <div>
        <label for="{{ form.local_market.id_for_label }}">{{ form.local_market.label }}</label>
        {{ form.local_market }}
    </div>
    <button type="submit">Submit</button>
</form>
```

---

### Autocomplete Views
Dynamic filtering logic is handled by autocomplete endpoints in the backend.

```python
class AutocompleteRegionView(AutocompleteModelView):
    model = Region
    search_lookups = ["name__icontains"]

class AutocompleteCountryView(AutocompleteModelView):
    model = Country
    filter_by = ("region", "parent_id")

class AutocompleteLocalMarketView(AutocompleteModelView):
    model = LocalMarket
    filter_by = ("country", "parent_id")
```
[View Full Code in Repository](#)

---

## Design and Implementation Notes

### Key Features
- **Dynamic Filtering**: Each dropdown is filtered based on the selected value of the parent dropdown.
- **Header Customization**: `PluginDropdownHeader` adds informative headers with columns like "Potential Readers" or "Markets."
- **Autocomplete Optimization**: Preloads suggestions as the user focuses on the dropdown.

### Design Decisions
- Using hierarchical filtering ensures scalability for large datasets without loading all options at once.
- Plugin configurations like `extra_columns` enhance the dropdown's usability by providing rich, tabular data.

### Alternative Approaches
- Implementing similar functionality with JavaScript-only libraries like Select2 but losing Django integration.
- Using `django_filters` for server-side filtering, though it requires page reloads.

### Potential Extensions
- Adding real-time search for each dropdown level.
- Enabling batch selection for markets or regions via checkboxes.
