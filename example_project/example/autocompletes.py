"""Autocomplete views for the example app."""

from django.db.models import Count, F, Q, Value
from django.db.models.functions import Concat

from django_tomselect.views import AutocompleteView

from .models import Author, Category, Edition, Magazine


class DemoEditionAutocompleteView(AutocompleteView):
    """Autocomplete that returns all Edition objects."""

    model = Edition
    search_lookups = ["name__icontains"]
    page_size = 20


class DemoEditionDependentAutocompleteView(AutocompleteView):
    """Autocomplete that returns only Edition objects that contain the number 3 in one of the search lookups."""

    model = Edition
    search_lookups = [
        "pages__icontains",
        "year__icontains",
        "pub_num__icontains",
    ]

    def has_add_permission(self, request):  # pylint: disable=W0613
        """Return True if the user has permission to add a new object (always True in this example app)."""
        return True  # no auth in this example app


class DemoMagazineAutocompleteView(AutocompleteView):
    """Autocomplete that returns all Magazine objects."""

    model = Magazine

    def has_add_permission(self, request):  # pylint: disable=W0613
        """Return True if the user has permission to add a new object (always True in this example app)."""
        return True  # no auth in this example app


class AuthorAutocompleteView(AutocompleteView):
    """Autocomplete view for Author model with annotations and advanced searching."""

    model = Author
    search_lookups = [
        "name__icontains",
        "bio__icontains",
    ]
    ordering = ["name"]
    page_size = 20

    def get_queryset(self):
        """Return a queryset of authors with article count annotations.

        Annotates:
        - Total number of articles by author
        - Number of active articles by author
        - Articles by magazine (as a string list)
        """
        queryset = (
            super()
            .get_queryset()
            .annotate(
                article_count=Count("article"),
                active_articles=Count("article", filter=Q(article__status="active")),
            )
            .distinct()
        )

        # Filter by magazine if specified
        magazine_id = self.request.GET.get("magazine")
        if magazine_id:
            queryset = queryset.filter(article__magazine_id=magazine_id)

        return queryset

    def prepare_results(self, results):
        """Prepare the results for JSON serialization with additional computed fields.

        Adds:
        - article_count
        - active_articles
        - magazine_names
        - formatted_name (includes article count)
        """
        data = []
        for author in results:
            author_data = {
                "id": author.id,
                "name": author.name,
                "bio": author.bio,
                "article_count": author.article_count,
                "active_articles": author.active_articles,
                # Include article count in the formatted name
                "formatted_name": f"{author.name} ({author.article_count} articles)",
            }
            data.append(author_data)
        return data

    def has_add_permission(self, request):
        """Return True if the user has permission to add authors."""
        if not request.user.is_authenticated:
            return False
        return request.user.has_perm("example.add_author")


class CategoryAutocompleteView(AutocompleteView):
    """Autocomplete view for Category model with hierarchical support."""

    model = Category
    search_lookups = [
        "name__icontains",
        "parent__name__icontains",
    ]
    ordering = ["name"]
    page_size = 20

    def hook_queryset(self, queryset):
        """Annotate the queryset with parent information and article counts."""
        return queryset.annotate(
            parent_name=F("parent__name"),
            full_path=Concat(
                "parent__name",
                Value(" → "),
                "name",
            ),
            direct_articles=Count("article"),
            total_articles=Count(
                "article", filter=Q(article__categories=F("id")) | Q(article__categories__parent=F("id"))
            ),
        )

    def get_queryset(self):
        """Return a queryset of categories with parent information and article counts.

        Annotates:
        - Full hierarchical path
        - Parent category name
        - Number of direct articles
        - Number of articles including subcategories
        """
        queryset = super().get_queryset()

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

    def prepare_results(self, results):
        """Prepare the results for JSON serialization with hierarchy information.

        Adds:
        - parent_name
        - full_path
        - direct_articles
        - total_articles
        - is_root
        - formatted_name (includes hierarchical information)
        """
        data = []
        for category in results:
            formatted_name = category.name
            if category.parent_name:
                formatted_name = f"{category.parent_name} → {category.name}"

            category_data = {
                "id": category.id,
                "name": category.name,
                "parent_name": category.parent_name,
                "full_path": category.full_path if category.parent_name else category.name,
                "direct_articles": category.direct_articles,
                "total_articles": category.total_articles,
                "is_root": category.parent_id is None,
                "formatted_name": formatted_name,
            }
            data.append(category_data)
        return data

    def has_add_permission(self, request):
        """Return True if the user has permission to add categories."""
        if not request.user.is_authenticated:
            return False
        return request.user.has_perm("example.add_category")

    def search(self, queryset, q):
        """Enhanced search that looks through the full hierarchy.

        Searches:
        - Category name
        - Parent category name
        - Full hierarchical path
        """
        if not q:
            return queryset

        q_objects = Q()
        for lookup in self.search_lookups:
            q_objects |= Q(**{lookup: q})

        # Add search in full path
        q_objects |= Q(full_path__icontains=q)

        return queryset.filter(q_objects)
