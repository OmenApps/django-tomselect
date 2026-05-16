"""Tests for django_tomselect caching - the @cache_permission decorator."""

import logging

import pytest
from django.test import override_settings

from django_tomselect.cache import cache_permission, permission_cache


@pytest.mark.django_db
class TestCachePermissionDecorator:
    """Test the cache_permission decorator."""

    @pytest.fixture
    def mock_view(self):
        """Create a mock view class."""

        class MockView:
            """Mock view class."""

            model = type("MockModel", (), {"_meta": type("Meta", (), {"model_name": "mock"})()})()
            skip_authorization = False
            allow_anonymous = False

            @cache_permission
            def check_permission(self, request, action="view"):
                """Test the cache_permission decorator."""
                return True

        return MockView()

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""

        class User:
            """Mock user class."""

            id = 1
            is_authenticated = True

        return type("MockRequest", (), {"user": User()})()

    def test_decorator_caches_result(self, mock_view, mock_request):
        """Test that the decorator caches permission check results."""
        # First call should cache the result
        result1 = mock_view.check_permission(mock_request)
        assert result1 is True

        # Second call should use cached result
        result2 = mock_view.check_permission(mock_request)
        assert result2 is True

    def test_decorator_skip_cache_for_anonymous(self, mock_view):
        """Test that decorator skips cache for anonymous users."""
        anon_request = type("MockRequest", (), {"user": type("User", (), {"is_authenticated": False})()})
        result = mock_view.check_permission(anon_request)
        assert result is True

    def test_decorator_skip_cache_for_authorization_override(self, mock_view, mock_request):
        """Test that decorator skips cache when authorization is overridden."""
        mock_view.skip_authorization = True
        result = mock_view.check_permission(mock_request)
        assert result is True

    @override_settings(DEBUG=True)
    def test_decorator_skip_cache_in_debug(self, mock_view, mock_request):
        """Test that decorator skips cache in DEBUG mode."""
        result = mock_view.check_permission(mock_request)
        assert result is True


@pytest.mark.django_db
class TestCachePermissionDecoratorComplete:
    """Comprehensive tests for cache_permission decorator."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model class."""

        class MockMeta:
            """Mock _meta class."""
            model_name = "testmodel"

        class MockModel:
            """Mock model class."""
            _meta = MockMeta()

        return MockModel

    @pytest.fixture
    def mock_view_class(self, mock_model):
        """Create a mock view class."""

        class MockView:
            """Mock view class."""
            model = mock_model
            skip_authorization = False
            allow_anonymous = False
            permission_result = True

            @cache_permission
            def check_permission(self, request, action="view"):
                """Test the cache_permission decorator."""
                return self.permission_result

        return MockView

    @pytest.fixture
    def authenticated_request(self):
        """Create an authenticated mock request."""

        class MockUser:
            """Mock user class."""
            id = 1
            is_authenticated = True

        class MockRequest:
            """Mock request class."""
            user = MockUser()

        return MockRequest()

    @pytest.fixture
    def anonymous_request(self):
        """Create an anonymous mock request."""

        class MockUser:
            """Mock user class."""
            is_authenticated = False

        class MockRequest:
            """Mock request class."""
            user = MockUser()

        return MockRequest()

    @pytest.mark.parametrize(
        "use_anonymous,skip_authorization,allow_anonymous",
        [
            (True, False, False),  # Anonymous user
            (False, True, False),  # skip_authorization=True
            (False, False, True),  # allow_anonymous=True
        ],
        ids=["anonymous_user", "skip_authorization", "allow_anonymous"],
    )
    def test_decorator_skips_cache(
        self,
        mock_view_class,
        authenticated_request,
        anonymous_request,
        caplog,
        use_anonymous,
        skip_authorization,
        allow_anonymous,
    ):
        """Test decorator skips cache for various skip conditions."""
        view = mock_view_class()
        view.skip_authorization = skip_authorization
        view.allow_anonymous = allow_anonymous
        request = anonymous_request if use_anonymous else authenticated_request

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(request)
        # Should call original function
        assert result is True

    def test_decorator_handles_missing_user_attribute(self, mock_view_class, caplog):
        """Test decorator handles request without user attribute."""

        class RequestWithoutUser:
            """Mock request class without user attribute."""
            pass

        view = mock_view_class()
        request = RequestWithoutUser()

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(request)
        # Should call original function even without user
        assert result is True

    def test_decorator_handles_missing_model(self, authenticated_request, caplog):
        """Test decorator handles view without model attribute."""

        class ViewWithoutModel:
            """Mock view class without model attribute."""
            skip_authorization = False
            allow_anonymous = False

            @cache_permission
            def check_permission(self, request, action="view"):
                """Test the cache_permission decorator."""
                return True

        view = ViewWithoutModel()

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(authenticated_request)
        # Should call original function
        assert result is True

    def test_decorator_handles_missing_model_meta(self, authenticated_request, caplog):
        """Test decorator handles model without _meta attribute."""

        class ModelWithoutMeta:
            """Mock model class without _meta attribute."""
            pass

        class ViewWithBadModel:
            """Mock view class with bad model."""
            model = ModelWithoutMeta()
            skip_authorization = False
            allow_anonymous = False

            @cache_permission
            def check_permission(self, request, action="view"):
                """Test the cache_permission decorator."""
                return True

        view = ViewWithBadModel()

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(authenticated_request)
        # Should call original function
        assert result is True

    def test_decorator_handles_none_user_id(self, mock_view_class, caplog):
        """Test decorator handles user with None id."""

        class MockUser:
            """Mock user class with None id."""
            id = None
            is_authenticated = True

        class MockRequest:
            """Mock request class."""
            user = MockUser()

        view = mock_view_class()
        request = MockRequest()

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(request)
        # Should call original function
        assert result is True

    def test_decorator_exception_fallback(self, mock_view_class, authenticated_request, monkeypatch, caplog):
        """Test decorator falls back to original function on exception."""
        view = mock_view_class()

        # Make permission_cache.is_enabled() raise an exception
        def mock_is_enabled():
            """Mock is_enabled that raises exception."""
            raise AttributeError("Cache check error")

        monkeypatch.setattr(permission_cache, "is_enabled", mock_is_enabled)

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(authenticated_request)
        # Original function should be called
        assert result is True
