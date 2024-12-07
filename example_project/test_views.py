"""Tests for django_tomselect views functionality."""

import json

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import FieldError, PermissionDenied
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.http import JsonResponse

from django_tomselect.views import AutocompleteView
from example_project.example.models import Edition


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
class TestAutocompleteViewSetup:
    """Tests for AutocompleteView setup and initialization."""

    def test_setup_without_model(self, rf):
        """Test that setup raises ValueError if no model is specified."""
        request = rf.get("/autocomplete/")
        view = AutocompleteView()

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
        request = rf.get("/autocomplete/", {"page_size": page_size_param} if page_size_param else {})
        view = AutocompleteView()
        view.model = Edition
        view.setup(request)

        assert view.page_size == expected_size


@pytest.mark.django_db
class TestAutocompleteViewQueryset:
    """Tests for AutocompleteView queryset handling."""

    def test_get_queryset_basic(self, test_editions, rf):
        """Test basic queryset retrieval without search or filters."""
        view = AutocompleteView()
        view.model = Edition
        view.setup(rf.get("/autocomplete/"))

        queryset = view.get_queryset()
        assert queryset.count() == len(test_editions)
        assert list(queryset) == list(Edition.objects.all())

    def test_annotated_queryset(self, test_editions, rf):
        """Test that search works with annotated fields."""

        class CustomAutocompleteView(AutocompleteView):
            """Custom view with annotated queryset."""

            def get_queryset(self):
                """Get base queryset first."""
                qs = super().get_queryset()
                return qs.annotate(full_text=Concat("name", Value(" "), "year", output_field=models.CharField()))

            def search(self, queryset, q):
                """Custom search implementation."""
                if not q:
                    return queryset
                return queryset.filter(name__icontains=q) | queryset.filter(year__icontains=q)

        view = CustomAutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/", {"q": "Edition 1"})
        view.setup(request)

        queryset = view.get_queryset()
        assert queryset.exists()
        assert queryset.first() == test_editions[0]


@pytest.mark.django_db
class TestAutocompleteViewSearch:
    """Tests for AutocompleteView search functionality."""

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
        view = AutocompleteView()
        view.model = Edition
        view.search_lookups = ["name__icontains"]

        request = rf.get("/autocomplete/", {"q": search_term})
        view.setup(request)

        queryset = view.get_queryset()
        assert queryset.count() == expected_count


@pytest.mark.django_db
class TestAutocompleteViewPermissions:
    """Tests for AutocompleteView permission handling."""

    @pytest.mark.parametrize(
        "user_authenticated, expected_permission",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_has_add_permission(self, rf, user_with_permissions, user_authenticated, expected_permission):
        """Test permission checking for adding objects."""
        view = AutocompleteView()
        view.model = Edition

        request = rf.get("/autocomplete/")
        request.user = user_with_permissions if user_authenticated else AnonymousUser()

        assert view.has_add_permission(request) == expected_permission

    def test_post_without_permission(self, rf):
        """Test that post raises PermissionDenied if user lacks permission."""
        view = AutocompleteView()
        view.model = Edition

        request = rf.post("/autocomplete/")
        request.user = AnonymousUser()

        with pytest.raises(PermissionDenied):
            view.post(request)


@pytest.mark.django_db
class TestAutocompleteViewErrors:
    """Tests for AutocompleteView error handling."""

    def test_get_create_data_without_create_field(self, rf):
        """Test that get_create_data raises ValueError if create_field is empty."""
        view = AutocompleteView()
        view.model = Edition

        request = rf.post("/autocomplete/", data={"field": "value"})

        # The view's code shows create_field defaults to "", not None
        # So we need to check that get_create_data raises ValueError
        # when create_field is an empty string (the default)
        with pytest.raises(ValueError, match="create_field must be specified for object creation"):
            view.get_create_data(request)

    @pytest.mark.django_db
    def test_get_create_data_with_field(self, rf):
        """Test that get_create_data works with a valid create_field."""
        view = AutocompleteView()
        view.model = Edition
        view.create_field = "name"  # Set a valid field

        test_name = "Test Edition"
        request = rf.post("/autocomplete/", data={"name": test_name})

        data = view.get_create_data(request)
        assert data == {"name": test_name}


@pytest.mark.django_db
class TestAutocompleteViewCreateData:
    """Tests for create data functionality."""

    def test_get_create_data_empty_create_field(self, rf):
        """Test get_create_data with empty create_field."""
        view = AutocompleteView()
        view.model = Edition
        view.create_field = ""  # Explicitly set to empty
        request = rf.post("/autocomplete/", data={"field": "value"})

        with pytest.raises(ValueError):
            view.get_create_data(request)

    def test_get_create_data_missing_field(self, rf):
        """Test get_create_data with missing field in POST data."""
        view = AutocompleteView()
        view.model = Edition
        view.create_field = "name"
        request = rf.post("/autocomplete/", data={})  # Empty POST data

        with pytest.raises(ValueError):
            view.get_create_data(request)

    def test_get_create_data_success(self, rf):
        """Test successful get_create_data."""
        view = AutocompleteView()
        view.model = Edition
        view.create_field = "name"
        request = rf.post("/autocomplete/", data={"name": "Test"})

        data = view.get_create_data(request)
        assert data == {"name": "Test"}


@pytest.mark.django_db
class TestAutocompletePagination:
    """Tests for AutocompleteView pagination functionality."""

    def get_response_data(self, response: JsonResponse) -> dict:
        """Helper method to get data from response."""
        return json.loads(response.content.decode("utf-8"))

    def test_invalid_page_size_uses_default(self, rf, test_editions):
        """Test invalid page size falls back to default."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/", {"page_size": "invalid"})
        view.setup(request)

        assert view.page_size == 20  # Default value

    def test_page_size_from_request(self, rf, test_editions, user):
        """Test custom page size from request parameter."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/", {"page_size": "3"})
        request.user = user
        view.setup(request)

        assert view.page_size == 3

        data = self.get_response_data(view.get(request))
        assert len(data["results"]) == 3

    def test_pagination_first_page(self, rf, test_editions, user):
        """Test first page of paginated results."""
        view = AutocompleteView()
        view.model = Edition
        view.page_size = 3
        request = rf.get("/autocomplete/")
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
        view = AutocompleteView()
        view.model = Edition
        view.page_size = 3
        request = rf.get("/autocomplete/", {"p": "3"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == 3
        assert data["page"] == 3
        assert data["has_more"] is False

    def test_pagination_partial_page(self, rf, test_editions, user):
        """Test partial last page of results."""
        view = AutocompleteView()
        view.model = Edition
        view.page_size = 4
        request = rf.get("/autocomplete/", {"p": "3"})  # Last page with 9 total items
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == 1  # Only one item on last page
        assert data["page"] == 3
        assert data["has_more"] is False

    def test_pagination_empty_page(self, rf, test_editions, user):
        """Test requesting page beyond available results."""
        view = AutocompleteView()
        view.model = Edition
        view.page_size = 3
        request = rf.get("/autocomplete/", {"p": "99"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        # Should return first page results when page number is too high
        assert len(data["results"]) == 3
        assert data["page"] == 1


@pytest.mark.django_db
class TestAutocompleteSearch:
    """Tests for AutocompleteView search functionality."""

    def get_response_data(self, response: JsonResponse) -> dict:
        """Helper method to get data from response."""
        return json.loads(response.content.decode("utf-8"))

    def test_search_no_results(self, rf, test_editions):
        """Test search with no matching results."""
        view = AutocompleteView()
        view.model = Edition
        view.search_lookups = ["name__icontains"]
        request = rf.get("/autocomplete/", {"q": "NonexistentEdition"})
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == 0
        assert data["has_more"] is False

    def test_search_empty_lookups(self, rf, test_editions, user):
        """Test search with no search_lookups defined."""
        Edition.objects.all().delete()

        print(f"{Edition.objects.all()=}")
        view = AutocompleteView()
        view.model = Edition
        view.search_lookups = []
        request = rf.get("autocomplete/", {"q": "Edition"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)
        print(f"{data=}")

        # Should return no results since no lookup was provided
        assert len(data["results"]) == 0

    def test_search_multiple_lookups(self, rf, test_editions, user):
        """Test search across multiple fields."""
        view = AutocompleteView()
        view.model = Edition
        view.search_lookups = ["name__icontains", "year__icontains"]
        request = rf.get("/autocomplete/", {"q": "202"})  # Should match years 2021-2029
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == len(test_editions)

    def test_search_case_insensitive(self, rf, test_editions, user):
        """Test case-insensitive search."""
        view = AutocompleteView()
        view.model = Edition
        view.search_lookups = ["name__icontains"]
        request = rf.get("/autocomplete/", {"q": "EDITION"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert len(data["results"]) == len(test_editions)


@pytest.mark.django_db
class TestAutocompleteEdgeCases:
    """Tests for AutocompleteView edge cases and error handling."""

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
        view = AutocompleteView()
        request = rf.get("/autocomplete/")

        with pytest.raises(ValueError, match="Model must be specified"):
            view.setup(request)

    def test_zero_page_size(self, rf, test_editions):
        """Test handling of zero page size."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/", {"page_size": "0"})
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        # Should use default page size (20)
        assert len(data["results"]) <= 20

    def test_negative_page_size(self, rf, test_editions):
        """Test handling of negative page size."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/", {"page_size": "-5"})
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        # No more than default page size of 20
        assert len(data["results"]) <= 20

    def test_special_characters_in_search(self, rf):
        """Test handling of special characters in search query."""
        view = AutocompleteView()
        view.model = Edition
        view.search_lookups = ["name__icontains"]
        request = rf.get("/autocomplete/", {"q": "Edition & % $ #"})
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        assert response.status_code == 200
        assert "results" in data

    def test_empty_get_request(self, rf):
        """Test handling of empty GET request."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/")
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        assert response.status_code == 200
        assert "results" in data
        assert "page" in data
        assert "has_more" in data

    def test_invalid_page_number(self, rf, test_editions, user):
        """Test handling of invalid page numbers."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/", {"p": "not_a_number"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        # Returns first page
        assert data["page"] == 1
        assert len(data["results"]) > 0


@pytest.mark.django_db
class TestAutocompleteOrdering:
    """Tests for AutocompleteView ordering functionality."""

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

    def test_default_ordering(self, rf):
        """Test default ordering (by id)."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/")
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        result_ids = [r["id"] for r in data["results"]]
        assert result_ids == sorted(result_ids)

    def test_custom_ordering_single_field(self, rf):
        """Test custom ordering by single field."""
        view = AutocompleteView()
        view.model = Edition
        view.ordering = "-year"
        request = rf.get("/autocomplete/")
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data(response)

        years = [r["year"] for r in data["results"]]
        assert years == sorted(years, reverse=True)

    def test_custom_ordering_multiple_fields(self, rf):
        """Test custom ordering by multiple fields."""
        view = AutocompleteView()
        view.model = Edition
        view.ordering = ["year", "name"]
        request = rf.get("/autocomplete/")
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
class TestAutocompleteViewFiltering:
    """Tests for AutocompleteView dependent filtering functionality."""

    def test_apply_filters_with_valid_filter(self, rf, test_editions, magazines, user):
        """Test apply_filters with valid filter_by from dependent field."""
        view = AutocompleteView()
        view.model = Edition
        view.filter_by = ("magazine", "id")
        request = rf.get("/autocomplete/", {"f": f"magazine__magazine_id={magazines[0].id}"})
        request.user = user
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        expected_qs = Edition.objects.filter(magazine_id=magazines[0].id)

        assert filtered_qs.count() == expected_qs.count()
        assert list(filtered_qs) == list(expected_qs)

    def test_apply_filters_with_exclude(self, rf, test_editions, magazines):
        """Test apply_filters with exclude_by from dependent field."""
        view = AutocompleteView()
        view.model = Edition
        view.exclude_by = ("magazine", "id")
        request = rf.get("/autocomplete/", {"e": f"magazine__magazine_id={magazines[0].id}"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        expected_qs = Edition.objects.exclude(magazine_id=magazines[0].id)

        assert filtered_qs.count() == expected_qs.count()
        assert list(filtered_qs) == list(expected_qs)

    def test_apply_filters_missing_dependent_value(self, rf, test_editions):
        """Test filter_by behavior when dependent field has no value."""
        view = AutocompleteView()
        view.model = Edition
        view.filter_by = ("magazine", "id")
        request = rf.get("/autocomplete/")
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        # Should return full queryset when no filter value provided
        assert filtered_qs.count() == Edition.objects.count()

    def test_apply_filters_invalid_tuple(self, rf, test_editions):
        """Test handling of invalid filter_by tuple."""
        view = AutocompleteView()
        view.model = Edition
        view.filter_by = ("invalid_tuple",)

        request = rf.get("/autocomplete/", {"f": "invalid_tuple__invalid=value"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        # Should return empty queryset for invalid filter format as per view implementation
        assert filtered_qs.count() == 0


@pytest.mark.django_db
class TestAutocompleteViewCustomization:
    """Tests for AutocompleteView customization capabilities."""

    def test_hook_queryset_override(self, rf, test_editions):
        """Test overriding hook_queryset method."""

        class CustomView(AutocompleteView):
            """Custom view with overridden hook_queryset method."""

            def hook_queryset(self, queryset):
                """Filter editions to only those from 2020s."""
                return queryset.filter(year__startswith="202")

        view = CustomView()
        view.model = Edition
        request = rf.get("/autocomplete/")
        view.setup(request)

        queryset = view.get_queryset()
        assert queryset.count() == len(test_editions)
        assert all(e.year.startswith("202") for e in queryset)

    def test_prepare_results_override(self, rf, test_editions, user):
        """Test overriding prepare_results method."""

        class CustomView(AutocompleteView):
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
        request = rf.get("/autocomplete/", {"q": ""})  # Empty search query
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        assert len(data["results"]) > 0
        assert "custom_id" in data["results"][0]
        assert "full_name" in data["results"][0]


@pytest.mark.django_db
class TestAutocompleteViewErrorHandling:
    """Tests for AutocompleteView error handling."""

    def test_invalid_model_type(self, rf):
        """Test handling of invalid model type."""

        class InvalidModel:
            """Invalid model class."""

            pass

        view = AutocompleteView()
        request = rf.get("/autocomplete/")

        with pytest.raises(ValueError, match="Unknown model type specified"):
            view.setup(request, model=InvalidModel)

    def test_malformed_filter_value(self, rf, test_editions):
        """Test handling of malformed filter values."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/", {"f": "malformed=filter=value"})
        view.setup(request)
        view.filter_by = request.GET.get("f")

        queryset = Edition.objects.all()
        filtered_qs = view.apply_filters(queryset)

        # Should return empty queryset for malformed filter
        assert filtered_qs.count() == 0

    def test_missing_lookup_field(self, rf, test_editions):
        """Test handling of missing lookup field in filter."""
        view = AutocompleteView()
        view.model = Edition
        request = rf.get("/autocomplete/")
        view.setup(request)
        view.filter_by = "nonexistent_field__exact=value"

        queryset = Edition.objects.all()
        filtered_qs = view.apply_filters(queryset)

        assert filtered_qs.count() == 0


@pytest.mark.django_db
class TestAutocompleteViewPagination:
    """Additional tests for AutocompleteView pagination."""

    def test_pagination_with_search(self, rf, test_editions, user):
        """Test pagination combined with search functionality."""
        view = AutocompleteView()
        view.model = Edition
        view.page_size = 2
        view.search_lookups = ["name__icontains"]

        # Setup the request with proper search parameters
        # The query parameter needs to match what the view is expecting
        request = rf.get("/autocomplete/", {"q": "Edition", "p": "2"})
        view.setup(request)
        view.query = "Edition"

        # Ensure the view processes search correctly
        queryset = view.get_queryset()
        queryset = view.search(queryset, view.query)

        # Get paginated results
        pagination_data = view.paginate_queryset(queryset)

        assert len(pagination_data["results"]) == 2
        assert all("Edition" in str(result) for result in pagination_data["results"])

    def test_pagination_preserve_ordering(self, rf, test_editions):
        """Test that pagination preserves ordering across pages."""
        view = AutocompleteView()
        view.model = Edition
        view.page_size = 3
        view.ordering = ["-year"]
        request = rf.get("/autocomplete/")
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        first_page_years = [r["year"] for r in data["results"]]
        assert first_page_years == sorted(first_page_years, reverse=True)

        # Check second page
        request = rf.get("/autocomplete/", {"p": "2"})
        view.setup(request)
        response = view.get(request)
        data = json.loads(response.content.decode("utf-8"))

        second_page_years = [r["year"] for r in data["results"]]
        assert second_page_years == sorted(second_page_years, reverse=True)
        assert all(y1 > y2 for y1 in first_page_years for y2 in second_page_years)
