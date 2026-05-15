"""Tests for TomSelectTokenField (forms.py) - validation owner for the token widget."""

from __future__ import annotations

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from django_tomselect.autocompletes import (
    CompositeAutocompleteView,
    Operator,
)
from django_tomselect.forms import TomSelectTokenField
from django_tomselect.widgets import TomSelectTokenWidget
from example_project.example.autocompletes import (
    ArticleStatusAutocompleteView,
    AuthorAutocompleteView,
    CategoryAutocompleteView,
    MagazineAutocompleteView,
)


@pytest.fixture
def composite_class():
    """A composite registered against URL ``autocomplete-article-token`` (added in M4 wiring)."""

    class _ArticleQueryView(CompositeAutocompleteView):
        operators = [
            Operator(
                key="author", view=AuthorAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="authors__id", max_count=3,
            ),
            Operator(
                key="category", view=CategoryAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="categories__id", multi=True,
            ),
            Operator(
                key="magazine", view=MagazineAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="magazine_id", max_count=1, min_count=0,
            ),
            Operator(
                key="status", view=ArticleStatusAutocompleteView,
                value_field="value", label_field="label",
                filter_lookup="status", multi=True,
            ),
        ]
        free_text_lookups = ["title__icontains"]

    return _ArticleQueryView


def test_field_constructs_widget_with_composite_view():
    """When composite_view is a URL name, the field auto-builds the rich widget."""
    field = TomSelectTokenField(composite_view="autocomplete-article-token")
    assert isinstance(field.widget, TomSelectTokenWidget)
    assert field.widget.composite_view == "autocomplete-article-token"
    assert field.widget.allow_free_text is True


def test_field_falls_back_to_textinput_for_class_ref(composite_class):
    """Class-reference composite_view falls back to plain TextInput.

    Server-side unit tests typically pass a class reference; the rich widget
    needs a URL the browser can call, so it falls back to TextInput.
    """
    field = TomSelectTokenField(composite_view=composite_class)
    assert not isinstance(field.widget, TomSelectTokenWidget)
    # clean() and parse() still work - rich UI is the only loss.
    assert field.parse("author:42").has("author")


def test_field_passes_caps_and_allow_free_text_to_widget():
    """Field forwards token caps and allow_free_text through to widget."""
    field = TomSelectTokenField(
        composite_view="autocomplete-article-token",
        allow_free_text=False,
        max_query_length=2048,
        max_tokens=10,
        max_values_per_operator=4,
    )
    assert field.widget.allow_free_text is False
    assert field.widget.max_query_length == 2048
    assert field.widget.max_tokens == 10


def test_field_widget_kwargs_propagate():
    """widget_kwargs entries land in the constructed widget."""
    field = TomSelectTokenField(
        composite_view="autocomplete-article-token",
        widget_kwargs={"placeholder": "Filter…", "css_framework": "bootstrap4"},
    )
    assert field.widget.attrs.get("placeholder") == "Filter…"
    assert field.widget.css_framework == "bootstrap4"


def test_clean_accepts_empty_value_when_not_required(composite_class):
    """Empty input is accepted when the field is not required."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    assert field.clean("") == ""


def test_clean_accepts_well_formed_input(composite_class):
    """Well-formed token input round-trips through clean unchanged."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    cleaned = field.clean("author:42 status:draft hello")
    assert cleaned == "author:42 status:draft hello"


def test_clean_rejects_unknown_operator(composite_class):
    """An unregistered operator key surfaces as a ValidationError."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    with pytest.raises(ValidationError) as exc_info:
        field.clean("nonsense:foo")
    assert "Unknown operator" in str(exc_info.value)


def test_clean_rejects_unterminated_quote(composite_class):
    """An unterminated quote surfaces as a ValidationError."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    with pytest.raises(ValidationError) as exc_info:
        field.clean('name:"foo')
    assert "Unterminated" in str(exc_info.value)


def test_clean_rejects_empty_operator_value(composite_class):
    """An operator with no value (``author:``) is rejected."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    with pytest.raises(ValidationError) as exc_info:
        field.clean("author:")
    assert "requires a value" in str(exc_info.value)


def test_clean_enforces_max_count(composite_class):
    """Operator.max_count caps how many times a key can appear."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    # author has max_count=3 in the fixture; 4 should reject.
    with pytest.raises(ValidationError) as exc_info:
        field.clean("author:1 author:2 author:3 author:4")
    assert "at most 3 time" in str(exc_info.value)


def test_clean_enforces_min_count():
    """Operator.min_count enforces required occurrences."""

    class _Composite(CompositeAutocompleteView):
        operators = [
            Operator(
                key="status", view=ArticleStatusAutocompleteView,
                value_field="value", label_field="label",
                filter_lookup="status", min_count=1,
            ),
            Operator(
                key="author", view=AuthorAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="authors__id",
            ),
        ]

    field = TomSelectTokenField(composite_view=_Composite, required=False)
    with pytest.raises(ValidationError) as exc_info:
        field.clean("author:1")  # no status:
    assert "is required" in str(exc_info.value)
    # With status: present, accepts.
    field.clean("author:1 status:draft")


def test_clean_rejects_free_text_when_disabled(composite_class):
    """Free-text terms are rejected when ``allow_free_text=False``."""
    field = TomSelectTokenField(
        composite_view=composite_class, required=False, allow_free_text=False,
    )
    with pytest.raises(ValidationError) as exc_info:
        field.clean("author:1 some free text")
    assert "Free-text input is not allowed" in str(exc_info.value)


def test_clean_enforces_caps(composite_class):
    """``max_tokens`` cap is enforced by clean()."""
    field = TomSelectTokenField(
        composite_view=composite_class, required=False,
        max_tokens=2,
    )
    with pytest.raises(ValidationError) as exc_info:
        field.clean("a b c d")
    assert "Too many tokens" in str(exc_info.value)


def test_parse_helper_returns_parsed_query(composite_class):
    """field.parse() returns a ParsedQuery exposing tokens and free_text."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    parsed = field.parse("author:42 hello")
    assert parsed.has("author")
    assert parsed.free_text == ["hello"]


def test_parse_helper_supports_cross_operator_form_validation(composite_class):
    """Form authors can use field.parse() in form.clean() for cross-operator rules."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)

    class MyForm(forms.Form):
        q = field

        def clean(self):
            cleaned = super().clean()
            parsed = self.fields["q"].parse(cleaned.get("q", "") or "")
            if parsed.has("author") and not parsed.has("category"):
                raise ValidationError("If you specify author:, you must also specify category:.")
            return cleaned

    f = MyForm({"q": "author:1"})
    assert not f.is_valid()
    assert "specify category" in str(f.errors)

    f = MyForm({"q": "author:1 category:5"})
    assert f.is_valid(), f.errors


def test_widget_rendering_includes_token_config(composite_class):
    """Ensure the rendered widget exposes the JSON config for the JS plugin."""
    RequestFactory()  # kept for parity with other tests
    widget = TomSelectTokenWidget(
        composite_view="autocomplete-author",  # any reversible URL works for this test
        placeholder="Filter…",
        allow_free_text=False,
        max_tokens=8,
    )
    # Render without committing to a real request
    rendered = widget.render(name="q", value="", attrs={"id": "id_q"})
    assert "data-django-tomselect-token" in rendered
    assert "data-target-name=\"q\"" in rendered
    assert "Filter…" in rendered or "Filter…" in rendered or "Filter\\u2026" in rendered
    assert "djangoTomSelectToken" in rendered  # init script reference


def test_widget_includes_token_css_in_media(composite_class):
    """Widget media includes both base and token CSS."""
    widget = TomSelectTokenWidget(composite_view="autocomplete-author")
    media_html = str(widget.media)
    assert "django-tomselect-token.css" in media_html
    # Existing widget CSS is also present.
    assert "django-tomselect.css" in media_html


@pytest.mark.parametrize("framework,expected", [
    ("default", "tom-select.default"),
    ("bootstrap4", "tom-select.bootstrap4"),
    ("bootstrap5", "tom-select.bootstrap5"),
])
def test_widget_css_framework_override(framework, expected, composite_class):
    """css_framework option swaps the Tom Select theme CSS path."""
    widget = TomSelectTokenWidget(
        composite_view="autocomplete-author",
        css_framework=framework,
    )
    paths = widget._get_css_paths()
    assert any(expected in p for p in paths), f"expected {expected} in {paths}"
    assert any("django-tomselect-token.css" in p for p in paths)


def test_widget_idempotent_init_attribute_emitted(composite_class):
    """Render output should include the init guard pattern."""
    widget = TomSelectTokenWidget(composite_view="autocomplete-author")
    rendered = widget.render(name="q", value="", attrs={"id": "id_q"})
    assert "djangoTomselectTokenInitialized" in rendered


def test_widget_inline_init_emits_valid_js_string_literal(composite_class):
    """Regression: inline init script must include a quoted JS string for the input name.

    Previous template used ``|escapejs|stringformat:"'%s'"`` which Django
    interpreted as the format spec ``'s'`` (the leading ``%`` is stripped),
    producing empty output and ``var inputName = ;`` (SyntaxError).
    """
    import re

    widget = TomSelectTokenWidget(composite_view="autocomplete-author")
    rendered = widget.render(name="q", value="", attrs={"id": "id_q"})
    match = re.search(r"var inputName = (.+);", rendered)
    assert match is not None, "inputName declaration not found"
    js_value = match.group(1).strip()
    # Must be a non-empty string literal - single or double quoted.
    assert js_value not in ("", "''", '""'), (
        f"inputName must be a non-empty string literal, got: {js_value!r}"
    )
    assert (js_value.startswith("'") and js_value.endswith("'")) or (
        js_value.startswith('"') and js_value.endswith('"')
    ), f"inputName must be a quoted string literal, got: {js_value!r}"
    # The actual name should be inside the quotes.
    inner = js_value[1:-1]
    assert inner == "q", f"inputName payload should be 'q', got: {inner!r}"


def test_widget_inline_init_escapes_special_chars_in_name(composite_class):
    """Apostrophes in a field name must not break the inline JS.

    Unlikely but possible; escapejs handles it.
    """
    import re

    widget = TomSelectTokenWidget(composite_view="autocomplete-author")
    rendered = widget.render(name="q'tricky", value="", attrs={"id": "id_q"})
    match = re.search(r"var inputName = ('[^;]*?');", rendered)
    assert match is not None
    # The literal is parseable as a JS string (no unescaped quote inside).
    js_str = match.group(1)
    # Bare ' inside a single-quoted JS literal would be a syntax error;
    # escapejs encodes it as '.
    assert "'" not in js_str[1:-1], f"unescaped quote in {js_str!r}"


def test_widget_rejects_class_reference_composite_view(composite_class):
    """Widget refuses class-reference composite_view at init.

    The JS plugin needs a URL it can call; a class reference leaves it without
    one, so the widget must fail fast.
    """
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured, match="URL name"):
        TomSelectTokenWidget(composite_view=composite_class)


def test_widget_fails_fast_on_unreversible_url():
    """Unreversible URL names raise ImproperlyConfigured at render time.

    Better to fail fast than emit a dead widget the JS plugin cannot bootstrap.
    """
    from django.core.exceptions import ImproperlyConfigured

    widget = TomSelectTokenWidget(composite_view="totally-bogus-url-zzz")
    with pytest.raises(ImproperlyConfigured, match="cannot reverse"):
        widget.render(name="q", value="", attrs={"id": "id_q"})


def test_field_textinput_fallback_translates_placeholder(composite_class):
    """Class-ref fallback accepts token-only widget_kwargs without crashing.

    placeholder and css_framework must be tolerated by the TextInput fallback.
    """
    field = TomSelectTokenField(
        composite_view=composite_class,
        widget_kwargs={"placeholder": "Filter…", "css_framework": "bootstrap5"},
    )
    # The fallback widget is a plain TextInput; placeholder lands in attrs.
    assert not isinstance(field.widget, TomSelectTokenWidget)
    assert field.widget.attrs.get("placeholder") == "Filter…"


def test_field_clean_rejects_empty_member_in_multi(composite_class):
    """category:1,,2 has an empty member; field.clean() must reject."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    with pytest.raises(ValidationError) as exc_info:
        field.clean("category:1,,2")
    msg = str(exc_info.value)
    assert "category" in msg and "value" in msg


def test_field_clean_rejects_trailing_comma_in_multi(composite_class):
    """A trailing comma in a multi-value operator is rejected."""
    field = TomSelectTokenField(composite_view=composite_class, required=False)
    with pytest.raises(ValidationError) as exc_info:
        field.clean("status:draft,")
    msg = str(exc_info.value)
    assert "status" in msg and "value" in msg


def test_widget_data_config_is_valid_json(composite_class):
    """The data-config attribute MUST be parseable JSON.

    Django's default rendering of a Python dict produces ``repr()`` output
    (single quotes, ``True`` not ``true``) which JSON.parse() rejects. The
    widget JSON-encodes the config in get_context() to avoid this.
    """
    import json
    import re

    widget = TomSelectTokenWidget(
        composite_view="autocomplete-author",
        allow_free_text=False,
        max_query_length=2048,
        max_tokens=12,
    )
    rendered = widget.render(name="q", value="", attrs={"id": "id_q"})

    # Extract the data-config attribute value.
    m = re.search(r'data-config="([^"]*)"', rendered)
    assert m is not None, "data-config attribute not found in rendered output"
    raw = m.group(1)

    # Browser un-escapes HTML entities in attribute values; do the same here.
    from html import unescape
    config = json.loads(unescape(raw))
    assert config == {
        "allow_free_text": False,
        "max_query_length": 2048,
        "max_tokens": 12,
    }
