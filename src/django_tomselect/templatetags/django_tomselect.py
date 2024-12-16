"""Template tags for including TomSelect CSS and JS when the form is unavailable.

Usage:

    {% load django_tomselect %}

    <!-- Include CSS and JS with default CSS framework -->
    {% tomselect_media %}

    <!-- Include CSS and JS with specific CSS framework -->
    {% tomselect_media css_framework="bootstrap5" %}

    <!-- Or only CSS with specific framework -->
    {% tomselect_media_css css_framework="bootstrap4" %}

    <!-- Or only JS -->
    {% tomselect_media_js %}
"""

from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from django_tomselect.app_settings import AllowedCSSFrameworks
from django_tomselect.widgets import TomSelectIterablesWidget

register = template.Library()


def to_static_url(path):
    """Convert a path to a static URL."""
    if path.startswith(("http://", "https://", "//")):
        return path
    return static(path)


def get_widget_with_config(css_framework: str = None, use_minified: bool = None) -> TomSelectIterablesWidget:
    """Get a TomSelectIterablesWidget instance with the specified configuration."""
    widget = TomSelectIterablesWidget()

    if css_framework is not None or use_minified is not None:
        if css_framework is not None:
            try:
                framework = AllowedCSSFrameworks(css_framework.lower()).value
                widget.css_framework = framework
            except ValueError:
                pass  # Keep default if invalid framework specified

        if use_minified is not None:
            widget.use_minified = use_minified

    return widget


def render_css_links(css_dict):
    """Render CSS links from a dictionary of media types and paths."""
    links = []
    for medium, paths in css_dict.items():
        for path in paths:
            url = to_static_url(path)
            links.append(f'<link href="{url}" rel="stylesheet" media="{medium}">')
    return "\n".join(links)


def render_js_scripts(js_list):
    """Render JS script tags from a list of paths."""
    scripts = []
    for path in js_list:
        url = to_static_url(path)
        scripts.append(f'<script src="{url}"></script>')
    return "\n".join(scripts)


@register.simple_tag
def tomselect_media(css_framework: str = None, use_minified: bool = None):
    """Return all CSS and JS tags for the TomSelectIterablesWidget."""
    widget = get_widget_with_config(css_framework, use_minified)
    css_html = render_css_links(widget.media._css)
    js_html = render_js_scripts(widget.media._js)
    return mark_safe(css_html + "\n" + js_html)


@register.simple_tag
def tomselect_media_css(css_framework: str = None, use_minified: bool = None):
    """Return only CSS tags for the TomSelectIterablesWidget."""
    widget = get_widget_with_config(css_framework, use_minified)
    return mark_safe(render_css_links(widget.media._css))


@register.simple_tag
def tomselect_media_js(use_minified: bool = None):
    """Return only JS tags for the TomSelectIterablesWidget."""
    widget = get_widget_with_config(use_minified=use_minified)
    return mark_safe(render_js_scripts(widget.media._js))
