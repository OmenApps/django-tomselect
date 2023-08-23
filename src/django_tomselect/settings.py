import logging

from django.conf import settings
from django.utils.module_loading import import_string

from .request import DefaultProxyRequest

logger = logging.getLogger(__name__)


DJANGO_TOMSELECT_BOOTSTRAP_VERSION = getattr(settings, "TOMSELECT_BOOTSTRAP_VERSION", 5)
DJANGO_TOMSELECT_PROXY_REQUEST = getattr(settings, "TOMSELECT_PROXY_REQUEST", None)

ProxyRequest = DefaultProxyRequest
if DJANGO_TOMSELECT_PROXY_REQUEST is not None and type(DJANGO_TOMSELECT_PROXY_REQUEST) == str:
    try:
        ProxyRequest = import_string(DJANGO_TOMSELECT_PROXY_REQUEST)
    except ImportError as e:
        logger.exception(
            "Could not import %s. Please check your TOMSELECT_PROXY_REQUEST setting. " + str(e),
            DJANGO_TOMSELECT_PROXY_REQUEST,
        )
elif DJANGO_TOMSELECT_PROXY_REQUEST is not None and issubclass(DJANGO_TOMSELECT_PROXY_REQUEST, DefaultProxyRequest):
    ProxyRequest = DJANGO_TOMSELECT_PROXY_REQUEST
