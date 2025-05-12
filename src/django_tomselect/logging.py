"""Logging wrapper for django-tomselect package."""

import logging
from functools import wraps
from typing import Any, Callable


class PackageLogger:
    """A wrapper around Python's logging module for the django-tomselect package.

    This class provides a convenient way to control logging across the entire package
    through Django settings while respecting the logging level configured in
    Django's LOGGING setting.
    """

    def __init__(self, logger_name: str):
        """Initialize the logger with a specific name.

        Args:
            logger_name: The name to use for the logger, typically __name__
        """
        from django_tomselect.app_settings import LOGGING_ENABLED

        self._logger = logging.getLogger(logger_name)
        self._enabled = LOGGING_ENABLED

    def _log_if_enabled(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message if logging is enabled.

        Args:
            level: The logging level to use
            msg: The message to log
            *args: Additional positional arguments for the logger
            **kwargs: Additional keyword arguments for the logger
        """
        if self._enabled:
            self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log_if_enabled(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._log_if_enabled(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log_if_enabled(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._log_if_enabled(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._log_if_enabled(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception message."""
        if self._enabled:
            self._logger.exception(msg, *args, **kwargs)

    @property
    def enabled(self) -> bool:
        """Return whether logging is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set whether logging is enabled.

        Args:
            value: True to enable logging, False to disable
        """
        self._enabled = bool(value)

    def temporarily_disabled(self) -> Callable:
        """Decorator to temporarily disable logging for a function.

        Returns:
            A decorator that will disable logging while the decorated function runs

        Example:
            @logger.temporarily_disabled()
            def my_function():
                # Logging will be disabled here
                pass
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                original_state = self._enabled
                self._enabled = False
                try:
                    return func(*args, **kwargs)
                finally:
                    self._enabled = original_state

            return wrapper

        return decorator


# Create a default logger instance
package_logger = PackageLogger(__name__)
