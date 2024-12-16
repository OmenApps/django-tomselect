# Filter-By Category

## Example Overview

- **Objective**: This example demonstrates the use of `django_tomselect` to create dependent dropdowns, where selecting a "Main Category" dynamically filters the options available in the "Subcategories" field. Subcategories will only be loaded when a main category with no parent is selected.
  - **Features Highlighted**:
    - Dynamic filtering of options using the `filter_by` parameter.
    - Integration with metadata-rich dropdowns using plugins like `PluginDropdownHeader`.

- **Use Case**:
  - Categorizing content (e.g., articles, products, or documents) by main and subcategories.
  - Applications that require hierarchical selections, such as taxonomies or multi-level product filters.

**Visual Examples**

![Screenshot: Filter-By Category](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/filter-by-category.png)

## Key Code Segments

### Forms
The form uses `TomSelectModelChoiceField` and `TomSelectModelMultipleChoiceField` for main categories and subcategories, respectively. The `subcategories` field is configured with the `filter_by` parameter.

:::{admonition} Form Definition
:class: dropdown

```python
category_header = PluginDropdownHeader(
    title=_("Category Selection"),
    show_value_field=False,
    extra_columns={
        "parent_name": _("Parent"),
        "direct_articles": _("Direct Articles"),
        "total_articles": _("Total Articles"),
    },
)

class FilterByCategoryForm(forms.Form):
    """Form with dependent fields demonstrating filter_by functionality."""

    main_category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            plugin_dropdown_header=category_header,
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
            max_items=None,
            plugin_remove_button=PluginRemoveButton(),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )
```
:::

**Explanation**:
- The `filter_by` parameter dynamically restricts the subcategory options to those associated with the selected main category.
- The `PluginDropdownHeader` plugin enriches the UI with additional metadata for categories.
- The `PluginRemoveButton` plugin allows users to quickly remove all selected subcategories at once.

### Templates
The template `filter_by_category.html` renders the form and highlights the cascading behavior of the dropdowns.

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
            <h2>Filter-By Category Demo</h2>
        </div>
        <div class="card-body">
            <div class="pb-5">
                This page demonstrates how to filter available options based on the selected value of another, related field.
                In this case, the options for Subcategory are limited to those associated with the selected Category.
                Unless a 'parent' type Category is selected, the Subcategory field will be empty of options.
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

### Autocomplete Views
`autocomplete-category` provides data for both dropdowns. The backend logic ensures that subcategories are filtered based on the selected main category.

A few key points:

- We override the `hook_queryset` method to annotate the queryset with parent information and article counts (see the manager method `with_header_data`).
- The `hook_prepare_results` method formats the results with hierarchy information and additional metadata.
- We enhance the search method to look through the full hierarchy, including category names, parent names, and full hierarchical paths.

As with most of the example app examples, we set `skip_authorization = True` to bypass the default authorization checks for simplicity.

:::{admonition} Autocomplete View
:class: dropdown

```python
class CategoryAutocompleteView(AutocompleteModelView):
    """Autocomplete view for Category model with hierarchical support."""

    model = Category
    search_lookups = [
        "name__icontains",
        "parent__name__icontains",
    ]
    ordering = ["name"]
    page_size = 20
    value_fields = [
        "id",
        "name",
        "parent_id",
        "parent_name",
        "full_path",
        "direct_articles",
        "total_articles",
    ]

    create_url = "category-create"
    update_url = "category-update"
    delete_url = "category-delete"

    skip_authorization = True

    def hook_queryset(self, queryset):
        """Annotate the queryset with parent information and article counts."""
        return queryset.with_header_data()

    def get_queryset(self):
        """Return a queryset of categories with parent information and article counts.

        Annotates:
        - Full hierarchical path
        - Parent category name
        - Number of direct articles
        - Number of articles including subcategories
        """
        queryset = super().get_queryset().distinct()  # Add distinct to base queryset

        # Filter by parent if specified
        parent_id = self.request.GET.get("parent")
        if parent_id:
            if parent_id == "root":
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)

        # Filter by depth level if specified
        depth = self.request.GET.get("depth")
        if depth == "root":
            queryset = queryset.filter(parent__isnull=True)
        elif depth == "children":
            queryset = queryset.filter(parent__isnull=False)

        return queryset

    def hook_prepare_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format results with hierarchy information.

        Adds:
        - formatted_name (includes hierarchical information)
        - full_path (corrected if parent is missing)
        - is_root (based on parent_id)
        """
        formatted_results = []
        for category in results:
            # Create the formatted name
            formatted_name = category["name"]
            if category["parent_name"]:
                formatted_name = f"{category['parent_name']} → {category['name']}"

            # Add all required data
            formatted_result = {
                "id": category["id"],
                "name": category["name"],
                "parent_name": category["parent_name"],
                "full_path": (category["full_path"] if category["parent_name"] else category["name"]),
                "direct_articles": category["direct_articles"],
                "total_articles": category["total_articles"],
                "is_root": category["parent_id"] is None,
                "formatted_name": formatted_name,
                "update_url": category.get("update_url", None),
                "delete_url": category.get("delete_url", None),
            }
            formatted_results.append(formatted_result)

        return formatted_results

    def search(self, queryset: QuerySet, query: str) -> QuerySet:
        """Enhanced search that looks through the full hierarchy.

        Searches:
        - Category name
        - Parent category name
        - Full hierarchical path
        """
        if not query:
            return queryset

        q_objects = Q()
        for lookup in self.search_lookups:
            q_objects |= Q(**{lookup: query})

        # Add search in full path
        q_objects |= Q(full_path__icontains=query)

        return queryset.filter(q_objects)
```
:::

## Design and Implementation Notes

- **Key Features**:
  - Use of `filter_by` to dynamically manage hierarchical relationships.
  - Enhanced dropdowns with metadata and UI plugins like `PluginDropdownHeader` and `PluginRemoveButton`.

- **Design Decisions**:
  - Subcategories are implemented as a `TomSelectModelMultipleChoiceField` to allow multi-selection.
  - Dropdowns use headers like `Parent Name` and `Total Articles` for better context.

See the Article List and Create example for a more comprehensive demonstration, which includes this functionality.
