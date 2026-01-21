# Utilities

This documentation covers the utility subsystems that support TomSelect's internal functionality: permission caching and logging.

## Permission Caching

The permission caching system improves performance by caching user permission checks for autocomplete views. This is particularly useful in high-traffic applications where the same permission checks occur repeatedly.

### Configuration

Permission caching is **disabled by default**. Enable it by setting a timeout in your Django settings:

```python
# settings.py
TOMSELECT = {
    "PERMISSION_CACHE": {
        "TIMEOUT": 300,        # Cache timeout in seconds (required to enable)
        "KEY_PREFIX": "myapp", # Optional: prefix for cache keys
        "NAMESPACE": "perms",  # Optional: namespace for cache keys (default: "tomselect")
    }
}
```

### Behavior

- **DEBUG mode**: Caching is automatically disabled when `DEBUG=True`
- **Anonymous users**: Permissions are never cached for unauthenticated users
- **Auth overrides**: Caching is skipped when `skip_authorization=True` or `allow_anonymous=True`

### Cache Backend Support

The system supports atomic operations for reliable cache invalidation:

| Backend | Atomic Operations | Pattern Deletion |
|---------|-------------------|------------------|
| Redis | Yes | Yes |
| Memcached | Yes | No |
| Local Memory | Partial | No |
| Database | No | No |

For production deployments with permission changes, Redis or Memcached is recommended.

### Invalidation

When user permissions change, invalidate the cache using the global `permission_cache` instance:

```python
from django_tomselect.cache import permission_cache

# Invalidate all cached permissions for a specific user
permission_cache.invalidate_user(user_id=42)

# Invalidate all cached permissions globally
permission_cache.invalidate_all()
```

### Using the Decorator

The `@cache_permission` decorator is used internally to cache permission check methods:

```python
from django_tomselect.cache import cache_permission

class MyAutocompleteView(AutocompleteModelView):
    model = MyModel

    @cache_permission
    def has_permission(self, request, action="view"):
        # This result will be cached per user/model/action
        return super().has_permission(request, action)
```

## Logging

The logging system provides a controllable wrapper around Python's standard logging module, with per-module loggers for fine-grained control.

### Configuration

Logging is **enabled by default**. Disable it globally in your Django settings:

```python
# settings.py
TOMSELECT = {
    "ENABLE_LOGGING": False,  # Disable all django-tomselect logging
}
```

### Per-Module Logging

Each module in django-tomselect uses its own logger, following Python's `logging.getLogger(__name__)` best practice. This allows you to configure different log levels for different parts of the package:

```python
# settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        # Configure all django-tomselect logging
        "django_tomselect": {
            "handlers": ["console"],
            "level": "WARNING",
        },
        # Enable debug logging only for autocomplete views
        "django_tomselect.autocompletes": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        # Quiet the widget rendering logs
        "django_tomselect.widgets": {
            "handlers": ["console"],
            "level": "ERROR",
        },
    },
}
```

#### Available Module Loggers

| Logger Name | Description |
|-------------|-------------|
| `django_tomselect.autocompletes` | Autocomplete view processing, filtering, pagination |
| `django_tomselect.widgets` | Widget rendering, URL resolution, context building |
| `django_tomselect.forms` | Form field initialization and validation |
| `django_tomselect.cache` | Permission caching operations |
| `django_tomselect.utils` | URL reversal, value escaping, sanitization |
| `django_tomselect.middleware` | Request storage in thread-local |
| `django_tomselect.lazy_utils` | Lazy view and URL resolution |
| `django_tomselect.templatetags.django_tomselect` | Template tag rendering |

### Runtime Control

You can control logging at runtime by getting a logger instance:

```python
from django_tomselect.logging import get_logger

# Get a module-specific logger
logger = get_logger("django_tomselect.autocompletes")

# Check if logging is enabled
if logger.enabled:
    print("Logging is active")

# Disable logging for this logger
logger.enabled = False
```

### Temporarily Disabling Logging

Use the `temporarily_disabled()` decorator to suppress logging within a specific function:

```python
from django_tomselect.logging import get_logger

logger = get_logger(__name__)

@logger.temporarily_disabled()
def my_function():
    # All logging from this logger is suppressed here
    do_something_noisy()
```

This is useful for tests or batch operations where logging output would be excessive.
