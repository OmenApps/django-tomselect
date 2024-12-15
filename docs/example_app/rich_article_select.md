# Rich Article Select

## Example Overview

The **Rich Article Select** example showcases an advanced implementation of `django_tomselect` that enriches the selection interface with a highly detailed, visually appealing dropdown. This example is perfect for scenarios where users need to search for and select articles based on multiple attributes such as title, authors, categories, word count, and completion progress.

**Objective**:
- Enhance the article selection experience with a detailed, visually rich dropdown interface.
- Demonstrates advanced `django_tomselect` features like custom rendering for options and selected items.

**Use Case**:
- Editorial platforms where editors need to browse articles with detailed information before selection.
- Project management tools with tasks that have multiple attributes to display in dropdowns.

**Visual Examples** *(Placeholders)*:
- `![Screenshot: Rich Article Dropdown](path-to-image)`
- `![GIF: Dropdown with Custom Styling](path-to-gif)`

---

## Key Code Segments

### Forms
The form uses a `TomSelectModelChoiceField` with advanced rendering configurations.

```python
class RichArticleSelectForm(forms.Form):
    article = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-rich-article",
            value_field="id",
            label_field="title",
            placeholder=_("Search articles..."),
            highlight=True,
            preload=True,
            minimum_query_length=1,
            css_framework="bootstrap5",
            attrs={
                "render": {
                    "option": """
                        return `<div class="article-option">
                            <div class="article-avatar">
                                ${data.authors.map(author => `
                                    <div class="author-avatar" title="${escape(author.name)}">
                                        ${escape(author.initials)}
                                    </div>
                                `).join('')}
                            </div>
                            <div class="article-info">
                                <div class="article-title">
                                    ${escape(data.title)}
                                </div>
                                <div class="article-meta">
                                    <span class="status-badge status-${data.status.toLowerCase()}">
                                        ${escape(data.status_display)}
                                    </span>
                                    <span class="freshness-indicator freshness-${data.freshness}"></span>
                                    ${data.categories.map(cat => `
                                        <span class="category-tag">
                                            ${escape(cat.name)}
                                        </span>
                                    `).join('')}
                                    <span>
                                        <i class="fa fa-file-text meta-icon"></i>
                                        ${escape(data.word_count)} words
                                    </span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-value" style="width: ${data.completion_score}%"></div>
                                </div>
                            </div>
                        </div>`;
                    """,
                    "item": """
                        return `<div class="selected-article d-flex align-items-center gap-2">
                            <span class="freshness-indicator freshness-${data.freshness}"></span>
                            <span class="status-badge status-${data.status.toLowerCase()}">
                                ${escape(data.status_display)}
                            </span>
                            ${escape(data.title)}
                            <small class="text-muted ms-2">
                                (${data.authors.map(a => escape(a.name)).join(', ')})
                            </small>
                        </div>`;
                    """,
                }
            },
        ),
        help_text=_("Search for articles by title, author, or category"),
    )
```
[View Full Code in Repository](#)

---

### Templates
The field is rendered in the form with minimal configuration, and custom rendering is handled in the `TomSelectConfig`.

```html
<form method="post">
    {% csrf_token %}
    <div class="mb-3">
        <label for="{{ form.article.id_for_label }}" class="form-label">{{ form.article.label }}</label>
        {{ form.article }}
        {% if form.article.errors %}
            <div class="alert alert-danger">{{ form.article.errors }}</div>
        {% endif %}
        <span class="helptext">{{ form.article.help_text }}</span>
    </div>
    <button type="submit" class="btn btn-primary">Submit</button>
</form>
```

---

### Autocomplete Views
The `autocomplete-rich-article` endpoint processes user queries and retrieves rich article data.

```python
class AutocompleteRichArticleView(AutocompleteModelView):
    model = Article
    search_lookups = ["title__icontains", "authors__name__icontains"]
    value_fields = ["id", "title", "status", "status_display", "word_count", "completion_score"]

    def hook_queryset(self, queryset):
        return queryset.prefetch_related("authors", "categories")

    def prepare_results(self, results):
        return [
            {
                "id": obj.id,
                "title": obj.title,
                "status": obj.get_status_display(),
                "status_display": obj.status_display,
                "word_count": obj.word_count,
                "completion_score": obj.completion_score,
                "freshness": obj.freshness_indicator(),
                "authors": [{"name": a.name, "initials": a.get_initials()} for a in obj.authors.all()],
                "categories": [{"name": c.name} for c in obj.categories.all()],
            }
            for obj in results
        ]
```
[View Full Code in Repository](#)

---

## Design and Implementation Notes

### Key Features
- **Custom Rendering**: The `attrs["render"]` configuration allows defining unique HTML structures for dropdown options and selected items.
- **Dynamic Attributes**: Supports displaying progress bars, badges, and tags to highlight article attributes visually.
- **Preloading**: The dropdown is preloaded when focused to enhance user experience.

### Design Decisions
- **Rich Metadata**: Incorporating multiple article attributes helps users make informed selections without leaving the form.
- **Bootstrap Integration**: Using `bootstrap5` ensures the dropdown aligns with modern UI standards.

### Alternative Approaches
- Render the dropdown without custom templates, relying on server-side JSON responses for simplicity.
- Use a combination of server-side rendered options and light JavaScript enhancements for interactivity.

### Potential Extensions
- Add support for inline editing or quick actions (e.g., archiving an article) directly from the dropdown.
- Enable multi-select functionality for batch article management.
