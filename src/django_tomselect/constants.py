"""Constants used across django_tomselect."""

from django.conf import settings

# Cache settings
PERMISSION_CACHE = getattr(settings, "PERMISSION_CACHE", {})
PERMISSION_CACHE_TIMEOUT = PERMISSION_CACHE.get("TIMEOUT", None)
PERMISSION_CACHE_KEY_PREFIX = PERMISSION_CACHE.get("KEY_PREFIX", "")
PERMISSION_CACHE_NAMESPACE = PERMISSION_CACHE.get("NAMESPACE", "tomselect")

# Autocomplete view constants
SEARCH_VAR = "q"
FILTERBY_VAR = "f"
EXCLUDEBY_VAR = "e"
PAGE_VAR = "p"
