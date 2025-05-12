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

    Caching is disabled by default and must be explicitly enabled by setting
    TOMSELECT_PERMISSION_CACHE_TIMEOUT.
    """

    def __init__(self):
        """Initialize the permission cache system.

        Sets up cache configuration and checks if caching is available and
        properly configured.
        """
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

        if self.enabled:
            package_logger.info("Permission caching is enabled with timeout: %s seconds", self.timeout)

    def is_enabled(self) -> bool:
        """Check if caching is enabled and available.

        Verifies that caching is enabled in settings, not in DEBUG mode,
        and that the cache backend supports the required operations.

        Returns:
            bool: True if caching is enabled and available, False otherwise
        """
        try:
            cache_is_enabled = (
                self.enabled and not settings.DEBUG and hasattr(self.cache, "get") and hasattr(self.cache, "set")
            )
            return cache_is_enabled
        except Exception as e:
            package_logger.error("Error checking if permission cache is enabled: %s", e)
            return False

    def _make_cache_key(self, user_id: int, model_name: str, action: str) -> str:
        """Generate a distributed-safe cache key.

        Creates a unique cache key for a user's permission on a specific model
        and action, incorporating version information to support invalidation.

        Args:
            user_id: The ID of the user
            model_name: The name of the model
            action: The permission action (e.g., "view", "change")

        Returns:
            A unique cache key string
        """
        try:
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
        except Exception as e:
            package_logger.error("Error generating cache key: %s", e)
            # Return a fallback key that's still unique but won't conflict
            fallback_key = f"tomselect_fallback_{user_id}_{model_name}_{action}_{hash(str(e))}"
            return hashlib.md5(fallback_key.encode()).hexdigest()

    def _get_version_key(self, user_id: int | None = None) -> str:
        """Generate the version key for a user or global version.

        Creates a cache key for tracking the version of a user's permissions
        or the global permissions version.

        Args:
            user_id: The user ID, or None for global version

        Returns:
            A version key string
        """
        prefix = PERMISSION_CACHE_KEY_PREFIX or ""

        if prefix and user_id is not None:
            return f"{prefix}:tomselect_perm:{user_id}:version"
        elif prefix:
            return f"{prefix}:tomselect_perm:global_version"
        elif user_id is not None:
            return f"tomselect_perm:{user_id}:version"
        else:
            return "tomselect_perm:global_version"

    def _atomic_increment(self, key: str) -> bool:
        """Attempt to atomically increment a cache value.

        Tries to use atomic increment operations available in the cache backend,
        falling back to non-atomic operations if necessary.

        Args:
            key: The cache key to increment

        Returns:
            True if successful, False if atomic operation not available
        """
        try:
            if isinstance(self.cache, RedisCache):
                # Redis supports atomic increments natively
                self.cache.client.incr(key)
                package_logger.debug("Atomic increment with Redis successful for key: %s", key)
                return True
            elif isinstance(self.cache, BaseMemcachedCache):
                # Memcached supports atomic increments natively
                self.cache.incr(key, delta=1, default=1)
                package_logger.debug("Atomic increment with Memcached successful for key: %s", key)
                return True
            elif hasattr(self.cache, "incr"):
                # Try generic incr if available
                try:
                    self.cache.incr(key, delta=1)
                    package_logger.debug("Atomic increment with generic incr successful for key: %s", key)
                    return True
                except ValueError:
                    # Key doesn't exist, set initial value
                    self.cache.set(key, "1", None)
                    package_logger.debug("Set initial value for key: %s", key)
                    return True
        except Exception as e:
            package_logger.warning(
                "Atomic increment failed for key %s: %s. Falling back to non-atomic operation.", key, e
            )
        return False

    def get_permission(self, user_id: int, model_name: str, action: str) -> bool | None:
        """Get cached permission if caching is enabled.

        Retrieves a previously cached permission value from the cache if available.

        Args:
            user_id: The ID of the user
            model_name: The name of the model
            action: The permission action (e.g., "view", "change")

        Returns:
            The cached permission value (True/False) or None if not in cache
        """
        if not self.is_enabled():
            return None

        try:
            if not user_id or not model_name or not action:
                package_logger.warning(
                    "Invalid parameters for permission cache get: user_id=%s, model_name=%s, action=%s",
                    user_id,
                    model_name,
                    action,
                )
                return None

            cache_key = self._make_cache_key(user_id, model_name, action)
            result = self.cache.get(cache_key)

            if result is not None:
                package_logger.debug(
                    "Permission cache hit for user=%s, model=%s, action=%s: %s", user_id, model_name, action, result
                )
            else:
                package_logger.debug(
                    "Permission cache miss for user=%s, model=%s, action=%s", user_id, model_name, action
                )

            return result
        except Exception as e:
            package_logger.warning(
                "Permission cache get failed for user=%s, model=%s, action=%s: %s", user_id, model_name, action, e
            )
            return None

    def set_permission(self, user_id: int, model_name: str, action: str, value: bool) -> None:
        """Cache a permission value if caching is enabled.

        Stores a permission value in the cache with the configured timeout.

        Args:
            user_id: The ID of the user
            model_name: The name of the model
            action: The permission action (e.g., "view", "change")
            value: The permission value to cache (True/False)
        """
        if not self.is_enabled():
            return

        try:
            if not user_id or not model_name or not action:
                package_logger.warning(
                    "Invalid parameters for permission cache set: user_id=%s, model_name=%s, action=%s",
                    user_id,
                    model_name,
                    action,
                )
                return

            cache_key = self._make_cache_key(user_id, model_name, action)
            self.cache.set(cache_key, value, self.timeout)

            package_logger.debug(
                "Permission cache set for user=%s, model=%s, action=%s: %s", user_id, model_name, action, value
            )
        except Exception as e:
            package_logger.warning(
                "Permission cache set failed for user=%s, model=%s, action=%s: %s", user_id, model_name, action, e
            )

    def invalidate_user(self, user_id: int) -> None:
        """Invalidate all cached permissions for a user.

        Invalidates the cache for a specific user by incrementing their
        version number, making all previous cache keys obsolete.

        Args:
            user_id: The ID of the user whose permissions to invalidate
        """
        if not self.is_enabled():
            return

        try:
            if not user_id:
                package_logger.warning("Invalid user_id for permission cache invalidation: %s", user_id)
                return

            version_key = self._get_version_key(user_id)

            package_logger.info("Invalidating permission cache for user: %s", user_id)

            # Try atomic increment first
            if not self._atomic_increment(version_key):
                # Fall back to non-atomic operation if atomic increment not available
                version = self.cache.get(version_key, "0")
                new_version = str(int(version) + 1)
                self.cache.set(version_key, new_version, None)  # No timeout for version keys
                package_logger.debug(
                    "Non-atomic version increment for user %s: %s -> %s", user_id, version, new_version
                )

        except Exception as e:
            package_logger.warning("Permission cache invalidation failed for user %s: %s", user_id, e)

    def invalidate_all(self) -> None:
        """Invalidate all cached permissions.

        Attempts to invalidate all cached permissions, first by trying pattern-based
        deletion if supported by the cache backend, then by incrementing the global
        version number.
        """
        if not self.is_enabled():
            return

        try:
            package_logger.info("Invalidating all permission cache entries")

            # Try pattern-based deletion first
            prefix = PERMISSION_CACHE_KEY_PREFIX or ""
            pattern = f"{prefix}:tomselect_perm:*" if prefix else "tomselect_perm:*"

            deleted = False
            if isinstance(self.cache, RedisCache):
                # Redis supports pattern-based deletion
                keys = self.cache.client.keys(pattern)
                if keys:
                    self.cache.client.delete(*keys)
                    package_logger.debug("Redis pattern deletion successful for %d keys", len(keys))
                deleted = True
            elif hasattr(self.cache, "delete_pattern"):
                self.cache.delete_pattern(pattern)
                package_logger.debug("Delete pattern successful")
                deleted = True
            elif hasattr(self.cache, "clear_prefix"):
                self.cache.clear_prefix(pattern)
                package_logger.debug("Clear prefix successful")
                deleted = True

            if not deleted:
                # Fall back to version increment if pattern deletion not available
                package_logger.debug("Pattern-based deletion not available, incrementing global version")
                version_key = self._get_version_key()
                if not self._atomic_increment(version_key):
                    # Last resort: non-atomic operation
                    version = self.cache.get(version_key, "0")
                    new_version = str(int(version) + 1)
                    self.cache.set(version_key, new_version, None)
                    package_logger.debug("Non-atomic global version increment: %s -> %s", version, new_version)

        except Exception as e:
            package_logger.warning("Permission cache clear failed: %s", e)


def cache_permission(func: Callable) -> Callable:
    """Decorator to cache permission checks.

    Wraps permission check methods to cache their results, improving performance
    by avoiding repeated permission checks for the same user, model, and action.
    Only caches if caching is enabled and conditions are met.

    Args:
        func: The permission check function to wrap

    Returns:
        The wrapped function with caching capability
    """

    @wraps(func)
    def wrapper(self, request, action="view"):
        try:
            # Check if caching is enabled
            if not permission_cache.is_enabled():
                package_logger.debug("Permission caching is disabled. Skipping cache.")
                return func(self, request, action)

            # Skip cache for anonymous users
            if not hasattr(request, "user") or not request.user.is_authenticated:
                package_logger.debug("Skipping permission cache for anonymous user")
                return func(self, request, action)

            # Skip cache if auth overrides are in effect
            if getattr(self, "skip_authorization", False) or getattr(self, "allow_anonymous", False):
                package_logger.debug("Skipping permission cache for auth override")
                return func(self, request, action)

            # Ensure we have valid model information
            if not hasattr(self, "model") or not hasattr(self.model, "_meta"):
                package_logger.warning("Cannot cache permission - missing model metadata")
                return func(self, request, action)

            model_name = self.model._meta.model_name
            user_id = request.user.id

            if not user_id or not model_name:
                package_logger.warning(
                    "Invalid user_id or model_name for permission cache: user_id=%s, model_name=%s", user_id, model_name
                )
                return func(self, request, action)

            # Try to get from cache
            cached_value = permission_cache.get_permission(user_id, model_name, action)
            if cached_value is not None:
                package_logger.debug(
                    "Permission cache hit for user=%s, model=%s, action=%s: %s",
                    user_id,
                    model_name,
                    action,
                    cached_value,
                )
                return cached_value

            # Calculate permission and cache it
            permission = func(self, request, action)
            permission_cache.set_permission(user_id, model_name, action, permission)
            package_logger.debug(
                "Permission cache miss, calculated permission for user=%s, model=%s, action=%s: %s",
                user_id,
                model_name,
                action,
                permission,
            )

            return permission
        except Exception as e:
            package_logger.error(
                "Error in permission cache decorator: %s. Falling back to uncached permission check.", e
            )
            # Fall back to original function if caching fails
            return func(self, request, action)

    return wrapper


# Global cache instance
permission_cache = PermissionCache()
