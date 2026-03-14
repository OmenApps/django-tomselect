"""Request object used by the widget to obtain the initial QuerySet."""

from __future__ import annotations

__all__ = [
    "DefaultProxyRequest",
]

from typing import TYPE_CHECKING, Any

from django_tomselect.constants import SEARCH_VAR

if TYPE_CHECKING:
    from django.db.models import Model


class DefaultProxyRequest:  # pylint: disable=R0903
    """Used as a stand-in for a real request when obtaining the initial QuerySet for the widget."""

    def __init__(  # pylint: disable=W0613
        self, *args: Any, model: type[Model] | None = None, user: Any = None, **kwargs: Any
    ) -> None:
        """Initialize the DefaultProxyRequest."""
        self.model = model
        self.POST: dict[str, Any] = {}  # pylint: disable=C0103
        self.GET: dict[str, str] = {
            SEARCH_VAR: "",
            "model": self.model._meta.label_lower if self.model else "",  # type: ignore[union-attr]
        }  # pylint: disable=C0103
        self.method = "GET"
        self.user = user
