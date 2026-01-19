"""Request object used by the widget to obtain the initial QuerySet."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django_tomselect.constants import SEARCH_VAR

if TYPE_CHECKING:
    from django.db.models import Model


class DefaultProxyRequest:  # pylint: disable=R0903
    """Used as a stand-in for a real request when obtaining the initial QuerySet for the widget."""

    def __init__(self, *args, model: Model = None, user=None, **kwargs):  # pylint: disable=W0613
        """Initialize the DefaultProxyRequest."""
        self.model = model
        self.POST = {}  # pylint: disable=C0103
        self.GET = {
            SEARCH_VAR: "",
            "model": self.model._meta.label_lower if self.model else "",
        }  # pylint: disable=C0103
        self.method = "GET"
        self.user = user
