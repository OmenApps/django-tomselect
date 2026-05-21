"""Tests for AutocompleteModelView filtering and allowed-field security.

Covers ``apply_filters`` (filter_by / exclude_by / constant filters), the
``allowed_ordering_fields`` and ``allowed_filter_fields`` allowlists, and the
DEBUG-gated visibility of filter-error diagnostics.
"""


import json

import pytest

from django_tomselect.autocompletes import AutocompleteModelView
from example_project.example.models import Edition, Magazine


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

    def test_apply_filters_with_no_filter_param_in_request(self, rf, test_editions):
        """Direct API hit with no `f` param at all: backend returns unfiltered queryset.

        The widget's dependent-field contract (empty parent => empty dropdown) is
        enforced in the JS load() short-circuit; the backend cannot know a view
        is *configured* as dependent without a filter param to inspect.
        """
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        assert filtered_qs.count() == Edition.objects.count()

    @pytest.mark.parametrize("param_key", ["f", "e"], ids=["filter_by", "exclude_by"])
    def test_apply_filters_with_empty_value_returns_empty(self, rf, test_editions, param_key):
        """`field__lookup=` (empty value, valid format) hits the empty-value guard.

        Distinct from `field=` (invalid format, caught in _parse_filter_string's
        ValueError path): this format parses successfully, so it reaches the
        ``not value or not value.strip()`` guard in _apply_single_filter. Pinning
        both branches separately keeps either guard from being silently dropped.
        """
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {param_key: "magazine__magazine_id="})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())
        assert filtered_qs.count() == 0

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

    @pytest.mark.parametrize("param_key", ["f", "e"], ids=["filter_by", "exclude_by"])
    @pytest.mark.parametrize(
        "invalid_filter",
        ["invalid", "field==value", "field=value=extra", "=value", "field="],
    )
    def test_filter_exclude_invalid_format(self, rf, test_editions, param_key, invalid_filter):
        """Test filter_by and exclude_by with invalid format."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {param_key: invalid_filter})
        view.setup(request)
        filtered_qs = view.apply_filters(Edition.objects.all())
        assert filtered_qs.count() == 0

    @pytest.mark.parametrize("param_key", ["f", "e"], ids=["filter_by", "exclude_by"])
    def test_filter_exclude_nonexistent_field(self, rf, test_editions, param_key):
        """Test filter_by and exclude_by with nonexistent field."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {param_key: "nonexistent_field__exact=value"})
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

    def test_apply_filters_multiple_filter_parameters(self, rf, test_editions, magazines):
        """Test apply_filters with multiple filter_by parameters."""
        # Update some editions with different magazines
        mag1 = magazines[0]
        mag2 = magazines[1] if len(magazines) > 1 else Magazine.objects.create(name="Magazine 2")

        for edition in test_editions[:5]:
            edition.magazine = mag1
            edition.year = "2024"
            edition.save()
        for edition in test_editions[5:]:
            edition.magazine = mag2
            edition.year = "2025"
            edition.save()

        view = AutocompleteModelView()
        view.model = Edition

        # Test with multiple filter parameters (list of f values)
        request = rf.get("", {"f": [f"magazine__magazine_id={mag1.id}", "edition__year=2024"]})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        # Should match editions with mag1 AND year 2024
        expected_count = Edition.objects.filter(magazine_id=mag1.id, year="2024").count()
        assert filtered_qs.count() == expected_count

    def test_apply_filters_constant_filter(self, rf, test_editions):
        """Test apply_filters with constant filter (__const__ prefix)."""
        # Set different years for different editions
        for i, edition in enumerate(test_editions):
            edition.year = "2024" if i < 5 else "2025"
            edition.save()

        view = AutocompleteModelView()
        view.model = Edition

        # Test constant filter - should always filter by year=2024
        request = rf.get("", {"f": "'__const__year=2024'"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        # Should return editions with year 2024
        expected_count = Edition.objects.filter(year="2024").count()
        assert filtered_qs.count() == expected_count
        assert all(e.year == "2024" for e in filtered_qs)

    def test_apply_filters_constant_exclude(self, rf, test_editions):
        """Test apply_filters with constant exclude (__const__ prefix)."""
        # Set different years for different editions
        for i, edition in enumerate(test_editions):
            edition.year = "2024" if i < 5 else "2025"
            edition.save()

        view = AutocompleteModelView()
        view.model = Edition

        # Test constant exclude - should always exclude year=2024
        request = rf.get("", {"e": "'__const__year=2024'"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        # Should return editions with year != 2024
        expected_count = Edition.objects.exclude(year="2024").count()
        assert filtered_qs.count() == expected_count
        assert all(e.year != "2024" for e in filtered_qs)

    def test_apply_filters_mixed_field_and_constant(self, rf, test_editions, magazines):
        """Test apply_filters with mixed field-based and constant filters."""
        mag1 = magazines[0]

        # Update editions
        for i, edition in enumerate(test_editions):
            if i < 3:
                edition.magazine = mag1
                edition.year = "2024"
            elif i < 5:
                edition.magazine = mag1
                edition.year = "2025"
            else:
                edition.magazine = None
                edition.year = "2024"
            edition.save()

        view = AutocompleteModelView()
        view.model = Edition

        # Filter by magazine AND constant year=2024
        request = rf.get("", {"f": [f"magazine__magazine_id={mag1.id}", "'__const__year=2024'"]})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        # Should match editions with mag1 AND year 2024
        expected_count = Edition.objects.filter(magazine_id=mag1.id, year="2024").count()
        assert filtered_qs.count() == expected_count
        assert filtered_qs.count() == 3

    def test_apply_filters_constant_in_lookup_splits_value(self, rf, test_editions):
        """Constant filter with __in lookup should comma-split value into a list."""
        ids = [e.id for e in test_editions[:3]]
        comma_joined = ",".join(str(i) for i in ids)

        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"f": f"'__const__id__in={comma_joined}'"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        assert filtered_qs.count() == 3
        assert sorted(e.id for e in filtered_qs) == sorted(ids)

    def test_apply_filters_field_in_lookup_splits_value(self, rf, test_editions, magazines):
        """Field-based filter with __in lookup should also comma-split."""
        ids = [e.id for e in test_editions[:2]]
        comma_joined = ",".join(str(i) for i in ids)

        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"f": f"'edition__id__in={comma_joined}'"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        assert filtered_qs.count() == 2
        assert sorted(e.id for e in filtered_qs) == sorted(ids)

    def test_apply_filters_constant_range_lookup_splits_value(self, rf, test_editions):
        """Constant filter with __range lookup should comma-split into a 2-tuple-like list."""
        for i, edition in enumerate(test_editions):
            edition.year = str(2020 + i)  # 2020, 2021, 2022, ...
            edition.save()

        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("", {"f": "'__const__year__range=2020,2022'"})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        expected = Edition.objects.filter(year__range=["2020", "2022"])
        assert filtered_qs.count() == expected.count()
        assert filtered_qs.count() == 3

    def test_apply_filters_multiple_excludes(self, rf, test_editions, magazines):
        """Test apply_filters with multiple exclude_by parameters."""
        mag1 = magazines[0]
        mag2 = magazines[1] if len(magazines) > 1 else Magazine.objects.create(name="Magazine 2")

        for i, edition in enumerate(test_editions):
            edition.magazine = mag1 if i < 5 else mag2
            edition.year = str(2020 + (i % 3))  # Years 2020, 2021, 2022
            edition.save()

        view = AutocompleteModelView()
        view.model = Edition

        # Exclude by magazine AND year
        request = rf.get("", {"e": [f"magazine__magazine_id={mag1.id}", "edition__year=2020"]})
        view.setup(request)

        filtered_qs = view.apply_filters(Edition.objects.all())

        # Should exclude editions with mag1 AND exclude editions with year 2020
        expected_count = Edition.objects.exclude(magazine_id=mag1.id).exclude(year="2020").count()
        assert filtered_qs.count() == expected_count


@pytest.mark.django_db
class TestAllowedOrderingFields:
    """Tests for allowed_ordering_fields security feature."""

    def setup_method(self, method):
        """Set up test data."""
        Edition.objects.all().delete()
        for i in range(1, 4):
            Edition.objects.create(name=f"Edition {i}", year=f"202{i}", pages=str(i * 10), pub_num=f"PUB-{i}")

    def test_allowed_ordering_permits_valid_field(self, rf, user):
        """Test that ordering by a field in allowed_ordering_fields works."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "year"]
        view.allowed_ordering_fields = ["name", "year"]
        request = rf.get("", {"ordering": "-year"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        years = [r["year"] for r in data["results"]]
        assert years == sorted(years, reverse=True)

    def test_allowed_ordering_rejects_disallowed_field(self, rf, user):
        """Test that ordering by a field NOT in allowed_ordering_fields falls back to default."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "year"]
        view.ordering = "name"
        view.allowed_ordering_fields = ["name"]
        request = rf.get("", {"ordering": "year"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        # Should fall back to default ordering (name), not use the rejected 'year'
        names = [r["name"] for r in data["results"]]
        assert names == sorted(names)

    def test_none_allowed_ordering_permits_any_field(self, rf, user):
        """Test that allowed_ordering_fields=None (default) allows any ordering."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "year"]
        # allowed_ordering_fields is None by default
        request = rf.get("", {"ordering": "-year"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        years = [r["year"] for r in data["results"]]
        assert years == sorted(years, reverse=True)

    def test_allowed_ordering_strips_descending_prefix(self, rf, user):
        """Test that the '-' prefix is stripped before checking against the allowlist."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "year"]
        view.allowed_ordering_fields = ["year"]
        request = rf.get("", {"ordering": "-year"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        years = [r["year"] for r in data["results"]]
        assert years == sorted(years, reverse=True)


@pytest.mark.django_db
class TestAllowedFilterFields:
    """Tests for allowed_filter_fields security feature."""

    def setup_method(self, method):
        """Set up test data."""
        Edition.objects.all().delete()
        mag = Magazine.objects.create(name="TestMag")
        for i in range(1, 4):
            Edition.objects.create(
                name=f"Edition {i}", year=f"202{i}", pages=str(i * 10), pub_num=f"PUB-{i}", magazine=mag
            )

    def test_allowed_filter_permits_valid_field(self, rf, user):
        """Test that filtering by a field in allowed_filter_fields works."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "year"]
        view.allowed_filter_fields = ["year"]
        request = rf.get("", {"f": "year=2021"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        assert all(r["year"] == "2021" for r in data["results"])

    def test_allowed_filter_rejects_disallowed_field(self, rf, user, monkeypatch):
        """Test that filtering by a field NOT in allowed_filter_fields is rejected."""
        from django.conf import settings

        monkeypatch.setattr(settings, "DEBUG", True)

        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "year"]
        view.allowed_filter_fields = ["year"]
        request = rf.get("", {"f": "name__icontains=Edition"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        assert "filter_error" in data
        assert "not in allowed" in data["filter_error"]

    def test_none_allowed_filter_permits_any_field(self, rf, user):
        """Test that allowed_filter_fields=None (default) allows any filter."""
        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name", "year"]
        # allowed_filter_fields is None by default
        request = rf.get("", {"f": "year=2021"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        assert all(r["year"] == "2021" for r in data["results"])

    def test_allowed_filter_checks_base_field_for_lookups(self, rf, user, monkeypatch):
        """Test that the base field (before __) is extracted and checked against the allowlist."""
        from django.conf import settings

        monkeypatch.setattr(settings, "DEBUG", True)

        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name"]
        view.allowed_filter_fields = ["name"]
        request = rf.get("", {"f": "year__exact=2021"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        assert "filter_error" in data


@pytest.mark.django_db
class TestFilterErrorDebugGating:
    """Tests for _filter_error gated behind settings.DEBUG."""

    def test_filter_error_shown_in_debug_mode(self, rf, user, monkeypatch):
        """Test that _filter_error is included in response when DEBUG=True."""
        from django.conf import settings

        monkeypatch.setattr(settings, "DEBUG", True)

        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name"]
        request = rf.get("", {"f": "nonexistent_field=value"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        assert "filter_error" in data

    def test_filter_error_hidden_in_production(self, rf, user, monkeypatch):
        """Test that _filter_error is NOT included in response when DEBUG=False."""
        from django.conf import settings

        monkeypatch.setattr(settings, "DEBUG", False)

        view = AutocompleteModelView()
        view.model = Edition
        view.value_fields = ["id", "name"]
        request = rf.get("", {"f": "nonexistent_field=value"})
        request.user = user
        view.setup(request)

        response = view.get(request)
        data = json.loads(response.content.decode())
        assert "filter_error" not in data
