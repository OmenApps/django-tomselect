"""Utility classes for lazy loading views and URLs."""

from typing import Any, Type

from django.contrib.auth.models import AnonymousUser, User
from django.db.models import Model, QuerySet
from django.urls import NoReverseMatch, resolve, reverse

from django_tomselect.app_settings import PROXY_REQUEST_CLASS
from django_tomselect.logging import package_logger
from django_tomselect.middleware import get_current_request
from django_tomselect.models import EmptyModel


class LazyView:
    """Lazy view resolution to avoid circular imports."""

    def __init__(
        self, url_name: str, model: Type[Model] | None = None, user: AnonymousUser | User | None = None
    ) -> None:
        self.url_name = url_name
        self.model = model
        self.user = user
        self._view: Any | None = None
        self._url: str | None = None

    def get_url(self) -> str:
        """Get the resolved URL, resolving it if needed."""
        if self._url is None:
            try:
                self._url = reverse(self.url_name)
                package_logger.debug("URL resolved in LazyView: %s", self._url)
            except NoReverseMatch as e:
                package_logger.error("Could not reverse URL in LazyView: %s - %s", self.url_name, e)
                raise
        return self._url

    def get_view(self) -> Any | None:
        """Get the view instance, resolving it if needed."""
        url = self.get_url()
        if not url:
            package_logger.error("Failed to get URL for: %s", self.url_name)
            return None

        try:
            # Resolve the URL to get the view
            package_logger.debug("Resolving URL: %s", url)
            resolved = resolve(url)
            view_class = resolved.func.view_class
            package_logger.debug("View class resolved: %s", view_class)

            # Create view instance
            view_instance = view_class()

            # Explicitly copy important attributes from class to instance
            for attr in ["skip_authorization", "allow_anonymous", "permission_required"]:
                if hasattr(view_class, attr) and not hasattr(view_instance, attr):
                    package_logger.debug("Setting attribute %s on view instance to %s", attr, getattr(view_class, attr))
                    setattr(view_instance, attr, getattr(view_class, attr))
            package_logger.debug("View instance created: %s", view_instance)

            # Set up with request
            proxy_request = get_current_request()
            if proxy_request is None:
                package_logger.debug("No current request found, using PROXY_REQUEST_CLASS.")
                proxy_request = PROXY_REQUEST_CLASS(model=self.model, user=self.user)
            else:
                package_logger.debug("Using current request: %s", proxy_request)
            view_instance.setup(request=proxy_request, model=self.model)

            self._view = view_instance
            package_logger.debug("View instance set up: %s", self._view)
            return self._view
        except Exception as e:
            package_logger.error("Error setting up view from URL %s: %s", url, e)
            return None

    def get_queryset(self) -> QuerySet:
        """Get the queryset from the view."""
        package_logger.debug("Getting queryset from view: %s", self.url_name)
        view = self.get_view()
        if view and hasattr(view, "get_queryset"):
            package_logger.debug("Queryset found in view: %s", view.get_queryset())
            try:
                return view.get_queryset()
            except Exception as e:
                package_logger.error("Error getting queryset from view: %s", e)
                return EmptyModel.objects.none()
        package_logger.debug("No queryset found in view: %s", self.url_name)
        return EmptyModel.objects.none()

    def get_model(self) -> Type[Model]:
        """Get the model from the view."""
        package_logger.debug("Getting model from view: %s", self.url_name)
        view = self.get_view()

        if view and hasattr(view, "model"):
            package_logger.debug("Model found in view: %s", view.model)
            return view.model
        package_logger.debug("No model found in view: %s", self.url_name)
        return EmptyModel
