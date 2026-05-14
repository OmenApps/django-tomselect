# Article Token-Style Search

## Example Overview

The **Article Token-Style Search** example demonstrates the `TomSelectTokenWidget` -
a single text input that parses `key:value` tokens against multiple bound autocomplete
views, with free-text fallback. It collapses what would normally be several side-by-side
filter dropdowns into one keyboard-friendly bar.

**Objective**:
- Show how to multiplex per-model autocomplete views into a single token-aware endpoint.
- Demonstrate URL-canonical, bookmarkable filter state with chip rehydration on reload.
- Show server-side validation across operator counts (`max_count`, `min_count`),
  free-text gating (`allow_free_text`), and ORM-coercion errors at apply time.

**Use Case**:
- List-page filter bars that today have 3+ sidebar dropdowns plus a search box.
- Admin / triage / inbox UIs where power users prefer typing operators while new users
  still get a discoverable dropdown affordance.
- Bookmark-driven saved views (no new database tables needed - the URL IS the saved view).

**Visual Examples**

![Screenshot: Article Token-Style Search - token options](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/article-token-search-1.png)
![Screenshot: Article Token-Style Search - "Category:" options](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/article-token-search-2.png)
![Screenshot: Article Token-Style Search - filtered by multiple tokens](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/article-token-search-3.png)

---

## Key Code Segments

### Composite Autocomplete View

```python
from django_tomselect.autocompletes import (
    AutocompleteIterablesView,
    AutocompleteModelView,
    CompositeAutocompleteView,
    Operator,
)
from django.utils.translation import gettext_lazy as _


class ArticleTokenQueryView(CompositeAutocompleteView):
    """Token-style article query.

    Each operator declares the JSON keys returned by its bound view
    (``value_field`` / ``label_field``) AND how to filter the parent ``Article``
    queryset (``filter_lookup`` for exact matching, or ``q_translator`` for
    custom Q construction).
    """

    operators = [
        Operator(
            key="author",
            view=AuthorAutocompleteView,
            value_field="id",
            label_field="name",
            filter_lookup="authors__id",  # parent QS lookup (M2M)
            label=_("Author"),
            max_count=3,
        ),
        Operator(
            key="category",
            view=CategoryAutocompleteView,
            value_field="id",
            label_field="name",
            filter_lookup="categories__id",
            label=_("Category"),
            multi=True,  # comma-separated values: category:1,2,3
        ),
        Operator(
            key="magazine",
            view=MagazineAutocompleteView,
            value_field="id",
            label_field="name",
            filter_lookup="magazine_id",
            label=_("Magazine"),
            max_count=1,
        ),
        Operator(
            key="status",
            view=ArticleStatusAutocompleteView,  # iterables view
            value_field="value",
            label_field="label",
            filter_lookup="status",
            label=_("Status"),
            multi=True,
        ),
    ]
    free_text_lookups = ["title__icontains"]
```

### Form

```python
from django_tomselect.forms import TomSelectTokenField


class ArticleTokenSearchForm(forms.Form):
    q = TomSelectTokenField(
        composite_view="autocomplete-article-token",
        required=False,
        allow_free_text=True,
        max_tokens=20,
        widget_kwargs={"placeholder": _(
            "Filter articles… try author:, category:, magazine:, status:, or free text"
        )},
    )
```

### View

```python
from django.core.exceptions import ValidationError
from django_tomselect.query import parse_query


def article_token_search_view(request):
    form = ArticleTokenSearchForm(request.GET or None)
    articles = Article.objects.none()

    if not request.GET:
        articles = Article.objects.all().distinct()[:50]
    elif form.is_valid():
        q = form.cleaned_data.get("q", "") or ""
        if q:
            parsed = parse_query(q, ArticleTokenQueryView)
            try:
                qs = parsed.apply(Article.objects.all())
                articles = qs.distinct()[:50]
            except ValidationError as exc:
                # ORM coercion errors (typed-but-not-selected values for id-based
                # operators) bubble up here. Surface them as field-level errors.
                form.add_error("q", exc)
        else:
            articles = Article.objects.all().distinct()[:50]

    return TemplateResponse(
        request,
        "example/advanced_demos/article_token_search.html",
        {"form": form, "articles": articles},
    )
```

### URL Wiring

```python
path(
    "autocomplete/article-token/",
    autocompletes.ArticleTokenQueryView.as_view(),
    name="autocomplete-article-token",
),
path("article-token-search/", views.article_token_search_view, name="article-token-search"),
```

---

## Try It

| Action | Result |
|---|---|
| Type `author:` | Dropdown shows authors. Select one - chip renders with id and italicized name. |
| Type `category:1,2,3` | Multi-OR - filters articles in any of categories 1, 2, or 3. |
| Type `status:draft,review` | Iterables-backed multi-OR. |
| Type `"long form essay"` | Free-text title search; quoted phrase stays a single icontains term. |
| Type `category:tech` (no selection) | Server returns a clean field-level `ValidationError` - the typed string can't coerce to an integer id. |
| Type `unknown:foo` | Field validation rejects with "Unknown operator 'unknown'." |
| Type 4+ `author:` chips | Field validation rejects (`max_count=3`). |
| Bookmark `?q=author:1+category:5+free+text` | Reload - chips rehydrate via `?mode=resolve` and the free-text token reappears. |

---

## Permission Caveats

Two limitations the implementation **does not** automatically solve:

1. **`AutocompleteIterablesView` has no `has_permission()` hook.** Operators bound to
   iterables views are public-by-default. The composite view emits a one-time
   `logger.warning` at subclass-registration time. If the iterable is sensitive,
   gate access at the form/view layer or extend the iterables view yourself.

2. **Object-level permissions are NOT enforced row-by-row.** `AutocompleteModelView`
   defines `has_object_permission()` but neither `get_queryset()` nor
   `prepare_results()` calls it on rows. The resolve flow inherits this: it enforces
   queryset-level scoping (whatever your `get_queryset()` filters out is gone) and
   dispatch-level `has_permission()`, but a user with model-level view permission can
   hydrate labels for any row your queryset returns. Override `get_queryset()` on the
   bound view to apply per-row checks if you need them.

---

## Related

- {doc}`article_bulk_actions` - the existing bulk-actions demo links to this page from
  its filter row. The two coexist: bulk actions retains its dropdown filters; this
  demo is a single-bar alternative for the same data.
- API reference: `TomSelectTokenWidget`, `TomSelectTokenField`,
  `CompositeAutocompleteView`, `Operator`, `parse_query`.
