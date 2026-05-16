"""Tests for CompositeAutocompleteView (operators / value / resolve modes)."""

from __future__ import annotations

import json

import pytest
from django.test import RequestFactory

from django_tomselect.autocompletes import (
    CompositeAutocompleteView,
    Operator,
)
from django_tomselect.lazy_utils import resolve_view_class
from example_project.example.autocompletes import (
    ArticleStatusAutocompleteView,
    AuthorAutocompleteView,
    CategoryAutocompleteView,
    MagazineAutocompleteView,
)
from example_project.example.models import Author, Magazine


@pytest.fixture
def rf():
    """Return a Django RequestFactory for building test requests."""
    return RequestFactory()


@pytest.fixture
def composite_class():
    """A composite that points at example_project's existing autocomplete views."""

    class _ArticleQueryView(CompositeAutocompleteView):
        operators = [
            Operator(
                key="author", view=AuthorAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="authors__id",
            ),
            Operator(
                key="category", view=CategoryAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="categories__id", multi=True,
            ),
            Operator(
                key="magazine", view=MagazineAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="magazine_id",
            ),
            Operator(
                key="status", view=ArticleStatusAutocompleteView,
                value_field="value", label_field="label",
                filter_lookup="status", multi=True,
            ),
        ]
        free_text_lookups = ["title__icontains"]

    return _ArticleQueryView


def test_mode_operators_returns_metadata(rf, composite_class, db):
    """mode=operators returns operator metadata with multi flags and free_text_lookups."""
    request = rf.get("/q/", {"mode": "operators"})
    view = composite_class.as_view()
    response = view(request)
    assert response.status_code == 200
    data = json.loads(response.content)
    keys = [op["key"] for op in data["operators"]]
    assert keys == ["author", "category", "magazine", "status"]
    # Multi flag is propagated.
    by_key = {op["key"]: op for op in data["operators"]}
    assert by_key["category"]["multi"] is True
    assert by_key["author"]["multi"] is False
    # filter_lookup operators are not free-form by default.
    assert by_key["author"]["free_form"] is False
    assert by_key["status"]["free_form"] is False
    assert data["free_text_lookups"] == ["title__icontains"]


def test_mode_operators_marks_q_translator_ops_as_free_form(rf, db):
    """q_translator-backed operators must surface free_form=True.

    The JS plugin can commit typed values directly and skip resolve.
    """
    from django.db.models import Q

    from django_tomselect.autocompletes import AutocompleteModelView

    class _EmptyView(AutocompleteModelView):
        """Minimal model view whose queryset is empty.

        Stands in for a free-form operator's bound view without coupling
        this test to the example_project's NoSuggestionAutocompleteView.
        """

        model = Author

        def get_queryset(self):
            return Author.objects.none()

    def _q_after(op, values):
        return Q(date_published__gte=values[0])

    class _FreeFormView(CompositeAutocompleteView):
        operators = [
            Operator(
                key="author", view=AuthorAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="authors__id",
            ),
            Operator(
                key="published_after", view=_EmptyView,
                value_field="id", label_field="id",
                q_translator=_q_after, max_count=1,
            ),
            Operator(
                key="opt_in_free_form", view=AuthorAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="authors__id", free_form=True,
            ),
        ]

    request = rf.get("/q/", {"mode": "operators"})
    response = _FreeFormView.as_view()(request)
    data = json.loads(response.content)
    by_key = {op["key"]: op for op in data["operators"]}
    assert by_key["author"]["free_form"] is False
    # Auto-derived from q_translator.
    assert by_key["published_after"]["free_form"] is True
    # Explicit override on a filter_lookup operator.
    assert by_key["opt_in_free_form"]["free_form"] is True


def test_operator_free_form_defaults_false_without_q_translator():
    """An Operator with only filter_lookup must default to free_form=False.

    Filter-lookup operators are server-backed; the client should fetch a
    suggestion list and require a row click to commit. The view-level test
    asserts the serialized flag; this test pins the dataclass invariant
    directly so future refactors of __post_init__ can't silently flip it.
    """
    op = Operator(
        key="author", view=AuthorAutocompleteView,
        value_field="id", label_field="name",
        filter_lookup="authors__id",
    )
    assert op.free_form is False


def test_operator_free_form_auto_derived_true_for_q_translator():
    """When q_translator is set and free_form defaults to None, coerce to True.

    __post_init__ must coerce it to True - the typed value IS the filter,
    so the client commits without a dropdown row.
    """
    from django.db.models import Q

    op = Operator(
        key="published_after", view=AuthorAutocompleteView,
        value_field="id", label_field="id",
        q_translator=lambda op_, values: Q(date_published__gte=values[0]),
        max_count=1,
    )
    assert op.free_form is True


def test_operator_explicit_free_form_false_overrides_q_translator_default():
    """Authors can opt out of free-form even when supplying a q_translator.

    For example, a translator that still wants suggestion-only commits.
    Explicit False must beat the auto-derivation.
    """
    from django.db.models import Q

    op = Operator(
        key="curated_translator", view=AuthorAutocompleteView,
        value_field="id", label_field="name",
        q_translator=lambda op_, values: Q(id__in=values),
        free_form=False,
    )
    assert op.free_form is False


def test_operator_free_form_never_none_after_init():
    """free_form must always be a concrete bool after __post_init__.

    It is typed bool | None at the field level, but downstream code (and
    the serialized meta endpoint) treats it as a bool.
    """
    op = Operator(
        key="author", view=AuthorAutocompleteView,
        value_field="id", label_field="name",
        filter_lookup="authors__id",
    )
    assert isinstance(op.free_form, bool)


def test_mode_operators_default_when_no_mode_param(rf, composite_class, db):
    """The default mode is ``operators`` (no mode param)."""
    request = rf.get("/q/")
    response = composite_class.as_view()(request)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "operators" in data


def test_mode_value_delegates_to_bound_view(rf, composite_class, db):
    """mode=value should pass the request through to the bound view's get()."""
    Author.objects.create(name="Alice")
    Author.objects.create(name="Bob")

    request = rf.get("/q/", {"mode": "value", "op": "author", "q": "Ali"})
    response = composite_class.as_view()(request)
    assert response.status_code == 200
    data = json.loads(response.content)
    names = [r["name"] for r in data["results"]]
    assert "Alice" in names
    assert "Bob" not in names


def test_mode_value_unknown_operator_returns_400(rf, composite_class, db):
    """mode=value with an unknown operator key returns HTTP 400."""
    request = rf.get("/q/", {"mode": "value", "op": "nonsense"})
    response = composite_class.as_view()(request)
    assert response.status_code == 400


def test_mode_value_search_lookups_override(rf, db):
    """Operator.search_lookups should narrow the bound view's search for this request."""

    class _MagazineSearchByName(MagazineAutocompleteView):
        # Pretend the bound view searches by both name and a fictitious "tag".
        search_lookups = ["name__icontains", "name__startswith"]

    Magazine.objects.create(name="Alice Weekly")
    Magazine.objects.create(name="The Bobzine")

    class _Composite(CompositeAutocompleteView):
        operators = [
            # Override: search ONLY by exact name match (bypassing icontains).
            Operator(
                key="magazine", view=_MagazineSearchByName,
                value_field="id", label_field="name",
                filter_lookup="magazine_id",
                search_lookups=["name__startswith"],
            ),
        ]

    request = rf.get("/q/", {"mode": "value", "op": "magazine", "q": "Alice"})
    response = _Composite.as_view()(request)
    data = json.loads(response.content)
    names = [r["name"] for r in data["results"]]
    # With startswith-only override, only "Alice Weekly" matches.
    assert names == ["Alice Weekly"]

    # The override is instance-scoped (subclass-per-request) and must not mutate
    # the source class. Confirm _MagazineSearchByName.search_lookups is unchanged.
    assert _MagazineSearchByName.search_lookups == ["name__icontains", "name__startswith"]


def test_mode_resolve_returns_labels_for_known_ids(rf, composite_class, db):
    """mode=resolve returns the label for each known (op, id) pair."""
    a = Author.objects.create(name="Alice")
    b = Author.objects.create(name="Bob")

    request = rf.get("/q/", {"mode": "resolve", "op": ["author", "author"], "id": [str(a.id), str(b.id)]})
    response = composite_class.as_view()(request)
    assert response.status_code == 200
    data = json.loads(response.content)
    by_id = {r["id"]: r for r in data["results"]}
    assert by_id[str(a.id)]["label"] == "Alice"
    assert by_id[str(b.id)]["label"] == "Bob"


def test_mode_resolve_marks_unknown_ids_missing(rf, composite_class, db):
    """mode=resolve marks unknown ids with missing=True instead of returning a label."""
    request = rf.get("/q/", {"mode": "resolve", "op": ["author"], "id": ["999999"]})
    response = composite_class.as_view()(request)
    data = json.loads(response.content)
    assert data["results"] == [{"op": "author", "id": "999999", "missing": True}]


def test_mode_resolve_too_many_ids_returns_400(rf, composite_class, db):
    """mode=resolve rejects oversized id batches with HTTP 400."""
    request = rf.get("/q/", {
        "mode": "resolve",
        "op": ["author"] * 100,
        "id": [str(i) for i in range(100)],
    })
    response = composite_class.as_view()(request)
    assert response.status_code == 400


def test_mode_resolve_mismatched_op_id_lengths_returns_400(rf, composite_class, db):
    """mode=resolve with mismatched op/id list lengths returns HTTP 400."""
    request = rf.get("/q/?mode=resolve&op=author&op=author&id=1")
    response = composite_class.as_view()(request)
    assert response.status_code == 400


def test_mode_resolve_unknown_operator_marks_missing(rf, composite_class, db):
    """An unknown operator key in resolve marks the ids missing rather than 400-ing the whole request."""
    a = Author.objects.create(name="Alice")
    request = rf.get("/q/", {"mode": "resolve", "op": ["nonsense", "author"], "id": ["x", str(a.id)]})
    response = composite_class.as_view()(request)
    assert response.status_code == 200
    data = json.loads(response.content)
    by_op = {(r["op"], r["id"]): r for r in data["results"]}
    assert by_op[("nonsense", "x")]["missing"] is True
    assert by_op[("author", str(a.id))]["label"] == "Alice"


def test_mode_resolve_permission_denied_marks_missing(rf, db):
    """When has_permission() returns False, all of that operator's ids surface as missing - no labels leak."""

    class _LockedAuthorView(AuthorAutocompleteView):
        skip_authorization = False
        permission_required = "auth.no_such_permission"

        def has_permission(self, request, action: str = "view") -> bool:
            return False

    class _Composite(CompositeAutocompleteView):
        operators = [
            Operator(
                key="author", view=_LockedAuthorView,
                value_field="id", label_field="name",
                filter_lookup="authors__id",
            ),
        ]

    a = Author.objects.create(name="SecretAlice")
    request = rf.get("/q/", {"mode": "resolve", "op": ["author"], "id": [str(a.id)]})
    response = _Composite.as_view()(request)
    data = json.loads(response.content)
    # Must NOT leak the label.
    assert data["results"][0] == {"op": "author", "id": str(a.id), "missing": True}


def test_mode_resolve_per_operator_isolation_on_failure(rf, db):
    """One operator failing must not poison resolve for other operators in the same batch."""

    class _ExplodingView(AuthorAutocompleteView):
        skip_authorization = True

        def get_queryset(self):
            raise RuntimeError("boom")

    class _Composite(CompositeAutocompleteView):
        operators = [
            Operator(
                key="author", view=AuthorAutocompleteView,
                value_field="id", label_field="name",
                filter_lookup="authors__id",
            ),
            Operator(
                key="exploder", view=_ExplodingView,
                value_field="id", label_field="name",
                filter_lookup="x__id",
            ),
        ]

    a = Author.objects.create(name="Alice")
    request = rf.get("/q/", {
        "mode": "resolve",
        "op": ["author", "exploder"],
        "id": [str(a.id), "1"],
    })
    response = _Composite.as_view()(request)
    data = json.loads(response.content)
    by_op = {(r["op"], r["id"]): r for r in data["results"]}
    assert by_op[("author", str(a.id))]["label"] == "Alice"
    assert by_op[("exploder", "1")]["missing"] is True


def test_mode_resolve_iterables_lookup_by_value_field(rf, composite_class, db):
    """Iterables operator should match items by Operator.value_field."""
    request = rf.get("/q/", {"mode": "resolve", "op": ["status"], "id": ["draft"]})
    response = composite_class.as_view()(request)
    data = json.loads(response.content)
    # The iterable view returns {value, label} dicts; we expect a label for "draft".
    assert data["results"][0]["op"] == "status"
    assert "missing" not in data["results"][0]


def test_resolve_view_class_class_ref_returns_class_and_empty_initkwargs():
    """A class reference resolves to the same class with no initkwargs."""
    cls, initkwargs = resolve_view_class(AuthorAutocompleteView)
    assert cls is AuthorAutocompleteView
    assert initkwargs == {}


def test_resolve_view_class_url_name_resolves_to_class():
    """A URL name resolves to the underlying view class."""
    cls, initkwargs = resolve_view_class("autocomplete-author")
    # The URL name resolves to the same class.
    assert cls.__name__ == "AuthorAutocompleteView"


def test_resolve_view_class_unknown_url_raises_improperly_configured():
    """An unknown URL name raises ImproperlyConfigured."""
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured):
        resolve_view_class("nonexistent-url-name-xyz")


def test_post_method_not_allowed(rf, composite_class, db):
    """POST requests are rejected with HTTP 405."""
    request = rf.post("/q/")
    response = composite_class.as_view()(request)
    assert response.status_code == 405


def test_unknown_mode_returns_400(rf, composite_class, db):
    """An unrecognized mode value returns HTTP 400."""
    request = rf.get("/q/", {"mode": "garbage"})
    response = composite_class.as_view()(request)
    assert response.status_code == 400


def test_resolve_applies_has_object_permission(rf, db):
    """Object-level has_object_permission must filter rows in resolve.

    Even when the bound view's get_queryset() returns the row, has_object_permission
    can deny it on a per-row basis. The resolve flow must respect that and surface
    `missing: true` rather than leaking the label.
    """
    secret = Magazine.objects.create(name="SecretMag")
    public = Magazine.objects.create(name="PublicMag")

    class _PerObjectMagazineView(MagazineAutocompleteView):
        skip_authorization = True

        def has_object_permission(self, request, obj, action="view"):
            # Deny anything whose name starts with "Secret".
            return not obj.name.startswith("Secret")

    class _Composite(CompositeAutocompleteView):
        operators = [
            Operator(
                key="magazine", view=_PerObjectMagazineView,
                value_field="id", label_field="name",
                filter_lookup="magazine_id",
            ),
        ]

    request = rf.get(
        "/q/",
        {"mode": "resolve", "op": ["magazine", "magazine"], "id": [str(secret.id), str(public.id)]},
    )
    response = _Composite.as_view()(request)
    data = json.loads(response.content)
    by_id = {r["id"]: r for r in data["results"]}
    # SecretMag must surface as missing - never leak the label.
    assert by_id[str(secret.id)] == {"op": "magazine", "id": str(secret.id), "missing": True}
    # PublicMag comes through normally.
    assert by_id[str(public.id)]["label"] == "PublicMag"


def test_view_initkwargs_baked_into_resolved_class(db):
    """as_view() init kwargs must flow through to parse_query via the URL name.

    When CompositeAutocompleteView.as_view(operators=...) is called, the
    init kwargs override class-level defaults - and parse_query MUST honor
    them when resolving via the URL name. This is the exact regression path
    Codex flagged in round 1.
    """
    from django_tomselect.query import parse_query

    # Use the existing autocomplete-article-token URL - its CBV has class-level
    # operators. We don't override via as_view here, but we do exercise the
    # full URL >> class + initkwargs >> ParsedQuery path (the prior implementation
    # discarded initkwargs entirely; the fix builds a one-shot subclass).
    parsed = parse_query("author:42 status:draft", "autocomplete-article-token")
    assert parsed.errors == []
    keys = sorted(t.key for t in parsed.tokens)
    assert keys == ["author", "status"]


def test_view_initkwargs_runtime_override_via_as_view(db, rf):
    """Runtime as_view() overrides must be reflected in parse_query resolution.

    If a project registers as_view(operators=[...]) at a URL, the resolved
    class used by parse_query must reflect those overrides, not the (possibly
    different) class-level defaults.
    """
    from django.urls import path
    from django.test import override_settings
    from django_tomselect.query import parse_query

    class _BaseEmpty(CompositeAutocompleteView):
        operators = []
        free_text_lookups = []

    runtime_operators = [
        Operator(
            key="status", view=ArticleStatusAutocompleteView,
            value_field="value", label_field="label",
            filter_lookup="status",
        ),
    ]

    urlpatterns = [
        path(
            "rt/", _BaseEmpty.as_view(operators=runtime_operators),
            name="runtime-composite",
        ),
    ]
    with override_settings(ROOT_URLCONF=type("_M", (), {"urlpatterns": urlpatterns})):
        parsed = parse_query("status:draft", "runtime-composite")
        # Class-level operators is [] but as_view-bound is the runtime list, so
        # status: must parse without an UNKNOWN_OPERATOR error.
        assert [e.code for e in parsed.errors] == []
        assert parsed.has("status")


def test_iterables_warning_for_url_name_operator(caplog, db):
    """The iterables-permission warning must fire for URL-name operators too."""
    import logging

    with caplog.at_level(logging.WARNING, logger="django_tomselect.autocompletes"):
        # Build a subclass that points at the iterables view via URL name.
        class _UrlNameComposite(CompositeAutocompleteView):
            operators = [
                Operator(
                    key="status",
                    view="autocomplete-article-status",  # URL name, not class ref
                    value_field="value",
                    label_field="label",
                    filter_lookup="status",
                ),
            ]

    msgs = [r.getMessage() for r in caplog.records]
    assert any("iterables" in m.lower() or "AutocompleteIterablesView" in m for m in msgs), msgs
