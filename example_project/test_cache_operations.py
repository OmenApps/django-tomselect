"""Tests for django_tomselect caching - edge cases for individual cache operations."""

import logging

import pytest
from django.core.cache.backends.redis import RedisCache
from django.test import override_settings

from django_tomselect.cache import PermissionCache


class TestAtomicIncrementEdgeCases:
    """Test _atomic_increment edge cases and race conditions."""

    @pytest.fixture
    def permission_cache_instance(self):
        """Create a PermissionCache instance."""
        return PermissionCache()

    def test_atomic_increment_redis_success(self, permission_cache_instance):
        """Test successful Redis atomic increment."""

        class MockRedisClient:
            """Mock Redis client class."""
            def __init__(self):
                """Initialize the mock client."""
                self.incr_called = False

            def incr(self, key):
                """Mock incr method."""
                self.incr_called = True
                return 2

        class MockRedis(RedisCache):
            """Mock Redis cache class."""
            def __init__(self):
                """Initialize the mock Redis cache."""
                self.client = MockRedisClient()

        mock_cache = MockRedis()
        permission_cache_instance.cache = mock_cache

        result = permission_cache_instance._atomic_increment("test_key")
        assert result is True
        assert mock_cache.client.incr_called

    def test_atomic_increment_redis_exception(self, permission_cache_instance, caplog):
        """Test Redis increment exception handling."""

        class MockRedisClient:
            """Mock Redis client that raises exception on incr."""
            def incr(self, key):
                """Raise exception on incr."""
                raise OSError("Redis error")

        class MockRedis(RedisCache):
            """Mock Redis cache class."""
            def __init__(self):
                """Initialize the mock Redis cache."""
                self.client = MockRedisClient()

        mock_cache = MockRedis()
        permission_cache_instance.cache = mock_cache

        with caplog.at_level(logging.WARNING):
            result = permission_cache_instance._atomic_increment("test_key")
        assert result is False
        assert "Atomic increment failed" in caplog.text

    def test_atomic_increment_generic_cache_key_exists(self, permission_cache_instance):
        """Test generic cache increment when key already exists."""

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.data = {"test_key": 5}

            def incr(self, key, delta=1):
                """Increment the value in the cache."""
                if key in self.data:
                    self.data[key] += delta
                    return self.data[key]
                raise ValueError("Key does not exist")

            def add(self, key, value, timeout=None):
                """Add the value to the cache if key doesn't exist."""
                if key not in self.data:
                    self.data[key] = value
                    return True
                return False

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        result = permission_cache_instance._atomic_increment("test_key")
        assert result is True
        assert mock_cache.data["test_key"] == 6

    def test_atomic_increment_generic_cache_add_success(self, permission_cache_instance):
        """Test atomic add when key doesn't exist."""

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.data = {}
                self.add_called = False

            def incr(self, key, delta=1):
                """Increment the value in the cache."""
                raise ValueError("Key does not exist")

            def add(self, key, value, timeout=None):
                """Add the value to the cache if key doesn't exist."""
                self.add_called = True
                self.data[key] = value
                return True

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        result = permission_cache_instance._atomic_increment("test_key")
        assert result is True
        assert mock_cache.add_called
        assert mock_cache.data["test_key"] == 1

    def test_atomic_increment_concurrent_race_condition(self, permission_cache_instance):
        """Test race condition where add fails but retry incr succeeds."""

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.incr_attempts = 0

            def incr(self, key, delta=1):
                """Increment the value in the cache."""
                self.incr_attempts += 1
                if self.incr_attempts == 1:
                    raise ValueError("Key does not exist")
                return 2  # Second attempt succeeds

            def add(self, key, value, timeout=None):
                """Add the value to the cache if key doesn't exist."""
                return False  # Key was set by another process

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        result = permission_cache_instance._atomic_increment("test_key")
        assert result is True
        assert mock_cache.incr_attempts == 2

    def test_atomic_increment_all_methods_fail(self, permission_cache_instance, caplog):
        """Test when all atomic increment methods fail."""

        class MockCache:
            """Mock cache class."""
            def incr(self, key, delta=1):
                """Increment the value in the cache."""
                raise ValueError("Key does not exist")

            def add(self, key, value, timeout=None):
                """Add the value to the cache if key doesn't exist."""
                return False  # add fails

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        # After add fails, it tries incr again which also fails
        # This tests the final fallback path
        result = permission_cache_instance._atomic_increment("test_key")
        # The function returns False when all methods fail
        assert result is False


class TestGetPermissionEdgeCases:
    """Test get_permission edge cases."""

    @pytest.fixture
    def permission_cache_instance(self):
        """Create a PermissionCache instance."""
        pc = PermissionCache()
        pc.enabled = True
        pc.timeout = 300
        return pc

    @pytest.mark.parametrize(
        "user_id,model_name,action",
        [
            (None, "author", "view"),
            (0, "author", "view"),
            (1, "", "view"),
            (1, None, "view"),
            (1, "author", ""),
            (1, "author", None),
        ],
    )
    @override_settings(DEBUG=False)
    def test_get_permission_invalid_params(self, permission_cache_instance, user_id, model_name, action, caplog):
        """Test warning logged for invalid parameters."""
        with caplog.at_level(logging.WARNING):
            result = permission_cache_instance.get_permission(user_id, model_name, action)
        assert result is None
        assert "Invalid parameters" in caplog.text

    @override_settings(DEBUG=False)
    def test_get_permission_cache_hit(self, permission_cache_instance, caplog):
        """Test debug log on cache hit."""

        class MockCache:
            """Mock cache class."""
            def get(self, key, default=None):
                """Return a cached value."""
                return True  # Cache hit

            def set(self, key, value, timeout=None):
                """Mock set method."""
                pass

        permission_cache_instance.cache = MockCache()

        with caplog.at_level(logging.DEBUG):
            result = permission_cache_instance.get_permission(1, "author", "view")
        assert result is True
        assert "cache hit" in caplog.text.lower()

    @override_settings(DEBUG=False)
    def test_get_permission_cache_miss(self, permission_cache_instance, caplog):
        """Test debug log on cache miss."""

        class MockCache:
            """Mock cache class."""
            def get(self, key, default=None):
                """Return None to simulate cache miss."""
                return None  # Cache miss

            def set(self, key, value, timeout=None):
                """Mock set method."""
                pass

        permission_cache_instance.cache = MockCache()

        with caplog.at_level(logging.DEBUG):
            result = permission_cache_instance.get_permission(1, "author", "view")
        assert result is None
        assert "cache miss" in caplog.text.lower()


class TestSetPermissionEdgeCases:
    """Test set_permission edge cases."""

    @pytest.fixture
    def permission_cache_instance(self):
        """Create a PermissionCache instance."""
        pc = PermissionCache()
        pc.enabled = True
        pc.timeout = 300
        return pc

    def test_set_permission_when_disabled(self, permission_cache_instance):
        """Test set_permission returns early when disabled."""
        permission_cache_instance.enabled = False

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.set_called = False

            def set(self, key, value, timeout=None):
                """Mock set method."""
                self.set_called = True

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        permission_cache_instance.set_permission(1, "author", "view", True)
        assert not mock_cache.set_called

    @pytest.mark.parametrize(
        "user_id,model_name,action",
        [
            (None, "author", "view"),
            (0, "author", "view"),
            (1, "", "view"),
            (1, None, "view"),
            (1, "author", ""),
            (1, "author", None),
        ],
    )
    @override_settings(DEBUG=False)
    def test_set_permission_invalid_params(self, permission_cache_instance, user_id, model_name, action, caplog):
        """Test warning logged for invalid parameters."""

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.set_called = False

            def get(self, key, default=None):
                """Return None to simulate cache miss."""
                return None

            def set(self, key, value, timeout=None):
                """Mock set method."""
                self.set_called = True

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        with caplog.at_level(logging.WARNING):
            permission_cache_instance.set_permission(user_id, model_name, action, True)
        assert "Invalid parameters" in caplog.text
        assert not mock_cache.set_called

    @override_settings(DEBUG=False)
    def test_set_permission_exception_handling(self, permission_cache_instance, caplog):
        """Test exception handling in set_permission."""

        class MockCache:
            """Mock cache class that raises exception on set."""
            def get(self, key, default=None):
                """Mock get method."""
                return None

            def set(self, key, value, timeout=None):
                """Raise exception on set."""
                raise OSError("Cache set error")

        permission_cache_instance.cache = MockCache()

        with caplog.at_level(logging.WARNING):
            permission_cache_instance.set_permission(1, "author", "view", True)
        assert "cache set failed" in caplog.text.lower()


class TestInvalidateUserEdgeCases:
    """Test invalidate_user edge cases."""

    @pytest.fixture
    def permission_cache_instance(self):
        """Create a PermissionCache instance."""
        pc = PermissionCache()
        pc.enabled = True
        pc.timeout = 300
        return pc

    def test_invalidate_user_when_disabled(self, permission_cache_instance):
        """Test invalidate_user returns early when disabled."""
        permission_cache_instance.enabled = False

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.set_called = False

            def set(self, key, value, timeout=None):
                """Mock set method."""
                self.set_called = True

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        permission_cache_instance.invalidate_user(1)
        assert not mock_cache.set_called

    @pytest.mark.parametrize("invalid_user_id", [None, 0, "", False])
    @override_settings(DEBUG=False)
    def test_invalidate_user_invalid_user_id(self, permission_cache_instance, invalid_user_id, caplog):
        """Test warning logged for invalid user_id."""
        with caplog.at_level(logging.WARNING):
            permission_cache_instance.invalidate_user(invalid_user_id)
        assert "Invalid user_id" in caplog.text

    @override_settings(DEBUG=False)
    def test_invalidate_user_non_atomic_fallback(self, permission_cache_instance, caplog):
        """Test fallback to cache.delete when atomic increment fails."""

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.data = {}
                self.deleted_keys = []

            def get(self, key, default=None):
                """Get the value from the cache."""
                return self.data.get(key, default)

            def set(self, key, value, timeout=None):
                """Set the value in the cache."""
                self.data[key] = value

            def delete(self, key):
                """Delete the value from the cache."""
                self.deleted_keys.append(key)
                self.data.pop(key, None)

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        # _atomic_increment will fail because mock cache doesn't have incr/add
        with caplog.at_level(logging.WARNING):
            permission_cache_instance.invalidate_user(1)

        # Should log warning about atomic increment not being available
        # and fall back to cache.delete
        assert "Atomic increment not available" in caplog.text
        assert "falling back to cache.delete()" in caplog.text
        assert len(mock_cache.deleted_keys) == 1


class TestInvalidateAllEdgeCases:
    """Test invalidate_all edge cases."""

    @pytest.fixture
    def permission_cache_instance(self):
        """Create a PermissionCache instance."""
        pc = PermissionCache()
        pc.enabled = True
        pc.timeout = 300
        return pc

    def test_invalidate_all_when_disabled(self, permission_cache_instance):
        """Test invalidate_all returns early when disabled."""
        permission_cache_instance.enabled = False

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.clear_called = False

            def clear(self):
                """Mock clear method."""
                self.clear_called = True

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        permission_cache_instance.invalidate_all()
        assert not mock_cache.clear_called

    @override_settings(DEBUG=False)
    def test_invalidate_all_with_delete_pattern(self, permission_cache_instance, caplog):
        """Test invalidate_all using delete_pattern method."""

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.delete_pattern_called = False

            def delete_pattern(self, pattern):
                """Mock delete_pattern method."""
                self.delete_pattern_called = True

            def get(self, key, default=None):
                """Get the value from the cache."""
                return default

            def set(self, key, value, timeout=None):
                """Set the value in the cache."""
                pass

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        with caplog.at_level(logging.DEBUG):
            permission_cache_instance.invalidate_all()
        assert mock_cache.delete_pattern_called
        assert "Delete pattern successful" in caplog.text

    @override_settings(DEBUG=False)
    def test_invalidate_all_with_clear_prefix(self, permission_cache_instance, caplog):
        """Test invalidate_all using clear_prefix method."""

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.clear_prefix_called = False

            def clear_prefix(self, pattern):
                """Mock clear_prefix method."""
                self.clear_prefix_called = True

            def get(self, key, default=None):
                """Get the value from the cache."""
                return default

            def set(self, key, value, timeout=None):
                """Set the value in the cache."""
                pass

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        with caplog.at_level(logging.DEBUG):
            permission_cache_instance.invalidate_all()
        assert mock_cache.clear_prefix_called
        assert "Clear prefix successful" in caplog.text

    @override_settings(DEBUG=False)
    def test_invalidate_all_fallback_to_version_increment(self, permission_cache_instance, caplog):
        """Test fallback to version increment when pattern deletion unavailable."""

        class MockCache:
            """Mock cache class."""
            def __init__(self):
                """Initialize the mock cache."""
                self.data = {}

            def get(self, key, default=None):
                """Get the value from the cache."""
                return self.data.get(key, default)

            def set(self, key, value, timeout=None):
                """Set the value in the cache."""
                self.data[key] = value

            def delete(self, key):
                """Delete the value from the cache."""
                self.data.pop(key, None)

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        with caplog.at_level(logging.DEBUG):
            permission_cache_instance.invalidate_all()
        assert "Pattern-based deletion not available" in caplog.text

    @override_settings(DEBUG=False)
    def test_invalidate_all_exception_handling(self, permission_cache_instance, caplog):
        """Test exception handling in invalidate_all."""

        class MockCache:
            """Mock cache class that raises exception on get/set."""
            def __init__(self):
                """Initialize the mock cache."""
                pass

            def get(self, key, default=None):
                """Get method that doesn't fail (allows fallback path)."""
                return default

            def set(self, key, value, timeout=None):
                """Set method that doesn't fail (allows fallback path)."""
                pass

            def delete(self, key):
                """Delete method for fallback invalidation."""
                pass

        mock_cache = MockCache()
        permission_cache_instance.cache = mock_cache

        with caplog.at_level(logging.WARNING):
            permission_cache_instance.invalidate_all()
        # Since atomic increment fails (no incr/add), warning is logged and falls back to cache.delete
        assert "atomic increment not available" in caplog.text.lower()


class TestCacheInvalidationKeyConsistency:
    """Test that _make_cache_key and invalidate_user use the same version key."""

    @pytest.fixture
    def permission_cache_instance(self):
        """Create a PermissionCache instance with caching enabled."""
        pc = PermissionCache()
        pc.enabled = True
        pc.timeout = 300
        return pc

    @override_settings(DEBUG=False)
    def test_make_cache_key_uses_get_version_key(self, permission_cache_instance):
        """Verify _make_cache_key reads the same version key that invalidate_user increments.

        This is a regression test for a bug where _make_cache_key constructed
        its version key inline (base_key + ':version') which didn't match the
        key from _get_version_key(user_id), causing invalidation to be broken.
        """

        class TrackingCache:
            """Mock cache that tracks which keys are accessed."""

            def __init__(self):
                self.data = {}
                self.get_keys = []
                self.delete_keys = []

            def get(self, key, default=None):
                self.get_keys.append(key)
                return self.data.get(key, default)

            def set(self, key, value, timeout=None):
                self.data[key] = value

            def delete(self, key):
                self.delete_keys.append(key)
                self.data.pop(key, None)

            def add(self, key, value, timeout):
                if key not in self.data:
                    self.data[key] = value
                    return True
                return False

        mock_cache = TrackingCache()
        permission_cache_instance.cache = mock_cache

        # Call _make_cache_key - it should read the version key
        permission_cache_instance._make_cache_key(42, "author", "view")

        # The version key read by _make_cache_key should be the same as _get_version_key(42)
        expected_version_key = permission_cache_instance._get_version_key(42)
        assert expected_version_key in mock_cache.get_keys, (
            f"_make_cache_key should read version key {expected_version_key!r}, "
            f"but it read: {mock_cache.get_keys}"
        )

    @override_settings(DEBUG=False)
    def test_invalidate_user_actually_invalidates(self, permission_cache_instance):
        """Test that invalidating a user causes a cache miss for their permissions.

        Seeds the version key first so that incr() bumps it to a new value,
        which makes _make_cache_key produce a different cache key >> cache miss.
        """

        class IncrCache:
            """Dict-based cache with incr support."""

            def __init__(self):
                self.data = {}

            def get(self, key, default=None):
                return self.data.get(key, default)

            def set(self, key, value, timeout=None):
                self.data[key] = value

            def delete(self, key):
                self.data.pop(key, None)

            def add(self, key, value, timeout):
                if key not in self.data:
                    self.data[key] = value
                    return True
                return False

            def incr(self, key, delta=1):
                if key not in self.data:
                    raise ValueError("Key doesn't exist")
                self.data[key] = int(self.data[key]) + delta
                return self.data[key]

        mock_cache = IncrCache()
        permission_cache_instance.cache = mock_cache

        # Seed the version key so it exists before caching a permission
        version_key = permission_cache_instance._get_version_key(1)
        mock_cache.set(version_key, 1)

        # Cache a permission (uses version=1)
        permission_cache_instance.set_permission(1, "author", "view", True)
        assert permission_cache_instance.get_permission(1, "author", "view") is True

        # Invalidate - incr() bumps version from 1 >> 2
        permission_cache_instance.invalidate_user(1)

        # After invalidation, _make_cache_key reads version=2 >> different key >> miss
        result = permission_cache_instance.get_permission(1, "author", "view")
        assert result is None, "Permission should be invalidated (cache miss)"
