"""Tests for django_tomselect context processors and middleware."""

import pytest
from django.http import HttpResponse

from django_tomselect.context_processors import tomselect
from django_tomselect.middleware import (
    TomSelectMiddleware,
    _request_local,
    get_current_request,
)


class TestContextProcessors:
    """Test the tomselect context processor."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""

        class MockRequest:
            """Mock request object."""

            def __init__(self):
                self.META = {}
                self.GET = {}
                self.POST = {}

        return MockRequest()

    def test_tomselect_context_processor(self, mock_request):
        """Test that the context processor adds request to context."""
        context = tomselect(mock_request)
        assert "tomselect_request" in context
        assert context["tomselect_request"] == mock_request

    def test_tomselect_context_processor_attributes(self, mock_request):
        """Test that the request in context has expected attributes."""
        context = tomselect(mock_request)
        request = context["tomselect_request"]
        assert hasattr(request, "META")
        assert hasattr(request, "GET")
        assert hasattr(request, "POST")


@pytest.mark.django_db
class TestTomSelectMiddleware:
    """Test the TomSelect middleware."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""

        class MockRequest:
            """Mock request object."""

            def __init__(self):
                self.META = {}
                self.path = "/test/"
                self.method = "GET"

        return MockRequest()

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""

        def get_response(request):
            return HttpResponse()

        return TomSelectMiddleware(get_response)

    def test_middleware_sets_request(self, middleware, mock_request):
        """Test that middleware sets request in thread local storage."""
        middleware(mock_request)
        assert get_current_request() is None  # Should be cleared after request

    def test_middleware_cleans_up_request(self, middleware, mock_request):
        """Test that middleware cleans up request from thread local storage."""
        middleware(mock_request)
        assert not hasattr(_request_local, "request")

    def test_middleware_handles_exceptions(self, middleware, mock_request):
        """Test that middleware cleans up even when exceptions occur."""

        def failing_get_response(request):
            raise ValueError("Test exception")

        middleware.get_response = failing_get_response

        with pytest.raises(ValueError):
            middleware(mock_request)

        assert not hasattr(_request_local, "request")

    def test_get_current_request_without_middleware(self):
        """Test get_current_request when no request is set."""
        assert get_current_request() is None

    @pytest.mark.asyncio
    async def test_middleware_async(self, middleware, mock_request):
        """Test async middleware operation."""

        async def async_get_response(request):
            return HttpResponse()

        middleware.get_response = async_get_response

        # Test the async call method
        response = await middleware.__acall__(mock_request)
        assert isinstance(response, HttpResponse)
        assert not hasattr(_request_local, "request")

    @pytest.mark.asyncio
    async def test_middleware_async_with_exception(self, middleware, mock_request):
        """Test async middleware handles exceptions."""

        async def failing_async_get_response(request):
            raise ValueError("Test async exception")

        middleware.get_response = failing_async_get_response

        with pytest.raises(ValueError):
            await middleware.__acall__(mock_request)

        assert not hasattr(_request_local, "request")

    def test_middleware_with_multiple_requests(self, middleware):
        """Test middleware handles multiple requests correctly."""
        request1 = type("MockRequest", (), {"path": "/test1/", "META": {}})()
        request2 = type("MockRequest", (), {"path": "/test2/", "META": {}})()

        middleware(request1)
        assert not hasattr(_request_local, "request")

        middleware(request2)
        assert not hasattr(_request_local, "request")

    @pytest.mark.asyncio
    async def test_middleware_async_request_isolation(self, middleware):
        """Test async middleware maintains request isolation."""
        request1 = type("MockRequest", (), {"path": "/async1/", "META": {}})()
        request2 = type("MockRequest", (), {"path": "/async2/", "META": {}})()

        async def async_get_response(request):
            return HttpResponse()

        middleware.get_response = async_get_response

        # Process multiple requests concurrently
        await middleware.__acall__(request1)
        assert not hasattr(_request_local, "request")

        await middleware.__acall__(request2)
        assert not hasattr(_request_local, "request")

    def test_middleware_request_cleanup_on_response_exception(self, middleware, mock_request):
        """Test cleanup when response generation raises exception."""

        def error_response(request):
            raise RuntimeError("Response error")

        middleware.get_response = error_response

        with pytest.raises(RuntimeError):
            middleware(mock_request)

        assert not hasattr(_request_local, "request")

    @pytest.mark.asyncio
    async def test_middleware_async_cleanup_on_response_exception(self, middleware, mock_request):
        """Test async cleanup when response generation raises exception."""

        async def error_response(request):
            raise RuntimeError("Async response error")

        middleware.get_response = error_response

        with pytest.raises(RuntimeError):
            await middleware.__acall__(mock_request)

        assert not hasattr(_request_local, "request")


@pytest.mark.django_db
class TestRequestLocalStorage:
    """Test the thread-local storage functionality."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        return type("MockRequest", (), {"path": "/test/", "META": {}})()

    def test_request_local_storage_isolation(self, mock_request):
        """Test that requests are isolated in thread-local storage."""
        _request_local.request = mock_request
        assert getattr(_request_local, "request", None) is mock_request

        delattr(_request_local, "request")
        assert not hasattr(_request_local, "request")

    def test_get_current_request_with_no_request(self):
        """Test get_current_request when no request is set."""
        assert get_current_request() is None

    def test_get_current_request_with_request(self, mock_request):
        """Test get_current_request when request is set."""
        _request_local.request = mock_request
        assert get_current_request() is mock_request
        delattr(_request_local, "request")

    @pytest.mark.asyncio
    async def test_request_local_storage_async_isolation(self, mock_request):
        """Test that requests are isolated in async context."""

        async def set_request():
            _request_local.request = mock_request
            assert getattr(_request_local, "request", None) is mock_request
            delattr(_request_local, "request")
            assert not hasattr(_request_local, "request")

        await set_request()
