# 3-Level Filter-By Example

## Example Overview

The "3-Level Filter-By" example demonstrates how to use `django_tomselect` to implement a hierarchical selection process, where options at one level depend on the user's choice in the previous level. This is ideal for use cases like selecting regions, countries, and local markets, where each level dynamically filters based on the prior selection.

**Objective**:
- To showcase a multi-tiered filtering process in forms using `TomSelectModelChoiceField`.
- Demonstrates the power of `django_tomselect` plugins like `PluginDropdownHeader` for organizing data.

**Use Case**:
- Content publishing platforms selecting publishing regions, countries, and local markets.
- Applications that require dependent dropdowns like car make → model → trim selection.

**Visual Examples**

![Screenshot: 3-Level Filter-By](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/three-level-filter-by.png)

---

## Key Code Segments

### Forms
The form leverages `TomSelectModelChoiceField` to define hierarchical filtering.

:::{admonition} Form Definition
:class: dropdown

```python
class MarketSelectionForm(forms.Form):
    """Form for selecting publishing markets in a three-level hierarchy."""

    region = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-region",
            value_field="id",
            label_field="name",
            placeholder="Select region...",
            highlight=True,
            preload="focus",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Publishing Regions",
                extra_columns={
                    "total_markets": "Markets",
                    "aggregated_readers": "Potential Readers (M)",
                    "aggregated_publications": "Active Publications",
                },
            ),
        ),
        required=True,
    )

    country = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-country",
            value_field="id",
            label_field="name",
            filter_by=("region", "parent_id"),
            placeholder="Select country...",
            highlight=True,
            plugin_dropdown_header=PluginDropdownHeader(
                title="Countries",
                extra_columns={
                    "total_local_markets": "Local Markets",
                    "total_reader_base": "Potential Readers (M)",
                    "total_pub_count": "Publications",
                },
            ),
        ),
        required=False,
    )

    local_market = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-local-market",
            value_field="id",
            label_field="name",
            filter_by=("country", "parent_id"),
            placeholder="Select local market...",
            highlight=True,
            plugin_dropdown_header=PluginDropdownHeader(
                title="Local Markets",
                extra_columns={
                    "market_size": "Potential Readers (M)",
                    "active_publications": "Active Publications",
                },
            ),
        ),
        required=False,
    )
```
:::

---

### Templates
The form fields are rendered dynamically in the template.

:::{admonition} Template Code
:class: dropdown

```html
{% extends 'example/base_with_bootstrap5.html' %}

{% block extra_header %}
    {{ form.media }}
    <style>
        .helptext {
            font-size: 12px;
            color: #6c757d;
        }
        .market-container {
            max-width: 600px;
            margin: 20px auto;
        }
    </style>
{% endblock %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h2>Publishing Market Selection</h2>
    </div>
    <div class="card-body">
        <div class="pb-3">
            <p>This example demonstrates a three-level geographic market hierarchy for international publishing operations:</p>
            <ul>
                <li>Regions show total market size and publication counts across all countries</li>
                <li>Countries display number of local markets and aggregated market metrics</li>
                <li>Local markets show specific market size and active publication counts</li>
                <li>Each level provides relevant publishing metrics in the header for market analysis</li>
            </ul>
        </div>

        <div class="market-container">
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label for="{{ form.region.id_for_label }}" class="form-label">Publishing Region</label>
                    {{ form.region }}
                    <div class="helptext">Major geographic regions (e.g., North America, Europe, Asia Pacific)</div>
                </div>

                <div class="mb-3">
                    <label for="{{ form.country.id_for_label }}" class="form-label">Country</label>
                    {{ form.country }}
                    <div class="helptext">Countries within the selected region</div>
                </div>

                <div class="mb-3">
                    <label for="{{ form.local_market.id_for_label }}" class="form-label">Local Market</label>
                    {{ form.local_market }}
                    <div class="helptext">Specific city or market area with active publishing operations</div>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```
:::

---

### Autocomplete Views
Dynamic filtering logic is handled by autocomplete endpoints in the backend.

:::{admonition} Autocomplete Views
:class: dropdown

```python
class PublishingMarket(models.Model):
    """Represents geographic markets for publishing operations.

    Creates a three-level hierarchy: Region -> Country -> City/Market
    """

    name = models.CharField(
        max_length=100,
        help_text="Name of the market. Either a region, country, or city/market.",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    market_size = models.IntegerField(
        default=0,
        help_text="Market size in millions of potential readers",
    )
    active_publications = models.IntegerField(
        default=0,
        help_text="Number of active publications in this market",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for the model."""

        ordering = ["name"]
        verbose_name = "Publishing Market"
        verbose_name_plural = "Publishing Markets"

    def __str__(self):
        return self.name
```
:::

---

## Design and Implementation Notes

### Key Features
- **Dynamic Filtering**: Each dropdown is filtered based on the selected value of the parent dropdown. Trying to select a country without a region will show an empty list. Likewise, trying to select a local market without a country will also show an empty list.
- **Header Customization**: `PluginDropdownHeader` adds informative headers with columns like "Potential Readers" and "Markets."

### Design Decisions
- Using hierarchical filtering ensures scalability for large datasets without loading all options at once.
- Plugin configurations like `extra_columns` enhance the dropdown's usability by providing rich, tabular data.
