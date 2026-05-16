"""Autocomplete views for the example app."""

import hashlib
import logging
import time
import zlib
from datetime import timedelta
from typing import Any

from django.core.cache import cache as _django_cache
from django.http import JsonResponse as _JsonResponse
from django.db.models import (
    Case,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    Max,
    Prefetch,
    Q,
    QuerySet,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Now
from django.utils import timezone

from django.utils.translation import gettext_lazy as _

from django_tomselect.autocompletes import (
    AutocompleteIterablesView,
    AutocompleteModelView,
    CompositeAutocompleteView,
    Operator,
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
        # Lazy import to avoid circular dependency with views module
        from example_project.example.views.intermediate_demos import get_range_statistics

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
                formatted_name = f"{category['parent_name']} >> {category['name']}"

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


# Status buckets for the Rich Author demo's status-mix bar.
# Exact-match allowlists are used (not substring matching), so "unpublished" is not
# miscounted as "published".
_PUBLISHED_STATUSES = {ArticleStatus.PUBLISHED.value, ArticleStatus.ACTIVE.value}
_DRAFT_STATUSES = {
    ArticleStatus.DRAFT.value,
    ArticleStatus.PENDING.value,
    ArticleStatus.ON_REVIEW.value,
    ArticleStatus.NEEDS_REVIEW.value,
    ArticleStatus.IN_PROGRESS.value,
    ArticleStatus.WIP.value,
}

_AVATAR_PALETTE_COUNT = 6


def _bucket_status(status_value: str) -> str:
    """Group ~40 ArticleStatus values into three demo-friendly buckets."""
    if status_value in _PUBLISHED_STATUSES:
        return "published"
    if status_value in _DRAFT_STATUSES:
        return "draft"
    return "other"


class RichAuthorAutocompleteView(AutocompleteModelView):
    """Autocomplete view with rich metadata for authors (powers the multi-select demo).

    Sibling of RichArticleAutocompleteView. Returns enough data per author to drive
    three distinct visual treatments in the same demo page (full kit, slim card,
    stats-forward) without any client-side data viz library.
    """

    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]
    ordering = ["-article_count", "name"]
    page_size = 10
    # Only concrete model fields here. Annotations and Python-derived fields are
    # added in prepare_results below; listing them would trigger the
    # non-concrete-field warning at autocompletes.py.
    value_fields = ["id", "name", "bio"]

    skip_authorization = True

    def hook_queryset(self, queryset):
        """Annotate with article/magazine counts and prefetch articles+relations.

        A single Prefetch with select_related("magazine") and
        prefetch_related("categories") keeps the per-author work in prepare_results
        N+1 free.
        """
        return queryset.annotate(
            article_count=Count("article", distinct=True),
            last_active=Max("article__updated_at"),
            magazines_count=Count("article__magazine", distinct=True),
        ).prefetch_related(
            Prefetch(
                "article_set",
                queryset=Article.objects.select_related("magazine").prefetch_related("categories"),
            )
        )

    def search(self, queryset, query):
        """Multi-term AND search across name and bio.

        Mirrors RichArticleAutocompleteView.search: every whitespace-separated term
        must match name OR bio (case-insensitive). Improves precision over plain LIKE.
        """
        if not query:
            return queryset

        terms = query.split()
        q_objects = Q()
        for term in terms:
            term_q = Q()
            for lookup in self.search_lookups:
                term_q |= Q(**{lookup: term})
            q_objects &= term_q
        return queryset.filter(q_objects)

    def prepare_results(self, results):  # noqa: C901
        """Build the rich payload that all three demo widgets render."""
        # Global rank map: rank by article_count across ALL authors, not just the
        # filtered/paginated subset. A Window function in hook_queryset would only
        # rank within the current search result.
        rank_ids = list(
            Author.objects.annotate(article_count=Count("article", distinct=True))
            .order_by("-article_count", "name")
            .values_list("id", flat=True)
        )
        rank_map = {pk: i + 1 for i, pk in enumerate(rank_ids)}

        now = timezone.now()
        current_year = now.year

        formatted_results = []
        for author in results:
            article_count = getattr(author, "article_count", 0) or 0
            magazines_count = getattr(author, "magazines_count", 0) or 0
            last_active = getattr(author, "last_active", None)

            initials = "".join(word[0].upper() for word in author.name.split() if word)[:2] or "?"
            avatar_palette_index = zlib.adler32(author.name.encode("utf-8")) % _AVATAR_PALETTE_COUNT

            # Activity bucket: same color conventions as the article demo's freshness.
            if last_active is None:
                activity_level = "never"
                last_active_display = "Never"
            else:
                days_old = (now - last_active).days
                if days_old <= 7:
                    activity_level = "recent"
                elif days_old <= 30:
                    activity_level = "medium"
                else:
                    activity_level = "old"
                last_active_display = last_active.strftime("%Y-%m-%d")

            # Bio: first sentence, truncated to ~120 chars.
            bio = author.bio or ""
            first_sentence = bio.split(".")[0].strip() if bio else ""
            if len(first_sentence) > 120:
                bio_snippet = first_sentence[:117] + "..."
            else:
                bio_snippet = first_sentence

            years_active = max(1, current_year - author.created_at.year) if author.created_at else 1

            # Walk the prefetched articles ONCE for categories, status mix, and sparkline.
            category_counts: dict[str, int] = {}
            status_bucket_counts = {"published": 0, "draft": 0, "other": 0}
            month_bins = [0] * 12
            # Boundary: the start of the month 11 months before the current month.
            # That gives us 12 months including the current one.
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            articles = list(author.article_set.all())
            total_articles_seen = len(articles)
            for article in articles:
                # Categories
                for category in article.categories.all():
                    category_counts[category.name] = category_counts.get(category.name, 0) + 1
                # Status mix
                status_bucket_counts[_bucket_status(article.status)] += 1
                # Sparkline: bucket by months-ago, 0=current month at index 11.
                updated = article.updated_at
                if updated is None:
                    continue
                months_ago = (current_month_start.year - updated.year) * 12 + (
                    current_month_start.month - updated.month
                )
                if 0 <= months_ago < 12:
                    month_bins[11 - months_ago] += 1

            top_categories = sorted(
                ({"name": name, "count": count} for name, count in category_counts.items()),
                key=lambda c: (-c["count"], c["name"]),
            )[:2]
            expertise = top_categories[0]["name"] if top_categories else "Generalist"

            # Status mix as exact-summing integer percentages with 3 segments.
            status_labels = {"published": "Published", "draft": "Draft", "other": "Other"}
            if total_articles_seen == 0:
                status_mix = [
                    {"key": k, "label": status_labels[k], "pct": 0} for k in ("published", "draft", "other")
                ]
            else:
                raw = {
                    k: 100 * v / total_articles_seen for k, v in status_bucket_counts.items()
                }
                rounded = {k: int(round(v)) for k, v in raw.items()}
                # Fix rounding drift: push remainder onto whichever bucket has the
                # largest raw share so the bar always sums to exactly 100.
                remainder = 100 - sum(rounded.values())
                if remainder != 0:
                    largest_key = max(raw, key=lambda k: (raw[k], rounded[k]))
                    rounded[largest_key] += remainder
                status_mix = [
                    {"key": k, "label": status_labels[k], "pct": int(max(0, min(100, rounded[k])))}
                    for k in ("published", "draft", "other")
                ]

            # Sparkline bars: server-side normalize to 0..100 for direct use in SVG.
            max_bin = max(month_bins) if month_bins else 0
            if max_bin > 0:
                sparkline_bars = [int(round(100 * c / max_bin)) for c in month_bins]
            else:
                sparkline_bars = [0] * 12

            formatted_results.append(
                {
                    "id": author.id,
                    "name": author.name,
                    "bio": bio,
                    "bio_snippet": bio_snippet,
                    "initials": initials,
                    "avatar_palette_index": int(avatar_palette_index),
                    "article_count": int(article_count),
                    "magazines_count": int(magazines_count),
                    "activity_level": activity_level,
                    "last_active_display": last_active_display,
                    "years_active": int(years_active),
                    "top_categories": top_categories,
                    "expertise": expertise,
                    "status_mix": status_mix,
                    "monthly_sparkline": month_bins,
                    "sparkline_bars": sparkline_bars,
                    "peer_rank": int(rank_map.get(author.id, 0)),
                }
            )

        return formatted_results


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
        # Optimize queries by selecting related magazine
        queryset = queryset.select_related("magazine")

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
                    "magazine_name": article.magazine.name if article.magazine else "",
                    "word_count": article.word_count or 0,
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


class ArticleTokenQueryView(CompositeAutocompleteView):
    """Token-style article query.

    Multiplexes the per-model autocomplete views into a single endpoint that
    powers the ``TomSelectTokenWidget`` on /article-token-search/.

    Each operator declares the fields the bound view returns
    (``value_field``/``label_field``) AND how to filter the parent ``Article``
    queryset (``filter_lookup``).
    """

    operators = [
        Operator(
            key="author",
            view=AuthorAutocompleteView,
            value_field="id",
            label_field="name",
            filter_lookup="authors__id",
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
            multi=True,
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
            view=ArticleStatusAutocompleteView,
            value_field="value",
            label_field="label",
            filter_lookup="status",
            label=_("Status"),
            multi=True,
        ),
    ]
    free_text_lookups = ["title__icontains"]


class NoSuggestionAutocompleteView(AutocompleteModelView):
    """Empty-result autocomplete used as a placeholder for free-form operators.

    Used as the ``view`` for operators whose values are not browse-able
    (dates, numeric comparisons). ``Operator`` requires ``view`` to be set,
    but for operators where the value is free-form (e.g.
    ``published_after:2024-01-01``) we don't want the token widget to pop a
    suggestion dropdown of unrelated rows.
    """

    model = Article
    value_fields = ["id"]
    skip_authorization = True

    def get_queryset(self) -> QuerySet:  # type: ignore[override]
        """Return an empty queryset so no suggestions appear in the dropdown."""
        return Article.objects.none()


def _parse_iso_date(values):
    """Parse a single ISO-8601 date from the operator's value list.

    Raises ``ValueError`` (caught by ``ParsedQuery.apply`` and re-raised as
    ``ValidationError``) if the value cannot be parsed.
    """
    from django.utils.dateparse import parse_date

    raw = (values[0] or "").strip()
    parsed = parse_date(raw)
    if not parsed:
        raise ValueError(_("Invalid date: %(raw)r. Use YYYY-MM-DD.") % {"raw": raw})
    return parsed


def _q_published_after(op, values):
    """Q-translator for ``published_after:<YYYY-MM-DD>``."""
    return Q(created_at__date__gte=_parse_iso_date(values))


def _q_published_before(op, values):
    """Q-translator for ``published_before:<YYYY-MM-DD>``."""
    return Q(created_at__date__lt=_parse_iso_date(values))


def _q_word_count(op, values):  # noqa: C901
    """Q-translator for ``word_count:<expr>``.

    Accepts ``>500``, ``<2000``, ``>=1000``, ``<=5000``, ``=500``,
    ``100..2000`` (inclusive range), or a plain integer ``500``.
    """
    raw = (values[0] or "").strip()
    if not raw:
        raise ValueError(_("word_count: expected a number or comparison (e.g. >500, 100..2000)."))
    if ".." in raw:
        lo_s, hi_s = raw.split("..", 1)
        try:
            lo, hi = int(lo_s), int(hi_s)
        except ValueError as exc:
            raise ValueError(_("word_count range needs two integers: '100..2000'.")) from exc
        if lo > hi:
            raise ValueError(_("word_count range is inverted: lo > hi."))
        return Q(word_count__gte=lo, word_count__lte=hi)
    for prefix, lookup in ((">=", "gte"), ("<=", "lte"), (">", "gt"), ("<", "lt"), ("=", "exact")):
        if raw.startswith(prefix):
            try:
                value = int(raw[len(prefix):])
            except ValueError as exc:
                raise ValueError(
                    _("word_count %(prefix)s expects an integer.") % {"prefix": prefix}
                ) from exc
            return Q(**{f"word_count__{lookup}": value})
    try:
        return Q(word_count__exact=int(raw))
    except ValueError as exc:
        raise ValueError(_("word_count: %(raw)r is not a number.") % {"raw": raw}) from exc


class ArticleAdvancedTokenQueryView(CompositeAutocompleteView):
    """Token-style article query with date/range/comparison operators.

    Demonstrates ``Operator.q_translator`` (the simple token demo only
    exercises ``filter_lookup``). Comparison/range syntax lives inside the
    token value because the tokenizer only understands ``key:value``.

    Operators with no useful value-suggestion dropdown bind to
    :class:`NoSuggestionAutocompleteView` so typing ``published_after:``
    doesn't pop unrelated article suggestions.
    """

    operators = [
        Operator(
            key="author",
            view=AuthorAutocompleteView,
            value_field="id",
            label_field="name",
            filter_lookup="authors__id",
            label=_("Author"),
            multi=True,
        ),
        Operator(
            key="status",
            view=ArticleStatusAutocompleteView,
            value_field="value",
            label_field="label",
            filter_lookup="status",
            label=_("Status"),
            multi=True,
        ),
        Operator(
            key="published_after",
            view=NoSuggestionAutocompleteView,
            value_field="id",
            label_field="id",
            q_translator=_q_published_after,
            label=_("Published after (YYYY-MM-DD)"),
            max_count=1,
        ),
        Operator(
            key="published_before",
            view=NoSuggestionAutocompleteView,
            value_field="id",
            label_field="id",
            q_translator=_q_published_before,
            label=_("Published before (YYYY-MM-DD)"),
            max_count=1,
        ),
        Operator(
            key="word_count",
            view=NoSuggestionAutocompleteView,
            value_field="id",
            label_field="id",
            q_translator=_q_word_count,
            label=_("Word count (e.g. >500, 100..2000)"),
            max_count=1,
        ),
    ]
    free_text_lookups = ["title__icontains"]


_GITHUB_USER_SEARCH_URL = "https://api.github.com/search/users"
_GITHUB_CACHE_PREFIX = "demo-github-user-search:"
_GITHUB_CACHE_TIMEOUT = 300  # seconds
_GITHUB_THROTTLE_KEY = "demo-github-user-search:throttled-until"


class GitHubUserAutocompleteView(AutocompleteIterablesView):
    """Autocompletes against the GitHub /search/users public API.

    Subclasses ``AutocompleteIterablesView`` but overrides ``get()`` to skip
    ``get_iterable``/``search``/``paginate_iterable`` — the upstream API does
    pagination and filtering for us.

    Cache, rate-limit, and error handling notes are intentionally kept inline
    so the demo template can reference them. Cache is per-process
    (``LocMemCache`` in the example project), so the protection is partial.
    """

    skip_authorization = True
    page_size = 20

    def get(self, request, *args, **kwargs):
        """Handle the autocomplete request by querying the GitHub search API."""
        from django_tomselect.utils import sanitize_dict

        q = (request.GET.get("q") or "").strip()
        try:
            page = max(int(request.GET.get("p", 1)), 1)
        except (TypeError, ValueError):
            page = 1

        if not q or len(q) < 2:
            return _JsonResponse({"results": [], "page": page, "has_more": False})

        throttled_until = _django_cache.get(_GITHUB_THROTTLE_KEY)
        if throttled_until and throttled_until > time.time():
            wait = int(throttled_until - time.time())
            return _JsonResponse({
                "results": [], "page": page, "has_more": False,
                "error": f"GitHub rate limit reached. Try again in {wait} seconds.",
            })

        # Hash the cache-key components: the raw query may contain spaces or
        # non-ASCII characters which are forbidden by some cache backends
        # (Memcached restricts keys to printable ASCII with no whitespace).
        # LocMemCache (the example project's default) tolerates anything,
        # but using a hash keeps the demo backend-portable.
        q_digest = hashlib.sha1(q.encode("utf-8")).hexdigest()[:16]
        cache_key = f"{_GITHUB_CACHE_PREFIX}{q_digest}:{page}"
        cached = _django_cache.get(cache_key)
        if cached is not None:
            return _JsonResponse(cached)

        try:
            payload = self._fetch_github(q, page)
        except Exception:  # noqa: BLE001 - we deliberately swallow upstream failures
            logger.exception("GitHub user search failed")
            # Don't cache transient errors — let the next request retry.
            return _JsonResponse({
                "results": [], "page": page, "has_more": False,
                "error": "Upstream error contacting GitHub.",
            })

        # Sanitize every row at the boundary — overriding get() means we skip
        # the package's automatic sanitization pass.
        payload["results"] = [sanitize_dict(r) for r in payload.get("results", [])]
        # Only cache successful payloads. Caching rate-limit/error responses
        # would lock the demo into a 5-minute "stale error" state even after
        # the throttle window expires.
        if not payload.get("error"):
            _django_cache.set(cache_key, payload, _GITHUB_CACHE_TIMEOUT)
        return _JsonResponse(payload)

    def _fetch_github(self, q: str, page: int) -> dict[str, Any]:  # noqa: C901
        """Call the GitHub search API and normalize the response shape."""
        import httpx  # imported lazily so the rest of the example app loads fine without it

        params = {"q": q, "per_page": self.page_size, "page": page}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(_GITHUB_USER_SEARCH_URL, params=params, headers={"Accept": "application/json"})

        # Rate-limit hard-stop: mark a throttle window so we stop hitting the API.
        if resp.status_code in (403, 429):
            retry_after = resp.headers.get("retry-after")
            try:
                wait = int(retry_after) if retry_after else 60
            except ValueError:
                wait = 60
            reset = resp.headers.get("x-ratelimit-reset")
            try:
                reset_at = int(reset) if reset else int(time.time() + wait)
            except ValueError:
                reset_at = int(time.time() + wait)
            _django_cache.set(_GITHUB_THROTTLE_KEY, reset_at, max(wait, 30))
            return {
                "results": [], "page": page, "has_more": False,
                "error": f"GitHub rate limit reached. Try again in {wait} seconds.",
            }

        if resp.status_code >= 400:
            return {
                "results": [], "page": page, "has_more": False,
                "error": f"Upstream error ({resp.status_code}).",
            }

        # If x-ratelimit-remaining is 0, throttle preemptively.
        remaining = resp.headers.get("x-ratelimit-remaining")
        if remaining == "0":
            reset = resp.headers.get("x-ratelimit-reset")
            try:
                reset_at = int(reset) if reset else int(time.time() + 60)
            except ValueError:
                reset_at = int(time.time() + 60)
            _django_cache.set(_GITHUB_THROTTLE_KEY, reset_at, 60)

        data = resp.json()
        items = data.get("items") or []
        total = data.get("total_count") or 0
        results = []
        for u in items:
            login = u.get("login") or ""
            # The row keys MUST match the widget's configured value_field /
            # label_field (here: "value"/"label"). Returning {"id": ...} would
            # make Tom Select see data.value === undefined and silently drop
            # every row to "No results found", even with a 200 response.
            results.append({
                "value": login,
                "label": login,
                "avatar_url": u.get("avatar_url") or "",
                "html_url": u.get("html_url") or "",
                "bio": (u.get("bio") or "")[:140],  # keep dropdown rows compact
            })
        has_more = page * self.page_size < total
        return {
            "results": results,
            "page": page,
            "has_more": has_more,
            # The package's frontend stores the next-page URL only when both
            # ``has_more`` AND ``next_page`` are present. Emit it so the
            # widget can fetch additional pages on scroll.
            "next_page": page + 1 if has_more else None,
        }


class MultiTypeFeaturedAdapterView(AutocompleteIterablesView):
    """Multi-type autocomplete adapter for the GFK picker.

    Subclasses ``AutocompleteIterablesView`` but overrides ``get()`` to fan
    out per-type subviews via Django's ``as_view()`` (mirroring the package's
    own ``_delegate_value`` pattern in ``CompositeAutocompleteView``). Each
    subview runs its own ``get_queryset → search → prepare_results →
    pagination`` flow, so we don't double-search.

    Result row shape: ``{value: "type:id", label: <human>, _type_key, _type_label}``.
    The ``value`` is prefixed with the operator key so consumers can route the
    selected value back to a ``ContentType`` and an object id without an
    extra round-trip.
    """

    skip_authorization = True
    page_size = 20

    # (key, human label, bound view class, label-field name)
    _routes: list[tuple[str, str, type, str]] = [
        ("article", "Article", None, "title"),   # filled in lazily — see _get_routes
        ("author", "Author", None, "name"),
        ("magazine", "Magazine", None, "name"),
    ]

    def _get_routes(self):
        # Lazy resolution to avoid forward-reference issues (subviews live in
        # this module too).
        return [
            ("article", "Article", ArticleAutocompleteView, "title"),
            ("author", "Author", AuthorAutocompleteView, "name"),
            ("magazine", "Magazine", MagazineAutocompleteView, "name"),
        ]

    def get(self, request, *args, **kwargs):
        """Fan out the request to each per-type subview and merge results."""
        from django.core.exceptions import PermissionDenied
        from django_tomselect.utils import sanitize_dict
        import json as _json

        scope = request.GET.get("scope")
        rows: list[dict[str, Any]] = []
        for key, type_label, view_cls, label_field in self._get_routes():
            if scope and scope != key:
                continue
            try:
                sub_resp = view_cls.as_view()(request)
            except PermissionDenied:
                continue
            if sub_resp.status_code != 200:
                continue
            try:
                sub_payload = _json.loads(sub_resp.content)
            except ValueError:
                continue
            # Defensive: AutocompleteModelView.value_fields defaults to [] when
            # the subview shapes its rows via prepare_results() instead of
            # declaring concrete value_fields. The ``or ["id"]`` keeps indexing
            # safe regardless of whether the subview later changes that default.
            pk_field = (getattr(view_cls, "value_fields", None) or ["id"])[0]
            for r in sub_payload.get("results", []):
                pk = r.get(pk_field, r.get("id", ""))
                rows.append(sanitize_dict({
                    "value": f"{key}:{pk}",
                    "label": str(r.get(label_field, "")),
                    "_type_key": key,
                    "_type_label": type_label,
                }))

        # The adapter genuinely is first-page-only: each subview is called
        # once (its own first page), results are merged, and we return
        # everything. No per-type cursoring. Emitting ``has_more=True`` with
        # ``next_page=None`` would lie to the frontend (which needs BOTH to
        # paginate) and silently hide rows beyond ``page_size``. Surface all
        # rows the subviews returned and set ``has_more=False``.
        return _JsonResponse({
            "results": rows,
            "page": 1,
            "has_more": False,
            "next_page": None,
        })
