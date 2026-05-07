"""End-to-end smoke tests for the article-token-search demo.

Wires the example project: form >> view >> template, plus the bulk-actions
cross-link.

These tests use ``django.test.Client`` to render full pages. On Python 3.14
combined with Django 4.2 / 5.1, Django's ``Context.__copy__`` raises
``AttributeError: 'super' object has no attribute 'dicts' and no __dict__``
when the test framework's ``store_rendered_templates`` signal copies the
context - this is a Django bug fixed in 5.2. We skip these tests on the
affected matrix; coverage is preserved on every other supported combination.
"""

from __future__ import annotations

import sys

import django
import pytest

from example_project.example.models import Article, Author, Category, Magazine

# Django < 5.2 + Python 3.14: Context.__copy__ is broken. Skip rather than
# carry a broken matrix combination.
_skip_py314_django_lt_52 = pytest.mark.skipif(
    sys.version_info >= (3, 14) and django.VERSION < (5, 2),
    reason=(
        "Django <5.2 Context.__copy__ is incompatible with Python 3.14 "
        "(AttributeError: 'super' object has no attribute 'dicts'). Fixed in Django 5.2."
    ),
)
pytestmark = _skip_py314_django_lt_52


@pytest.fixture
def sample_data(db):
    """Seed two articles with distinct authors/categories for token-search tests."""
    mag = Magazine.objects.create(name="Test Magazine")
    a1 = Author.objects.create(name="Alice")
    a2 = Author.objects.create(name="Bob")
    cat_tech = Category.objects.create(name="Tech")
    cat_news = Category.objects.create(name="News")

    art1 = Article.objects.create(title="Hello world", magazine=mag, status="draft", word_count=100)
    art1.authors.add(a1)
    art1.categories.add(cat_tech)

    art2 = Article.objects.create(title="Goodbye moon", magazine=mag, status="published", word_count=200)
    art2.authors.add(a2)
    art2.categories.add(cat_news)

    return {
        "mag": mag, "a1": a1, "a2": a2,
        "cat_tech": cat_tech, "cat_news": cat_news,
        "art1": art1, "art2": art2,
    }


def test_demo_page_renders(client, sample_data):
    """Demo page renders with token widget markup and seeded articles."""
    r = client.get("/article-token-search/")
    assert r.status_code == 200
    assert b"Article Token-Style Search" in r.content
    assert b"data-django-tomselect-token" in r.content
    # The token JSON config blob is present on the wrapper.
    assert b"data-config" in r.content
    # Initial render with no filter shows all articles (capped at 50).
    assert b"Hello world" in r.content
    assert b"Goodbye moon" in r.content


def test_composite_mode_operators(client, sample_data):
    """``mode=operators`` returns the registered operator metadata."""
    r = client.get("/autocomplete/article-token/?mode=operators")
    assert r.status_code == 200
    data = r.json()
    keys = [op["key"] for op in data["operators"]]
    assert keys == ["author", "category", "magazine", "status"]
    by_key = {op["key"]: op for op in data["operators"]}
    assert by_key["category"]["multi"] is True
    assert by_key["author"]["max_count"] == 3


def test_composite_mode_value_delegates(client, sample_data):
    """``mode=value`` delegates to the operator's autocomplete view."""
    r = client.get("/autocomplete/article-token/?mode=value&op=author&q=Ali")
    assert r.status_code == 200
    names = [row["name"] for row in r.json()["results"]]
    assert "Alice" in names
    assert "Bob" not in names


def test_composite_mode_resolve_hydrates_known_and_marks_unknown(client, sample_data):
    """``mode=resolve`` hydrates known ids and marks unknown ones as missing."""
    a1 = sample_data["a1"]
    r = client.get(
        f"/autocomplete/article-token/?mode=resolve&op=author&id={a1.id}&op=author&id=999999"
    )
    assert r.status_code == 200
    by_id = {row["id"]: row for row in r.json()["results"]}
    assert by_id[str(a1.id)]["label"] == "Alice"
    assert by_id["999999"].get("missing") is True


def test_demo_filters_by_author(client, sample_data):
    """``author:<id>`` token narrows the article list to that author."""
    a1 = sample_data["a1"]
    r = client.get(f"/article-token-search/?q=author%3A{a1.id}")
    assert r.status_code == 200
    assert b"Hello world" in r.content     # Alice's article
    assert b"Goodbye moon" not in r.content


def test_demo_filters_by_category_multi(client, sample_data):
    """``category:<id>,<id>`` returns articles in any listed category."""
    tech = sample_data["cat_tech"]
    news = sample_data["cat_news"]
    r = client.get(f"/article-token-search/?q=category%3A{tech.id}%2C{news.id}")
    assert r.status_code == 200
    assert b"Hello world" in r.content
    assert b"Goodbye moon" in r.content


def test_demo_typed_value_for_id_operator_surfaces_validation_error(client, sample_data):
    """``category:tech`` (string) against id-based filter_lookup is a clean error."""
    r = client.get("/article-token-search/?q=category%3Atech")
    assert r.status_code == 200
    # Form rendered the field-level error.
    assert b"Invalid value" in r.content or b"select an option from the dropdown" in r.content


def test_demo_unknown_operator_is_rejected(client, sample_data):
    """An unknown operator key surfaces as a form-level error in the page."""
    r = client.get("/article-token-search/?q=nonsense%3Afoo")
    assert r.status_code == 200
    # Form-level error in the rendered output.
    assert b"Unknown operator" in r.content


def test_bulk_actions_cross_link_present(client, sample_data):
    """Bulk-actions page advertises the new token-style search."""
    r = client.get("/article-bulk-action/")
    assert r.status_code == 200
    assert b"Try the new token-style search" in r.content
    # Ensure the bulk-action page itself still works (filters form still rendered).
    assert b"date_range" in r.content
