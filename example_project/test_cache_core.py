"""Tests for django_tomselect caching - core PermissionCache behavior and helpers."""

import logging

import pytest
from django.core.cache.backends.redis import RedisCache
from django.test import override_settings

from django_tomselect.cache import PermissionCache


class TestPermissionCache:
    """Test the PermissionCache class functionality."""

    @pytest.fixture
    def permission_cache(self):
        """Create a fresh PermissionCache instance for each test."""
        return PermissionCache()

    @pytest.fixture
    def mock_redis_cache(self, monkeypatch):  # noqa: C901
        """Create a mock Redis cache without using mocker."""

        class MockRedisClient:
            """Mock Redis client class."""

            def __init__(self):
                self.incremented = {}
                self.deleted = set()
                self.keys_list = ["key1", "key2"]
                self.data = {}

            def incr(self, key):
                """Increment the value in the cache."""
                if key not in self.data:
                    self.data[key] = "1"
                self.incremented[key] = int(self.data[key]) + 1
                self.data[key] = str(self.incremented[key])
                return self.incremented[key]

            def keys(self, pattern):
                """Return keys matching the pattern."""
                return self.keys_list

            def delete(self, *keys):
                """Delete keys from the cache."""
                self.deleted.update(keys)
                for key in keys:
                    if key in self.data:
                        del self.data[key]

        class MockRedis(RedisCache):
            """Mock Redis cache class."""

            def __init__(self):
                """Initialize the mock Redis cache."""
                self.client = MockRedisClient()

            def get(self, key, default=None):
                """Get the value from the cache."""
                return self.client.data.get(key, default)

            def set(self, key, value, timeout=None):
                """Set the value in the cache."""
                self.client.data[key] = value

        return MockRedis()

    @pytest.fixture
    def mock_memcached_cache(self, monkeypatch):
        """Create a mock Memcached cache without using mocker."""

        class MockMemcached:
            """Mock Memcached cache class."""

            def __init__(self):
                self.incremented = {}

            def incr(self, key, delta=1, default=1):
                """Increment the value in the cache."""
                self.incremented[key] = self.incremented.get(key, default) + delta - 1
                return self.incremented[key]

        return MockMemcached()

    def test_cache_key_generation_with_prefix(self, permission_cache):
        """Test cache key generation with prefix."""
        with override_settings(PERMISSION_CACHE={"KEY_PREFIX": "test_prefix"}):
            key = permission_cache._make_cache_key(1, "author", "view")
            assert isinstance(key, str)
            assert len(key) == 32  # MD5 hash length

    def test_cache_key_generation_with_namespace(self, permission_cache):
        """Test cache key generation with namespace."""
        with override_settings(PERMISSION_CACHE={"NAMESPACE": "test_namespace"}):
            key = permission_cache._make_cache_key(1, "author", "view")
            assert isinstance(key, str)
            assert len(key) == 32  # MD5 hash length

    def test_version_key_generation(self, permission_cache):
        """Test version key generation."""
        # Test user-specific version key
        user_key = permission_cache._get_version_key(1)
        assert "tomselect_perm:1:version" in user_key

        # Test global version key
        global_key = permission_cache._get_version_key()
        assert "tomselect_perm:global_version" in global_key

    @pytest.mark.django_db
    def test_permission_caching_operations(self, permission_cache, settings):
        """Test basic permission caching operations."""
        # Enable caching and set timeout
        settings.PERMISSION_CACHE = {"TIMEOUT": 300}
        permission_cache.enabled = True
        permission_cache.timeout = 300

        # Test set and get
        permission_cache.set_permission(1, "author", "view", True)
        assert permission_cache.get_permission(1, "author", "view") is True

    def test_atomic_increment_memcached(self, permission_cache, mock_memcached_cache):
        """Test atomic increment with Memcached cache."""
        permission_cache.cache = mock_memcached_cache
        assert permission_cache._atomic_increment("test_key") is True
        assert mock_memcached_cache.incremented["test_key"] == 1

    def test_atomic_increment_generic(self, permission_cache):
        """Test atomic increment with generic cache."""

        class MockCache:
            """Mock cache class."""

            def __init__(self):
                self.data = {}
                self.increment_calls = 0
                self.set_calls = 0
                self.add_calls = 0

            def incr(self, key, delta=1):
                """Increment the value in the cache."""
                self.increment_calls += 1
                if key not in self.data:
                    raise ValueError("Key doesn't exist")
                self.data[key] = self.data[key] + delta
                return self.data[key]

            def set(self, key, value, timeout=None):
                """Set the value in the cache."""
                self.set_calls += 1
                self.data[key] = int(value)

            def add(self, key, value, timeout=None):
                """Add the value to the cache if key doesn't exist (atomic)."""
                self.add_calls += 1
                if key in self.data:
                    return False  # Key already exists
                self.data[key] = int(value)
                return True

        mock_cache = MockCache()
        permission_cache.cache = mock_cache

        assert permission_cache._atomic_increment("test_key") is True
        assert mock_cache.add_calls == 1  # Uses atomic add() instead of set()
        assert mock_cache.data["test_key"] == 1

    def test_invalidate_all_redis(self, permission_cache, mock_redis_cache):
        """Test all permissions invalidation with Redis cache."""
        permission_cache.cache = mock_redis_cache
        permission_cache.enabled = True
        # Set some test data first
        mock_redis_cache.client.data = {"key1": "value1", "key2": "value2"}
        permission_cache.invalidate_all()
        assert mock_redis_cache.client.deleted == {"key1", "key2"}

    def test_error_handling(self, permission_cache):
        """Test error handling in cache operations."""

        class ErrorCache:
            """Cache class that raises exceptions."""

            def get(self, *args, **kwargs):
                """Raise exception on get."""
                raise OSError("Cache error")

            def set(self, *args, **kwargs):
                """Raise exception on set."""
                raise OSError("Cache error")

        permission_cache.cache = ErrorCache()
        permission_cache.enabled = True

        # Test get_permission error handling
        assert permission_cache.get_permission(1, "author", "view") is None

        # Test set_permission error handling
        permission_cache.set_permission(1, "author", "view", True)  # Should not raise

        # Test invalidate_user error handling
        permission_cache.invalidate_user(1)  # Should not raise

        # Test invalidate_all error handling
        permission_cache.invalidate_all()  # Should not raise


class TestPermissionCacheIsEnabled:
    """Test is_enabled method edge cases."""

    @pytest.fixture
    def permission_cache_instance(self):
        """Create a PermissionCache instance."""
        return PermissionCache()

    @override_settings(DEBUG=True)
    def test_is_enabled_returns_false_in_debug_mode(self, permission_cache_instance):
        """Test cache is disabled in DEBUG mode."""
        permission_cache_instance.enabled = True
        permission_cache_instance.timeout = 300
        result = permission_cache_instance.is_enabled()
        assert result is False

    @override_settings(DEBUG=False)
    def test_is_enabled_returns_true_when_properly_configured(self, permission_cache_instance):
        """Test cache is enabled when properly configured."""
        permission_cache_instance.enabled = True
        permission_cache_instance.timeout = 300
        result = permission_cache_instance.is_enabled()
        assert result is True

    def test_is_enabled_returns_false_when_disabled(self, permission_cache_instance):
        """Test cache disabled when self.enabled is False."""
        permission_cache_instance.enabled = False
        result = permission_cache_instance.is_enabled()
        assert result is False

    def test_is_enabled_exception_handling(self, permission_cache_instance, monkeypatch, caplog):
        """Test is_enabled returns False on exception."""
        permission_cache_instance.enabled = True

        # Make settings.DEBUG raise an exception
        def raise_error():
            """Raise an exception."""
            raise AttributeError("Settings error")

        class MockSettings:
            """Mock settings class that raises exception on DEBUG access."""
            @property
            def DEBUG(self):  # noqa: N802
                """Raise exception when accessed."""
                raise AttributeError("Settings error")

        monkeypatch.setattr("django_tomselect.cache.settings", MockSettings())

        with caplog.at_level(logging.ERROR):
            result = permission_cache_instance.is_enabled()
        assert result is False
        assert "Error checking if permission cache is enabled" in caplog.text


class TestVersionKeyGeneration:
    """Test _get_version_key with various combinations."""

    @pytest.fixture
    def permission_cache_instance(self):
        """Create a PermissionCache instance."""
        return PermissionCache()

    @pytest.mark.parametrize(
        "user_id,expected_contains",
        [
            (1, "tomselect_perm:1:version"),
            (42, "tomselect_perm:42:version"),
            (None, "tomselect_perm:global_version"),
        ],
    )
    def test_version_key_user_variations(self, permission_cache_instance, user_id, expected_contains):
        """Test version key generation with different user_id values."""
        key = permission_cache_instance._get_version_key(user_id)
        assert expected_contains in key
