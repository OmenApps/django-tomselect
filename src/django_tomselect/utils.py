"""Utility functions for django-tomselect."""

import re
from typing import Any, Optional

from django.utils.html import escape


def safe_escape(value: Any) -> str:
    """Safely escape a value, ensuring proper HTML encoding.

    This function handles various input types, converts them to strings,
    and applies proper HTML escaping to prevent XSS attacks.

    Args:
        value: Any value that needs to be safely displayed in HTML

    Returns:
        Properly escaped string
    """
    if value is None:
        return ""

    # Convert to string if not already
    if not isinstance(value, str):
        value = str(value)

    # Apply HTML escaping - ensure we're always returning a string
    return escape(value)


def safe_url(url: Optional[str]) -> Optional[str]:
    """Validate and sanitize a URL to prevent javascript: protocol and other unsafe schemes.

    Args:
        url: URL string to validate

    Returns:
        Safe URL or None if the URL is unsafe
    """
    if not url:
        return None

    # List of allowed protocols
    ALLOWED_PROTOCOLS = ["http://", "https://", "mailto:", "tel:", "/"]

    # Check if URL starts with an allowed protocol or is relative
    for protocol in ALLOWED_PROTOCOLS:
        if url.startswith(protocol):
            return escape(url)

    # Check for relative URL (starting with / or ./)
    if url.startswith("/") or url.startswith("./"):
        return escape(url)

    # Check for javascript: protocol and other potentially dangerous schemes
    if re.match(r"^(javascript|data|vbscript|file):", url.lower()):
        return None

    # Default to http:// if no protocol specified but URL looks like a domain
    if re.match(r"^[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}", url):
        return escape("http://" + url)

    # If we can't determine if it's safe, escape it
    return escape(url)


def sanitize_dict(data: dict, escape_keys: bool = False) -> dict:
    """Sanitize all values in a dictionary to prevent XSS.

    Args:
        data: Dictionary containing potentially unsafe values
        escape_keys: Whether to also escape dictionary keys

    Returns:
        Dictionary with all values safely escaped
    """
    result = {}

    for key, value in data.items():
        safe_key = safe_escape(key) if escape_keys else key

        if isinstance(value, dict):
            result[safe_key] = sanitize_dict(value, escape_keys)
        elif isinstance(value, list):
            result[safe_key] = [
                sanitize_dict(item, escape_keys) if isinstance(item, dict) else safe_escape(item) for item in value
            ]
        elif key.endswith("_url") and isinstance(value, str):
            # Special handling for URL fields
            result[safe_key] = safe_url(value)
        else:
            result[safe_key] = safe_escape(value)

    return result
