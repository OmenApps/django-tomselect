"""Tests for django_tomselect LazyView class."""

import pytest
from django.db.models import QuerySet
from django.urls import NoReverseMatch

from django_tomselect.lazy_utils import LazyView
from example_project.example.models import Edition


class TestLazyViewGetUrl:
    """Tests for LazyView.get_url()."""

    def test_get_url_resolves_valid_url(self, db):
        """Test that get_url resolves a valid URL name."""
        lazy_view = LazyView(url_name="autocomplete-edition")
        url = lazy_view.get_url()
        assert url is not None
        assert isinstance(url, str)
        assert len(url) > 0

    def test_get_url_caches_result(self, db):
        """Test that get_url caches the resolved URL."""
        lazy_view = LazyView(url_name="autocomplete-edition")
        url1 = lazy_view.get_url()
        url2 = lazy_view.get_url()
        assert url1 == url2
        assert lazy_view._url is not None

    def test_get_url_raises_on_invalid_url(self, db):
        """Test that get_url raises NoReverseMatch for invalid URL names."""
        lazy_view = LazyView(url_name="nonexistent-url-name")
        with pytest.raises(NoReverseMatch):
            lazy_view.get_url()


class TestLazyViewGetView:
    """Tests for LazyView.get_view()."""

    def test_get_view_returns_view_instance(self, db):
        """Test that get_view returns a view instance."""
        lazy_view = LazyView(url_name="autocomplete-edition", model=Edition)
        view = lazy_view.get_view()
        assert view is not None

    def test_get_view_returns_none_for_invalid_url(self, db):
        """Test that get_view raises for an invalid URL."""
        lazy_view = LazyView(url_name="nonexistent-url")
        with pytest.raises(NoReverseMatch):
            lazy_view.get_view()

    def test_get_view_preserves_view_attributes(self, db):
        """Test that get_view preserves important view attributes like skip_authorization."""
        lazy_view = LazyView(url_name="autocomplete-edition", model=Edition)
        view = lazy_view.get_view()
        # EditionAutocompleteView has skip_authorization = True
        assert view is not None
        assert getattr(view, "skip_authorization", False) is True

    def test_get_view_sets_model(self, db):
        """Test that get_view sets the model on the view instance."""
        lazy_view = LazyView(url_name="autocomplete-edition", model=Edition)
        view = lazy_view.get_view()
        assert view is not None
        assert view.model == Edition


class TestLazyViewGetQueryset:
    """Tests for LazyView.get_queryset()."""

    def test_get_queryset_returns_queryset(self, db):
        """Test that get_queryset returns a QuerySet."""
        lazy_view = LazyView(url_name="autocomplete-edition", model=Edition)
        qs = lazy_view.get_queryset()
        assert isinstance(qs, QuerySet)

    def test_get_queryset_returns_empty_for_invalid_url(self, db):
        """Test that get_queryset returns empty queryset for invalid URL."""
        lazy_view = LazyView(url_name="nonexistent-url")
        with pytest.raises(NoReverseMatch):
            lazy_view.get_queryset()

    def test_get_queryset_contains_model_instances(self, db, sample_edition):
        """Test that get_queryset returns a queryset containing model instances."""
        lazy_view = LazyView(url_name="autocomplete-edition", model=Edition)
        qs = lazy_view.get_queryset()
        assert qs.count() >= 1
        assert sample_edition in qs


class TestLazyViewGetModel:
    """Tests for LazyView.get_model()."""

    def test_get_model_returns_model_class(self, db):
        """Test that get_model returns the correct model class."""
        lazy_view = LazyView(url_name="autocomplete-edition", model=Edition)
        model = lazy_view.get_model()
        assert model == Edition

    def test_get_model_returns_empty_model_for_invalid_url(self, db):
        """Test that get_model raises for an invalid URL."""
        lazy_view = LazyView(url_name="nonexistent-url")
        with pytest.raises(NoReverseMatch):
            lazy_view.get_model()

    def test_get_model_from_view_without_explicit_model(self, db):
        """Test that get_model discovers model from the view when not explicitly provided."""
        lazy_view = LazyView(url_name="autocomplete-edition")
        model = lazy_view.get_model()
        # EditionAutocompleteView has model = Edition
        assert model == Edition


class TestLazyViewInitialization:
    """Tests for LazyView initialization and configuration."""

    def test_init_stores_url_name(self):
        """Test that __init__ stores the url_name."""
        lazy_view = LazyView(url_name="autocomplete-edition")
        assert lazy_view.url_name == "autocomplete-edition"

    def test_init_stores_model(self):
        """Test that __init__ stores the model."""
        lazy_view = LazyView(url_name="autocomplete-edition", model=Edition)
        assert lazy_view.model == Edition

    def test_init_stores_user(self):
        """Test that __init__ stores the user."""
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        lazy_view = LazyView(url_name="autocomplete-edition", user=anon)
        assert lazy_view.user == anon

    def test_init_defaults(self):
        """Test that __init__ sets proper defaults."""
        lazy_view = LazyView(url_name="test")
        assert lazy_view.model is None
        assert lazy_view.user is None
        assert lazy_view._view is None
        assert lazy_view._url is None
