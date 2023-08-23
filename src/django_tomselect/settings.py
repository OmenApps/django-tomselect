from django.conf import settings

from .request import ProxyRequest

DJANGO_TOMSELECT_BOOTSTRAP_VERSION = getattr(settings, "TOMSELECT_BOOTSTRAP_VERSION", 5)
DJANGO_TOMSELECT_PROXY_REQUEST = getattr(settings, "TOMSELECT_PROXY_REQUEST", ProxyRequest)
