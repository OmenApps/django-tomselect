"""Caching for user permissions in TomSelect fields."""

import hashlib
from collections.abc import Callable
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.memcached import BaseMemcachedCache
from django.core.cache.backends.redis import RedisCache

from django_tomselect.constants import (
    PERMISSION_CACHE_KEY_PREFIX,
    PERMISSION_CACHE_NAMESPACE,
    PERMISSION_CACHE_TIMEOUT,
)
from django_tomselect.logging import package_logger


class PermissionCache:
    """Caches and manages user permissions for TomSelect fields.

    Caching is disabled by default and must be explicitly enabled.
    """

    def __init__(self):
        self.cache = cache
        # Default to disabled caching
        self.timeout = PERMISSION_CACHE_TIMEOUT
        self.enabled = self.timeout is not None

        if self.enabled and not hasattr(cache, "get"):
            package_logger.warning(
                "TOMSELECT_PERMISSION_CACHE_TIMEOUT is set but caching appears to be disabled. "
                "Permission caching will be disabled."
            )
            self.enabled = False

    def is_enabled(self) -> bool:
        """Check if caching is enabled and available."""
        cache_is_enabled = (
            self.enabled and not settings.DEBUG and hasattr(self.cache, "get") and hasattr(self.cache, "set")
        )
        return cache_is_enabled

    def _make_cache_key(self, user_id: int, model_name: str, action: str) -> str:
        """Generate a distributed-safe cache key."""
        # Include deployment-specific prefix if available
        prefix = f"{PERMISSION_CACHE_KEY_PREFIX}:" if PERMISSION_CACHE_KEY_PREFIX else ""

        # Include namespace if available
        namespace = f"{PERMISSION_CACHE_NAMESPACE}:" if PERMISSION_CACHE_NAMESPACE else ""

        base_key = f"{prefix}{namespace}tomselect_perm:{user_id}:{model_name}:{action}"

        # Get version for this user's permissions
        version_key = f"{base_key}:version"
        version = self.cache.get(version_key, "1")

        # Create unique key including version
        unique_key = f"{base_key}:v{version}"
        final_key = hashlib.md5(unique_key.encode()).hexdigest()
        package_logger.debug("Permission cache key: %s", final_key)
        return final_key

    def _get_version_key(self, user_id: int | None = None) -> str:
        """Generate the version key for a user or global version."""
        prefix = PERMISSION_CACHE_KEY_PREFIX
        if user_id is not None:
            return f"{prefix}:tomselect_perm:{user_id}:version" if prefix else f"tomselect_perm:{user_id}:version"
        return f"{prefix}:tomselect_perm:global_version" if prefix else "tomselect_perm:global_version"

    def _atomic_increment(self, key: str) -> bool:
        """
        Attempt to atomically increment a cache value.
        Returns True if successful, False if atomic operation not available.
        """
        try:
            if isinstance(self.cache, RedisCache):
                # Redis supports atomic increments natively
                self.cache.client.incr(key)
                return True
            elif isinstance(self.cache, BaseMemcachedCache):
                # Memcached supports atomic increments natively
                self.cache.incr(key, delta=1, default=1)
                return True
            elif hasattr(self.cache, "incr"):
                # Try generic incr if available
                try:
                    self.cache.incr(key, delta=1)
                    return True
                except ValueError:
                    # Key doesn't exist, set initial value
                    self.cache.set(key, "1", None)
                    return True
        except Exception as e:
            package_logger.warning("Atomic increment failed: %s. Falling back to non-atomic operation.", e)
        return False

    def get_permission(self, user_id: int, model_name: str, action: str) -> bool | None:
        """Get cached permission if caching is enabled."""
        if not self.is_enabled():
            return None

        try:
            cache_key = self._make_cache_key(user_id, model_name, action)
            return self.cache.get(cache_key)
        except Exception as e:
            package_logger.warning("Permission cache get failed: %s", e)
            return None

    def set_permission(self, user_id: int, model_name: str, action: str, value: bool) -> None:
        """Cache a permission value if caching is enabled."""
        if not self.is_enabled():
            return

        try:
            cache_key = self._make_cache_key(user_id, model_name, action)
            self.cache.set(cache_key, value, self.timeout)
        except Exception as e:
            package_logger.warning("Permission cache set failed: %s", e)

    def invalidate_user(self, user_id: int) -> None:
        """Invalidate all cached permissions for a user."""
        if not self.is_enabled():
            return

        try:
            version_key = self._get_version_key(user_id)

            # Try atomic increment first
            if not self._atomic_increment(version_key):
                # Fall back to non-atomic operation if atomic increment not available
                version = self.cache.get(version_key, "0")
                new_version = str(int(version) + 1)
                self.cache.set(version_key, new_version, None)  # No timeout for version keys

        except Exception as e:
            package_logger.warning("Permission cache invalidation failed for user %s: %s", user_id, e)

    def invalidate_all(self) -> None:
        """Invalidate all cached permissions."""
        if not self.is_enabled():
            return

        try:
            # Try pattern-based deletion first
            prefix = PERMISSION_CACHE_KEY_PREFIX
            pattern = f"{prefix}:tomselect_perm:*" if prefix else "tomselect_perm:*"

            deleted = False
            if isinstance(self.cache, RedisCache):
                # Redis supports pattern-based deletion
                keys = self.cache.client.keys(pattern)
                if keys:
                    self.cache.client.delete(*keys)
                deleted = True
            elif hasattr(self.cache, "delete_pattern"):
                self.cache.delete_pattern(pattern)
                deleted = True
            elif hasattr(self.cache, "clear_prefix"):
                self.cache.clear_prefix(pattern)
                deleted = True

            if not deleted:
                # Fall back to version increment if pattern deletion not available
                version_key = self._get_version_key()
                if not self._atomic_increment(version_key):
                    # Last resort: non-atomic operation
                    version = self.cache.get(version_key, "0")
                    new_version = str(int(version) + 1)
                    self.cache.set(version_key, new_version, None)

        except Exception as e:
            package_logger.warning("Permission cache clear failed: %s", e)


def cache_permission(func: Callable) -> Callable:
    """Decorator to cache permission checks.

    Only caches if caching is enabled.
    """

    @wraps(func)
    def wrapper(self, request, action="view"):
        # Skip cache for anonymous users
        if not hasattr(request, "user") or not request.user.is_authenticated:
            package_logger.debug("Skipping permission cache for anonymous user")
            return func(self, request, action)

        # Skip cache if auth overrides are in effect
        if getattr(self, "skip_authorization", False) or getattr(self, "allow_anonymous", False):
            package_logger.debug("Skipping permission cache for auth override")
            return func(self, request, action)

        if not permission_cache.is_enabled():
            package_logger.debug("Permission caching is disabled. Skipping cache.")
            return func(self, request, action)

        model_name = self.model._meta.model_name
        user_id = request.user.id

        # Try to get from cache
        cached_value = permission_cache.get_permission(user_id, model_name, action)
        if cached_value is not None:
            package_logger.debug("Permission cache hit: %s", cached_value)
            return cached_value

        # Calculate permission and cache it
        permission = func(self, request, action)
        permission_cache.set_permission(user_id, model_name, action, permission)
        package_logger.debug("Permission cache miss: %s", permission)

        return permission

    return wrapper


# Global cache instance
permission_cache = PermissionCache()
