# Weighted Author Search

## Example Overview

- **Objective**: This example demonstrates how to implement a sophisticated weighted search for authors using `django_tomselect`. Results are dynamically ordered based on relevance metrics like name match, article count, and recent activity, providing an enhanced search experience.
  - **Problem Solved**: Standard alphabetical sorting isn't always sufficient for user-friendly searches. This weighted search prioritizes results based on meaningful criteria, improving user satisfaction and efficiency.
  - **Features Highlighted**:
    - Dynamic search result ordering using weighted relevance.
    - Enhanced dropdown display with metadata for each result.

- **Use Case**:
  - Applications requiring intelligent search ordering, such as finding authors, contributors, or experts.
  - Scenarios where results need to be ranked by relevance rather than alphabetical or arbitrary order.

- **Visual Elements**:
  *(Placeholders for images or GIFs)*:
  - `![Screenshot: Weighted Author Search](path-to-image)`
  - `![GIF: Weighted Search Interaction](path-to-gif)`

## Key Code Segments

### Forms
The form uses `TomSelectModelChoiceField` to configure the dropdown, with a `DropdownHeader` plugin to add metadata to the search results.

```python
class WeightedAuthorSearchForm(forms.Form):
    author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-weighted-author",
            value_field="id",
            label_field="name",
            placeholder=_("Search for authors..."),
            highlight=True,
            minimum_query_length=1,
            preload=True,
            css_framework="bootstrap5",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Author Search Results"),
                show_value_field=False,
                label_field_label=_("Author"),
                extra_columns={
                    "relevance_score": _("Relevance"),
                    "article_count": _("Articles"),
                    "last_active": _("Last Active"),
                },
            ),
        ),
        help_text=_(
            "Results are ordered by name match, article count, and recent activity"
        ),
    )
```

**Explanation**:
- The `PluginDropdownHeader` plugin adds extra metadata columns (e.g., relevance score, article count) to the dropdown results.
- The `minimum_query_length` and `preload` settings ensure responsiveness and efficiency.

**Repository Link**: [View WeightedAuthorSearchForm Code](#)

### Templates
The form is rendered in the `weighted_author_search.html` template, displaying metadata for the selected author and search results.

```html
<form method="post">
    {% csrf_token %}
    <div class="mb-3">
        {{ form.author }}
        {% if form.author.help_text %}
            <div class="helptext">{{ form.author.help_text }}</div>
        {% endif %}
    </div>
    <button type="submit" class="btn btn-primary">Search</button>
</form>
```

**Key Elements**:
- The form is styled with Bootstrap 5 for a modern look.
- Help text below the field explains the search prioritization criteria.

**Repository Link**: [View Template Code](#)

### Autocomplete Views
The `autocomplete-weighted-author` endpoint provides the backend logic for ordering results based on weighted relevance.

```python
class AutocompleteWeightedAuthor(AutocompleteModelView):
    model = Author
    search_lookups = ["name__icontains"]
    value_fields = ["id", "name", "relevance_score", "article_count", "last_active"]
    ordering = "-relevance_score"

    def hook_queryset(self, queryset):
        """Add relevance scores to the queryset for weighted ordering."""
        return queryset.annotate(
            relevance_score=(
                Case(
                    When(name__iexact=self.query, then=Value(100)),
                    When(name__istartswith=self.query, then=Value(50)),
                    When(name__icontains=self.query, then=Value(25)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ) + F("article_count") * 0.25
            + Case(
                When(last_active__gte=timezone.now() - timedelta(days=30), then=Value(25)),
                When(last_active__isnull=False, then=Value(10)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
```

**Explanation**:
- The `hook_queryset` method calculates relevance scores based on name match, article count, and recent activity.
- Results are dynamically ordered by the `relevance_score` annotation.

**Repository Link**: [View Autocomplete Code](#)

### Dependencies
- Models: An `Author` model with fields like `name`, `article_count`, and `last_active`.
- Autocomplete URLs: Ensure `autocomplete-weighted-author` is correctly defined in the Django URLs.

## Design and Implementation Notes

- **Key Features**:
  - Relevance-based ordering using annotations in the `hook_queryset` method.
  - Rich metadata display in dropdown results, including article count and last active date.

- **Design Decisions**:
  - The `relevance_score` combines multiple factors for intelligent search ranking.
  - Metadata columns (e.g., `Articles`, `Relevance`) provide clear insights into each result.

- **Alternative Approaches**:
  - Implement custom JavaScript for client-side result ranking (less scalable).
  - Use a dedicated search engine like Elasticsearch for complex queries (overhead for small projects).

- **Potential Extensions**:
  - Add sorting toggles for different criteria (e.g., most recent activity).
  - Include additional metrics like co-authorship or citations.
