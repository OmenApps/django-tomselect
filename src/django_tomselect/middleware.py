"""Middleware for django_tomselect to manage request objects."""

try:
    from asgiref.local import Local as local
except ImportError:
    from threading import local

from django.http import HttpRequest

from django_tomselect.logging import package_logger

# Create a single local instance for storing request
_request_local = local()


def get_current_request() -> HttpRequest | None:
    """Get the current request from thread/async-local storage."""
    return getattr(_request_local, "request", None)


class TomSelectMiddleware:
    """Stores the request object in thread/async-local storage.

    Compatible with both WSGI and ASGI deployments.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request in local storage
        _request_local.request = request

        try:
            response = self.get_response(request)
            package_logger.debug("Request object stored in local storage.")
            return response
        finally:
            # Always clean up the local storage
            if hasattr(_request_local, "request"):
                del _request_local.request

    async def __acall__(self, request):
        """Handle async requests in ASGI deployments."""
        # Store request in local storage
        _request_local.request = request

        try:
            response = await self.get_response(request)
            package_logger.debug("Request object stored in local storage.")
            return response
        finally:
            # Always clean up the local storage
            if hasattr(_request_local, "request"):
                del _request_local.request
