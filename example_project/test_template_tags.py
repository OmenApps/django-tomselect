"""Tests for django_tomselect template tag functionality."""

import pytest
from django.template import Context, Template
from django.templatetags.static import static
from django.test.utils import override_settings

from django_tomselect.templatetags.django_tomselect import (
    get_widget_with_config,
    to_static_url,
    tomselect_media,
    tomselect_media_css,
    tomselect_media_js,
)


@pytest.mark.django_db
class TestTomSelectTemplateTags:
    """Test cases for TomSelect template tags."""

    def test_to_static_url_with_absolute_urls(self):
        """Test to_static_url with absolute URLs."""
        absolute_urls = [
            "http://example.com/style.css",
            "https://example.com/script.js",
            "//example.com/font.woff",
        ]
        for url in absolute_urls:
            assert to_static_url(url) == url

    def test_to_static_url_with_relative_path(self):
        """Test to_static_url with relative paths."""
        relative_path = "django_tomselect/css/style.css"
        expected = static(relative_path)
        assert to_static_url(relative_path) == expected

    @pytest.mark.parametrize(
        "css_framework,expected_framework",
        [
            ("bootstrap4", "bootstrap4"),
            ("bootstrap5", "bootstrap5"),
            ("default", "default"),
            ("BOOTSTRAP4", "bootstrap4"),  # Test case insensitivity
        ],
    )
    def test_get_widget_with_config_valid_frameworks(self, css_framework, expected_framework):
        """Test get_widget_with_config with valid CSS frameworks."""
        widget = get_widget_with_config(css_framework=css_framework)
        assert widget.css_framework == expected_framework

    def test_get_widget_with_config_invalid_framework(self):
        """Test get_widget_with_config with invalid framework falls back to system default."""
        widget = get_widget_with_config(css_framework="invalid")
        assert widget.css_framework == "default"

    @pytest.mark.parametrize("use_minified", [True, False])
    def test_get_widget_with_minification(self, use_minified):
        """Test get_widget_with_config minification setting."""
        widget = get_widget_with_config(use_minified=use_minified)
        assert widget.use_minified == use_minified

    def test_tomselect_media_tag(self):
        """Test the tomselect_media template tag."""
        html = tomselect_media()

        # Check for CSS inclusion
        assert 'rel="stylesheet"' in html
        assert "tom-select" in html
        assert "django-tomselect.css" in html

        # Check for JS inclusion
        assert '<script src="' in html
        assert "django-tomselect" in html

    def test_tomselect_media_css_tag(self):
        """Test the tomselect_media_css template tag."""
        html = tomselect_media_css()

        # Should include CSS but not JS
        assert 'rel="stylesheet"' in html
        assert "tom-select" in html
        assert "django-tomselect.css" in html
        assert "<script" not in html

    def test_tomselect_media_js_tag(self):
        """Test the tomselect_media_js template tag."""
        html = tomselect_media_js()

        # Should include JS but not CSS
        assert '<script src="' in html
        assert "django-tomselect" in html
        assert 'rel="stylesheet"' not in html

    def test_template_tag_in_template(self):
        """Test using the template tags in an actual template."""
        template = Template("{% load django_tomselect %}" "{% tomselect_media %}")
        html = template.render(Context({}))

        # Verify both CSS and JS are included
        assert 'rel="stylesheet"' in html
        assert '<script src="' in html
        assert "tom-select" in html
        assert "django-tomselect" in html

    def test_empty_widget_config(self):
        """Test get_widget_with_config with no parameters."""
        widget = get_widget_with_config()
        assert widget.css_framework == "default"
        assert hasattr(widget, "use_minified")

    def test_template_tag_escaping(self):
        """Test proper HTML escaping in template tags."""
        template = Template(
            "{% load django_tomselect %}" '{% tomselect_media css_framework="malicious\\"><script>alert(1)</script>" %}'
        )
        html = template.render(Context({}))

        # Verify potentially dangerous content is escaped
        assert "><script>alert(1)</script>" not in html
        assert "tom-select.default" in html  # System uses default framework

    @override_settings(DEBUG=True)
    def test_debug_vs_production_mode(self):
        """Test how DEBUG setting affects the output."""
        debug_html = tomselect_media()

        with override_settings(DEBUG=False):
            prod_html = tomselect_media()

        # In either mode, the output should be valid
        assert 'rel="stylesheet"' in debug_html
        assert 'rel="stylesheet"' in prod_html
        assert '<script src="' in debug_html
        assert '<script src="' in prod_html

    @override_settings(STATIC_URL="/custom-static/")
    def test_custom_static_url(self):
        """Test template tags with custom STATIC_URL setting."""
        html = tomselect_media()
        assert "/custom-static/django_tomselect/" in html

    def test_framework_specific_output(self):
        """Test output contains correct framework-specific files."""
        for framework in ["bootstrap4", "bootstrap5", "default"]:
            html = tomselect_media(css_framework=framework)
            assert f"tom-select.{framework}" in html

    def test_minification_output(self):
        """Test minification affects output correctly."""
        minified_html = tomselect_media(use_minified=True)
        unminified_html = tomselect_media(use_minified=False)

        # Minified should contain .min., unminified should not
        assert ".min." in minified_html
        assert ".min." not in unminified_html
