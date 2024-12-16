"""Custom template tags for charts."""

from django import template

register = template.Library()


@register.filter
def percentage_of_max(value, max_value):
    """Calculate percentage against maximum value."""
    try:
        return int((float(value) / float(max_value)) * 100)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0
