"""Tests for django_tomselect caching functionality."""

import pytest
from django.core.cache.backends.redis import RedisCache
from django.test import override_settings

from django_tomselect.app_settings import bool_or_callable
from django_tomselect.cache import PermissionCache, cache_permission


class TestPermissionCache:
    """Test the PermissionCache class functionality."""

    @pytest.fixture
    def permission_cache(self):
        """Create a fresh PermissionCache instance for each test."""
        return PermissionCache()

    @pytest.fixture
    def mock_redis_cache(self, monkeypatch):
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

        mock_cache = MockCache()
        permission_cache.cache = mock_cache

        assert permission_cache._atomic_increment("test_key") is True
        assert mock_cache.set_calls == 1
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
                raise Exception("Cache error")

            def set(self, *args, **kwargs):
                """Raise exception on set."""
                raise Exception("Cache error")

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


class TestCacheUtilityFunctions:
    """Test utility functions in the cache module."""

    def test_bool_or_callable_with_boolean(self):
        """Test bool_or_callable with boolean values."""
        assert bool_or_callable(True) is True
        assert bool_or_callable(False) is False

    def test_bool_or_callable_with_callable(self):
        """Test bool_or_callable with callable."""

        def test_func():
            return True

        assert bool_or_callable(test_func) is True

    def test_bool_or_callable_with_lambda(self):
        """Test bool_or_callable with lambda."""
        assert bool_or_callable(lambda: True) is True
        assert bool_or_callable(lambda: False) is False
