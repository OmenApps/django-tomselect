"""Tests for django-tomselect's utils."""

import pytest

from django_tomselect.utils import safe_escape, safe_url, sanitize_dict


class TestUtilityFunctions:
    """Test utility functions for proper escaping."""

    def test_safe_escape(self):
        """Test that safe_escape properly handles HTML content."""
        # Test with HTML content
        html = '<script>alert("XSS");</script>'
        assert safe_escape(html) == "&lt;script&gt;alert(&quot;XSS&quot;);&lt;/script&gt;"

        # Test with None value
        assert safe_escape(None) == ""

        # Test with non-string value
        assert safe_escape(123) == "123"

    def test_safe_url(self):
        """Test that safe_url validates and sanitizes URLs correctly."""
        # Test with safe URLs
        assert safe_url("http://example.com") == "http://example.com"
        assert safe_url("https://example.com") == "https://example.com"
        assert safe_url("/relative/path") == "/relative/path"
        assert safe_url("./relative/path") == "./relative/path"

        # Test with unsafe URLs
        assert safe_url("javascript:alert(1)") is None
        assert safe_url("data:text/html,<script>alert(1)</script>") is None
        assert safe_url('vbscript:msgbox("Hello")') is None

        # Test with None value
        assert safe_url(None) is None

    def test_sanitize_dict(self):
        """Test that sanitize_dict properly escapes dictionary values."""
        # Test with a simple dictionary
        data = {
            "name": "<strong>Test</strong>",
            "description": '<script>alert("XSS");</script>',
            "url": "http://example.com",
            "evil_url": "javascript:alert(1)",
        }

        sanitized = sanitize_dict(data)

        assert sanitized["name"] == "&lt;strong&gt;Test&lt;/strong&gt;"
        assert sanitized["description"] == "&lt;script&gt;alert(&quot;XSS&quot;);&lt;/script&gt;"
        assert sanitized["url"] == "http://example.com"
        assert sanitized["evil_url"] != "javascript:alert(1)"

        # Test with nested dictionary
        nested_data = {
            "user": {"name": "<em>John</em>", "profile_url": "javascript:alert(2)"},
            "items": [{"name": "<b>Item 1</b>"}, {"name": "<script>alert(3)</script>"}],
        }

        sanitized = sanitize_dict(nested_data)

        assert sanitized["user"]["name"] == "&lt;em&gt;John&lt;/em&gt;"
        assert sanitized["user"]["profile_url"] != "javascript:alert(2)"
        assert sanitized["items"][0]["name"] == "&lt;b&gt;Item 1&lt;/b&gt;"
        assert sanitized["items"][1]["name"] == "&lt;script&gt;alert(3)&lt;/script&gt;"


@pytest.mark.django_db
class TestSecurityEscaping:
    """Tests for security escaping in TomSelect widgets."""

    @pytest.fixture
    def malicious_edition(self, sample_edition):
        """Create an edition with malicious content."""
        original_name = sample_edition.name
        sample_edition.name = '<script>alert("XSS");</script>'
        sample_edition.save()

        yield sample_edition

        # Restore original name after test
        sample_edition.name = original_name
        sample_edition.save()

    @pytest.fixture
    def edition_with_html(self, sample_edition):
        """Create an edition with HTML tags in its name."""
        original_name = sample_edition.name
        sample_edition.name = '<strong>with formatting</strong> and <img src="x" onerror="alert(1)">'
        sample_edition.save()

        yield sample_edition

        # Restore original name after test
        sample_edition.name = original_name
        sample_edition.save()
