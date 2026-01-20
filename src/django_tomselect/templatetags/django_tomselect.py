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
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from django_tomselect.app_settings import AllowedCSSFrameworks
from django_tomselect.logging import get_logger
from django_tomselect.widgets import TomSelectIterablesWidget

logger = get_logger(__name__)

register = template.Library()


def to_static_url(path: str) -> str:
    """Convert a path to a static URL.

    Takes a path and returns either the absolute URL if it's already a complete
    URL, or converts it to a static URL using Django's static function.

    Args:
        path: The path to convert to a static URL

    Returns:
        The static URL for the given path
    """
    try:
        if not path:
            logger.warning("Empty path provided to to_static_url")
            return ""

        if path.startswith(("http://", "https://", "//")):
            return path
        return static(path)
    except (ValueError, TypeError) as e:
        logger.error("Error converting path '%s' to static URL: %s", path, e, exc_info=True)
        # Return an empty string or the original path as fallback
        return path


def get_widget_with_config(
    css_framework: str | None = None, use_minified: bool | None = None
) -> TomSelectIterablesWidget:
    """Get a TomSelectIterablesWidget instance with the specified configuration.

    Creates a new widget instance and configures it with the specified CSS framework
    and minification preference if provided.

    Args:
        css_framework: Optional name of the CSS framework to use
        use_minified: Optional flag to use minified CSS/JS files

    Returns:
        A configured TomSelectIterablesWidget instance
    """
    try:
        widget = TomSelectIterablesWidget()

        if css_framework is not None or use_minified is not None:
            if css_framework is not None:
                try:
                    framework = AllowedCSSFrameworks(css_framework.lower()).value
                    widget.css_framework = framework
                    logger.debug("Using CSS framework: %s", framework)
                except ValueError:
                    logger.warning(
                        "Invalid CSS framework specified: '%s'Using default framework: %s",
                        css_framework,
                        widget.css_framework,
                    )

            if use_minified is not None:
                widget.use_minified = use_minified
                logger.debug("Using minified assets: %s", use_minified)

        return widget
    except (ValueError, TypeError) as e:
        logger.error("Error creating widget with config: %s", e, exc_info=True)
        # Return a default widget as fallback
        return TomSelectIterablesWidget()


def render_css_links(css_dict: dict) -> str:
    """Render CSS links from a dictionary of media types and paths.

    Takes a dictionary mapping media types to lists of CSS file paths and
    renders them as HTML link tags.

    Args:
        css_dict: Dictionary mapping media types to lists of CSS file paths

    Returns:
        HTML string containing link tags for the CSS files
    """
    try:
        if not css_dict:
            logger.debug("No CSS files to render")
            return ""

        links = []
        for medium, paths in css_dict.items():
            if not paths:
                continue

            for path in paths:
                url = to_static_url(path)
                if url:
                    links.append(format_html('<link href="{}" rel="stylesheet" media="{}">', url, medium))

        return "\n".join(links)
    except (TypeError, KeyError, AttributeError) as e:
        logger.error("Error rendering CSS links: %s", e, exc_info=True)
        return ""


def render_js_scripts(js_list: list) -> str:
    """Render JS script tags from a list of paths.

    Takes a list of JavaScript file paths and renders them as HTML script tags.

    Args:
        js_list: List of JavaScript file paths

    Returns:
        HTML string containing script tags for the JavaScript files
    """
    try:
        if not js_list:
            logger.debug("No JS files to render")
            return ""

        scripts = []
        for path in js_list:
            url = to_static_url(path)
            if url:
                scripts.append(format_html('<script src="{}"></script>', url))

        return "\n".join(scripts)
    except (TypeError, AttributeError) as e:
        logger.error("Error rendering JS scripts: %s", e, exc_info=True)
        return ""


@register.simple_tag
def tomselect_media(css_framework: str | None = None, use_minified: bool | None = None) -> str:
    """Return all CSS and JS tags for the TomSelectIterablesWidget.

    Creates the necessary HTML tags to include TomSelect CSS and JavaScript
    files in a template.

    Args:
        css_framework: Optional name of the CSS framework to use
        use_minified: Optional flag to use minified CSS/JS files

    Returns:
        Safe HTML string containing all required CSS and JS tags
    """
    try:
        widget = get_widget_with_config(css_framework, use_minified)

        if not hasattr(widget, "media") or not hasattr(widget.media, "_css") or not hasattr(widget.media, "_js"):
            logger.error("Widget media attributes not found")
            return ""

        css_html = render_css_links(widget.media._css)
        js_html = render_js_scripts(widget.media._js)

        result = ""
        if css_html:
            result += css_html + "\n"
        if js_html:
            result += js_html

        logger.debug(
            "Generated tomselect_media with css_framework: %s, use_minified: %s",
            css_framework,
            use_minified,
        )
        return mark_safe(result)  # nosec B308 B703
    except (AttributeError, TypeError, ValueError) as e:
        logger.error("Error in tomselect_media: %s", e, exc_info=True)
        return mark_safe("<!-- Error loading TomSelect media -->")  # nosec B308 B703


@register.simple_tag
def tomselect_media_css(css_framework: str | None = None, use_minified: bool | None = None) -> str:
    """Return only CSS tags for the TomSelectIterablesWidget.

    Creates the necessary HTML tags to include only TomSelect CSS files in a template.

    Args:
        css_framework: Optional name of the CSS framework to use
        use_minified: Optional flag to use minified CSS files

    Returns:
        Safe HTML string containing all required CSS tags
    """
    try:
        widget = get_widget_with_config(css_framework, use_minified)

        if not hasattr(widget, "media") or not hasattr(widget.media, "_css"):
            logger.error("Widget media CSS attributes not found")
            return ""

        css_html = render_css_links(widget.media._css)

        logger.debug(
            "Generated tomselect_media_css with css_framework: %s, use_minified: %s",
            css_framework,
            use_minified,
        )
        return mark_safe(css_html)  # nosec B308 B703
    except (AttributeError, TypeError, ValueError) as e:
        logger.error("Error in tomselect_media_css: %s", e, exc_info=True)
        return mark_safe("<!-- Error loading TomSelect CSS -->")  # nosec B308 B703


@register.simple_tag
def tomselect_media_js(use_minified: bool | None = None) -> str:
    """Return only JS tags for the TomSelectIterablesWidget.

    Creates the necessary HTML tags to include only TomSelect JavaScript files in a template.

    Args:
        use_minified: Optional flag to use minified JS files

    Returns:
        Safe HTML string containing all required JS tags
    """
    try:
        widget = get_widget_with_config(use_minified=use_minified)

        if not hasattr(widget, "media") or not hasattr(widget.media, "_js"):
            logger.error("Widget media JS attributes not found")
            return ""

        js_html = render_js_scripts(widget.media._js)

        logger.debug("Generated tomselect_media_js with use_minified: %s", use_minified)
        return mark_safe(js_html)  # nosec B308 B703
    except (AttributeError, TypeError, ValueError) as e:
        logger.error("Error in tomselect_media_js: %s", e, exc_info=True)
        return mark_safe("<!-- Error loading TomSelect JS -->")  # nosec B308 B703
