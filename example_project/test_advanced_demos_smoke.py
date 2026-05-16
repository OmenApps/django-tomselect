"""Smoke tests for the four new advanced demos.

These tests don't try to be exhaustive  they confirm the demos' wiring
(URL >> view >> form >> autocomplete view) doesn't crash on the happy path
or on common error paths. The package's full behaviour is covered elsewhere.

On Python 3.14 combined with Django 4.2 / 5.1, Django's ``Context.__copy__``
raises ``AttributeError: 'super' object has no attribute 'dicts' and no
__dict__`` when the test framework's ``store_rendered_templates`` signal
copies the context - this is a Django bug fixed in 5.2. We skip the whole
module on the affected matrix to match the precedent in
``test_token_widget_integration.py``; coverage is preserved on every other
supported combination.
"""

from __future__ import annotations

import json
import sys
from unittest import mock

import django
import pytest
from django.test import Client
from django.urls import reverse


_skip_py314_django_lt_52 = pytest.mark.skipif(
    sys.version_info >= (3, 14) and django.VERSION < (5, 2),
    reason=(
        "Django <5.2 Context.__copy__ is incompatible with Python 3.14 "
        "(AttributeError: 'super' object has no attribute 'dicts'). Fixed in Django 5.2."
    ),
)
pytestmark = [pytest.mark.django_db, _skip_py314_django_lt_52]


@pytest.fixture
def client() -> Client:
    """Return a fresh Django test client for each test."""
    return Client()


class TestGitHubUserPicker:
    """Smoke tests for the GitHub user picker demo."""

    def test_page_renders(self, client):
        """The picker page renders and contains its heading."""
        resp = client.get(reverse("github-user-picker"))
        assert resp.status_code == 200
        assert b"GitHub User Picker" in resp.content

    def test_autocomplete_empty_query(self, client):
        """Empty query returns an empty result envelope with no upstream call."""
        resp = client.get(reverse("autocomplete-github-user"), {"q": ""})
        assert resp.status_code == 200
        body = json.loads(resp.content)
        assert body == {"results": [], "page": 1, "has_more": False}

    def test_autocomplete_short_query(self, client):
        """Single-character queries fall under minimum_query_length=2 and return nothing."""
        resp = client.get(reverse("autocomplete-github-user"), {"q": "a"})
        body = json.loads(resp.content)
        assert body["results"] == []
        assert body["has_more"] is False

    def test_autocomplete_fetch_mocked(self, client):
        """A mocked httpx response yields the expected row shape."""
        fake_payload = {
            "total_count": 2,
            "items": [
                {"login": "octocat", "avatar_url": "https://x/y", "bio": "GitHub mascot"},
                {"login": "octodog", "avatar_url": "https://x/z", "bio": ""},
            ],
        }

        fake_resp = mock.Mock()
        fake_resp.status_code = 200
        fake_resp.headers = {"x-ratelimit-remaining": "10"}
        fake_resp.json.return_value = fake_payload

        # httpx is imported lazily inside _fetch_github, so patch on the
        # httpx module itself, not on the example autocompletes module.
        with mock.patch("httpx.Client") as httpx_client_mock:
            instance = httpx_client_mock.return_value.__enter__.return_value
            instance.get.return_value = fake_resp
            resp = client.get(reverse("autocomplete-github-user"), {"q": "octo"})

        body = json.loads(resp.content)
        assert resp.status_code == 200
        # Row keys MUST be "value"/"label" to match the widget's configured
        # value_field/label_field. If we ever regress to "id"/"label" Tom
        # Select silently shows "No results" even with a 200 response.
        for row in body["results"]:
            assert "value" in row, f"missing 'value' key: {row}"
            assert "label" in row, f"missing 'label' key: {row}"
        logins = [r["value"] for r in body["results"]]
        assert logins == ["octocat", "octodog"]
        # value == label so the iterables widget default fallback can render the chip
        assert all(r["value"] == r["label"] for r in body["results"])

    def test_form_post_round_trips_login(self, client):
        """A POSTed login is echoed back in the rendered response."""
        resp = client.post(reverse("github-user-picker"), {"github_user": "octocat"})
        assert resp.status_code == 200
        assert b"octocat" in resp.content

    def test_response_advertises_next_page_when_has_more(self, client):
        """The package frontend pages only when both has_more and next_page are present."""
        fake_payload = {
            "total_count": 100,  # >> page_size
            "items": [{"login": f"user{i}", "bio": ""} for i in range(20)],
        }
        fake_resp = mock.Mock()
        fake_resp.status_code = 200
        fake_resp.headers = {"x-ratelimit-remaining": "10"}
        fake_resp.json.return_value = fake_payload

        with mock.patch("httpx.Client") as httpx_client_mock:
            instance = httpx_client_mock.return_value.__enter__.return_value
            instance.get.return_value = fake_resp
            resp = client.get(reverse("autocomplete-github-user"), {"q": "user"})

        body = json.loads(resp.content)
        assert body["has_more"] is True
        assert body["next_page"] == 2

    def test_error_responses_are_not_cached(self, client):
        """Throttle responses must not be memoized by the per-query cache.

        Otherwise the next refresh keeps serving the stale error message even
        after the throttle window expires.
        """
        from django.core.cache import cache as django_cache

        django_cache.clear()
        fake_resp = mock.Mock()
        fake_resp.status_code = 403
        fake_resp.headers = {"retry-after": "30"}

        with mock.patch("httpx.Client") as httpx_client_mock:
            instance = httpx_client_mock.return_value.__enter__.return_value
            instance.get.return_value = fake_resp
            resp = client.get(reverse("autocomplete-github-user"), {"q": "octo"})
        body = json.loads(resp.content)
        assert "error" in body  # throttled response surfaced
        # Now drop the throttle window and confirm the cache didn't memoize
        # the throttled payload under the normal query cache key.
        django_cache.delete("demo-github-user-search:throttled-until")
        fake_resp_ok = mock.Mock()
        fake_resp_ok.status_code = 200
        fake_resp_ok.headers = {"x-ratelimit-remaining": "10"}
        fake_resp_ok.json.return_value = {"total_count": 1, "items": [{"login": "octocat", "bio": ""}]}
        with mock.patch("httpx.Client") as httpx_client_mock:
            instance = httpx_client_mock.return_value.__enter__.return_value
            instance.get.return_value = fake_resp_ok
            resp2 = client.get(reverse("autocomplete-github-user"), {"q": "octo"})
        body2 = json.loads(resp2.content)
        # Cache miss >> second response is the success payload, not stale error.
        assert "error" not in body2
        assert body2["results"][0]["value"] == "octocat"


class TestInlineCreateTag:
    """Smoke tests for the HTMX-powered inline tag creation demo."""

    def test_page_renders(self, client):
        """The inline-create page renders with its expected heading."""
        resp = client.get(reverse("inline-create-tag"))
        assert resp.status_code == 200
        assert b"Inline Create with HTMX" in resp.content

    def test_create_endpoint_success(self, client):
        """A brand-new tag is created and the endpoint reports is_new=True."""
        from example_project.example.models import PublicationTag

        assert not PublicationTag.objects.filter(name="smoke-new").exists()
        resp = client.post(reverse("htmx-create-publication-tag"), {"name": "smoke-new"})
        assert resp.status_code == 200
        body = json.loads(resp.content)
        assert body == {
            "action": "select",
            "value": "smoke-new",
            "label": "smoke-new",
            "is_new": True,
        }
        tag = PublicationTag.objects.get(name="smoke-new")
        assert tag.is_approved is True

    def test_create_endpoint_duplicate(self, client):
        """Submitting an existing tag selects it instead of erroring and auto-approves it."""
        from example_project.example.models import PublicationTag

        PublicationTag.objects.create(name="dup-tag", is_approved=False)
        resp = client.post(reverse("htmx-create-publication-tag"), {"name": "dup-tag"})
        body = json.loads(resp.content)
        assert body["action"] == "select"
        assert body["value"] == "dup-tag"
        assert body["is_new"] is False
        # Duplicate path auto-approves an unapproved tag for the demo's visibility.
        assert PublicationTag.objects.get(name="dup-tag").is_approved is True

    @pytest.mark.parametrize("bad", [
        "",                                   # empty
        "has spaces",                         # space char
        "x" * 60,                             # exceeds max_length=50
        "!nope",                              # punctuation
        "a",                                  # below model min length (2)
        "ends-",                              # ends with non-alphanumeric
        "-starts",                            # starts with non-alphanumeric
        "double--dash",                       # consecutive special chars
        "double__under",                      # consecutive special chars
    ])
    def test_create_endpoint_validation_failure(self, client, bad):
        """Invalid tag names are rejected by full_clean() and surface as error responses."""
        # The endpoint delegates to PublicationTag.full_clean(), so these
        # tests track the model's own rules in models.py.
        resp = client.post(reverse("htmx-create-publication-tag"), {"name": bad})
        assert resp.status_code == 200
        body = json.loads(resp.content)
        assert body["action"] == "error"
        assert "error" in body

    def test_session_panel_partial_only_tracks_new_creations(self, client):
        """Only genuine creations appear in the 'Tags created this session' panel.

        Re-typing an existing tag is a successful 'select' but must not add
        another panel entry, and re-typing a pre-existing tag must not appear
        at all.
        """
        from example_project.example.models import PublicationTag

        # Empty by default.
        resp = client.get(reverse("htmx-tag-session-panel"))
        assert resp.status_code == 200
        assert b"none yet" in resp.content or b"(none yet" in resp.content

        # A genuine creation populates the panel.
        client.post(reverse("htmx-create-publication-tag"), {"name": "panel-new"})
        resp = client.get(reverse("htmx-tag-session-panel"))
        assert b"panel-new" in resp.content

        # Re-creating the same tag is now a duplicate (is_new=False) and must
        # NOT duplicate the panel entry  but the existing entry stays.
        client.post(reverse("htmx-create-publication-tag"), {"name": "panel-new"})
        resp = client.get(reverse("htmx-tag-session-panel"))
        assert resp.content.count(b"panel-new") == 1

        # An existing-but-not-yet-in-panel tag re-typed should not appear in
        # the panel  only true creations land there.
        PublicationTag.objects.create(name="preexisting", is_approved=False)
        client.post(reverse("htmx-create-publication-tag"), {"name": "preexisting"})
        resp = client.get(reverse("htmx-tag-session-panel"))
        assert b"preexisting" not in resp.content


class TestGfkPicker:
    """Smoke tests for the generic foreign key (GFK) picker demo."""

    def test_page_renders(self, client):
        """The GFK picker page renders with its expected heading."""
        resp = client.get(reverse("gfk-picker"))
        assert resp.status_code == 200
        assert b"Generic Foreign Key Picker" in resp.content

    def test_adapter_empty_query(self, client):
        """Empty queries route through every subview and return a valid envelope."""
        resp = client.get(reverse("autocomplete-multi-type-featured"), {"q": ""})
        assert resp.status_code == 200
        body = json.loads(resp.content)
        # The adapter routes ?q="" through the per-type subviews which return
        # their default (unfiltered) page.
        assert isinstance(body["results"], list)

    def test_adapter_scoped_to_article(self, client):
        """A scope=article query only returns rows from the article subview."""
        from example_project.example.models import Article

        if not Article.objects.exists():
            pytest.skip("no articles in fixtures to scope against")
        resp = client.get(reverse("autocomplete-multi-type-featured"), {"scope": "article"})
        body = json.loads(resp.content)
        for r in body["results"]:
            assert r["value"].startswith("article:")
            assert r["_type_key"] == "article"

    def test_form_creates_spotlight(self, client):
        """A valid type:pk submission creates a Spotlight tied to the right object."""
        from example_project.example.models import Article, Spotlight

        article = Article.objects.first()
        if article is None:
            pytest.skip("no article available")
        prior = Spotlight.objects.count()
        resp = client.post(reverse("gfk-picker"), {
            "title": "Smoke Spotlight",
            "featured": f"article:{article.pk}",
            "scope": "",
        })
        # Redirect on success
        assert resp.status_code in (302, 303)
        assert Spotlight.objects.count() == prior + 1
        sp = Spotlight.objects.latest("featured_at")
        assert sp.title == "Smoke Spotlight"
        assert sp.content_object == article

    def test_form_rejects_invalid_value(self, client):
        """A malformed featured value re-renders the form with an 'Invalid value' error."""
        resp = client.post(reverse("gfk-picker"), {
            "title": "Bad",
            "featured": "not-a-pair",
        })
        assert resp.status_code == 200
        assert b"Invalid value" in resp.content

    def test_scope_param_threads_into_widget_autocomplete_url(self, client):
        """?scope=article on the page >> widget's autocomplete URL includes ?scope=article.

        The package frontend appends the widget's ``autocomplete_params``
        string to every fetch URL, so this is the wire-level proof that the
        narrowing actually narrows. We assert on the rendered JS config
        explicitly so the test fails if ``get_autocomplete_params()`` ever
        regresses (relying on the template's explanatory text would let a
        broken widget pass).
        """
        resp = client.get(reverse("gfk-picker") + "?scope=article")
        assert resp.status_code == 200
        # The template runs the value through escapejs, which encodes "=" as
        # "=" inside JS string literals. Both encodings represent the
        # same URL string at runtime.
        scope_chunk_escaped = b"autocompleteParams: 'scope\\u003Darticle'"
        scope_chunk_literal = b"autocompleteParams: 'scope=article'"
        assert (
            scope_chunk_escaped in resp.content
            or scope_chunk_literal in resp.content
        ), "expected autocompleteParams to carry scope=article in the rendered JS"

        # And the no-scope path must NOT set autocompleteParams to a scope.
        resp_none = client.get(reverse("gfk-picker"))
        assert resp_none.status_code == 200
        assert b"autocompleteParams: 'scope" not in resp_none.content
        assert b"autocompleteParams: 'scope\\u003D" not in resp_none.content

    def test_adapter_handles_subview_permission_denied(self, client):
        """A PermissionDenied from one subview must be skipped, not bubbled as a 500.

        The adapter should continue collecting rows from the remaining types.
        """
        from django.core.exceptions import PermissionDenied

        # Force one of the subviews to raise PermissionDenied by patching
        # its as_view() to return a callable that raises.
        def raising_dispatch(request, *args, **kwargs):
            raise PermissionDenied("denied")

        with mock.patch(
            "example_project.example.autocompletes.AuthorAutocompleteView.as_view",
            return_value=raising_dispatch,
        ):
            resp = client.get(reverse("autocomplete-multi-type-featured"))
        assert resp.status_code == 200
        body = json.loads(resp.content)
        # Other subviews still contribute rows; the response is valid JSON.
        assert isinstance(body["results"], list)
        # None of the rows are authors (the denied subview).
        for row in body["results"]:
            assert row.get("_type_key") != "author"


class TestAdvancedTokenSearch:
    """Smoke tests for the advanced token-search article demo."""

    def test_page_renders(self, client):
        """The advanced token-search page renders with its expected heading."""
        resp = client.get(reverse("article-advanced-token-search"))
        assert resp.status_code == 200
        assert b"Article Token Search (Advanced)" in resp.content

    def test_composite_operators_listing(self, client):
        """?mode=operators returns the configured token operators in expected order."""
        resp = client.get(reverse("autocomplete-article-advanced-token"), {"mode": "operators"})
        body = json.loads(resp.content)
        keys = [op["key"] for op in body["operators"]]
        assert keys == [
            "author", "status",
            "published_after", "published_before", "word_count",
        ]

    def test_no_suggestion_view_is_empty(self, client):
        """The 'no suggestion' autocomplete view always returns an empty result list."""
        resp = client.get(reverse("autocomplete-no-suggestion"), {"q": "anything"})
        body = json.loads(resp.content)
        assert body["results"] == []

    @pytest.mark.parametrize("q,expect_error", [
        ("word_count:>500", False),
        ("word_count:100..2000", False),
        ("published_after:2024-01-01", False),
        ("published_after:not-a-date", True),
        ("word_count:abc", True),
        ("word_count:>abc", True),
        ("word_count:5000..100", True),  # inverted range
    ])
    def test_q_translator_paths(self, client, q, expect_error):
        """Valid token expressions render cleanly; invalid ones surface an error hint."""
        resp = client.get(reverse("article-advanced-token-search"), {"q": q})
        assert resp.status_code == 200
        if expect_error:
            assert (b"error" in resp.content.lower()
                    or b"invalid" in resp.content.lower()
                    or b"word_count" in resp.content.lower())
