# Introduction to the Example Project

The example project demonstrates how to use the `django-tomselect` package in a Django project. It consists of a number of basic, intermediate, and advanced implementations all using the theme of publishing articles in a magazine.

## Prerequisites

- Python 3.10+
- Django 4.2+
- `django-tomselect` package
- Basic understanding of Django forms and views

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/OmenApps/django-tomselect.git
    ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

   Or with `uv`:

   ```bash
    uv sync
    ```

## Running the Example Project

1. Navigate to the `example_app` directory:

   ```bash
   cd example_app
   ```

2. Apply the migrations:

   ```bash
   python manage.py migrate
   ```

3. Create the example data:

   ```bash
   python manage.py create_examples
   ```

4. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

5. Run the Django development server:

   ```bash
    python manage.py runserver 0.0.0.0:8000
    ```

6. Open the browser and go to `http://localhost:8000/admin` to login (or directly `http://localhost:8000/` to view as AnonymousUser - some links and bttons to list/create/update/delete will not be available).

7. Go to `http://localhost:8000/` to view the example project.

## Example Project Structure

### Basic Examples

- [Styling](styling.md)
- [HTMX Integration](htmx.md)

### Intermediate Examples

- [Filter by Magazine](filter_by_magazine.md)
- [Filter by Category](filter_by_category.md)
- [Exclude by Primary Author](exclude_by_primary_author.md)
- [View Range Based Data](view_range_based_data.md)
- [Tagging](tagging.md)
- [Custom Content Display](custom_content_display.md)
- [Weighted Author Search](weighted_author_search.md)

### Advanced Examples

- [Three-Level Filter-By](three_level_filter_by.md)
- [Rich Article Select](rich_article_select.md)
- [Article List and Create](article_list_and_create.md)
- [Article Bulk Actions](article_bulk_actions.md)

### CRUD

There are also several standard CRUD views, but they are not documented here.

## Models

Here is the simplified code for the models to aid in understanding the examples.

See the actual models in the [`example_project/example/models.py`](https://github.com/OmenApps/django-tomselect/blob/main/example_project/example/models.py) file.

```python
class ArticleStatus(models.TextChoices):
    """Choices for the status field of the Article model.

    Used to demonstrate the AutocompleteIterablesView.
    """

    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
    PUBLISHED = "published", "Published"
    PENDING = "pending", "Pending"
    LOCKED = "locked", "Locked"
    ON_HOLD = "on_hold", "On Hold"
    ON_REVIEW = "on_review", "On Review"
    # Additional statuses skipped for brevity


class ArticlePriority(models.IntegerChoices):
    """Choices for the priority field of the Article model.

    Used to demonstrate the AutocompleteIterablesView.
    """

    LOW = 1, "Low"
    MEDIUM = 2, "Medium"
    HIGH = 3, "High"
    CRITICAL = 4, "Critical"
    URGENT = 5, "Urgent"
    IMMEDIATE = 6, "Immediate"
    NONE = 7, "None"
    # Additional priorities skipped for brevity


class EmbargoTimeframe(models.TextChoices):
    """Choices for the embargo_timeframe field of the Article model."""

    PRE_RELEASE = "pre", "Pre-Release (2 weeks)"
    STANDARD = "std", "Standard (1 month)"
    EXTENDED = "extd", "Extended (3 months)"
    EXTREME = "extr", "Extreme (6 months)"


# A list of years for the Edition model
# Used to demonstrate the AutocompleteIterablesView
edition_year = [
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
]

# A list of word count ranges for the Edition model
# Used to demonstrate the AutocompleteIterablesView
word_count_range = (
    (0, 100),
    (100, 200),
    (200, 300),
    (300, 400),
    (400, 500),
    (500, 600),
    (600, 700),
    # Additional ranges skipped for brevity
)


market_tier_choices = [
    (1, "Tier 1"),
    (2, "Tier 2"),
    (3, "Tier 3"),
]


class EmbargoRegion(models.Model):
    """A model representing a region with embargo information."""

    name = models.CharField(max_length=100)
    market_tier = models.IntegerField(choices=market_tier_choices)
    content_restrictions = models.TextField()
    typical_embargo_days = models.IntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SearchQueryset(models.QuerySet):
    """A queryset providing a search method."""

    def search(self, q):
        """Return a queryset filtered by the search term."""
        return self.filter(name__icontains=q)


class Edition(models.Model):
    """A model representing an edition of a magazine."""

    name = models.CharField("Name", max_length=50)
    year = models.CharField("Year", max_length=50)
    pages = models.CharField("Pages", max_length=50)
    pub_num = models.CharField("Publication Number", max_length=50)

    magazine = models.ForeignKey(
        "Magazine",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SearchQueryset.as_manager()


class Magazine(models.Model):
    """A model representing a magazine."""

    class AcceptsNewArticles(models.TextChoices):
        """Choices for the accepts_new_articles field."""

        YES = "yes", "Yes"
        NO = "no", "No"
        MAYBE = "maybe", "Maybe"

    name = models.CharField("Name", max_length=50)
    accepts_new_articles = models.CharField(
        "Accepts New Articles",
        max_length=10,
        choices=AcceptsNewArticles.choices,
        default=AcceptsNewArticles.YES,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CategoryQuerySet(models.QuerySet):
    """Queryset for the Category model."""

    def with_header_data(self):
        """Annotate the queryset with parent information and article counts."""
        return self.annotate(
            parent_name=F("parent__name"),
            full_path=Concat(
                "parent__name",
                Value(" → "),
                "name",
            ),
            direct_articles=Count("article"),
            total_articles=Count(
                "article",
                filter=Q(article__categories=F("id")) | Q(article__categories__parent=F("id")),
            ),
        ).select_related("parent")


class Category(models.Model):
    """A model representing an article category."""

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(CategoryQuerySet)()


class AuthorQuerySet(models.QuerySet):
    """Queryset for the Author model."""

    def with_details(self):
        """Return a queryset of authors with article count annotations."""
        return self.annotate(
            article_count=Count("article"),
            active_articles=Count("article", filter=Q(article__status="active")),
        ).distinct()


class Author(models.Model):
    """A model representing an article author."""

    name = models.CharField(max_length=100)
    bio = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(AuthorQuerySet)()


class Article(models.Model):
    """A model representing an article in a magazine."""

    title = models.CharField(max_length=200)
    word_count = models.PositiveSmallIntegerField()
    authors = models.ManyToManyField("Author")
    categories = models.ManyToManyField("Category")
    magazine = models.ForeignKey("Magazine", on_delete=models.CASCADE)
    edition = models.ForeignKey(
        "Edition",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=30,
        choices=ArticleStatus.choices,
        default=ArticleStatus.DRAFT,
    )
    priority = models.IntegerField(
        choices=ArticlePriority.choices,
        default=ArticlePriority.NORMAL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)


class PublishingMarket(models.Model):
    """Represents geographic markets for publishing operations.

    Creates a three-level hierarchy: Region -> Country -> City/Market
    """

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    market_size = models.IntegerField(default=0)
    active_publications = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PublicationTag(models.Model):
    """Represents a tag/keyword for publications with validation rules."""

    name = models.CharField(max_length=50, unique=True)
    usage_count = models.IntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```
