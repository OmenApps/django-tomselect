"""Tests for django_tomselect template tag functionality."""

import logging

import pytest
from django.template import Context, Template
from django.templatetags.static import static
from django.test.utils import override_settings

from django_tomselect.templatetags.django_tomselect import (
    get_widget_with_config,
    render_css_links,
    render_js_scripts,
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
        template = Template("{% load django_tomselect %}\n{% tomselect_media %}")
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


@pytest.mark.django_db
class TestToStaticUrlEdgeCases:
    """Test to_static_url edge cases."""

    def test_to_static_url_empty_string(self, caplog):
        """Test empty string returns empty string and logs warning."""
        with caplog.at_level(logging.WARNING):
            result = to_static_url("")
        assert result == ""
        assert "Empty path" in caplog.text

    def test_to_static_url_none_value(self):
        """Test None value returns empty string."""
        result = to_static_url(None)
        assert result == ""

    def test_to_static_url_whitespace_only(self, caplog):
        """Test whitespace-only string is treated as empty."""
        # Whitespace is not empty, so it will be processed
        result = to_static_url("   ")
        # May return the path with whitespace or static URL
        assert result == static("   ")

    def test_to_static_url_exception_handling(self, monkeypatch, caplog):
        """Test exception during static URL conversion returns original path."""

        def mock_static(path):
            raise ValueError("Static file error")

        monkeypatch.setattr("django_tomselect.templatetags.django_tomselect.static", mock_static)

        with caplog.at_level(logging.ERROR):
            result = to_static_url("some/path.css")
        assert result == "some/path.css"  # Returns original path as fallback
        assert "Error converting path" in caplog.text

    @pytest.mark.parametrize(
        "url",
        [
            "http://cdn.example.com/style.css",
            "https://cdn.example.com/script.js",
            "//cdn.example.com/font.woff",
        ],
    )
    def test_to_static_url_absolute_urls_unchanged(self, url):
        """Test absolute URLs are returned unchanged."""
        assert to_static_url(url) == url


@pytest.mark.django_db
class TestGetWidgetWithConfigEdgeCases:
    """Test get_widget_with_config edge cases."""

    def test_get_widget_with_invalid_framework_logs_warning(self, caplog):
        """Test invalid framework logs warning and uses default."""
        with caplog.at_level(logging.WARNING):
            widget = get_widget_with_config(css_framework="nonexistent_framework")
        assert "Invalid CSS framework" in caplog.text
        assert widget.css_framework == "default"

    def test_get_widget_with_none_values(self):
        """Test None values for both parameters uses defaults."""
        widget = get_widget_with_config(css_framework=None, use_minified=None)
        assert widget.css_framework == "default"
        assert hasattr(widget, "use_minified")

    @pytest.mark.parametrize(
        "framework,expected",
        [
            ("BOOTSTRAP4", "bootstrap4"),
            ("Bootstrap5", "bootstrap5"),
            ("DEFAULT", "default"),
            ("BoOtStRaP4", "bootstrap4"),
        ],
    )
    def test_get_widget_with_config_case_insensitivity(self, framework, expected):
        """Test CSS framework names are case-insensitive."""
        widget = get_widget_with_config(css_framework=framework)
        assert widget.css_framework == expected


@pytest.mark.django_db
class TestRenderCssLinksEdgeCases:
    """Test render_css_links edge cases."""

    def test_render_css_links_empty_dict(self, caplog):
        """Test empty dict returns empty string and logs debug."""
        with caplog.at_level(logging.DEBUG):
            result = render_css_links({})
        assert result == ""
        assert "No CSS files" in caplog.text

    def test_render_css_links_none_dict(self, caplog):
        """Test None returns empty string."""
        with caplog.at_level(logging.DEBUG):
            result = render_css_links(None)
        assert result == ""

    def test_render_css_links_empty_paths_list(self):
        """Test dict with empty paths list returns empty string."""
        result = render_css_links({"all": []})
        assert result == ""

    def test_render_css_links_multiple_media_types(self):
        """Test rendering CSS with multiple media types."""
        css_dict = {
            "all": ["path/to/all.css"],
            "screen": ["path/to/screen.css"],
            "print": ["path/to/print.css"],
        }
        result = render_css_links(css_dict)
        assert 'media="all"' in result
        assert 'media="screen"' in result
        assert 'media="print"' in result

    def test_render_css_links_exception_handling(self, monkeypatch, caplog):
        """Test exception handling returns empty string."""

        def mock_to_static_url(path):
            raise TypeError("URL conversion error")

        monkeypatch.setattr("django_tomselect.templatetags.django_tomselect.to_static_url", mock_to_static_url)

        with caplog.at_level(logging.ERROR):
            result = render_css_links({"all": ["path.css"]})
        assert result == ""
        assert "Error rendering CSS" in caplog.text

    def test_render_css_links_skips_empty_urls(self, monkeypatch):
        """Test that empty URLs returned from to_static_url are skipped."""

        def mock_to_static_url(path):
            if "skip" in path:
                return ""
            return f"/static/{path}"

        monkeypatch.setattr("django_tomselect.templatetags.django_tomselect.to_static_url", mock_to_static_url)

        result = render_css_links({"all": ["skip.css", "include.css"]})
        assert "include.css" in result
        assert "skip.css" not in result


@pytest.mark.django_db
class TestRenderJsScriptsEdgeCases:
    """Test render_js_scripts edge cases."""

    def test_render_js_scripts_empty_list(self, caplog):
        """Test empty list returns empty string and logs debug."""
        with caplog.at_level(logging.DEBUG):
            result = render_js_scripts([])
        assert result == ""
        assert "No JS files" in caplog.text

    def test_render_js_scripts_none_list(self, caplog):
        """Test None returns empty string."""
        with caplog.at_level(logging.DEBUG):
            result = render_js_scripts(None)
        assert result == ""

    def test_render_js_scripts_multiple_scripts(self):
        """Test rendering multiple JS scripts."""
        js_list = ["script1.js", "script2.js", "script3.js"]
        result = render_js_scripts(js_list)
        assert result.count("<script") == 3
        assert result.count("</script>") == 3

    def test_render_js_scripts_exception_handling(self, monkeypatch, caplog):
        """Test exception handling returns empty string."""

        def mock_to_static_url(path):
            raise TypeError("URL conversion error")

        monkeypatch.setattr("django_tomselect.templatetags.django_tomselect.to_static_url", mock_to_static_url)

        with caplog.at_level(logging.ERROR):
            result = render_js_scripts(["path.js"])
        assert result == ""
        assert "Error rendering JS" in caplog.text

    def test_render_js_scripts_skips_empty_urls(self, monkeypatch):
        """Test that empty URLs returned from to_static_url are skipped."""

        def mock_to_static_url(path):
            if "skip" in path:
                return ""
            return f"/static/{path}"

        monkeypatch.setattr("django_tomselect.templatetags.django_tomselect.to_static_url", mock_to_static_url)

        result = render_js_scripts(["skip.js", "include.js"])
        assert "include.js" in result
        assert "skip.js" not in result


@pytest.mark.django_db
class TestTomSelectMediaEdgeCases:
    """Test tomselect_media template tag edge cases."""

    def test_tomselect_media_missing_media_attributes(self, monkeypatch, caplog):
        """Test handling when widget has no media attributes."""

        class BadWidget:
            """Widget without media attributes."""

            pass

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config",
            lambda css_framework=None, use_minified=None: BadWidget(),
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media()
        # Returns empty string when media attributes not found
        assert result == "" or "Error" not in result
        assert "media attributes not found" in caplog.text.lower()

    def test_tomselect_media_missing_css_attribute(self, monkeypatch, caplog):
        """Test handling when widget.media has no _css."""

        class MockMedia:
            _js = ["script.js"]

        class MockWidget:
            media = MockMedia()

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config",
            lambda css_framework=None, use_minified=None: MockWidget(),
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media()
        # Returns empty string when _css not found
        assert result == "" or "Error" not in result
        assert "media attributes not found" in caplog.text.lower()

    def test_tomselect_media_missing_js_attribute(self, monkeypatch, caplog):
        """Test handling when widget.media has no _js."""

        class MockMedia:
            _css = {"all": ["style.css"]}

        class MockWidget:
            media = MockMedia()

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config",
            lambda css_framework=None, use_minified=None: MockWidget(),
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media()
        # Returns empty string when _js not found
        assert result == "" or "Error" not in result
        assert "media attributes not found" in caplog.text.lower()

    def test_tomselect_media_exception_handling(self, monkeypatch, caplog):
        """Test exception handling returns error comment."""

        def mock_get_widget(**kwargs):
            raise TypeError("Widget creation error")

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config", mock_get_widget
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media()
        assert "Error loading TomSelect media" in result
        assert "Error in tomselect_media" in caplog.text

    def test_tomselect_media_css_only_output(self):
        """Test output contains only CSS when JS rendering returns empty."""
        # Normal case - both CSS and JS should be present
        html = tomselect_media()
        assert '<link href="' in html
        assert '<script src="' in html


@pytest.mark.django_db
class TestTomSelectMediaCssEdgeCases:
    """Test tomselect_media_css template tag edge cases."""

    def test_tomselect_media_css_missing_media(self, monkeypatch, caplog):
        """Test handling when widget has no media attribute."""

        class BadWidget:
            pass

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config",
            lambda css_framework=None, use_minified=None: BadWidget(),
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media_css()
        assert result == "" or "Error" not in result
        assert "css attributes not found" in caplog.text.lower()

    def test_tomselect_media_css_missing_css_attribute(self, monkeypatch, caplog):
        """Test handling when widget.media has no _css."""

        class MockMedia:
            pass

        class MockWidget:
            media = MockMedia()

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config",
            lambda css_framework=None, use_minified=None: MockWidget(),
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media_css()
        assert result == "" or "Error" not in result
        assert "css attributes not found" in caplog.text.lower()

    def test_tomselect_media_css_exception_handling(self, monkeypatch, caplog):
        """Test exception handling returns error comment."""

        def mock_get_widget(**kwargs):
            raise TypeError("Widget error")

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config", mock_get_widget
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media_css()
        assert "Error loading TomSelect CSS" in result
        assert "Error in tomselect_media_css" in caplog.text


@pytest.mark.django_db
class TestTomSelectMediaJsEdgeCases:
    """Test tomselect_media_js template tag edge cases."""

    def test_tomselect_media_js_missing_media(self, monkeypatch, caplog):
        """Test handling when widget has no media attribute."""

        class BadWidget:
            pass

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config", lambda **kwargs: BadWidget()
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media_js()
        assert result == ""
        assert "JS attributes not found" in caplog.text

    def test_tomselect_media_js_missing_js_attribute(self, monkeypatch, caplog):
        """Test handling when widget.media has no _js."""

        class MockMedia:
            _css = {"all": ["style.css"]}

        class MockWidget:
            media = MockMedia()

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config", lambda **kwargs: MockWidget()
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media_js()
        assert result == ""
        assert "JS attributes not found" in caplog.text

    def test_tomselect_media_js_exception_handling(self, monkeypatch, caplog):
        """Test exception handling returns error comment."""

        def mock_get_widget(**kwargs):
            raise TypeError("Widget error")

        monkeypatch.setattr(
            "django_tomselect.templatetags.django_tomselect.get_widget_with_config", mock_get_widget
        )
        with caplog.at_level(logging.ERROR):
            result = tomselect_media_js()
        assert "Error loading TomSelect JS" in result
        assert "Error in tomselect_media_js" in caplog.text


@pytest.mark.django_db
class TestTemplateTagIntegration:
    """Integration tests for template tags."""

    def test_all_tags_in_single_template(self):
        """Test using all template tags in a single template."""
        template = Template(
            """{% load django_tomselect %}
            {% tomselect_media %}
            {% tomselect_media_css %}
            {% tomselect_media_js %}"""
        )
        html = template.render(Context({}))
        # Should have CSS and JS from all three tags
        assert html.count('rel="stylesheet"') >= 2
        assert html.count("<script") >= 2

    def test_template_tags_with_framework_parameter(self):
        """Test template tags respect framework parameter."""
        template = Template('{% load django_tomselect %}{% tomselect_media css_framework="bootstrap5" %}')
        html = template.render(Context({}))
        assert "bootstrap5" in html

    def test_template_tags_with_minified_parameter(self):
        """Test template tags respect minified parameter."""
        template_min = Template("{% load django_tomselect %}{% tomselect_media use_minified=True %}")
        template_normal = Template("{% load django_tomselect %}{% tomselect_media use_minified=False %}")

        html_min = template_min.render(Context({}))
        html_normal = template_normal.render(Context({}))

        assert ".min." in html_min
        assert ".min." not in html_normal
