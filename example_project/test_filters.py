"""Tests for FilterSpec, Const, and filter validation/normalization on TomSelectConfig."""

import pytest
from django.core.exceptions import ValidationError

from django_tomselect.app_settings import (
    Const,
    FilterSpec,
    TomSelectConfig,
)


def _is_filterspec_instance(obj):
    """Helper to check if an object is a FilterSpec, resilient to module reloading."""
    return type(obj).__name__ == "FilterSpec" and hasattr(obj, "source") and hasattr(obj, "lookup")


class TestFilterSpec:
    """Tests for the FilterSpec dataclass and Const helper."""

    def test_filterspec_creation(self):
        """Test creating FilterSpec with default source_type."""
        spec = FilterSpec(source="category", lookup="category_id")
        assert spec.source == "category"
        assert spec.lookup == "category_id"
        assert spec.source_type == "field"

    def test_filterspec_with_const_source_type(self):
        """Test creating FilterSpec with const source_type."""
        spec = FilterSpec(source="published", lookup="status", source_type="const")
        assert spec.source == "published"
        assert spec.lookup == "status"
        assert spec.source_type == "const"

    def test_filterspec_from_tuple(self):
        """Test creating FilterSpec from a 2-tuple."""
        spec = FilterSpec.from_tuple(("category", "category_id"))
        assert spec.source == "category"
        assert spec.lookup == "category_id"
        assert spec.source_type == "field"

    def test_const_helper(self):
        """Test the Const helper function."""
        spec = Const("published", "status")
        assert _is_filterspec_instance(spec)
        assert spec.source == "published"
        assert spec.lookup == "status"
        assert spec.source_type == "const"

    def test_const_converts_to_string(self):
        """Test that Const converts numeric values to strings."""
        spec = Const(123, "category_id")
        assert spec.source == "123"
        assert spec.lookup == "category_id"
        assert spec.source_type == "const"

    def test_filterspec_frozen(self):
        """Test that FilterSpec is frozen (immutable)."""
        spec = FilterSpec(source="category", lookup="category_id")
        with pytest.raises(AttributeError):
            spec.source = "new_value"

    def test_const_with_list_value(self):
        """Const should comma-join list values for use with __in lookups."""
        spec = Const([11, 13], "id__in")
        assert spec.source == "11,13"
        assert spec.lookup == "id__in"
        assert spec.source_type == "const"

    def test_const_with_tuple_value(self):
        """Const should comma-join tuple values too."""
        spec = Const((1, 2, 3), "id__in")
        assert spec.source == "1,2,3"
        assert spec.source_type == "const"

    def test_const_with_single_element_list(self):
        """Const with a single-element list still produces a usable spec."""
        spec = Const([42], "id__in")
        assert spec.source == "42"

    def test_const_rejects_empty_list(self):
        """Const should reject empty lists/tuples to avoid silently no-op filters."""
        with pytest.raises(ValidationError):
            Const([], "id__in")
        with pytest.raises(ValidationError):
            Const((), "id__in")

    def test_const_rejects_items_with_commas(self):
        """Const should reject list items containing commas (would create ambiguous splits)."""
        with pytest.raises(ValidationError):
            Const(["a,b", "c"], "name__in")

    def test_filterspec_levels_up_default_zero(self):
        """levels_up defaults to 0 (sibling at the same nesting depth)."""
        spec = FilterSpec(source="customer", lookup="id")
        assert spec.levels_up == 0

    def test_filterspec_levels_up_positive(self):
        """levels_up accepts positive integers."""
        spec = FilterSpec(source="customer", lookup="id", levels_up=1)
        assert spec.levels_up == 1

    def test_filterspec_levels_up_rejects_negative(self):
        """Negative levels_up is meaningless (can't walk below the current row)."""
        with pytest.raises(ValidationError):
            FilterSpec(source="customer", lookup="id", levels_up=-1)

    def test_filterspec_levels_up_rejects_string(self):
        """levels_up must be a real int; strings would render raw into JS."""
        with pytest.raises(ValidationError):
            FilterSpec(source="customer", lookup="id", levels_up="1")

    def test_filterspec_levels_up_rejects_bool(self):
        """Reject bool because Python's bool is an int subtype that would slip past isinstance(int)."""
        with pytest.raises(ValidationError):
            FilterSpec(source="customer", lookup="id", levels_up=True)

    def test_filterspec_levels_up_rejects_float(self):
        """Float would render as e.g. '1.5' in JS, breaking the filterFields lookup."""
        with pytest.raises(ValidationError):
            FilterSpec(source="customer", lookup="id", levels_up=1.5)

    def test_filterspec_const_with_levels_up_rejected(self):
        """levels_up on a const filter is incoherent: there's no form field to walk up to."""
        with pytest.raises(ValidationError):
            FilterSpec(source="published", lookup="status", source_type="const", levels_up=1)

    def test_filterspec_const_with_levels_up_zero_allowed(self):
        """Const + default levels_up=0 is valid (no walk requested)."""
        spec = FilterSpec(source="published", lookup="status", source_type="const")
        assert spec.levels_up == 0

    def test_filterspec_from_tuple_defaults_levels_up_zero(self):
        """Legacy 2-tuple has no levels_up; from_tuple keeps the default."""
        spec = FilterSpec.from_tuple(("category", "category_id"))
        assert spec.levels_up == 0


class TestMultipleFiltersValidation:
    """Tests for TomSelectConfig filter_by/exclude_by validation with new formats."""

    def test_empty_tuple_still_works(self):
        """Test that empty tuple still works for no filtering."""
        config = TomSelectConfig(filter_by=(), exclude_by=())
        assert config.filter_by == ()
        assert config.exclude_by == ()

    def test_legacy_2_tuple_still_works(self):
        """Test that legacy 2-tuple format still works."""
        config = TomSelectConfig(
            filter_by=("category", "category_id"),
            exclude_by=("author", "author_id"),
        )
        assert config.filter_by == ("category", "category_id")
        assert config.exclude_by == ("author", "author_id")

    def test_single_filterspec(self):
        """Test using a single FilterSpec for filter_by."""
        spec = FilterSpec(source="category", lookup="category_id")
        config = TomSelectConfig(filter_by=spec)
        assert config.filter_by == spec

    def test_list_of_tuples(self):
        """Test using a list of 2-tuples for multiple filters."""
        config = TomSelectConfig(
            filter_by=[
                ("category", "category_id"),
                ("brand", "brand_id"),
            ]
        )
        assert len(config.filter_by) == 2
        assert config.filter_by[0] == ("category", "category_id")
        assert config.filter_by[1] == ("brand", "brand_id")

    def test_list_of_filterspecs(self):
        """Test using a list of FilterSpec objects."""
        specs = [
            FilterSpec(source="category", lookup="category_id"),
            FilterSpec(source="brand", lookup="brand_id"),
        ]
        config = TomSelectConfig(filter_by=specs)
        assert len(config.filter_by) == 2

    def test_mixed_list_of_tuples_and_filterspecs(self):
        """Test using a mixed list of tuples and FilterSpecs."""
        config = TomSelectConfig(
            filter_by=[
                ("category", "category_id"),
                Const("published", "status"),
            ]
        )
        assert len(config.filter_by) == 2

    def test_invalid_tuple_length_raises_error(self):
        """Test that invalid tuple length raises ValidationError."""
        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=("single",))

        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=("one", "two", "three"))

    def test_invalid_list_item_raises_error(self):
        """Test that invalid items in list raise ValidationError."""
        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=["not_a_tuple_or_spec"])

        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=[("valid", "tuple"), "invalid"])

    def test_identical_filter_and_exclude_raises_error(self):
        """Test that identical filter and exclude conditions raise error."""
        with pytest.raises(ValidationError):
            TomSelectConfig(
                filter_by=("field", "lookup"),
                exclude_by=("field", "lookup"),
            )

    def test_identical_filterspecs_in_lists_raises_error(self):
        """Test that identical FilterSpecs in filter_by and exclude_by raise error."""
        spec = FilterSpec(source="field", lookup="lookup")
        with pytest.raises(ValidationError):
            TomSelectConfig(
                filter_by=[spec],
                exclude_by=[spec],
            )

    def test_tuple_of_filterspecs_accepted(self):
        """A tuple (rather than list) of FilterSpec objects should be accepted."""
        config = TomSelectConfig(
            filter_by=(
                FilterSpec(source="11", lookup="id", source_type="const"),
                FilterSpec(source="13", lookup="id", source_type="const"),
            )
        )
        filters = config.get_normalized_filters()
        assert len(filters) == 2
        assert filters[0].source == "11"
        assert filters[1].source == "13"

    def test_three_tuple_of_filterspecs_accepted(self):
        """A 3-tuple of FilterSpec should be treated as a sequence, not rejected."""
        config = TomSelectConfig(
            filter_by=(
                FilterSpec(source="a", lookup="id"),
                FilterSpec(source="b", lookup="id"),
                FilterSpec(source="c", lookup="id"),
            )
        )
        assert len(config.get_normalized_filters()) == 3

    def test_tuple_with_const_for_in_lookup(self):
        """End-to-end: tuple of Const values produces a filter usable for __in."""
        config = TomSelectConfig(filter_by=(Const([11, 13], "id__in"),))
        filters = config.get_normalized_filters()
        assert len(filters) == 1
        assert filters[0].source == "11,13"
        assert filters[0].lookup == "id__in"
        assert filters[0].source_type == "const"

    def test_different_filters_and_excludes_allowed(self):
        """Test that different filter and exclude conditions are allowed."""
        config = TomSelectConfig(
            filter_by=[
                ("category", "category_id"),
                Const("published", "status"),
            ],
            exclude_by=[("author", "author_id")],
        )
        assert len(config.filter_by) == 2
        assert len(config.exclude_by) == 1


class TestFilterNormalization:
    """Tests for TomSelectConfig filter normalization methods."""

    def test_normalize_empty_tuple(self):
        """Test normalizing empty tuple returns empty list."""
        config = TomSelectConfig(filter_by=())
        assert config.get_normalized_filters() == []

    def test_normalize_legacy_2_tuple(self):
        """Test normalizing legacy 2-tuple returns list with one FilterSpec."""
        config = TomSelectConfig(filter_by=("category", "category_id"))
        filters = config.get_normalized_filters()
        assert len(filters) == 1
        assert _is_filterspec_instance(filters[0])
        assert filters[0].source == "category"
        assert filters[0].lookup == "category_id"
        assert filters[0].source_type == "field"

    def test_normalize_single_filterspec(self):
        """Test normalizing single FilterSpec returns list with one FilterSpec."""
        spec = FilterSpec(source="category", lookup="category_id")
        config = TomSelectConfig(filter_by=spec)
        filters = config.get_normalized_filters()
        assert len(filters) == 1
        # Check by values instead of identity (resilient to module reload)
        assert filters[0].source == spec.source
        assert filters[0].lookup == spec.lookup
        assert filters[0].source_type == spec.source_type

    def test_normalize_list_of_tuples(self):
        """Test normalizing list of tuples returns list of FilterSpecs."""
        config = TomSelectConfig(
            filter_by=[
                ("category", "category_id"),
                ("brand", "brand_id"),
            ]
        )
        filters = config.get_normalized_filters()
        assert len(filters) == 2
        assert all(_is_filterspec_instance(f) for f in filters)
        assert filters[0].source == "category"
        assert filters[1].source == "brand"

    def test_normalize_mixed_list(self):
        """Test normalizing mixed list of tuples and FilterSpecs."""
        config = TomSelectConfig(
            filter_by=[
                ("category", "category_id"),
                Const("published", "status"),
            ]
        )
        filters = config.get_normalized_filters()
        assert len(filters) == 2
        assert filters[0].source_type == "field"
        assert filters[1].source_type == "const"

    def test_normalize_excludes(self):
        """Test normalizing exclude_by works the same way."""
        config = TomSelectConfig(
            exclude_by=[
                ("author", "author_id"),
                Const("archived", "status"),
            ]
        )
        excludes = config.get_normalized_excludes()
        assert len(excludes) == 2
        assert excludes[0].source == "author"
        assert excludes[1].source == "archived"

    def test_normalize_preserves_levels_up_single_filterspec(self):
        """A single FilterSpec with levels_up survives normalization."""
        spec = FilterSpec(source="customer", lookup="id", levels_up=1)
        config = TomSelectConfig(filter_by=spec)
        filters = config.get_normalized_filters()
        assert filters[0].levels_up == 1

    def test_normalize_preserves_levels_up_list_of_filterspecs(self):
        """A list-of-FilterSpecs path preserves levels_up per entry."""
        config = TomSelectConfig(
            filter_by=[
                FilterSpec(source="category", lookup="id", levels_up=0),
                FilterSpec(source="customer", lookup="id", levels_up=2),
            ]
        )
        filters = config.get_normalized_filters()
        assert filters[0].levels_up == 0
        assert filters[1].levels_up == 2

    def test_normalize_preserves_levels_up_duck_typed_single(self):
        """Duck-typed FilterSpec (module-reload path at app_settings.py:580-584) preserves levels_up."""
        # Build a FilterSpec-like via plain dataclass that mimics the structure.
        # We use _is_filterspec_instance() to confirm duck-typing detection works.
        from dataclasses import dataclass as _dc

        @_dc(frozen=True)
        class FakeFilterSpec:
            source: str
            lookup: str
            source_type: str
            levels_up: int

        FakeFilterSpec.__name__ = "FilterSpec"  # Trip the duck-typed detection
        fake = FakeFilterSpec(source="customer", lookup="id", source_type="field", levels_up=1)
        config = TomSelectConfig(filter_by=fake)
        filters = config.get_normalized_filters()
        assert filters[0].levels_up == 1
        # Confirm it became a real FilterSpec (not the fake)
        assert type(filters[0]).__module__.startswith("django_tomselect")

    def test_normalize_preserves_levels_up_duck_typed_in_list(self):
        """Duck-typed FilterSpec inside a list (app_settings.py:596-605) preserves levels_up."""
        from dataclasses import dataclass as _dc

        @_dc(frozen=True)
        class FakeFilterSpec:
            source: str
            lookup: str
            source_type: str
            levels_up: int

        FakeFilterSpec.__name__ = "FilterSpec"
        fake = FakeFilterSpec(source="customer", lookup="id", source_type="field", levels_up=3)
        config = TomSelectConfig(filter_by=[fake])
        filters = config.get_normalized_filters()
        assert filters[0].levels_up == 3
