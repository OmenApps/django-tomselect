"""Tests for django_tomselect logging functionality."""

import logging

import pytest

from django_tomselect.logging import PackageLogger, get_logger, package_logger


class TestPackageLoggerInit:
    """Tests for PackageLogger initialization."""

    def test_logger_initialization(self):
        """Test logger initializes with correct attributes."""
        logger = PackageLogger("test_logger")
        assert hasattr(logger, "_logger")
        assert hasattr(logger, "_enabled")
        assert logger._logger.name == "test_logger"

    def test_default_package_logger_exists(self):
        """Test default package_logger is created."""
        assert package_logger is not None
        assert isinstance(package_logger, PackageLogger)


class TestPackageLoggerLogMethods:
    """Tests for PackageLogger log methods."""

    @pytest.fixture
    def logger(self):
        """Create a PackageLogger instance for testing."""
        return PackageLogger("test_logger")

    @pytest.mark.parametrize(
        "method_name,level",
        [
            ("debug", logging.DEBUG),
            ("info", logging.INFO),
            ("warning", logging.WARNING),
            ("error", logging.ERROR),
            ("critical", logging.CRITICAL),
        ],
    )
    def test_log_methods_when_enabled(self, logger, caplog, method_name, level):
        """Test all log methods work when enabled."""
        logger._enabled = True
        method = getattr(logger, method_name)
        with caplog.at_level(level, logger="test_logger"):
            method("Test %s message", method_name)
        assert f"Test {method_name} message" in caplog.text

    @pytest.mark.parametrize(
        "method_name",
        ["debug", "info", "warning", "error", "critical"],
    )
    def test_log_methods_when_disabled(self, logger, caplog, method_name):
        """Test log methods do nothing when disabled."""
        logger._enabled = False
        method = getattr(logger, method_name)
        with caplog.at_level(logging.DEBUG, logger="test_logger"):
            method("Test message should not appear")
        assert "Test message should not appear" not in caplog.text

    def test_log_if_enabled_early_return(self, logger, caplog):
        """Test _log_if_enabled returns early when disabled."""
        logger._enabled = False
        with caplog.at_level(logging.DEBUG, logger="test_logger"):
            logger._log_if_enabled(logging.INFO, "Should not log")
        assert "Should not log" not in caplog.text

    def test_log_with_args(self, logger, caplog):
        """Test log methods with format arguments."""
        logger._enabled = True
        with caplog.at_level(logging.INFO, logger="test_logger"):
            logger.info("User %s performed action %s", "john", "login")
        assert "User john performed action login" in caplog.text

    def test_log_with_kwargs(self, logger, caplog):
        """Test log methods with extra kwargs."""
        logger._enabled = True
        with caplog.at_level(logging.INFO, logger="test_logger"):
            logger.info("Test message", extra={"custom": "data"})
        assert "Test message" in caplog.text


class TestPackageLoggerException:
    """Tests for PackageLogger exception method."""

    @pytest.fixture
    def logger(self):
        """Create a PackageLogger instance for testing."""
        return PackageLogger("test_logger")

    def test_exception_method_when_enabled(self, logger, caplog):
        """Test exception method logs with exception info when enabled."""
        logger._enabled = True
        try:
            raise ValueError("Test error message")
        except ValueError:
            with caplog.at_level(logging.ERROR, logger="test_logger"):
                logger.exception("Caught an exception")
        assert "Caught an exception" in caplog.text
        assert "ValueError" in caplog.text
        assert "Test error message" in caplog.text

    def test_exception_method_when_disabled(self, logger, caplog):
        """Test exception method does nothing when disabled."""
        logger._enabled = False
        try:
            raise ValueError("Test error")
        except ValueError:
            with caplog.at_level(logging.ERROR, logger="test_logger"):
                logger.exception("Should not log")
        assert "Should not log" not in caplog.text


class TestPackageLoggerEnabledProperty:
    """Tests for PackageLogger enabled property."""

    @pytest.fixture
    def logger(self):
        """Create a PackageLogger instance for testing."""
        return PackageLogger("test_logger")

    def test_enabled_property_getter_true(self, logger):
        """Test enabled property returns True correctly."""
        logger._enabled = True
        assert logger.enabled is True

    def test_enabled_property_getter_false(self, logger):
        """Test enabled property returns False correctly."""
        logger._enabled = False
        assert logger.enabled is False

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            (True, True),
            (False, False),
            (1, True),
            (0, False),
            ("truthy", True),
            ("", False),
            ([], False),
            ([1], True),
            (None, False),
        ],
    )
    def test_enabled_property_setter_converts_to_bool(self, logger, input_value, expected):
        """Test enabled property setter converts values to bool."""
        logger.enabled = input_value
        assert logger._enabled is expected


class TestPackageLoggerTemporarilyDisabled:
    """Tests for PackageLogger temporarily_disabled decorator."""

    @pytest.fixture
    def logger(self):
        """Create a PackageLogger instance for testing."""
        return PackageLogger("test_logger")

    def test_temporarily_disabled_decorator_disables_logging(self, logger, caplog):
        """Test decorator disables logging during function execution."""
        logger._enabled = True

        @logger.temporarily_disabled()
        def my_function():
            logger.info("Inside decorated function")
            return "result"

        with caplog.at_level(logging.INFO, logger="test_logger"):
            result = my_function()

        assert result == "result"
        assert "Inside decorated function" not in caplog.text

    @pytest.mark.parametrize("initial_state", [True, False], ids=["enabled", "disabled"])
    def test_temporarily_disabled_restores_state(self, logger, initial_state):
        """Test decorator restores state after function completes normally."""
        logger._enabled = initial_state

        @logger.temporarily_disabled()
        def my_function():
            return "done"

        my_function()
        assert logger._enabled is initial_state

    @pytest.mark.parametrize("initial_state", [True, False], ids=["enabled", "disabled"])
    def test_temporarily_disabled_restores_state_on_exception(self, logger, initial_state):
        """Test decorator restores state even when function raises exception."""
        logger._enabled = initial_state

        @logger.temporarily_disabled()
        def failing_function():
            raise ValueError("Intentional error")

        with pytest.raises(ValueError, match="Intentional error"):
            failing_function()

        assert logger._enabled is initial_state

    def test_temporarily_disabled_with_function_args(self, logger, caplog):
        """Test decorator works with function arguments."""
        logger._enabled = True

        @logger.temporarily_disabled()
        def add_numbers(a, b):
            logger.info("Adding numbers")
            return a + b

        with caplog.at_level(logging.INFO, logger="test_logger"):
            result = add_numbers(5, 3)

        assert result == 8
        assert "Adding numbers" not in caplog.text

    def test_temporarily_disabled_with_function_kwargs(self, logger, caplog):
        """Test decorator works with function keyword arguments."""
        logger._enabled = True

        @logger.temporarily_disabled()
        def greet(name, greeting="Hello"):
            logger.info("Greeting %s", name)
            return f"{greeting}, {name}!"

        with caplog.at_level(logging.INFO, logger="test_logger"):
            result = greet("World", greeting="Hi")

        assert result == "Hi, World!"
        assert "Greeting World" not in caplog.text

    def test_temporarily_disabled_nested_calls(self, logger, caplog):
        """Test decorator handles nested decorated functions."""
        logger._enabled = True

        @logger.temporarily_disabled()
        def outer():
            logger.info("Outer function")
            return inner()

        @logger.temporarily_disabled()
        def inner():
            logger.info("Inner function")
            return "inner result"

        with caplog.at_level(logging.INFO, logger="test_logger"):
            result = outer()

        assert result == "inner result"
        assert "Outer function" not in caplog.text
        assert "Inner function" not in caplog.text
        assert logger._enabled is True

    def test_temporarily_disabled_preserves_function_name(self, logger):
        """Test decorator preserves the original function name."""
        logger._enabled = True

        @logger.temporarily_disabled()
        def my_named_function():
            return "result"

        assert my_named_function.__name__ == "my_named_function"

    def test_temporarily_disabled_preserves_docstring(self, logger):
        """Test decorator preserves the original function docstring."""
        logger._enabled = True

        @logger.temporarily_disabled()
        def documented_function():
            """This is the docstring."""
            return "result"

        assert documented_function.__doc__ == """This is the docstring."""


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_returns_package_logger(self):
        """Test get_logger returns a PackageLogger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, PackageLogger)

    def test_get_logger_sets_correct_name(self):
        """Test get_logger creates logger with the provided name."""
        logger = get_logger("my_custom_module")
        assert logger._logger.name == "my_custom_module"

    def test_get_logger_with_dunder_name(self):
        """Test get_logger works with __name__ pattern."""
        logger = get_logger(__name__)
        assert isinstance(logger, PackageLogger)
        assert logger._logger.name == __name__

    def test_get_logger_returns_independent_instances(self):
        """Test get_logger returns new instance each call."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1 is not logger2
        assert logger1._logger.name != logger2._logger.name

    def test_get_logger_logs_to_correct_logger(self, caplog):
        """Test messages go to the correctly named logger."""
        logger = get_logger("django_tomselect.test_module")
        logger._enabled = True
        with caplog.at_level(logging.INFO, logger="django_tomselect.test_module"):
            logger.info("Test message from specific module")
        assert "Test message from specific module" in caplog.text

    def test_get_logger_hierarchy(self, caplog):
        """Test logger hierarchy works correctly."""
        child_logger = get_logger("django_tomselect.widgets")
        child_logger._enabled = True

        # Child logger messages should propagate to parent
        with caplog.at_level(logging.INFO, logger="django_tomselect"):
            child_logger.info("Child module message")

        assert "Child module message" in caplog.text
