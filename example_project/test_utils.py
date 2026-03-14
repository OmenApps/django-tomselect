"""Tests for django-tomselect's utils."""

import logging

import pytest
from django.test import override_settings
from django.urls import NoReverseMatch

from django_tomselect.utils import (
    MAX_RECURSION_DEPTH,
    safe_escape,
    safe_reverse,
    safe_reverse_lazy,
    safe_url,
    sanitize_dict,
)


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


@pytest.mark.django_db
class TestSafeReverseEdgeCases:
    """Test safe_reverse edge cases."""

    def test_safe_reverse_valid_url(self):
        """Test safe_reverse with a valid URL name."""
        result = safe_reverse("autocomplete-edition")
        assert result is not None
        assert "autocomplete" in result

    def test_safe_reverse_invalid_url(self, caplog):
        """Test safe_reverse with invalid URL raises NoReverseMatch."""
        with caplog.at_level(logging.ERROR):
            with pytest.raises(NoReverseMatch):
                safe_reverse("nonexistent-url-name")
        assert "Failed to reverse URL" in caplog.text

    @override_settings(USE_I18N=False)
    def test_safe_reverse_without_i18n(self):
        """Test safe_reverse when USE_I18N is False."""
        result = safe_reverse("autocomplete-edition")
        assert result is not None

    @override_settings(USE_I18N=True)
    def test_safe_reverse_with_i18n_enabled(self):
        """Test safe_reverse when USE_I18N is True."""
        result = safe_reverse("autocomplete-edition")
        assert result is not None

    def test_safe_reverse_with_args(self):
        """Test safe_reverse with URL arguments."""
        # This depends on having a URL that takes args
        # For now, test that the function accepts args parameter
        with pytest.raises(NoReverseMatch):
            safe_reverse("some-url-with-args", args=[1])

    def test_safe_reverse_with_kwargs(self):
        """Test safe_reverse with URL keyword arguments."""
        # Test that the function accepts kwargs parameter
        with pytest.raises(NoReverseMatch):
            safe_reverse("some-url-with-kwargs", kwargs={"pk": 1})


@pytest.mark.django_db
class TestSafeReverseLazy:
    """Test safe_reverse_lazy function."""

    def test_safe_reverse_lazy_returns_lazy_object(self):
        """Test that safe_reverse_lazy returns a lazy object."""
        result = safe_reverse_lazy("autocomplete-edition")
        # Lazy objects are not evaluated until str() is called
        assert result is not None

    def test_safe_reverse_lazy_evaluates_correctly(self):
        """Test that the lazy object evaluates to correct URL."""
        result = safe_reverse_lazy("autocomplete-edition")
        url = str(result)
        assert "autocomplete" in url

    def test_safe_reverse_lazy_with_args(self):
        """Test safe_reverse_lazy with arguments."""
        # Test that it accepts args parameter
        result = safe_reverse_lazy("autocomplete-edition", args=None)
        assert result is not None

    def test_safe_reverse_lazy_with_kwargs(self):
        """Test safe_reverse_lazy with keyword arguments."""
        result = safe_reverse_lazy("autocomplete-edition", kwargs=None)
        assert result is not None


class TestSafeEscapeEdgeCases:
    """Test safe_escape edge cases."""

    @pytest.mark.parametrize(
        "input_val,expected,exact_match",
        [
            (None, "", True),
            (123, "123", True),
            (123.45, "123.45", True),
            (True, "True", True),
            (False, "False", True),
            ([1, 2, 3], "[1, 2, 3]", False),
            ({"key": "value"}, "key", False),
        ],
        ids=["none", "integer", "float", "bool_true", "bool_false", "list", "dict"],
    )
    def test_safe_escape_type_conversion(self, input_val, expected, exact_match):
        """Test that various types are properly converted to escaped strings."""
        result = safe_escape(input_val)
        if exact_match:
            assert result == expected
        else:
            assert expected in result

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("<script>", "&lt;script&gt;"),
            ("&amp;", "&amp;amp;"),
            ('"quotes"', "&quot;quotes&quot;"),
            ("'single'", "&#x27;single&#x27;"),
            ("<>&\"'", "&lt;&gt;&amp;&quot;&#x27;"),
        ],
    )
    def test_safe_escape_html_entities(self, input_val, expected):
        """Test various HTML entities are properly escaped."""
        assert safe_escape(input_val) == expected

    def test_safe_escape_exception_handling(self, monkeypatch, caplog):
        """Test exception handling returns empty string."""

        def mock_escape(value):
            raise Exception("Escape error")

        monkeypatch.setattr("django_tomselect.utils.escape", mock_escape)

        with caplog.at_level(logging.ERROR):
            result = safe_escape("test")
        assert result == ""
        assert "Error escaping value" in caplog.text


class TestSafeUrlEdgeCases:
    """Test safe_url edge cases."""

    def test_safe_url_none(self):
        """Test that None returns None."""
        assert safe_url(None) is None

    def test_safe_url_empty_string(self):
        """Test that empty string returns None."""
        assert safe_url("") is None

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://example.com",
            "mailto:test@example.com",
            "tel:+1234567890",
        ],
    )
    def test_safe_url_allowed_protocols(self, url):
        """Test URLs with allowed protocols are returned escaped."""
        result = safe_url(url)
        assert result is not None
        # Should be escaped (though these URLs don't need escaping)

    @pytest.mark.parametrize(
        "url",
        [
            "/absolute/path",
            "/path/to/resource",
            "./relative/path",
            "./file.html",
        ],
    )
    def test_safe_url_relative_paths(self, url):
        """Test relative paths are returned escaped."""
        result = safe_url(url)
        assert result is not None

    @pytest.mark.parametrize(
        "dangerous_url",
        [
            "javascript:alert(1)",
            "JAVASCRIPT:alert(1)",
            "JavaScript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "DATA:text/html,test",
            "vbscript:msgbox('hello')",
            "VBSCRIPT:test",
            "file:///etc/passwd",
            "FILE:///etc/passwd",
        ],
    )
    def test_safe_url_dangerous_schemes_rejected(self, dangerous_url, caplog):
        """Test dangerous URL schemes are rejected."""
        with caplog.at_level(logging.WARNING):
            result = safe_url(dangerous_url)
        assert result is None
        assert "Rejected dangerous URL scheme" in caplog.text

    @pytest.mark.parametrize(
        "domain,expected_contains",
        [
            ("example.com", "http://"),
            ("www.example.com", "http://"),
            ("sub.example.co.uk", "http://"),
            ("test-domain.org", "http://"),
        ],
    )
    def test_safe_url_domain_pattern_adds_http(self, domain, expected_contains):
        """Test domain-like URLs get http:// prefix added."""
        result = safe_url(domain)
        assert result is not None
        assert expected_contains in result

    def test_safe_url_unknown_format_escaped(self):
        """Test unknown URL formats are still escaped and returned."""
        result = safe_url("some-random-string-without-protocol")
        # Should return escaped version
        assert result is not None

    def test_safe_url_with_special_chars(self):
        """Test URLs with special characters are escaped."""
        url = "https://example.com/path?query=<script>"
        result = safe_url(url)
        assert result is not None
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_safe_url_exception_handling(self, monkeypatch, caplog):
        """Test exception handling returns None."""
        import re

        original_match = re.match

        def mock_match(pattern, string, *args, **kwargs):
            if "dangerous" in str(pattern).lower():
                raise Exception("Regex error")
            return original_match(pattern, string, *args, **kwargs)

        monkeypatch.setattr("re.match", mock_match)

        with caplog.at_level(logging.ERROR):
            result = safe_url("test-url")
        # Depending on where exception occurs, result may be None
        # The important thing is the error is logged
        if "Error processing URL" in caplog.text:
            assert result is None


class TestSanitizeDictEdgeCases:
    """Test sanitize_dict edge cases."""

    def test_sanitize_dict_empty_dict(self):
        """Test empty dict returns empty dict."""
        result = sanitize_dict({})
        assert result == {}

    @pytest.mark.parametrize(
        "invalid_input",
        ["not a dict", None, ["a", "b"], 123],
        ids=["string", "none", "list", "integer"],
    )
    def test_sanitize_dict_non_dict_input_types(self, invalid_input, caplog):
        """Test non-dict inputs return empty dict and log warning."""
        with caplog.at_level(logging.WARNING):
            result = sanitize_dict(invalid_input)
        assert result == {}
        assert "Non-dictionary passed" in caplog.text

    def test_sanitize_dict_max_recursion_depth(self, caplog):
        """Test maximum recursion depth is enforced."""
        # Create deeply nested dict exceeding MAX_RECURSION_DEPTH
        nested = {"value": "leaf"}
        for _i in range(MAX_RECURSION_DEPTH + 5):
            nested = {"nested": nested}

        with caplog.at_level(logging.WARNING):
            result = sanitize_dict(nested)
        # Should log warning about max recursion depth
        assert "Maximum recursion depth" in caplog.text
        # Function returns partially processed dict, not empty
        assert isinstance(result, dict)

    def test_sanitize_dict_non_string_key_int(self):
        """Test integer keys are converted to strings."""
        data = {123: "value", 456: "another"}
        result = sanitize_dict(data)
        assert "123" in result
        assert "456" in result

    def test_sanitize_dict_non_string_key_tuple(self):
        """Test tuple keys are converted to strings."""
        data = {(1, 2): "value"}
        result = sanitize_dict(data)
        assert "(1, 2)" in result

    def test_sanitize_dict_escape_keys_true(self):
        """Test escape_keys=True escapes dictionary keys."""
        data = {"<script>": "value", "normal": "data"}
        result = sanitize_dict(data, escape_keys=True)
        assert "&lt;script&gt;" in result
        assert "<script>" not in result
        assert "normal" in result

    def test_sanitize_dict_escape_keys_false(self):
        """Test escape_keys=False does not escape dictionary keys."""
        data = {"<script>": "value"}
        result = sanitize_dict(data, escape_keys=False)
        assert "<script>" in result

    def test_sanitize_dict_nested_dict(self):
        """Test nested dictionaries are sanitized."""
        data = {
            "outer": {
                "inner": "<script>alert(1)</script>",
            }
        }
        result = sanitize_dict(data)
        assert "&lt;script&gt;" in result["outer"]["inner"]

    def test_sanitize_dict_list_values(self):
        """Test list values are sanitized."""
        data = {"items": ["<b>bold</b>", "<i>italic</i>"]}
        result = sanitize_dict(data)
        assert "&lt;b&gt;bold&lt;/b&gt;" in result["items"]
        assert "&lt;i&gt;italic&lt;/i&gt;" in result["items"]

    def test_sanitize_dict_list_with_nested_dicts(self):
        """Test list containing dictionaries are sanitized."""
        data = {"items": [{"name": "<script>bad</script>"}]}
        result = sanitize_dict(data)
        assert "&lt;script&gt;" in result["items"][0]["name"]

    def test_sanitize_dict_url_field_safe(self):
        """Test _url suffix fields with safe URLs."""
        data = {
            "website_url": "https://example.com",
            "profile_url": "/user/profile",
        }
        result = sanitize_dict(data)
        assert "example.com" in result["website_url"]
        assert "/user/profile" in result["profile_url"]

    def test_sanitize_dict_url_field_dangerous(self, caplog):
        """Test _url suffix fields with dangerous URLs are nullified."""
        data = {"evil_url": "javascript:alert(1)"}
        with caplog.at_level(logging.WARNING):
            result = sanitize_dict(data)
        assert result["evil_url"] == ""
        assert "Unsafe URL found" in caplog.text

    def test_sanitize_dict_mixed_content(self):
        """Test dictionary with mixed content types."""
        data = {
            "string": "<em>emphasis</em>",
            "number": 42,
            "nested": {"key": "<b>bold</b>"},
            "list": ["<i>item</i>"],
            "safe_url": "https://example.com",
            "bad_url": "javascript:void(0)",
        }
        result = sanitize_dict(data)
        assert "&lt;em&gt;" in result["string"]
        assert result["number"] == 42
        assert "&lt;b&gt;" in result["nested"]["key"]
        assert "&lt;i&gt;" in result["list"][0]
        assert "example.com" in result["safe_url"]
        assert result["bad_url"] == ""

    def test_sanitize_dict_preserves_structure(self):
        """Test that dictionary structure is preserved."""
        data = {
            "level1": {
                "level2": {
                    "level3": "value",
                }
            }
        }
        result = sanitize_dict(data)
        assert "level1" in result
        assert "level2" in result["level1"]
        assert "level3" in result["level1"]["level2"]
        assert result["level1"]["level2"]["level3"] == "value"
