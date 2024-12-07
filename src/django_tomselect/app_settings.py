"""Settings for the django-tomselect package."""

import logging
from enum import Enum

from django.conf import settings
from django.utils.module_loading import import_string

from .configs import (
    GeneralConfig,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
)
from .request import DefaultProxyRequest

logger = logging.getLogger(__name__)


# Cache dictionary
_settings_cache = {}


def get_cached_setting(setting_name, default=None):
    """Retrieve a setting value from the cache or django.conf.settings.

    Args:
        setting_name (str): The name of the setting to retrieve.
        default: The default value to return if the setting is not found.

    Returns:
        The value of the setting.
    """
    if setting_name not in _settings_cache:
        _settings_cache[setting_name] = getattr(settings, setting_name, default)
    return _settings_cache[setting_name]


class AllowedCSSFrameworks(Enum):
    """Enum for allowed CSS frameworks."""

    DEFAULT = "default"
    BOOTSTRAP4 = "bootstrap4"
    BOOTSTRAP5 = "bootstrap5"


# Retrieve framework and version from settings
DJANGO_TOMSELECT_CSS_FRAMEWORK = get_cached_setting("TOMSELECT_CSS_FRAMEWORK", AllowedCSSFrameworks.DEFAULT.value)

if DJANGO_TOMSELECT_CSS_FRAMEWORK.lower() not in (framework.value for framework in AllowedCSSFrameworks):
    raise ValueError("CSS Framework must be one of the allowed values.")


def get_proxy_request_class():
    """Retrieve and validate the ProxyRequest class based on settings.

    Returns:
        A subclass of DefaultProxyRequest.
    """
    proxy_request_setting = get_cached_setting("TOMSELECT_PROXY_REQUEST", None)

    if proxy_request_setting is None:
        return DefaultProxyRequest

    if isinstance(proxy_request_setting, str):
        try:
            proxy_request_class = import_string(proxy_request_setting)
        except ImportError as e:
            logger.exception(
                "Could not import %s. Please check your TOMSELECT_PROXY_REQUEST setting. %s",
                proxy_request_setting,
                e,
            )
            raise ImportError(f"Failed to import TOMSELECT_PROXY_REQUEST: {e}") from e

    elif issubclass(proxy_request_setting, DefaultProxyRequest):
        proxy_request_class = proxy_request_setting
    else:
        raise TypeError(
            "TOMSELECT_PROXY_REQUEST must be a subclass of DefaultProxyRequest "
            "or an importable string pointing to such a subclass."
        )

    if not issubclass(proxy_request_class, DefaultProxyRequest):
        raise TypeError("The TOMSELECT_PROXY_REQUEST must be a subclass of DefaultProxyRequest.")

    return proxy_request_class


ProxyRequest = get_proxy_request_class()


def currently_in_production_mode():
    """Default method to determine whether to use minified files or not by checking the DEBUG setting."""
    return get_cached_setting("DEBUG", False) is False


# Should be either a boolean or a callable that returns a boolean
DJANGO_TOMSELECT_MINIFIED = get_cached_setting("TOMSELECT_MINIFIED", currently_in_production_mode())


config_defaults = {
    "TOMSELECT_GENERAL_CONFIG": GeneralConfig(),
    "TOMSELECT_PLUGIN_CLEAR_BUTTON": PluginClearButton(),
    "TOMSELECT_PLUGIN_REMOVE_BUTTON": PluginRemoveButton(),
    "TOMSELECT_PLUGIN_DROPDOWN_INPUT": PluginDropdownInput(),
    "TOMSELECT_PLUGIN_DROPDOWN_HEADER": PluginDropdownHeader(),
    "TOMSELECT_PLUGIN_DROPDOWN_FOOTER": PluginDropdownFooter(),
    "TOMSELECT_PLUGIN_CHECKBOX_OPTIONS": PluginCheckboxOptions(),
}

# Retrieve settings with defaults
DJANGO_TOMSELECT_SETTINGS = {key: get_cached_setting(key, default) for key, default in config_defaults.items()}

DJANGO_TOMSELECT_GENERAL_CONFIG = DJANGO_TOMSELECT_SETTINGS["TOMSELECT_GENERAL_CONFIG"]
DJANGO_TOMSELECT_PLUGIN_CLEAR_BUTTON = DJANGO_TOMSELECT_SETTINGS["TOMSELECT_PLUGIN_CLEAR_BUTTON"]
DJANGO_TOMSELECT_PLUGIN_REMOVE_BUTTON = DJANGO_TOMSELECT_SETTINGS["TOMSELECT_PLUGIN_REMOVE_BUTTON"]
DJANGO_TOMSELECT_PLUGIN_DROPDOWN_INPUT = DJANGO_TOMSELECT_SETTINGS["TOMSELECT_PLUGIN_DROPDOWN_INPUT"]
DJANGO_TOMSELECT_PLUGIN_DROPDOWN_HEADER = DJANGO_TOMSELECT_SETTINGS["TOMSELECT_PLUGIN_DROPDOWN_HEADER"]
DJANGO_TOMSELECT_PLUGIN_DROPDOWN_FOOTER = DJANGO_TOMSELECT_SETTINGS["TOMSELECT_PLUGIN_DROPDOWN_FOOTER"]
DJANGO_TOMSELECT_PLUGIN_CHECKBOX_OPTIONS = DJANGO_TOMSELECT_SETTINGS["TOMSELECT_PLUGIN_CHECKBOX_OPTIONS"]
