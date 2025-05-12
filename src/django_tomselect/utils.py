"""Utility functions for django-tomselect."""

import re
from typing import Any, Optional

from django.utils.html import escape

from django_tomselect.logging import package_logger

# Constants for URL validation
ALLOWED_URL_PROTOCOLS = ["http://", "https://", "mailto:", "tel:", "/"]
DANGEROUS_URL_SCHEMES = r"^(javascript|data|vbscript|file):"
DOMAIN_PATTERN = r"^[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}"

# Maximum recursion depth for dictionary sanitization
MAX_RECURSION_DEPTH = 10


def safe_escape(value: Any) -> str:
    """Safely escape a value, ensuring proper HTML encoding.

    Handles various input types, converts them to strings,
    and applies proper HTML escaping to prevent XSS attacks.

    Args:
        value: Any value that needs to be safely displayed in HTML

    Returns:
        Properly escaped string
    """
    try:
        if value is None:
            return ""

        # Convert to string if not already
        if not isinstance(value, str):
            value = str(value)

        # Apply HTML escaping - ensure we're always returning a string
        return escape(value)
    except Exception as e:
        package_logger.error("Error escaping value: %s", e)
        # Fail safely by returning an empty string
        return ""


def safe_url(url: Optional[str]) -> Optional[str]:
    """Validate and sanitize a URL to prevent unsafe schemes.

    Checks URLs against allowed protocols and patterns, sanitizing or
    rejecting potentially dangerous URLs that could lead to XSS attacks.

    Args:
        url: URL string to validate

    Returns:
        Safe URL or None if the URL is unsafe
    """
    if not url:
        return None

    try:
        # Check if URL starts with an allowed protocol
        for protocol in ALLOWED_URL_PROTOCOLS:
            if url.startswith(protocol):
                return escape(url)

        # Check for relative URL (starting with / or ./)
        if url.startswith("/") or url.startswith("./"):
            return escape(url)

        # Check for dangerous schemes
        if re.match(DANGEROUS_URL_SCHEMES, url.lower()):
            package_logger.warning("Rejected dangerous URL scheme: %s", url)
            return None

        # Default to http:// if no protocol specified but URL looks like a domain
        if re.match(DOMAIN_PATTERN, url):
            return escape(f"http://{url}")

        # If we can't determine if it's safe, escape it
        return escape(url)
    except Exception as e:
        package_logger.error("Error processing URL %s: %s", url, e)
        return None


def sanitize_dict(data: dict, escape_keys: bool = False, depth: int = 0) -> dict:
    """Sanitize all values in a dictionary to prevent XSS.

    Recursively processes dictionary values, applying appropriate
    sanitization methods based on value type and key names.

    Args:
        data: Dictionary containing potentially unsafe values
        escape_keys: Whether to also escape dictionary keys
        depth: Current recursion depth to prevent stack overflow

    Returns:
        Dictionary with all values safely escaped
    """
    if not isinstance(data, dict):
        package_logger.warning("Non-dictionary passed to sanitize_dict of type: %s", type(data))
        return {}

    if depth > MAX_RECURSION_DEPTH:
        package_logger.warning("Maximum recursion depth reached in sanitize_dict")
        return {}

    result = {}
    try:
        for key, value in data.items():
            # Ensure key is a valid string
            if not isinstance(key, str):
                key = str(key)

            safe_key = safe_escape(key) if escape_keys else key

            if isinstance(value, dict):
                result[safe_key] = sanitize_dict(value, escape_keys, depth + 1)
            elif isinstance(value, list):
                sanitized_list = []
                for item in value:
                    if isinstance(item, dict):
                        sanitized_list.append(sanitize_dict(item, escape_keys, depth + 1))
                    else:
                        sanitized_list.append(safe_escape(item))
                result[safe_key] = sanitized_list
            elif key.endswith("_url") and isinstance(value, str):
                # Special handling for URL fields
                sanitized_url = safe_url(value)
                if sanitized_url is not None:
                    result[safe_key] = sanitized_url
                else:
                    # If URL sanitization fails, store an empty string as a safe fallback
                    result[safe_key] = ""
                    package_logger.warning("Unsafe URL found and nullified in key: %s", key)
            else:
                result[safe_key] = safe_escape(value)
    except Exception as e:
        package_logger.error("Error sanitizing dictionary: %s", e)
        # Return whatever was successfully processed
        if not result:
            return {}

    return result
