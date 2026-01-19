"""Autocomplete views for the example app."""

import logging
from datetime import timedelta
from typing import Any

from django.db.models import (
    Case,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    Max,
    Q,
    QuerySet,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Now
from django.utils import timezone

from django_tomselect.autocompletes import (
    AutocompleteIterablesView,
    AutocompleteModelView,
)
from example_project.example.models import (
    Article,
    ArticlePriority,
    ArticleStatus,
    Author,
    Category,
    Edition,
    EmbargoRegion,
    EmbargoTimeframe,
    Magazine,
    ModelWithPKIDAndUUIDId,
    ModelWithUUIDPk,
    PublicationTag,
    PublishingMarket,
    edition_year,
    word_count_range,
)
from example_project.example.views import get_range_statistics

logger = logging.getLogger(__name__)


class ArticleStatusAutocompleteView(AutocompleteIterablesView):
    """Autocomplete view for ArticleStatus TextChoices."""

    iterable = ArticleStatus


class ArticlePriorityAutocompleteView(AutocompleteIterablesView):
    """Autocomplete view for ArticlePriority IntegerChoices."""

    iterable = ArticlePriority


class EditionYearAutocompleteView(AutocompleteIterablesView):
    """Autocomplete view for edition_year list."""

    iterable = edition_year


class WordCountAutocompleteView(AutocompleteIterablesView):
    """Autocomplete view for word_count_range tuple."""

    iterable = word_count_range

    def get_iterable(self) -> list[dict[str, str | int]]:
        """Customize formatting of value and label."""
        if not self.iterable:
            logger.warning("No iterable provided")
            return []

        try:
            # Handle tuple iterables of ranges
            return [
                {
                    "value": str(item),  # Store the full tuple as a string for value
                    "label": f"{item[0]:,} - {item[1]:,} words",  # Formatted label for display
                }
                for item in self.iterable
            ]
        except Exception as e:
            logger.error("Error getting iterable: %s", str(e))  # Fixed error printing format
            return []


class EditionAutocompleteView(AutocompleteModelView):
    """Autocomplete that returns all Edition objects."""

    model = Edition
    search_lookups = ["name__icontains"]
    page_size = 20
    value_fields = ["id", "name", "year", "pages", "pub_num"]

    list_url = "edition-list"
    create_url = "edition-create"
    update_url = "edition-update"
    delete_url = "edition-delete"

    skip_authorization = True


class MagazineAutocompleteView(AutocompleteModelView):
    """Autocomplete that returns all Magazine objects."""

    model = Magazine
    search_lookups = ["name__icontains"]
    value_fields = ["id", "name", "accepts_new_articles"]

    list_url = "magazine-list"
    create_url = "magazine-create"
    update_url = "magazine-update"
    delete_url = "magazine-delete"

    skip_authorization = True
    permission_required = None
    allow_anonymous = True


class RegionAutocompleteView(AutocompleteModelView):
    """Autocomplete view for top-level regions."""

    model = PublishingMarket
    search_lookups = ["name__icontains"]
    value_fields = [
        "id",
        "name",
        "total_markets",
        "aggregated_readers",
        "aggregated_publications",
    ]

    skip_authorization = True

    def get_queryset(self):
        """Return queryset of top-level regions with annotations."""
        return (
            super()
            .get_queryset()
            .filter(parent__isnull=True)
            .annotate(
                total_markets=Count("children__children"),
                aggregated_readers=Sum("children__children__market_size"),
                aggregated_publications=Sum("children__children__active_publications"),
            )
            .order_by("name")
        )


class CountryAutocompleteView(AutocompleteModelView):
    """Autocomplete view for countries within a region."""

    model = PublishingMarket
    search_lookups = ["name__icontains"]
    value_fields = [
        "id",
        "name",
        "total_local_markets",
        "total_reader_base",
        "total_pub_count",
    ]

    skip_authorization = True

    def get_queryset(self):
        """Return queryset of countries with annotations."""
        queryset = super().get_queryset()

        parent_id = self.request.GET.get("parent_id")
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        return (
            queryset.filter(parent__isnull=False, children__isnull=False)
            .annotate(
                total_local_markets=Count("children"),
                total_reader_base=Sum("children__market_size"),
                total_pub_count=Sum("children__active_publications"),
            )
            .distinct()
            .order_by("name")
        )


class LocalMarketAutocompleteView(AutocompleteModelView):
    """Autocomplete view for local markets within a country."""

    model = PublishingMarket
    search_lookups = ["name__icontains"]
    value_fields = ["id", "name", "market_size", "active_publications"]

    skip_authorization = True

    def get_queryset(self):
        """Return queryset of local markets."""
        queryset = super().get_queryset()

        parent_id = self.request.GET.get("parent_id")
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        return (
            queryset.filter(parent__parent__isnull=False)
            .filter(children__isnull=True)  # Only get leaf nodes
            .order_by("name")
        )


class PublicationTagAutocompleteView(AutocompleteModelView):
    """Autocomplete view for publication tags with iterable support."""

    model = PublicationTag
    search_lookups = ["name__icontains"]
    ordering = ["-usage_count", "name"]
    value_fields = ["id", "name", "usage_count", "created_at"]

    skip_authorization = True
    iterable = []

    def get_queryset(self):
        """Return queryset with usage statistics."""
        return super().get_queryset().filter(is_approved=True)

    def get_iterable(self):
        """Provide iterable interface for TomSelectIterablesWidget compatibility."""
        results = self.get_queryset()
        return [
            {
                "value": tag.name,  # Value used for selection
                "label": tag.name,  # Label shown in dropdown
                "usage_count": tag.usage_count,
                "created_at": tag.created_at.strftime("%Y-%m-%d"),
            }
            for tag in results
        ]

    def prepare_results(self, results):
        """Prepare results with formatted value/label pairs."""
        return [
            {
                "value": tag.name,  # Value used for selection
                "label": tag.name,  # Label shown in dropdown
                "usage_count": tag.usage_count,
                "created_at": tag.created_at.strftime("%Y-%m-%d"),
            }
            for tag in results
        ]


class WordCountRangeAutocompleteView(AutocompleteIterablesView):
    """Autocomplete view for the word count ranges with actual statistics."""

    iterable = word_count_range
    page_size = 10

    def get_iterable(self):
        """Convert the word count range tuples into labeled options with counts."""
        stats = get_range_statistics()
        ranges = []

        for stat in stats:
            start, end = stat["range_tuple"]
            label = f"{stat['range']} words ({stat['count']} articles)"
            value = f"({start}, {end})"  # Tuple string representation
            ranges.append({"value": value, "label": label})
        return ranges


class EmbargoRegionAutocompleteView(AutocompleteModelView):
    """Autocomplete view for embargo regions."""

    model = EmbargoRegion
    search_lookups = ["name__icontains"]
    value_fields = [
        "id",
        "name",
        "market_tier",
        "typical_embargo_days",
        "content_restrictions",
    ]

    skip_authorization = True

    def hook_prepare_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format results with tier information and restrictions."""
        formatted_results = []
        for region in results:
            formatted_results.append(
                {
                    "id": region["id"],
                    "name": str(region["name"]),
                    "market_tier": f"Tier {region['market_tier']}",
                    "typical_embargo_days": region["typical_embargo_days"],
                    "content_restrictions": region["content_restrictions"],
                }
            )
        return formatted_results


class EmbargoTimeframeAutocompleteView(AutocompleteIterablesView):
    """Autocomplete view for embargo timeframes."""

    iterable = EmbargoTimeframe


class AuthorAutocompleteView(AutocompleteModelView):
    """Autocomplete view for Author model with annotations and advanced searching."""

    model = Author
    search_lookups = [
        "name__icontains",
        "bio__icontains",
    ]
    ordering = ["name"]
    page_size = 20
    value_fields = ["id", "name", "bio", "article_count", "active_articles"]

    list_url = "author-list"
    create_url = "author-create"
    update_url = "author-update"
    delete_url = "author-delete"

    skip_authorization = True

    def get_queryset(self):
        """Return a queryset of authors with article count annotations.

        Annotates:
        - Total number of articles by author
        - Number of active articles by author
        - Articles by magazine (as a string list)
        """
        queryset = super().get_queryset().with_details()

        # Filter by magazine if specified
        magazine_id = self.request.GET.get("magazine")
        if magazine_id:
            queryset = queryset.filter(article__magazine_id=magazine_id)

        return queryset

    def hook_prepare_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add formatted_name to each result."""
        for author in results:
            author["formatted_name"] = f"{author['name']} ({author['article_count']} articles)"
        return results


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

    list_url = "category-list"
    detail_url = "category-detail"
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
        queryset = (
            super().get_queryset().distinct().order_by(F("parent_id").asc(nulls_first=True), "name")
        )  # Use distinct categories, with root categories (those with no parent) listed first

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


class WeightedAuthorAutocompleteView(AutocompleteModelView):
    """Autocomplete view that returns authors ordered by weighted relevance."""

    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]
    value_fields = [
        "id",
        "name",
        "bio",
        "article_count",
        "last_active",
        "relevance_score",
    ]

    skip_authorization = True

    def hook_queryset(self, queryset):
        """Add annotations for weighted search."""
        # Get base queryset with article count and last activity
        queryset = queryset.annotate(article_count=Count("article"), last_active=Max("article__updated_at"))
        return queryset

    def search(self, queryset, query):
        """Implement weighted search ordering."""
        # Calculate individual scoring components
        now = timezone.now()
        month_ago = now - timedelta(days=30)

        return (
            queryset.annotate(
                # Exact name match (highest weight)
                exact_match=Case(
                    When(name__iexact=query, then=Value(100.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                # Starts with match (high weight)
                starts_with=Case(
                    When(name__istartswith=query, then=Value(50.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                # Contains match (medium weight)
                contains=Case(
                    When(name__icontains=query, then=Value(25.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                # Article count weight (up to 25 points)
                article_weight=ExpressionWrapper(F("article_count") * Value(0.25), output_field=FloatField()),
                # Recency weight (up to 25 points)
                recency_weight=Case(
                    When(last_active__gte=month_ago, then=Value(25.0)),
                    When(last_active__isnull=False, then=Value(10.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                # Calculate final relevance score
                relevance_score=ExpressionWrapper(
                    F("exact_match") + F("starts_with") + F("contains") + F("article_weight") + F("recency_weight"),
                    output_field=FloatField(),
                ),
            )
            .filter(Q(name__icontains=query) | Q(bio__icontains=query))
            .order_by("-relevance_score", "name")
        )

    def hook_prepare_results(self, results):
        """Format the results for display."""
        for result in results:
            # Format the relevance score
            result["relevance_score"] = f"{result['relevance_score']:.1f}"

            # Format last active date
            if result.get("last_active"):
                result["last_active"] = result["last_active"].strftime("%Y-%m-%d")
            else:
                result["last_active"] = "Never"

            # Format article count
            result["article_count"] = f"{result['article_count']} articles"

        return results


class ArticleAutocompleteView(AutocompleteModelView):
    """Autocomplete view for articles with detailed information."""

    model = Article
    search_lookups = [
        "title__icontains",
        "authors__name__icontains",
        "categories__name__icontains",
    ]
    ordering = ["-created_at", "title"]
    page_size = 20

    skip_authorization = True

    def setup(self, request, *args, **kwargs):
        """Set up the view with request parameters."""
        super().setup(request, *args, **kwargs)
        # Extract filter parameters from the request URL
        self.date_range = request.GET.get("date_range")
        self.main_category = request.GET.get("main_category")
        self.status = request.GET.get("status")

    def hook_queryset(self, queryset: QuerySet) -> QuerySet:
        """Apply date range, category, and status filters to the queryset."""
        # Apply date range filter
        if self.date_range and self.date_range != "all":
            now = timezone.now()
            date_filters = {
                "today": {"created_at__date": now.date()},
                "week": {"created_at__gte": now - timedelta(days=7)},
                "month": {"created_at__gte": now - timedelta(days=30)},
                "quarter": {"created_at__gte": now - timedelta(days=90)},
                "year": {"created_at__gte": now - timedelta(days=365)},
            }
            if self.date_range in date_filters:
                queryset = queryset.filter(**date_filters[self.date_range])

        # Apply category filter
        if self.main_category:
            try:
                if self.main_category not in ("None", "", "undefined"):
                    category_id = int(self.main_category)
                    queryset = queryset.filter(categories__id=category_id)
            except (ValueError, TypeError) as e:
                logger.warning("Invalid category_id (%s): %s", self.main_category, e)

        # Apply status filter
        if self.status:
            if self.status not in ("None", "", "undefined"):
                queryset = queryset.filter(status=self.status)

        return queryset.distinct()

    def prepare_results(self, results):
        """Format the article data for display in the dropdown."""
        formatted_results = []
        for article in results:
            categories = list(article.categories.all())
            authors = list(article.authors.all())

            formatted_results.append(
                {
                    "id": article.id,
                    "title": article.title,
                    "status": article.get_status_display(),
                    "category": ", ".join(c.name for c in categories),
                    "authors": ", ".join(a.name for a in authors),
                    "created_at": article.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        return formatted_results


class RichArticleAutocompleteView(AutocompleteModelView):
    """Autocomplete view with rich metadata for articles."""

    model = Article
    search_lookups = [
        "title__icontains",
        "authors__name__icontains",
        "categories__name__icontains",
    ]
    ordering = ["-updated_at", "title"]
    page_size = 10

    skip_authorization = True

    def hook_queryset(self, queryset):
        """Add annotations for progress and prefetch related data."""
        return (
            queryset.select_related("magazine")
            .prefetch_related("authors", "categories")
            .annotate(
                days_since_update=Now() - F("updated_at"),
                completion_score=Case(
                    When(status="published", then=Value(100)),
                    When(
                        status="draft",
                        then=Case(
                            When(word_count__gte=1000, then=Value(75)),
                            When(word_count__gte=500, then=Value(50)),
                            When(word_count__gte=100, then=Value(25)),
                            default=Value(10),
                        ),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
            .distinct()
        )

    def search(self, queryset, query):
        """Implement custom search that includes related fields."""
        if not query:
            return queryset

        # Split query into terms for more flexible matching
        terms = query.split()

        q_objects = Q()
        for term in terms:
            term_q = Q()
            for lookup in self.search_lookups:
                term_q |= Q(**{lookup: term})
            q_objects &= term_q

        return queryset.filter(q_objects)

    def prepare_results(self, results):
        """Format the article data with rich metadata."""
        formatted_results = []
        for article in results:
            # Calculate article freshness
            days_old = (timezone.now() - article.updated_at).days if article.updated_at else None
            freshness = "recent" if days_old and days_old < 7 else "medium" if days_old and days_old < 30 else "old"

            # Format authors with initials
            authors_data = [
                {
                    "name": author.name,
                    "initials": "".join(word[0].upper() for word in author.name.split() if word),
                    "article_count": author.article_set.count(),
                }
                for author in article.authors.all()
            ]

            # Format categories
            categories_data = [
                {
                    "name": category.name,
                    "article_count": category.article_set.count(),
                }
                for category in article.categories.all()
            ]

            formatted_results.append(
                {
                    "id": article.id,
                    "title": article.title,
                    "status": article.status,
                    "status_display": article.get_status_display(),
                    "word_count": article.word_count,
                    "completion_score": getattr(article, "completion_score", 0),
                    "freshness": freshness,
                    "authors": authors_data,
                    "categories": categories_data,
                    "updated_at": (article.updated_at.strftime("%Y-%m-%d %H:%M") if article.updated_at else ""),
                    "created_at": (article.created_at.strftime("%Y-%m-%d %H:%M") if article.created_at else ""),
                }
            )

        return formatted_results


class ModelWithUUIDPkAutocompleteView(AutocompleteModelView):
    """Autocomplete view for ModelWithUUIDPk."""

    model = ModelWithUUIDPk
    search_lookups = ["name__icontains"]
    value_fields = ["id", "name"]
    ordering = ["name"]
    page_size = 20
    allow_anonymous = True


class ModelWithPKIDAndUUIDIdAutocompleteView(AutocompleteModelView):
    """Autocomplete view for ModelWithPKIDAndUUIDId."""

    model = ModelWithPKIDAndUUIDId
    search_lookups = ["name__icontains"]
    value_fields = ["pkid", "id", "name"]
    ordering = ["name"]
    page_size = 20
    allow_anonymous = True
