"""Utility classes for lazy loading views and URLs."""

__all__ = [
    "LazyView",
]

from typing import Any

from django.contrib.auth.models import AnonymousUser, User
from django.db.models import Model, QuerySet
from django.urls import NoReverseMatch, Resolver404, resolve

from django_tomselect.app_settings import PROXY_REQUEST_CLASS
from django_tomselect.logging import get_logger
from django_tomselect.middleware import get_current_request
from django_tomselect.models import EmptyModel
from django_tomselect.utils import safe_reverse

logger = get_logger(__name__)


class LazyView:
    """Lazy view resolution to avoid circular imports."""

    def __init__(
        self, url_name: str, model: type[Model] | None = None, user: AnonymousUser | User | None = None
    ) -> None:
        """Initialize the LazyView."""
        self.url_name = url_name
        self.model = model
        self.user = user
        self._view: Any | None = None
        self._url: str | None = None

    def get_url(self) -> str:
        """Get the resolved URL, resolving it if needed."""
        if self._url is None:
            try:
                self._url = safe_reverse(self.url_name)
                logger.debug("URL resolved in LazyView: %s", self._url)
            except NoReverseMatch as e:
                logger.error("Could not reverse URL in LazyView: %s - %s", self.url_name, e)
                raise
        return self._url

    def get_view(self) -> Any | None:
        """Get the view instance, resolving it if needed."""
        url = self.get_url()
        if not url:
            logger.error("Failed to get URL for: %s", self.url_name)
            return None

        try:
            # Resolve the URL to get the view
            logger.debug("Resolving URL: %s", url)
            resolved = resolve(url)
            view_class = resolved.func.view_class
            logger.debug("View class resolved: %s", view_class)

            # Create view instance
            view_instance = view_class()

            # Explicitly copy important attributes from class to instance
            for attr in ["skip_authorization", "allow_anonymous", "permission_required"]:
                if hasattr(view_class, attr) and not hasattr(view_instance, attr):
                    logger.debug("Setting attribute %s on view instance to %s", attr, getattr(view_class, attr))
                    setattr(view_instance, attr, getattr(view_class, attr))
            logger.debug("View instance created: %s", view_instance)

            # Set up with request
            proxy_request = get_current_request()
            if proxy_request is None:
                logger.debug("No current request found, using PROXY_REQUEST_CLASS.")
                proxy_request = PROXY_REQUEST_CLASS(model=self.model, user=self.user)
            else:
                logger.debug("Using current request: %s", proxy_request)
            view_instance.setup(request=proxy_request, model=self.model)

            self._view = view_instance
            logger.debug("View instance set up: %s", self._view)
            return self._view
        except (AttributeError, TypeError, Resolver404) as e:
            logger.error("Error setting up view from URL %s: %s", url, e, exc_info=True)
            return None

    def get_queryset(self) -> QuerySet:
        """Get the queryset from the view."""
        logger.debug("Getting queryset from view: %s", self.url_name)
        view = self.get_view()
        if view and hasattr(view, "get_queryset"):
            logger.debug("Queryset found in view: %s", view.get_queryset())
            try:
                return view.get_queryset()
            except (AttributeError, TypeError) as e:
                logger.error("Error getting queryset from view: %s", e, exc_info=True)
                return EmptyModel.objects.none()
        logger.debug("No queryset found in view: %s", self.url_name)
        return EmptyModel.objects.none()

    def get_model(self) -> type[Model]:
        """Get the model from the view."""
        logger.debug("Getting model from view: %s", self.url_name)
        view = self.get_view()

        if view and hasattr(view, "model"):
            logger.debug("Model found in view: %s", view.model)
            return view.model
        logger.debug("No model found in view: %s", self.url_name)
        return EmptyModel
