"""Tests for django_tomselect.query - token parser and ParsedQuery.apply.

The parser test cases are driven by the shared JSON fixture corpus at
``tests/fixtures/parser_corpus.json``. The same corpus is consumed by the JS
parser tests so the two implementations stay in lockstep.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import Q

from django_tomselect.autocompletes import (
    AutocompleteModelView,
    CompositeAutocompleteView,
    Operator,
)
from django_tomselect.query import (
    MAX_RAW_LENGTH_DEFAULT,
    MAX_TOKENS_DEFAULT,
    MAX_VALUES_PER_OPERATOR_DEFAULT,
    parse_query,
)


CORPUS_PATH = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "parser_corpus.json"


def _load_corpus() -> dict:
    with CORPUS_PATH.open() as f:
        return json.load(f)


def _build_composite(operator_specs: dict[str, dict], free_text_lookups=("title__icontains",)):
    """Build a CompositeAutocompleteView subclass for a fixture's operator config.

    Uses a stub model view as the bound view - these tests don't exercise
    delegation, only parsing. The bound view never receives a request.
    """

    class _StubModelView(AutocompleteModelView):
        search_lookups = ["name__icontains"]

    operators = []
    for key, spec in operator_specs.items():
        operators.append(
            Operator(
                key=key,
                view=_StubModelView,
                value_field="id",
                label_field="name",
                filter_lookup="id",
                multi=spec.get("multi", False),
            )
        )

    composite = type(
        "_FixtureComposite",
        (CompositeAutocompleteView,),
        {"operators": operators, "free_text_lookups": list(free_text_lookups)},
    )
    return composite


@pytest.fixture(scope="module")
def corpus() -> dict:
    """Return the parsed JSON corpus shared with the JS parser tests."""
    return _load_corpus()


def _corpus_cases():
    corpus = _load_corpus()
    return [(case["name"], case, corpus) for case in corpus["cases"]]


@pytest.mark.parametrize(
    "name,case,corpus", _corpus_cases(), ids=[c[0] for c in _corpus_cases()]
)
def test_parser_corpus(name: str, case: dict, corpus: dict) -> None:
    """Each entry in the parser corpus must produce the expected parse output."""
    operator_specs = corpus["default_operators"]
    composite = _build_composite(operator_specs)

    caps = {
        "max_raw_length": MAX_RAW_LENGTH_DEFAULT,
        "max_tokens": MAX_TOKENS_DEFAULT,
        "max_values_per_operator": MAX_VALUES_PER_OPERATOR_DEFAULT,
    }
    caps.update(case.get("caps", {}))

    parsed = parse_query(case["input"], composite, **caps)

    expected_token_keys = [(t["key"], tuple(t["values"]), t["was_quoted"]) for t in case["tokens"]]
    actual_token_keys = [(t.key, t.values, t.was_quoted) for t in parsed.tokens]
    assert actual_token_keys == expected_token_keys, f"{name}: token mismatch"

    assert parsed.free_text == case["free_text"], f"{name}: free_text mismatch"

    expected_error_codes = case["errors"]
    actual_error_codes = [e.code for e in parsed.errors]
    assert actual_error_codes == expected_error_codes, f"{name}: error codes mismatch"


class _FakeQS:
    """Minimal QuerySet stand-in that records .filter() calls and re-raises ORM-style errors."""

    def __init__(self, raise_value_error_on: dict[str, type] | None = None):
        self.applied: list[Q] = []
        self.raise_value_error_on = raise_value_error_on or {}

    def filter(self, *args, **kwargs):
        if args and isinstance(args[0], Q):
            for child in args[0].children:
                if isinstance(child, tuple):
                    field, value = child
                    expected = self.raise_value_error_on.get(field)
                    if expected and not isinstance(value, expected):
                        raise ValueError(f"Field {field!r} expects {expected.__name__}, got {value!r}.")
            self.applied.append(args[0])
        return self


def test_apply_with_filter_lookup_single():
    """A single-value filter_lookup operator applies one Q to the queryset."""
    op = Operator(
        key="status", view=_DummyModelView, value_field="value", label_field="label",
        filter_lookup="status",
    )
    composite = _make_composite([op], free_text_lookups=["title__icontains"])
    parsed = parse_query("status:draft", composite)
    qs = _FakeQS()
    parsed.apply(qs)
    assert qs.applied, "filter() should have been called"


def test_apply_with_filter_lookup_multi_in_semantics():
    """Multi-valued operators emit a single ``__in`` lookup over the values."""
    op = Operator(
        key="category", view=_DummyModelView, value_field="id", label_field="name",
        filter_lookup="categories__id", multi=True,
    )
    composite = _make_composite([op], free_text_lookups=[])
    parsed = parse_query("category:1,2,3", composite)
    qs = _FakeQS()
    parsed.apply(qs)
    # The Q should contain a categories__id__in lookup.
    assert qs.applied, "filter() should have been called"
    rendered = str(qs.applied[0])
    assert "categories__id__in" in rendered, f"expected __in lookup, got {rendered}"


def test_apply_with_q_translator():
    """A custom q_translator receives the operator and parsed values, returns a Q."""
    captured = {}

    def translator(operator: Operator, values: list) -> Q:
        captured["op"] = operator
        captured["values"] = values
        return Q(custom__lookup="x")

    op = Operator(
        key="custom", view=_DummyModelView, value_field="id", label_field="name",
        q_translator=translator,
    )
    composite = _make_composite([op])
    parsed = parse_query("custom:foo", composite)
    qs = _FakeQS()
    parsed.apply(qs)
    assert captured["values"] == ["foo"]
    assert captured["op"].key == "custom"


def test_apply_refuses_when_errors_present():
    """apply() raises ValidationError when the parse contains any errors."""
    op = Operator(
        key="author", view=_DummyModelView, value_field="id", label_field="name",
        filter_lookup="authors__id",
    )
    composite = _make_composite([op])
    # Unknown operator triggers ParseError.
    parsed = parse_query("nonsense:foo", composite)
    assert parsed.errors, "should have UNKNOWN_OPERATOR"
    qs = _FakeQS()
    with pytest.raises(ValidationError):
        parsed.apply(qs)


def test_apply_translates_orm_coercion_to_validation_error():
    """category:tech against an int filter should surface a clean ValidationError."""
    op = Operator(
        key="category", view=_DummyModelView, value_field="id", label_field="name",
        filter_lookup="categories__id", multi=True,
    )
    composite = _make_composite([op])
    parsed = parse_query("category:tech,sports", composite)
    # Configure the fake QS to raise ValueError on string values for int lookup.
    qs = _FakeQS(raise_value_error_on={"categories__id__in": list})  # placeholder; we'll force from filter
    # The fake doesn't actually do coercion - we'll patch filter to raise.

    def _raise(*a, **k):
        raise ValueError("invalid literal for int(): 'tech'")

    qs.filter = _raise  # type: ignore[assignment]
    with pytest.raises(ValidationError) as exc_info:
        parsed.apply(qs)
    msg = str(exc_info.value)
    assert "category" in msg
    assert "select an option from the dropdown" in msg


def test_apply_free_text_or_anded():
    """Free-text terms each OR'd across free_text_lookups, terms ANDed together."""
    op = Operator(
        key="author", view=_DummyModelView, value_field="id", label_field="name",
        filter_lookup="authors__id",
    )
    composite = _make_composite([op], free_text_lookups=["title__icontains", "body__icontains"])
    parsed = parse_query("foo bar", composite)
    assert parsed.tokens == []
    assert parsed.free_text == ["foo", "bar"]
    qs = _FakeQS()
    parsed.apply(qs)
    # Two terms >> two filter calls (each with an OR Q across lookups).
    assert len(qs.applied) == 2


def test_apply_no_op_when_empty():
    """apply() does nothing when there are no tokens or free-text terms."""
    op = Operator(
        key="author", view=_DummyModelView, value_field="id", label_field="name",
        filter_lookup="authors__id",
    )
    composite = _make_composite([op])
    parsed = parse_query("", composite)
    qs = _FakeQS()
    parsed.apply(qs)
    assert qs.applied == []


def test_operator_requires_value_field():
    """Operator construction without value_field raises ImproperlyConfigured."""
    with pytest.raises(ImproperlyConfigured, match="requires value_field"):
        Operator(key="x", view=_DummyModelView, label_field="name", filter_lookup="x")


def test_operator_requires_label_field():
    """Operator construction without label_field raises ImproperlyConfigured."""
    with pytest.raises(ImproperlyConfigured, match="requires label_field"):
        Operator(key="x", view=_DummyModelView, value_field="id", filter_lookup="x")


def test_operator_requires_filter_or_translator():
    """Operator must specify either filter_lookup or q_translator."""
    with pytest.raises(ImproperlyConfigured, match="requires filter_lookup or q_translator"):
        Operator(key="x", view=_DummyModelView, value_field="id", label_field="name")


def test_operator_rejects_both_filter_and_translator():
    """Setting both filter_lookup and q_translator is rejected."""
    with pytest.raises(ImproperlyConfigured, match="cannot set both filter_lookup and q_translator"):
        Operator(
            key="x", view=_DummyModelView, value_field="id", label_field="name",
            filter_lookup="x", q_translator=lambda o, v: Q(),
        )


def test_operator_bound_lookup_defaults_to_value_field():
    """bound_lookup falls back to value_field when not explicitly set."""
    op = Operator(
        key="x", view=_DummyModelView, value_field="id", label_field="name",
        filter_lookup="id",
    )
    assert op.bound_lookup == "id"


def test_operator_bound_lookup_explicit_override():
    """An explicit bound_lookup wins over the value_field default."""
    op = Operator(
        key="x", view=_DummyModelView, value_field="rendered_id",
        label_field="name", filter_lookup="id", bound_lookup="id",
    )
    assert op.bound_lookup == "id"


class _DummyModelView(AutocompleteModelView):
    search_lookups = ["name__icontains"]


def _make_composite(operators: list[Operator], free_text_lookups=()) -> type[CompositeAutocompleteView]:
    """Build a composite subclass on the fly. Module-scoped ``type()`` call."""
    return type(
        "_TestComposite",
        (CompositeAutocompleteView,),
        {"operators": list(operators), "free_text_lookups": list(free_text_lookups)},
    )
