# Article Bulk Actions

## Example Overview

The **Article Bulk Actions** example demonstrates how to use `django_tomselect` to enable selecting multiple articles and applying bulk actions like publishing, archiving, or assigning categories/authors. The example highlights dynamic filtering and multi-select capabilities with rich dropdowns.

**Objective**:
- Showcase multi-select dropdowns for managing multiple articles at once.
- Demonstrate filtering articles dynamically based on user-selected criteria such as date range, category, or status.

**Use Case**:
- Editorial platforms managing large volumes of articles requiring bulk operations.
- Content moderation tools for efficiently updating the status or attributes of multiple items.

**Visual Examples** *(Placeholders)*:
- `![Screenshot: Bulk Actions Dropdown](path-to-image)`
- `![GIF: Selecting Articles and Applying Actions](path-to-gif)`

---

## Key Code Segments

### Forms
The bulk action form combines filters and actions with dynamic dropdowns for flexible workflows.

```python
class ArticleBulkActionForm(forms.Form):
    date_range = forms.ChoiceField(
        choices=[
            ("all", _("All Time")),
            ("today", _("Today")),
            ("week", _("Past Week")),
            ("month", _("Past Month")),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
    )

    main_category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            placeholder=_("Filter by category..."),
            highlight=True,
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Categories"),
                extra_columns={"total_articles": _("Total Articles")},
            ),
        ),
        required=False,
    )

    status = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
            placeholder=_("Filter by status..."),
            preload="focus",
        ),
        required=False,
    )

    selected_articles = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article",
            value_field="id",
            label_field="title",
            placeholder=_("Select articles..."),
            highlight=True,
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Articles"),
                extra_columns={"status": _("Status"), "category": _("Category")},
            ),
        ),
        required=False,
    )

    action = forms.ChoiceField(
        choices=[
            ("publish", _("Publish")),
            ("archive", _("Archive")),
            ("change_category", _("Change Category")),
            ("assign_author", _("Assign Author")),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )

    target_category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            placeholder=_("Select target category..."),
        ),
        required=False,
    )

    target_author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            placeholder=_("Select target author..."),
        ),
        required=False,
    )

    def clean(self):
        """Ensure the selected action has the required target fields."""
        cleaned_data = super().clean()
        action = cleaned_data.get("action")

        if action in ["change_category", "assign_author"]:
            required_field = "target_category" if action == "change_category" else "target_author"
            if not cleaned_data.get(required_field):
                raise ValidationError(_(f"{required_field.replace('_', ' ').capitalize()} is required for this action."))
        return cleaned_data
```
[View Full Code in Repository](#)

---

### Templates
The form is rendered dynamically in the template, allowing users to filter articles and apply actions.

```html
<form method="post" class="mb-4">
    {% csrf_token %}
    <div class="row mb-3">
        <div class="col">
            <label for="{{ form.date_range.id_for_label }}" class="form-label">Date Range</label>
            {{ form.date_range }}
        </div>
        <div class="col">
            <label for="{{ form.main_category.id_for_label }}" class="form-label">Category</label>
            {{ form.main_category }}
        </div>
        <div class="col">
            <label for="{{ form.status.id_for_label }}" class="form-label">Status</label>
            {{ form.status }}
        </div>
    </div>
    <div class="row mb-3">
        <div class="col">
            <label for="{{ form.selected_articles.id_for_label }}" class="form-label">Selected Articles</label>
            {{ form.selected_articles }}
        </div>
        <div class="col">
            <label for="{{ form.action.id_for_label }}" class="form-label">Action</label>
            {{ form.action }}
        </div>
    </div>
    <div class="row mb-3">
        <div class="col">
            <label for="{{ form.target_category.id_for_label }}" class="form-label">Target Category</label>
            {{ form.target_category }}
        </div>
        <div class="col">
            <label for="{{ form.target_author.id_for_label }}" class="form-label">Target Author</label>
            {{ form.target_author }}
        </div>
    </div>
    <button type="submit" class="btn btn-primary">Apply Action</button>
</form>
```

---

### Views

```python
class BulkActionView(FormView):
    template_name = "example/bulk_actions.html"
    form_class = ArticleBulkActionForm
    success_url = reverse_lazy("article-list")

    def form_valid(self, form):
        action = form.cleaned_data["action"]
        articles = form.cleaned_data["selected_articles"]

        if action == "publish":
            articles.update(status="published")
        elif action == "archive":
            articles.update(status="archived")
        elif action == "change_category":
            target_category = form.cleaned_data["target_category"]
            articles.update(category=target_category)
        elif action == "assign_author":
            target_author = form.cleaned_data["target_author"]
            for article in articles:
                article.authors.add(target_author)
        return super().form_valid(form)
```

---

## Design and Implementation Notes

### Key Features
- **Multi-Select Dropdowns**: Easily select multiple articles and apply bulk operations.
- **Dynamic Filtering**: Filters such as date range, category, and status dynamically refine the article selection process.

### Design Decisions
- `PluginDropdownHeader` provides additional metadata for each dropdown (e.g., category total articles).
- Target fields like "Category" or "Author" are conditionally required based on the action type, ensuring flexibility.

### Alternative Approaches
- Implement server-side bulk actions via `django-admin` but sacrifice flexibility in the user interface.
- Use JavaScript for purely client-side bulk operations with limited interaction with server data.

### Potential Extensions
- Add preview capabilities to view selected articles before applying the action.
- Enable undo functionality for bulk actions, providing better user control.
