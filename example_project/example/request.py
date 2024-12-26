"""Custom proxy request class for testing."""

from django_tomselect.request import DefaultProxyRequest


class CustomProxyRequest(DefaultProxyRequest):
    """Valid proxy request class."""
