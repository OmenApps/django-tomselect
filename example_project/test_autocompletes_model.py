"""Tests for django_tomselect AutocompleteModelView functionality."""

import json

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.http import JsonResponse

from django_tomselect.autocompletes import AutocompleteModelView
from example_project.example.models import Edition, Magazine


@pytest.fixture
def test_editions(db, magazines):
    """Create a specific set of test editions with known data."""
    Edition.objects.all().delete()  # Clear any existing editions

    editions = []
    for i in range(1, 10):  # Create exactly 9 editions
        edition = Edition.objects.create(
            name=f"Edition {i}",
            year=f"202{i}",  # 2021-2029
            pages=str(i * 10),
            pub_num=f"PUB-{i}",
            magazine=magazines[0] if magazines else None,
        )
        editions.append(edition)

    return editions


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

    def test_pagination_first_page(self, rf, test_editions, user):
        """Test first page of paginated results."""
        view = AutocompleteModelView()
        view.model = Edition
        view.page_size = 3
        request = rf.get("")
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == 3
        assert data["page"] == 1
        assert data["has_more"] is True

        # Verify we got first 3 editions
        result_ids = [r["id"] for r in data["results"]]
        expected_ids = [e.id for e in test_editions[:3]]
        assert result_ids == expected_ids

    def test_pagination_last_page(self, rf, test_editions, user):
        """Test last page of paginated results."""
        view = AutocompleteModelView()
        view.model = Edition
        view.page_size = 3
        request = rf.get("", {"p": "3"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == 3
        assert data["page"] == 3
        assert data["has_more"] is False

    def test_pagination_partial_page(self, rf, test_editions, user):
        """Test partial last page of results."""
        view = AutocompleteModelView()
        view.model = Edition
        view.page_size = 4
        request = rf.get("", {"p": "3"})  # Last page with 9 total items
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == 1  # Only one item on last page
        assert data["page"] == 3
        assert data["has_more"] is False

    def test_pagination_empty_page(self, rf, test_editions, user):
        """Test requesting page beyond available results."""
        view = AutocompleteModelView()
        view.model = Edition
        view.page_size = 3
        request = rf.get("", {"p": "99"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        # Should return first page results when page number is too high
        assert len(data["results"]) == 3
        assert data["page"] == 1

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
class TestAutocompleteModelViewFiltering:
    """Tests for AutocompleteModelView dependent filtering functionality."""

    def test_apply_filters_with_valid_filter(self, rf, test_editions, magazines, user):
        """Test apply_filters with valid filter_by from dependent field."""
        view = AutocompleteModelView()
        view.model = Edition
        view.filter_by = ("magazine", "id")
        request = rf.get("", {"f": f"magazine__magazine_id={magazines[0].id}"})
        request.user = user
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        expected_qs = Edition.objects.filter(magazine_id=magazines[0].id)

        assert filtered_qs.count() == expected_qs.count()
        assert list(filtered_qs) == list(expected_qs)

    def test_apply_filters_with_exclude(self, rf, test_editions, magazines):
        """Test apply_filters with exclude_by from dependent field."""
        view = AutocompleteModelView()
        view.model = Edition
        view.exclude_by = ("magazine", "id")
        request = rf.get("", {"e": f"magazine__magazine_id={magazines[0].id}"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        expected_qs = Edition.objects.exclude(magazine_id=magazines[0].id)

        assert filtered_qs.count() == expected_qs.count()
        assert list(filtered_qs) == list(expected_qs)

    def test_apply_filters_missing_dependent_value(self, rf, test_editions):
        """Test filter_by behavior when dependent field has no value."""
        view = AutocompleteModelView()
        view.model = Edition
        view.filter_by = ("magazine", "id")
        request = rf.get("")
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        # Should return full queryset when no filter value provided
        assert filtered_qs.count() == Edition.objects.count()

    def test_apply_filters_invalid_tuple(self, rf, test_editions):
        """Test handling of invalid filter_by tuple."""
        view = AutocompleteModelView()
        view.model = Edition
        view.filter_by = ("invalid_tuple",)

        request = rf.get("", {"f": "invalid_tuple__invalid=value"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        # Should return empty queryset for invalid filter format as per view implementation
        assert filtered_qs.count() == 0

    def test_filter_by_and_exclude_by_together(self, rf, test_editions):
        """Test behavior when both filter_by and exclude_by are present."""
        view = AutocompleteModelView()
        view.model = Edition

        # Since filter_by and exclude_by aren't handled together in the view,
        # we need to test them individually first
        request_filter = rf.get(
            "/autocomplete/",
            {
                "f": "magazine__magazine_id=1",
            },
        )
        view.setup(request_filter)
        filter_qs = view.apply_filters(Edition.objects.all())

        request_exclude = rf.get("", {"e": "magazine__magazine_id=2"})
        view.setup(request_exclude)
        _ = view.apply_filters(Edition.objects.all())

        # Now test both together
        request_both = rf.get("", {"f": "magazine__magazine_id=1", "e": "magazine__magazine_id=2"})
        view.setup(request_both)
        both_qs = view.apply_filters(Edition.objects.all())

        # The view processes each independently, so results should match filter_qs
        assert both_qs.count() == filter_qs.count()

    def test_filter_by_invalid_format(self, rf, test_editions):
        """Test filter_by with invalid format."""
        view = AutocompleteModelView()
        view.model = Edition
        invalid_filters = ["invalid", "field==value", "field=value=extra", "=value", "field="]

        for invalid_filter in invalid_filters:
            request = rf.get("", {"f": invalid_filter})
            view.setup(request)
            filtered_qs = view.apply_filters(Edition.objects.all())
            assert filtered_qs.count() == 0

    def test_exclude_by_invalid_format(self, rf, test_editions):
        """Test exclude_by with invalid format."""
        view = AutocompleteModelView()
        view.model = Edition
        invalid_filters = ["invalid", "field==value", "field=value=extra", "=value", "field="]

        for invalid_filter in invalid_filters:
            request = rf.get("", {"e": invalid_filter})
            view.setup(request)
            filtered_qs = view.apply_filters(Edition.objects.all())
            assert filtered_qs.count() == 0

    def test_filter_by_nonexistent_field(self, rf, test_editions):
        """Test filter_by with nonexistent field."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"f": "nonexistent_field__exact=value"})
        view.setup(request)
        filtered_qs = view.apply_filters(Edition.objects.all())
        assert filtered_qs.count() == 0

    def test_exclude_by_nonexistent_field(self, rf, test_editions):
        """Test exclude_by with nonexistent field."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"e": "nonexistent_field__exact=value"})
        view.setup(request)
        filtered_qs = view.apply_filters(Edition.objects.all())
        assert filtered_qs.count() == 0

    def test_filter_by_with_nested_foreign_key_lookup(self, rf, test_editions, magazines):
        """Test filter_by with nested foreign key lookup (double underscores in lookup field)."""
        # Create magazines
        magazine1 = magazines[0]
        magazine1.name = "Tech Magazine"
        magazine1.save()

        magazine2 = magazines[1] if len(magazines) > 1 else Magazine.objects.create(name="Science Magazine")
        magazine2.name = "Science Magazine"
        magazine2.save()

        # Update editions to use the magazines
        for edition in test_editions[:5]:
            edition.magazine = magazine1
            edition.save()
        for edition in test_editions[5:]:
            edition.magazine = magazine2
            edition.save()

        view = AutocompleteModelView()
        view.model = Edition
        view.filter_by = ("magazine", "magazine__name")
        request = rf.get("", {"f": f"magazine__magazine__name={magazine1.name}"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        expected_qs = Edition.objects.filter(magazine__name=magazine1.name)

        assert filtered_qs.count() == expected_qs.count()
        assert filtered_qs.count() == 5
        assert all(edition.magazine.name == "Tech Magazine" for edition in filtered_qs)

    def test_exclude_by_with_nested_foreign_key_lookup(self, rf, test_editions, magazines):
        """Test exclude_by with nested foreign key lookup (double underscores in lookup field)."""
        # Create magazines
        magazine1 = magazines[0]
        magazine1.name = "Tech Magazine"
        magazine1.save()

        magazine2 = magazines[1] if len(magazines) > 1 else Magazine.objects.create(name="Science Magazine")
        magazine2.name = "Science Magazine"
        magazine2.save()

        # Update editions to use the magazines
        for edition in test_editions[:5]:
            edition.magazine = magazine1
            edition.save()
        for edition in test_editions[5:]:
            edition.magazine = magazine2
            edition.save()

        view = AutocompleteModelView()
        view.model = Edition
        view.exclude_by = ("magazine", "magazine__name")
        request = rf.get("", {"e": f"magazine__magazine__name={magazine1.name}"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        expected_qs = Edition.objects.exclude(magazine__name=magazine1.name)

        assert filtered_qs.count() == expected_qs.count()
        assert filtered_qs.count() == 4
        assert all(edition.magazine.name == "Science Magazine" for edition in filtered_qs)

    def test_filter_by_with_deeper_nested_lookup(self, rf, db):
        """Test filter_by with deeper level of nesting in the lookup field."""
        from example_project.example.models import Category

        # Create a set of nested categories
        parent_cat = Category.objects.create(name="Technology")
        Category.objects.create(name="Software", parent=parent_cat)

        magazine = Magazine.objects.create(name="Tech Magazine")
        Edition.objects.create(name="Special Edition", year="2024", pages="100", pub_num="SP-1", magazine=magazine)

        view = AutocompleteModelView()
        view.model = Edition
        view.filter_by = ("magazine", "magazine__edition__magazine__name")
        request = rf.get("", {"f": f"magazine__magazine__edition__magazine__name={magazine.name}"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        expected_qs = Edition.objects.filter(magazine__edition__magazine__name=magazine.name)

        # Deeply nested lookup
        assert filtered_qs.count() == expected_qs.count()

    def test_filter_by_with_spaces_in_value(self, rf, magazines):
        """Test filter_by when the value contains spaces."""
        # Create a magazine with spaces in its name
        magazine = Magazine.objects.create(name="Tech Science Magazine")
        Edition.objects.create(name="Special Edition", year="2024", pages="100", pub_num="SP-1", magazine=magazine)

        view = AutocompleteModelView()
        view.model = Edition
        view.filter_by = ("magazine", "magazine__name")
        request = rf.get("", {"f": "magazine__magazine__name=Tech Science Magazine"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        assert filtered_qs.count() == 1
        assert filtered_qs.first().magazine.name == "Tech Science Magazine"


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

        assert response.status_code == 200  # Should still return 200
        if debug:
            assert data["error"] == "Database error"
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

        assert response.status_code == 200
        if debug:
            assert data["error"] == "Filter error"
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

    def test_zero_page_size(self, rf, test_editions, user):
        """Test handling of zero page size."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"page_size": "0"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        # Should use default page size (20)
        assert len(data["results"]) <= 20

    def test_negative_page_size(self, rf, test_editions, user):
        """Test handling of negative page size."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"page_size": "-5"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        # No more than default page size of 20
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


@pytest.mark.django_db
class TestAutocompleteModelViewPermissions:
    """Tests for AutocompleteModelView permissions handling."""

    class NoPermissionsView(AutocompleteModelView):
        """Test view with no permissions required."""

        model = Edition
        permission_required = None
        search_lookups = ["name__icontains"]

    class WithPermissionsView(AutocompleteModelView):
        """Test view with explicit permissions required."""

        model = Edition
        permission_required = ["example.view_edition"]
        search_lookups = ["name__icontains"]

    def test_no_permissions_required(self, mock_request):
        """Test that views with permission_required = None don't check permissions."""
        view = self.NoPermissionsView()
        view.setup(mock_request)

        # This should not raise PermissionDenied
        response = view.dispatch(mock_request)
        assert response.status_code == 200

    def test_explicit_permissions_required_with_permission(self, mock_request):
        """Test that views with explicit permissions work when user has permission."""
        view = self.WithPermissionsView()
        view.setup(mock_request)

        # Should not raise PermissionDenied since mock_request user has all permissions
        response = view.dispatch(mock_request)
        assert response.status_code == 200

    def test_explicit_permissions_required_without_permission(self, user):
        """Test that views with explicit permissions fail when user lacks permission."""

        class UnauthorizedRequest:
            """Mock request with unauthorized user."""

            def __init__(self, user):
                self.user = user
                self.method = "GET"
                self.GET = {}

            def get_full_path(self):
                return "/test/"

        request = UnauthorizedRequest(user)
        view = self.WithPermissionsView()
        view.setup(request)

        # Should raise PermissionDenied since user doesn't have permission
        with pytest.raises(PermissionDenied):
            view.dispatch(request)

    def test_get_permission_required_none(self, mock_request):
        """Test that get_permission_required returns empty list when permission_required is None."""
        view = self.NoPermissionsView()
        view.setup(mock_request)
        assert view.get_permission_required() == []

    def test_get_permission_required_list(self, mock_request):
        """Test that get_permission_required returns list for explicit permissions."""
        view = self.WithPermissionsView()
        view.setup(mock_request)
        assert view.get_permission_required() == ["example.view_edition"]

    def test_get_permission_required_string(self, mock_request):
        """Test that get_permission_required handles string permission."""

        class StringPermissionView(AutocompleteModelView):
            """Test view with string permission_required."""

            model = Edition
            permission_required = "example.view_edition"

        view = StringPermissionView()
        view.setup(mock_request)
        assert view.get_permission_required() == ["example.view_edition"]

    def test_has_permission_with_none(self, mock_request):
        """Test that has_permission returns True when no permissions are required."""
        view = self.NoPermissionsView()
        view.setup(mock_request)
        assert view.has_permission(mock_request) is True

    def test_has_permission_with_allow_anonymous(self, mock_request):
        """Test that has_permission returns True when allow_anonymous is True."""
        view = self.WithPermissionsView()
        view.allow_anonymous = True
        view.setup(mock_request)
        assert view.has_permission(mock_request) is True

    def test_has_permission_with_skip_authorization(self, mock_request):
        """Test that has_permission returns True when skip_authorization is True."""
        view = self.WithPermissionsView()
        view.skip_authorization = True
        view.setup(mock_request)
        assert view.has_permission(mock_request) is True

    def test_unauthenticated_user(self):
        """Test that has_permission returns False for unauthenticated users."""

        class UnauthenticatedUser:
            """Mock user class for unauthenticated users."""

            id = 1
            is_authenticated = False

        class UnauthenticatedRequest:
            """Mock request class for unauthenticated requests."""

            def __init__(self):
                self.user = UnauthenticatedUser()
                self.method = "GET"
                self.GET = {}

            def get_full_path(self):
                """Mock method to get full path."""
                return "/test/"

        request = UnauthenticatedRequest()
        view = self.WithPermissionsView()
        view.setup(request)
        assert view.has_permission(request) is False

    def test_queryset_with_no_permissions(self, mock_request, editions):
        """Test that queryset is accessible when no permissions are required."""
        view = self.NoPermissionsView()
        view.setup(mock_request)
        queryset = view.get_queryset()
        assert queryset.count() == len(editions)

    def test_queryset_with_permissions(self, mock_request, editions):
        """Test that queryset is accessible with proper permissions."""
        view = self.WithPermissionsView()
        view.setup(mock_request)
        queryset = view.get_queryset()
        assert queryset.count() == len(editions)

    def test_has_permission_anonymous_user(self, rf):
        """Test permission handling for anonymous users."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)

        assert not view.has_permission(request)

    def test_has_permission_skip_authorization(self, rf):
        """Test permission handling when skip_authorization is True."""
        view = AutocompleteModelView()
        view.model = Edition
        view.skip_authorization = True
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)

        assert view.has_permission(request)

    def test_has_permission_allow_anonymous(self, rf):
        """Test permission handling when allow_anonymous is True."""
        view = AutocompleteModelView()
        view.model = Edition
        view.allow_anonymous = True
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)

        assert view.has_permission(request)

    def test_permission_required_string(self, rf, user):
        """Test handling of string permission_required."""
        view = AutocompleteModelView()
        view.model = Edition
        view.permission_required = "example.view_edition"
        request = rf.get("")
        request.user = user
        view.setup(request)

        assert not view.has_permission(request)  # Should be False since user has no perms

    def test_permission_required_list(self, rf, user):
        """Test handling of list permission_required."""
        view = AutocompleteModelView()
        view.model = Edition
        view.permission_required = ["example.view_edition", "example.add_edition"]
        request = rf.get("")
        request.user = user
        view.setup(request)

        assert not view.has_permission(request)  # Should be False since user has no perms

    def test_permission_no_requirements(self, rf, user):
        """Test permission handling when no permissions are required."""
        view = AutocompleteModelView()
        view.model = Edition
        view.permission_required = []
        request = rf.get("")
        request.user = user
        view.setup(request)

        assert view.has_permission(request)

    def test_object_permission_default(self, rf, test_editions):
        """Test default object-level permission handling."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")

        assert view.has_object_permission(request, test_editions[0])

    def test_object_permission_custom_handler(self, rf, test_editions):
        """Test custom object-level permission handler."""

        class CustomView(AutocompleteModelView):
            """Custom view with custom object-level permission handler."""

            def has_view_permission(self, request, obj):
                """Custom permission handler."""
                return obj.year.startswith("202")

        view = CustomView()
        view.model = Edition
        request = rf.get("")

        assert view.has_object_permission(request, test_editions[0], "view")

    def test_dispatch_permission_denied(self, rf):
        """Test dispatch method when permission is denied."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)

        with pytest.raises(PermissionDenied):
            view.dispatch(request)

    def test_handle_no_permission_anonymous(self, rf):
        """Test handle_no_permission for anonymous users."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("/test/")
        request.user = AnonymousUser()
        view.setup(request)  # Add setup so view.user is set

        response = view.handle_no_permission(request)
        assert response.url.startswith("/accounts/login/")

    def test_add_permission_anonymous(self, rf):
        """Test add permission for anonymous users."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)  # Add setup so view.user is set

        assert not view.has_add_permission(request)

    def test_add_permission_authenticated(self, rf, user):
        """Test add permission for authenticated users without permissions."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        request.user = user
        view.setup(request)  # Add setup so view.user is set

        assert not view.has_add_permission(request)

    def test_invalidate_permissions_user(self, rf, user):
        """Test invalidating permissions for specific user."""
        view = AutocompleteModelView()
        view.model = Edition

        # Should not raise any errors
        view.invalidate_permissions(user)

    def test_invalidate_permissions_all(self, rf):
        """Test invalidating all permissions."""
        view = AutocompleteModelView()
        view.model = Edition

        # Should not raise any errors
        view.invalidate_permissions()


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
class TestVirtualFields:
    """Tests for virtual fields functionality in AutocompleteModelView."""

    def test_init_subclass_creates_new_lists(self):
        """Test that __init_subclass__ creates a new value_fields list for each subclass."""
        # Create two subclasses with different value_fields
        class FirstAutocompleteView(AutocompleteModelView):
            model = Edition
            value_fields = ["id", "name"]

        class SecondAutocompleteView(AutocompleteModelView):
            model = Edition
            value_fields = ["id", "year"]

        # Modify the value_fields of one subclass
        FirstAutocompleteView.value_fields.append("pages")

        # Verify each class has its own value_fields list
        assert FirstAutocompleteView.value_fields == ["id", "name", "pages"]
        assert SecondAutocompleteView.value_fields == ["id", "year"]
        assert AutocompleteModelView.value_fields == []

    def test_virtual_fields_excluded_from_query(self, rf):
        """Test that virtual fields are excluded from database queries."""

        class CustomAutocompleteView(AutocompleteModelView):
            """Custom autocomplete view with virtual field."""
            model = Edition
            value_fields = ["id", "name", "display_name"]
            virtual_fields = ["display_name"]

            def hook_prepare_results(self, results):
                for result in results:
                    result["display_name"] = f"{result['name']} (Edition)"
                return results

        view = CustomAutocompleteView()
        request = rf.get("")
        view.setup(request)

        # This should not raise a FieldError, since display_name should be excluded from the query
        fields = view.get_value_fields()
        assert "display_name" not in fields
        assert set(fields) == {"id", "name"}

    def test_hook_prepare_results_with_virtual_field(self, rf, test_editions):
        """Test that hook_prepare_results can add virtual fields."""

        class CustomAutocompleteView(AutocompleteModelView):
            """Custom autocomplete view with virtual field."""
            model = Edition
            value_fields = ["id", "name", "year"]
            virtual_fields = ["combined"]

            def hook_prepare_results(self, results):
                for result in results:
                    result["combined"] = f"{result['name']} ({result['year']})"
                return results

        view = CustomAutocompleteView()
        request = rf.get("")
        view.setup(request)

        # Get the results directly from hook_prepare_results
        queryset = view.get_queryset()
        results = list(queryset.values(*view.get_value_fields()))
        modified_results = view.hook_prepare_results(results)

        # Check that the virtual field is added
        assert len(modified_results) > 0
        assert "combined" in modified_results[0]
        assert modified_results[0]["combined"] == f"{modified_results[0]['name']} ({modified_results[0]['year']})"
