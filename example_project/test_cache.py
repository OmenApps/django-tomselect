"""Tests for django_tomselect caching functionality."""

import logging

import pytest
from django.core.cache.backends.redis import RedisCache
from django.test import override_settings

from django_tomselect.cache import PermissionCache, cache_permission, permission_cache


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


@pytest.mark.django_db
class TestCachePermissionDecorator:
    """Test the cache_permission decorator."""

    @pytest.fixture
    def mock_view(self):
        """Create a mock view class."""

        class MockView:
            """Mock view class."""

            model = type("MockModel", (), {"_meta": type("Meta", (), {"model_name": "mock"})()})()
            skip_authorization = False
            allow_anonymous = False

            @cache_permission
            def check_permission(self, request, action="view"):
                """Test the cache_permission decorator."""
                return True

        return MockView()

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""

        class User:
            """Mock user class."""

            id = 1
            is_authenticated = True

        return type("MockRequest", (), {"user": User()})()

    def test_decorator_caches_result(self, mock_view, mock_request):
        """Test that the decorator caches permission check results."""
        # First call should cache the result
        result1 = mock_view.check_permission(mock_request)
        assert result1 is True

        # Second call should use cached result
        result2 = mock_view.check_permission(mock_request)
        assert result2 is True

    def test_decorator_skip_cache_for_anonymous(self, mock_view):
        """Test that decorator skips cache for anonymous users."""
        anon_request = type("MockRequest", (), {"user": type("User", (), {"is_authenticated": False})()})
        result = mock_view.check_permission(anon_request)
        assert result is True

    def test_decorator_skip_cache_for_authorization_override(self, mock_view, mock_request):
        """Test that decorator skips cache when authorization is overridden."""
        mock_view.skip_authorization = True
        result = mock_view.check_permission(mock_request)
        assert result is True

    @override_settings(DEBUG=True)
    def test_decorator_skip_cache_in_debug(self, mock_view, mock_request):
        """Test that decorator skips cache in DEBUG mode."""
        result = mock_view.check_permission(mock_request)
        assert result is True


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


@pytest.mark.django_db
class TestCachePermissionDecoratorComplete:
    """Comprehensive tests for cache_permission decorator."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model class."""

        class MockMeta:
            """Mock _meta class."""
            model_name = "testmodel"

        class MockModel:
            """Mock model class."""
            _meta = MockMeta()

        return MockModel

    @pytest.fixture
    def mock_view_class(self, mock_model):
        """Create a mock view class."""

        class MockView:
            """Mock view class."""
            model = mock_model
            skip_authorization = False
            allow_anonymous = False
            permission_result = True

            @cache_permission
            def check_permission(self, request, action="view"):
                """Test the cache_permission decorator."""
                return self.permission_result

        return MockView

    @pytest.fixture
    def authenticated_request(self):
        """Create an authenticated mock request."""

        class MockUser:
            """Mock user class."""
            id = 1
            is_authenticated = True

        class MockRequest:
            """Mock request class."""
            user = MockUser()

        return MockRequest()

    @pytest.fixture
    def anonymous_request(self):
        """Create an anonymous mock request."""

        class MockUser:
            """Mock user class."""
            is_authenticated = False

        class MockRequest:
            """Mock request class."""
            user = MockUser()

        return MockRequest()

    @pytest.mark.parametrize(
        "use_anonymous,skip_authorization,allow_anonymous",
        [
            (True, False, False),  # Anonymous user
            (False, True, False),  # skip_authorization=True
            (False, False, True),  # allow_anonymous=True
        ],
        ids=["anonymous_user", "skip_authorization", "allow_anonymous"],
    )
    def test_decorator_skips_cache(
        self,
        mock_view_class,
        authenticated_request,
        anonymous_request,
        caplog,
        use_anonymous,
        skip_authorization,
        allow_anonymous,
    ):
        """Test decorator skips cache for various skip conditions."""
        view = mock_view_class()
        view.skip_authorization = skip_authorization
        view.allow_anonymous = allow_anonymous
        request = anonymous_request if use_anonymous else authenticated_request

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(request)
        # Should call original function
        assert result is True

    def test_decorator_handles_missing_user_attribute(self, mock_view_class, caplog):
        """Test decorator handles request without user attribute."""

        class RequestWithoutUser:
            """Mock request class without user attribute."""
            pass

        view = mock_view_class()
        request = RequestWithoutUser()

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(request)
        # Should call original function even without user
        assert result is True

    def test_decorator_handles_missing_model(self, authenticated_request, caplog):
        """Test decorator handles view without model attribute."""

        class ViewWithoutModel:
            """Mock view class without model attribute."""
            skip_authorization = False
            allow_anonymous = False

            @cache_permission
            def check_permission(self, request, action="view"):
                """Test the cache_permission decorator."""
                return True

        view = ViewWithoutModel()

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(authenticated_request)
        # Should call original function
        assert result is True

    def test_decorator_handles_missing_model_meta(self, authenticated_request, caplog):
        """Test decorator handles model without _meta attribute."""

        class ModelWithoutMeta:
            """Mock model class without _meta attribute."""
            pass

        class ViewWithBadModel:
            """Mock view class with bad model."""
            model = ModelWithoutMeta()
            skip_authorization = False
            allow_anonymous = False

            @cache_permission
            def check_permission(self, request, action="view"):
                """Test the cache_permission decorator."""
                return True

        view = ViewWithBadModel()

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(authenticated_request)
        # Should call original function
        assert result is True

    def test_decorator_handles_none_user_id(self, mock_view_class, caplog):
        """Test decorator handles user with None id."""

        class MockUser:
            """Mock user class with None id."""
            id = None
            is_authenticated = True

        class MockRequest:
            """Mock request class."""
            user = MockUser()

        view = mock_view_class()
        request = MockRequest()

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(request)
        # Should call original function
        assert result is True

    def test_decorator_exception_fallback(self, mock_view_class, authenticated_request, monkeypatch, caplog):
        """Test decorator falls back to original function on exception."""
        view = mock_view_class()

        # Make permission_cache.is_enabled() raise an exception
        def mock_is_enabled():
            """Mock is_enabled that raises exception."""
            raise AttributeError("Cache check error")

        monkeypatch.setattr(permission_cache, "is_enabled", mock_is_enabled)

        with caplog.at_level(logging.DEBUG):
            result = view.check_permission(authenticated_request)
        # Original function should be called
        assert result is True


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

        # Call _make_cache_key — it should read the version key
        permission_cache_instance._make_cache_key(42, "author", "view")

        # The version key read by _make_cache_key should be the same as _get_version_key(42)
        expected_version_key = permission_cache_instance._get_version_key(42)
        assert expected_version_key in mock_cache.get_keys, (
            f"_make_cache_key should read version key '{expected_version_key}', "
            f"but it read: {mock_cache.get_keys}"
        )

    @override_settings(DEBUG=False)
    def test_invalidate_user_actually_invalidates(self, permission_cache_instance):
        """Test that invalidating a user causes a cache miss for their permissions.

        Seeds the version key first so that incr() bumps it to a new value,
        which makes _make_cache_key produce a different cache key → cache miss.
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

        # Invalidate — incr() bumps version from 1 → 2
        permission_cache_instance.invalidate_user(1)

        # After invalidation, _make_cache_key reads version=2 → different key → miss
        result = permission_cache_instance.get_permission(1, "author", "view")
        assert result is None, "Permission should be invalidated (cache miss)"
