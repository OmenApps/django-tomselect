"""Tests for AutocompleteModelView core query mechanics.

Covers view setup, queryset retrieval, pagination, search, ordering,
customization hooks, error/edge-case handling, URL handling, and the
split-search behavior. Filtering-specific tests live alongside
``test_autocompletes_model_filtering`` and the advanced permissions/
virtual-fields/JSON encoder tests live in ``test_autocompletes_model_advanced``.
"""


import json

import pytest
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.http import JsonResponse

from django_tomselect.autocompletes import AutocompleteModelView
from example_project.example.models import Edition


@pytest.mark.django_db
class TestAutocompleteModelViewSetup:
    """Tests for AutocompleteModelView setup and initialization."""

    def test_setup_without_model(self, rf):
        """Test that setup raises ValueError if no model is specified."""
        request = rf.get("")
        view = AutocompleteModelView()

        with pytest.raises(ValueError, match="Model must be specified"):
            view.setup(request)

    @pytest.mark.parametrize(
        "page_size_param, expected_size",
        [
            ("10", 10),
            ("20", 20),
            ("invalid", 20),  # Should fall back to default
            (None, 20),  # Should fall back to default
        ],
    )
    def test_setup_page_size(self, rf, page_size_param, expected_size):
        """Test that page_size is properly set from request parameters."""
        request = rf.get("", {"page_size": page_size_param} if page_size_param else {})
        view = AutocompleteModelView()
        view.model = Edition
        view.setup(request)

        assert view.page_size == expected_size


@pytest.mark.django_db
class TestAutocompleteModelViewQueryset:
    """Tests for AutocompleteModelView queryset handling."""

    def test_get_queryset_basic(self, test_editions, rf):
        """Test basic queryset retrieval without search or filters."""
        view = AutocompleteModelView()
        view.model = Edition
        view.setup(rf.get(""))

        queryset = view.get_queryset()
        assert queryset.count() == len(test_editions)
        assert list(queryset) == list(Edition.objects.all())

    def test_annotated_queryset(self, test_editions, rf):
        """Test that search works with annotated fields."""

        class CustomAutocompleteModelView(AutocompleteModelView):
            """Custom view with annotated queryset."""

            def get_queryset(self):
                """Get base queryset first."""
                qs = super().get_queryset()
                return qs.annotate(full_text=Concat("name", Value(" "), "year", output_field=models.CharField()))

            def search(self, queryset, query):
                """Custom search implementation."""
                if not query:
                    return queryset
                return queryset.filter(name__icontains=query) | queryset.filter(year__icontains=query)

        view = CustomAutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"q": "Edition 1"})
        view.setup(request)

        queryset = view.get_queryset()
        assert queryset.exists()
        assert queryset.first() == test_editions[0]


@pytest.mark.django_db
class TestAutocompleteModelViewPagination:
    """Tests for AutocompleteModelView pagination functionality."""

    def get_response_data(self, response: JsonResponse) -> dict:
        """Helper method to get data from response."""
        return json.loads(response.content.decode("utf-8"))

    def test_invalid_page_size_uses_default(self, rf, test_editions):
        """Test invalid page size falls back to default."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"page_size": "invalid"})
        view.setup(request)

        assert view.page_size == 20  # Default value

    def test_page_size_from_request(self, rf, test_editions, user):
        """Test custom page size from request parameter."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"page_size": "3"})
        request.user = user
        view.setup(request)

        assert view.page_size == 3

        data = self.get_response_data(view.get(request))
        assert len(data["results"]) == 3

    @pytest.mark.parametrize(
        "page_size,page_num,expected_count,expected_has_more,expected_page",
        [
            (3, None, 3, True, 1),  # first page
            (3, "3", 3, False, 3),  # last page
            (4, "3", 1, False, 3),  # partial page (9 total items, page 3 with page_size=4)
            (3, "99", 3, True, 1),  # beyond range -> returns first page
        ],
        ids=["first_page", "last_page", "partial_page", "beyond_range"],
    )
    def test_pagination_scenarios(
        self, rf, test_editions, user, page_size, page_num, expected_count, expected_has_more, expected_page
    ):
        """Test various pagination scenarios."""
        view = AutocompleteModelView()
        view.model = Edition
        view.page_size = page_size
        params = {"p": page_num} if page_num else {}
        request = rf.get("", params)
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == expected_count
        assert data["page"] == expected_page
        assert data["has_more"] is expected_has_more

    def test_pagination_with_search(self, rf, test_editions, user):
        """Test pagination combined with search functionality."""
        view = AutocompleteModelView()
        view.model = Edition
        view.page_size = 2
        view.search_lookups = ["name__icontains"]

        # Setup the request with proper search parameters
        # The query parameter needs to match what the view is expecting
        request = rf.get("", {"q": "Edition", "p": "2"})
        view.setup(request)
        view.query = "Edition"

        # Ensure the view processes search correctly
        queryset = view.get_queryset()
        queryset = view.search(queryset, view.query)

        # Get paginated results
        pagination_data = view.paginate_queryset(queryset)

        assert len(pagination_data["results"]) == 2
        assert all("Edition" in str(result) for result in pagination_data["results"])

    def test_pagination_preserve_ordering(self, rf, test_editions, user):
        """Test that pagination preserves ordering across pages."""
        view = AutocompleteModelView()
        view.model = Edition
        view.page_size = 3
        view.value_fields = ["id", "name", "pages", "pub_num", "year"]
        view.ordering = ["-year"]
        request = rf.get("")
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        first_page_years = [r["year"] for r in data["results"]]
        assert first_page_years == sorted(first_page_years, reverse=True)

        # Check second page
        request = rf.get("", {"p": "2"})
        view.setup(request)
        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        second_page_years = [r["year"] for r in data["results"]]
        assert second_page_years == sorted(second_page_years, reverse=True)
        assert all(y1 > y2 for y1 in first_page_years for y2 in second_page_years)


@pytest.mark.django_db
class TestAutocompleteModelViewSearch:
    """Tests for AutocompleteModelView search functionality."""

    def get_response_data(self, response: JsonResponse) -> dict:
        """Helper method to get data from response."""
        return json.loads(response.content.decode("utf-8"))

    def test_search_no_results(self, rf, test_editions, user):
        """Test search with no matching results."""
        view = AutocompleteModelView()
        view.model = Edition
        view.search_lookups = ["name__icontains"]
        request = rf.get("", {"q": "NonexistentEdition"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == 0
        assert data["has_more"] is False

    def test_search_empty_lookups(self, rf, test_editions, user):
        """Test search with no search_lookups defined."""
        Edition.objects.all().delete()

        print(f"{Edition.objects.all()=}")
        view = AutocompleteModelView()
        view.model = Edition
        view.search_lookups = []
        request = rf.get("", {"q": "Edition"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)
        print(f"{data=}")

        # Should return no results since no lookup was provided
        assert len(data["results"]) == 0

    def test_search_multiple_lookups(self, rf, test_editions, user):
        """Test search across multiple fields."""
        view = AutocompleteModelView()
        view.model = Edition
        view.search_lookups = ["name__icontains", "year__icontains"]
        request = rf.get("", {"q": "202"})  # Should match years 2021-2029
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == len(test_editions)

    def test_search_case_insensitive(self, rf, test_editions, user):
        """Test case-insensitive search."""
        view = AutocompleteModelView()
        view.model = Edition
        view.search_lookups = ["name__icontains"]
        request = rf.get("", {"q": "EDITION"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == len(test_editions)

    @pytest.mark.parametrize(
        "search_term, expected_count",
        [
            ("Edition 1", 1),
            ("Edition", 9),
            ("NonExistent", 0),
        ],
    )
    def test_basic_search(self, test_editions, rf, search_term, expected_count):
        """Test search functionality with various terms."""
        view = AutocompleteModelView()
        view.model = Edition
        view.search_lookups = ["name__icontains"]

        request = rf.get("", {"q": search_term})
        view.setup(request)

        queryset = view.get_queryset()
        assert queryset.count() == expected_count


@pytest.mark.django_db
class TestAutocompleteModelViewOrdering:
    """Tests for AutocompleteModelView ordering functionality."""

    def setup_method(self, method):
        """Set up test data before each test method."""
        # Clear any existing data
        Edition.objects.all().delete()

        # Create a list of test editions
        self.editions = []
        for i in range(1, 10):
            edition = Edition.objects.create(
                name=f"Edition {i}",
                year=f"202{i}",
                pages=str(i * 10),
                pub_num=f"PUB-{i}",
            )
            self.editions.append(edition)

    def get_response_data(self, response: JsonResponse) -> dict:
        """Helper method to get data from response."""
        return json.loads(response.content.decode("utf-8"))

    def test_default_ordering(self, rf, user):
        """Test default ordering (by id)."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "pages", "pub_num", "year"]
        request = rf.get("")
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        result_ids = [r["id"] for r in data["results"]]
        assert result_ids == sorted(result_ids)

    def test_custom_ordering_single_field(self, rf, user):
        """Test custom ordering by single field."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "pages", "pub_num", "year"]
        view.ordering = "-year"
        request = rf.get("")
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        years = [r["year"] for r in data["results"]]
        assert years == sorted(years, reverse=True)

    def test_custom_ordering_multiple_fields(self, rf, user):
        """Test custom ordering by multiple fields."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "pages", "pub_num", "year"]
        view.ordering = ["year", "name"]
        request = rf.get("")
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        # Check that results are sorted by year, then name
        results = data["results"]
        for i in range(len(results) - 1):
            current = results[i]
            next_item = results[i + 1]
            if current["year"] == next_item["year"]:
                assert current["name"] <= next_item["name"]
            else:
                assert current["year"] <= next_item["year"]


@pytest.mark.django_db
class TestAutocompleteModelViewCustomization:
    """Tests for AutocompleteModelView customization capabilities."""

    def test_hook_queryset_override(self, rf, test_editions):
        """Test overriding hook_queryset method."""

        class CustomView(AutocompleteModelView):
            """Custom view with overridden hook_queryset method."""

            def hook_queryset(self, queryset):
                """Filter editions to only those from 2020s."""
                return queryset.filter(year__startswith="202")

        view = CustomView()
        view.model = Edition
        request = rf.get("")
        view.setup(request)

        queryset = view.get_queryset()
        assert queryset.count() == len(test_editions)
        assert all(e.year.startswith("202") for e in queryset)

    def test_prepare_results_override(self, rf, test_editions, user):
        """Test overriding prepare_results method."""

        class CustomView(AutocompleteModelView):
            """Custom view with overridden prepare_results method."""

            def prepare_results(self, results):
                """Customize results to include full name."""
                return [{"custom_id": obj.id, "full_name": f"{obj.name} ({obj.year})"} for obj in results]

            def search(self, queryset, query):
                """Ensure queryset is returned regardless of search query."""
                return queryset

            def get_queryset(self):
                """Ensure we get all results."""
                queryset = super().get_queryset()
                return queryset.all()

        view = CustomView()
        view.model = Edition
        request = rf.get("", {"q": ""})  # Empty search query
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        assert len(data["results"]) > 0
        assert "custom_id" in data["results"][0]
        assert "full_name" in data["results"][0]


@pytest.mark.django_db
class TestAutocompleteModelViewErrorHandling:
    """Tests for AutocompleteModelView error handling."""

    def test_invalid_model_type(self, rf):
        """Test handling of invalid model type."""

        class InvalidModel:
            """Invalid model class."""

        view = AutocompleteModelView()
        request = rf.get("")

        with pytest.raises(ValueError, match="Unknown model type specified"):
            view.setup(request, model=InvalidModel)

    def test_malformed_filter_value(self, rf, test_editions):
        """Test handling of malformed filter values."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"f": "malformed=filter=value"})
        view.setup(request)
        view.filter_by = request.GET.get("f")

        queryset = Edition.objects.all()
        filtered_qs = view.apply_filters(queryset)

        # Should return empty queryset for malformed filter
        assert filtered_qs.count() == 0

    def test_missing_lookup_field(self, rf, test_editions):
        """Test handling of missing lookup field in filter."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        view.setup(request)
        view.filter_by = "nonexistent_field__exact=value"

        queryset = Edition.objects.all()
        filtered_qs = view.apply_filters(queryset)

        assert filtered_qs.count() == 0


@pytest.mark.django_db
class TestAutocompleteModelViewGetRequestErrorHandling:
    """Tests for error handling in AutocompleteModelView GET requests."""

    @pytest.mark.parametrize("debug", [True, False])
    def test_get_with_database_error(self, rf, user, monkeypatch, debug):
        """Test handling of database errors during GET request."""

        class ErrorView(AutocompleteModelView):
            """View that raises a database error during get_queryset."""

            def get_queryset(self):
                raise Exception("Database error")

        view = ErrorView()
        view.model = Edition
        request = rf.get("")
        request.user = user
        view.setup(request)

        # override settings.DEBUG
        from django.conf import settings

        monkeypatch.setattr(settings, "DEBUG", debug)

        response = view.get(request)
        data = json.loads(response.content.decode())

        assert response.status_code == 500
        if debug:
            assert "Database error" in data["error"]
        else:
            assert "error" not in data

        assert data["results"] == []
        assert data["page"] == 1
        assert data["has_more"] is False
        assert data["show_create_option"] is False

    @pytest.mark.parametrize("debug", [True, False])
    def test_get_with_filter_error(self, rf, user, monkeypatch, debug):
        """Test handling of filter errors during GET request."""

        class ErrorView(AutocompleteModelView):
            """View that raises a filter error during apply_filters."""

            def apply_filters(self, queryset):
                raise Exception("Filter error")

        view = ErrorView()
        view.model = Edition
        request = rf.get("", {"f": "invalid_filter"})
        request.user = user
        view.setup(request)

        # override settings.DEBUG
        from django.conf import settings

        monkeypatch.setattr(settings, "DEBUG", debug)

        response = view.get(request)
        data = json.loads(response.content.decode())

        assert response.status_code == 500
        if debug:
            assert "Filter error" in data["error"]
        else:
            assert "error" not in data

        assert data["results"] == []
        assert data["show_create_option"] is False


@pytest.mark.django_db
class TestAutocompleteModelViewEdgeCases:
    """Tests for AutocompleteModelView edge cases and error handling."""

    def setup_method(self, method):
        """Set up test data before each test method."""
        # Clear any existing data
        Edition.objects.all().delete()

        # Create test editions
        self.editions = []
        for i in range(1, 10):
            edition = Edition.objects.create(
                name=f"Edition {i}",
                year=f"202{i}",
                pages=str(i * 10),
                pub_num=f"PUB-{i}",
            )
            self.editions.append(edition)

    def get_response_data(self, response: JsonResponse) -> dict:
        """Helper method to get data from response."""
        return json.loads(response.content.decode("utf-8"))

    def test_missing_model(self, rf):
        """Test handling of missing model."""
        view = AutocompleteModelView()
        request = rf.get("")

        with pytest.raises(ValueError, match="Model must be specified"):
            view.setup(request)

    @pytest.mark.parametrize("invalid_page_size", ["0", "-5"], ids=["zero", "negative"])
    def test_invalid_page_sizes_use_default(self, rf, test_editions, user, invalid_page_size):
        """Test handling of zero and negative page sizes."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"page_size": invalid_page_size})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        # Should use default page size (20)
        assert len(data["results"]) <= 20

    def test_special_characters_in_search(self, rf, user):
        """Test handling of special characters in search query."""
        view = AutocompleteModelView()
        view.model = Edition
        view.search_lookups = ["name__icontains"]
        request = rf.get("", {"q": "Edition & % $ #"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert response.status_code == 200
        assert "results" in data

    def test_empty_get_request(self, rf, user):
        """Test handling of empty GET request."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        assert response.status_code == 200
        assert "results" in data
        assert "page" in data
        assert "has_more" in data

    def test_invalid_page_number(self, rf, test_editions, user):
        """Test handling of invalid page numbers."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"p": "not_a_number"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        # Returns first page
        assert data["page"] == 1
        assert len(data["results"]) > 0


class TestAutocompleteModelViewURLHandling:
    """Tests for URL handling in AutocompleteModelView."""

    def test_list_and_detail_urls(self, rf, test_editions):
        """Test that list and detail URLs are handled correctly in POST."""
        view = AutocompleteModelView()
        view.model = Edition
        view.list_url = "example:edition-list"
        view.detail_url = "example:edition-detail"
        request = rf.post("")
        view.setup(request)

        response = view.post(request)
        assert response.status_code == 405
        assert json.loads(response.content)["error"] == "Method not allowed"

    def test_post_method_not_allowed(self, rf):
        """Test that POST requests are not allowed."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.post("")
        view.setup(request)

        response = view.post(request)
        assert response.status_code == 405
        assert json.loads(response.content)["error"] == "Method not allowed"


@pytest.mark.django_db
class TestAutocompleteModelViewSplitSearch:
    """Tests for opt-in split_search (whitespace-aware tokenizer-based search)."""

    def _setup_editions_with_split_search(self, rf, request_q, user, *, lookups, split=True):
        view = AutocompleteModelView()
        view.model = Edition
        view.search_lookups = list(lookups)
        view.split_search = split
        request = rf.get("", {"q": request_q})
        request.user = user
        view.setup(request)
        return view, request

    def test_split_search_default_off_preserves_behavior(self, rf, test_editions, user):
        """With split_search=False (default), the whole query is one icontains."""
        view, request = self._setup_editions_with_split_search(
            rf, "Edition 1", user, lookups=["name__icontains"], split=False
        )
        response = view.get(request)
        data = json.loads(response.content.decode())
        names = sorted(r["name"] for r in data["results"])
        # Default behavior: matches Edition 1 only (literal "Edition 1" substring).
        assert names == ["Edition 1"]

    def test_split_search_and_composes_terms(self, rf, test_editions, user):
        """With split_search=True, terms are AND-composed."""
        view, request = self._setup_editions_with_split_search(
            rf, "Edition 1", user, lookups=["name__icontains"], split=True
        )
        response = view.get(request)
        data = json.loads(response.content.decode())
        names = sorted(r["name"] for r in data["results"])
        # Each term ANDed: "Edition" AND "1" >> only "Edition 1".
        assert names == ["Edition 1"]

    def test_split_search_with_quoted_phrase_preserves_phrase(self, rf, test_editions, user):
        """Quoted phrases stay as a single icontains term."""
        view, request = self._setup_editions_with_split_search(
            rf, '"Edition 1"', user, lookups=["name__icontains"], split=True
        )
        response = view.get(request)
        data = json.loads(response.content.decode())
        names = [r["name"] for r in data["results"]]
        assert "Edition 1" in names

    def test_split_search_or_across_lookups_within_term(self, rf, test_editions, user):
        """Each term is OR'd across search_lookups; terms are then ANDed."""
        # Looking for "Edition" matching name AND "1" matching either name or pages.
        view, request = self._setup_editions_with_split_search(
            rf, "Edition 1", user, lookups=["name__icontains", "pages"], split=True
        )
        response = view.get(request)
        data = json.loads(response.content.decode())
        names = [r["name"] for r in data["results"]]
        # Edition 1 has pages=1 and name contains "Edition" + "1" >> matches.
        assert "Edition 1" in names

    def test_split_search_empty_query_is_noop(self, rf, test_editions, user):
        """Empty query returns the unfiltered queryset, same as default."""
        view, request = self._setup_editions_with_split_search(
            rf, "", user, lookups=["name__icontains"], split=True
        )
        response = view.get(request)
        data = json.loads(response.content.decode())
        # All editions visible.
        assert len(data["results"]) > 0

    def test_split_search_unterminated_quote_falls_back_to_single_term(
        self, rf, test_editions, user
    ):
        """Tokenize failure should fall back to single-term icontains."""
        view, request = self._setup_editions_with_split_search(
            rf, 'Edition "1', user, lookups=["name__icontains"], split=True
        )
        # Should not raise; falls back to literal-string icontains.
        response = view.get(request)
        data = json.loads(response.content.decode())
        # The literal substring 'Edition "1' won't match anything; that's fine.
        assert "results" in data
