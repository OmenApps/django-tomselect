# List and Create Articles

## Example Overview

The **List and Create Articles** example demonstrates how to integrate `django_tomselect` for filtering and managing articles efficiently. The "List" view enables filtering based on various attributes like categories, statuses, and more, while the "Create" view facilitates adding new articles with advanced fields powered by `django_tomselect`.

**Objective**:
- Showcase dynamic filtering in the article list view using `TomSelectChoiceField` and `TomSelectModelChoiceField`.
- Demonstrate a feature-rich "Create Article" form leveraging the power of plugins and configurations in `django_tomselect`.

**Use Case**:
- Editorial teams managing a library of articles with advanced filtering capabilities.
- Content platforms offering streamlined workflows for creating and managing content.

**Visual Examples** *(Placeholders)*:
- `![Screenshot: Article List with Filters](path-to-image)`
- `![Screenshot: Create Article Form](path-to-image)`
- `![GIF: Filter Articles Dynamically](path-to-gif)`

---

## Key Code Segments

### Forms

#### List Articles Filters
The filtering form utilizes `TomSelectChoiceField` for selecting statuses and categories dynamically.

```python
class ArticleListFilterForm(forms.Form):
    category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            placeholder=_("Filter by category..."),
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
            highlight=True,
        ),
        required=False,
    )
```

#### Create Article Form
The "Create Article" form employs `TomSelectModelChoiceField` and `TomSelectModelMultipleChoiceField` to manage relationships like authors, categories, and more.

```python
class CreateArticleForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            show_list=True,
            show_create=True,
            placeholder=_("Select a magazine..."),
            plugin_dropdown_footer=PluginDropdownFooter(),
        ),
    )
    authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            placeholder=_("Select authors..."),
            highlight=True,
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Authors"),
                extra_columns={"article_count": _("Articles Written")},
            ),
        ),
    )

    class Meta:
        model = Article
        fields = ["title", "magazine", "authors"]
```
[View Full Code in Repository](#)

---

### Templates

#### List Articles View
The filter form and article list are rendered in the template with built-in styling and dynamic updates.

```html
<form method="get" action="{% url 'article-list' %}">
    {% csrf_token %}
    <div class="row">
        <div class="col">
            <label for="{{ form.category.id_for_label }}" class="form-label">Category</label>
            {{ form.category }}
        </div>
        <div class="col">
            <label for="{{ form.status.id_for_label }}" class="form-label">Status</label>
            {{ form.status }}
        </div>
    </div>
    <button type="submit" class="btn btn-primary mt-2">Apply Filters</button>
</form>

<table class="table table-striped mt-4">
    <thead>
        <tr>
            <th>Title</th>
            <th>Category</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        {% for article in articles %}
            <tr>
                <td>{{ article.title }}</td>
                <td>{{ article.category.name }}</td>
                <td>{{ article.get_status_display }}</td>
            </tr>
        {% endfor %}
    </tbody>
</table>
```

#### Create Article Form
The form is displayed using Bootstrap styling and `django_tomselect` integrations.

```html
<form method="post">
    {% csrf_token %}
    <div class="mb-3">
        <label for="{{ form.title.id_for_label }}" class="form-label">{{ form.title.label }}</label>
        {{ form.title }}
    </div>
    <div class="mb-3">
        <label for="{{ form.magazine.id_for_label }}" class="form-label">{{ form.magazine.label }}</label>
        {{ form.magazine }}
    </div>
    <div class="mb-3">
        <label for="{{ form.authors.id_for_label }}" class="form-label">{{ form.authors.label }}</label>
        {{ form.authors }}
    </div>
    <button type="submit" class="btn btn-primary">Create Article</button>
</form>
```

---

### Views

#### List Articles
Dynamic filters retrieve data using autocomplete endpoints.

```python
class ArticleListView(ListView):
    model = Article
    template_name = "example/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get("category")
        status = self.request.GET.get("status")

        if category:
            queryset = queryset.filter(category__id=category)
        if status:
            queryset = queryset.filter(status=status)

        return queryset
```

#### Create Article
The create view manages both the article and its relationships.

```python
class ArticleCreateView(CreateView):
    model = Article
    form_class = CreateArticleForm
    template_name = "example/create_article.html"
    success_url = reverse_lazy("article-list")
```

---

## Design and Implementation Notes

### Key Features
- **Dynamic Filtering**: Use `django_tomselect` for real-time filtering in the article list.
- **Relationship Management**: Leverage multi-select dropdowns for managing complex relationships like authors and categories.

### Design Decisions
- Using `plugin_dropdown_header` enhances the dropdown with contextual information (e.g., article count for authors).
- `plugin_dropdown_footer` allows quick navigation to related views, like creating new magazines.

### Alternative Approaches
- Server-side filtering with `django_filters`, though less dynamic than `django_tomselect`.
- Combining client-side filtering with preloaded data for simpler use cases.

### Potential Extensions
- Add advanced search capabilities like keyword-based filtering.
- Integrate inline editing for articles directly in the list view.
