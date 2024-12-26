"""Tests for django_tomselect AutocompleteIterablesView functionality."""

import json

import pytest
from django.db.models import IntegerChoices, TextChoices
from django.http import JsonResponse

from django_tomselect.autocompletes import AutocompleteIterablesView
from example_project.example.models import (
    ArticlePriority,
    ArticleStatus,
    Edition,
    word_count_range,
)


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
class TestAutocompleteIterablesView:
    """Tests for AutocompleteIterablesView functionality."""

    def get_response_data(self, response: JsonResponse) -> dict:
        """Helper method to get data from response."""
        return response.content.decode("utf-8")

    def get_response_data_json(self, response: JsonResponse) -> dict:
        """Helper method to get data from response."""
        return json.loads(response.content.decode("utf-8"))

    def test_get_iterable_text_choices(self, rf):
        """Test get_iterable with TextChoices."""

        class CustomTextChoices(TextChoices):
            """Custom TextChoices class for testing."""

            ONE = "one", "First Choice"
            TWO = "two", "Second Choice"
            THREE = "three", "Third Choice"

        view = AutocompleteIterablesView()
        view.iterable = CustomTextChoices
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert len(items) == 3
        assert items[0] == {"value": "one", "label": "First Choice"}
        assert items[1] == {"value": "two", "label": "Second Choice"}
        assert items[2] == {"value": "three", "label": "Third Choice"}

    def test_get_iterable_integer_choices(self, rf):
        """Test get_iterable with IntegerChoices."""

        class CustomIntegerChoices(IntegerChoices):
            """Custom IntegerChoices class for testing."""

            ONE = 1, "First"
            TWO = 2, "Second"
            THREE = 3, "Third"

        view = AutocompleteIterablesView()
        view.iterable = CustomIntegerChoices
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert len(items) == 3
        assert items[0] == {"value": "1", "label": "First"}
        assert items[1] == {"value": "2", "label": "Second"}
        assert items[2] == {"value": "3", "label": "Third"}

    def test_get_iterable_tuple_range(self, rf):
        """Test get_iterable with tuple range like word_count_range."""
        test_range = [(0, 100), (100, 200), (200, 300)]

        view = AutocompleteIterablesView()
        view.iterable = test_range
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert len(items) == 3
        assert items[0] == {"value": "(0, 100)", "label": "0 - 100 words"}
        assert items[1] == {"value": "(100, 200)", "label": "100 - 200 words"}
        assert items[2] == {"value": "(200, 300)", "label": "200 - 300 words"}

    def test_get_iterable_simple_list(self, rf):
        """Test get_iterable with simple list."""
        simple_list = [2020, 2021, 2022, 2023]

        view = AutocompleteIterablesView()
        view.iterable = simple_list
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert len(items) == 4
        assert all(isinstance(item["value"], str) for item in items)
        assert [item["value"] for item in items] == ["2020", "2021", "2022", "2023"]

    def test_get_iterable_empty(self, rf):
        """Test get_iterable with empty iterable."""
        view = AutocompleteIterablesView()
        view.iterable = []
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert items == []

    def test_get_iterable_none(self, rf):
        """Test get_iterable with None iterable."""
        view = AutocompleteIterablesView()
        view.iterable = None
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert items == []

    def test_search_functionality(self, rf):
        """Test search functionality with ArticleStatus choices."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"q": "draft"})
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data_json(response)

        assert len(data["results"]) == 1
        assert data["results"][0]["value"] == "draft"
        assert data["results"][0]["label"] == "Draft"

    def test_search_case_insensitive(self, rf):
        """Test case-insensitive search."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"q": "DRAFT"})
        view.setup(request)

        items = view.get_iterable()
        filtered = view.search(items)
        assert len(filtered) == 1
        assert filtered[0]["value"] == "draft"

        response = view.get(request)
        data = self.get_response_data_json(response)

        assert len(data["results"]) == 1
        assert data["results"][0]["value"] == "draft"
        assert data["results"][0]["label"] == "Draft"

    def test_search_no_results(self, rf):
        """Test search with no matching results."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"q": "nonexistent"})
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data_json(response)

        assert len(data["results"]) == 0
        assert data["has_more"] is False

    def test_pagination(self, rf):
        """Test pagination of iterable results."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        view.page_size = 2
        request = rf.get("", {"p": "1"})
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data_json(response)

        assert len(data["results"]) == 2
        assert data["has_more"] is True
        assert data["page"] == 1

    def test_pagination_last_page(self, rf):
        """Test pagination last page."""
        total_choices = len(ArticleStatus.choices)
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        view.page_size = 2
        last_page = (total_choices + 1) // 2
        request = rf.get("", {"p": str(last_page)})
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data_json(response)

        assert data["has_more"] is False
        assert data["page"] == last_page

    @pytest.mark.parametrize("invalid_page", ["-1", "0", "invalid"])
    def test_pagination_invalid_pages(self, rf, invalid_page):
        """Test pagination with invalid page numbers."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"p": invalid_page})
        view.setup(request)

        response = view.get(request)
        data = self.get_response_data_json(response)

        assert data["page"] == 1  # All invalid pages should convert to page 1
        assert len(data["results"]) <= view.page_size
        assert isinstance(data["results"], list)
        assert "has_more" in data

        # Verify we got the first page of results
        all_items = view.get_iterable()
        expected_results = all_items[: view.page_size]
        assert data["results"] == expected_results

    def test_get_iterable_tuple_list(self, rf):
        """Test get_iterable with tuple list."""
        view = AutocompleteIterablesView()
        test_tuples = [(1, 100), (101, 200), (201, 300)]
        view.iterable = test_tuples
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert len(items) == len(test_tuples)
        for item, original in zip(items, test_tuples):
            assert item["value"] == str(original)
            assert item["label"] == f"{original[0]:,} - {original[1]:,} words"

    def test_search_in_value_and_label(self, rf):
        """Test search matches in both value and label fields."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"q": "act"})  # Should match 'active' and 'inactive'
        view.setup(request)

        items = view.get_iterable()
        filtered = view.search(items)
        assert len(filtered) > 1
        assert any("active" in item["value"] for item in filtered)
        assert any("inactive" in item["value"] for item in filtered)

    @pytest.mark.parametrize(
        "page_size,page_num,expected_size,has_more",
        [
            (2, 1, 2, True),  # First page
            (2, 2, 2, True),  # Middle page
            (2, 0, 2, True),  # Invalid page (zero) - should return first page
            (2, -1, 2, True),  # Invalid page (negative) - should return first page
            (5, 1, 5, True),  # Larger page size
            (100, 1, 55, False),  # Page size larger than total items (ArticleStatus has 55 choices)
        ],
    )
    def test_paginate_iterable(self, rf, page_size, page_num, expected_size, has_more):
        """Test pagination with various page sizes and numbers."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        view.page_size = page_size
        request = rf.get("", {"p": str(page_num)})
        view.setup(request)

        items = view.get_iterable()
        data = view.paginate_iterable(items)

        assert len(data["results"]) == min(expected_size, len(ArticleStatus.choices))
        assert data["has_more"] == has_more
        if has_more:
            assert data["next_page"] == data["page"] + 1

    def test_out_of_range_page_handling(self, rf):
        """Test handling of out-of-range page numbers."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        view.page_size = 10

        # Calculate last valid page number
        total_items = len(ArticleStatus.choices)
        last_valid_page = (total_items + view.page_size - 1) // view.page_size

        # Test page number beyond last valid page
        request = rf.get("", {"p": str(last_valid_page + 1)})
        view.setup(request)

        items = view.get_iterable()
        data = view.paginate_iterable(items)

        # Verify it returns empty results for invalid page
        assert len(data["results"]) == 0
        assert not data["has_more"]
        assert data["page"] == last_valid_page + 1  # Keeps the requested page number

    def test_invalid_page_handling(self, rf):
        """Test handling of invalid page numbers and edge cases."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        view.page_size = 10

        invalid_pages = ["abc", "", None, "0", "-1"]
        for invalid_page in invalid_pages:
            request = rf.get("", {"p": invalid_page} if invalid_page is not None else {})
            view.setup(request)

            items = view.get_iterable()
            data = view.paginate_iterable(items)

            # Should return first page results for invalid page numbers
            assert len(data["results"]) == min(10, len(ArticleStatus.choices))
            assert data["page"] == 1
            assert data["has_more"] == (len(ArticleStatus.choices) > 10)

    def test_get_without_iterable(self, rf):
        """Test GET request when no iterable is set."""
        view = AutocompleteIterablesView()
        request = rf.get("")
        view.setup(request)

        response = view.get(request)
        data = response.content.decode("utf-8")

        assert response.status_code == 200
        assert '"results": []' in data
        assert '"page": 1' in data
        assert '"has_more": false' in data

    def test_invalid_page_size_handling(self, rf):
        """Test handling of invalid page_size parameter."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"page_size": "invalid"})
        view.setup(request)

        assert view.page_size == 20  # Should keep default

        request = rf.get("", {"page_size": "-5"})
        view.setup(request)

        assert view.page_size == 20  # Should keep default

    def test_search_special_characters(self, rf):
        """Test search with special characters."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"q": "draft & % $ #"})
        view.setup(request)

        items = view.get_iterable()
        filtered = view.search(items)

        assert isinstance(filtered, list)
        # Should not raise any exceptions for special characters

    def test_empty_search_returns_all(self, rf):
        """Test that empty search returns all items."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"q": ""})
        view.setup(request)

        items = view.get_iterable()
        filtered = view.search(items)

        assert len(filtered) == len(items)
        assert filtered == items

    def test_undefined_search_handling(self, rf):
        """Test handling of 'undefined' search term."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        request = rf.get("", {"q": "undefined"})
        view.setup(request)

        assert view.query == ""  # Should convert "undefined" to empty string

    def test_partial_page_results(self, rf):
        """Test pagination with partial last page."""
        view = AutocompleteIterablesView()
        view.iterable = ArticleStatus
        view.page_size = 10
        total_items = len(ArticleStatus.choices)
        last_page = (total_items // 10) + 1

        request = rf.get("", {"p": str(last_page)})
        view.setup(request)

        items = view.get_iterable()
        data = view.paginate_iterable(items)

        expected_items = total_items % 10 if total_items % 10 != 0 else 10
        assert len(data["results"]) == expected_items
        assert not data["has_more"]


@pytest.mark.django_db
class TestAutocompleteIterablesViewEdgeCases:
    """Additional edge case tests for AutocompleteIterablesView."""

    def test_empty_search(self, rf):
        """Test search behavior with empty query."""
        view = AutocompleteIterablesView()
        view.iterable = ArticlePriority
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert items == view.search(items)  # Should return all items when no query

    def test_search_matching(self, rf):
        """Test search matches in both value and label fields."""
        view = AutocompleteIterablesView()
        view.iterable = ArticlePriority
        request = rf.get("", {"q": "1"})
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        # Should find items with "1" in value or label
        assert any("1" in str(item["value"]) or "1" in str(item["label"]) for item in data["results"])

        # Test with label search
        request = rf.get("", {"q": "Low"})
        view.setup(request)
        response = view.get(request)
        data = json.loads(response.content.decode())
        assert any(item["label"] == "Low" for item in data["results"])

    def test_word_count_range_formatting(self, rf):
        """Test formatting of word count range tuples."""
        view = AutocompleteIterablesView()
        view.iterable = word_count_range
        request = rf.get("")
        view.setup(request)

        items = view.get_iterable()
        assert all(" - " in item["label"] for item in items)
        assert all("words" in item["label"] for item in items)
        assert all(isinstance(eval(item["value"]), tuple) for item in items)

    @pytest.mark.parametrize(
        "page_input,expected_page",
        [
            ("0", 1),  # Zero should become 1
            ("-1", 1),  # Negative should become 1
            ("abc", 1),  # Non-numeric should become 1
            ("1.5", 1),  # Float should become 1
            ("", 1),  # Empty string should become 1
        ],
    )
    def test_invalid_page_handling(self, rf, page_input, expected_page):
        """Test handling of various invalid page inputs."""
        view = AutocompleteIterablesView()
        view.iterable = ArticlePriority
        request = rf.get("", {"p": page_input} if page_input else {})
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        assert data["page"] == expected_page
