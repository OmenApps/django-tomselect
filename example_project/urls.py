"""URL configuration for example project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie

from django_tomselect.autocompletes import AutocompleteIterablesView, AutocompleteModelView


@ensure_csrf_cookie
def csrf_cookie_view(request):
    """View to set the CSRF cookie."""
    return HttpResponse()


def stub_view(request):
    """Stub view."""
    return HttpResponse()


urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("", include("example_project.example.urls")),
        path("csrf/", csrf_cookie_view, name="csrf"),
        path("stub/url/", lambda r: HttpResponse(), name="stub_url"),
        path(
            "autocomplete",
            AutocompleteModelView.as_view(),
            name="autocomplete-minus-slash",
        ),
        path("autocomplete/", AutocompleteModelView.as_view(), name="autocomplete"),
        path(
            "autocomplete-iterables",
            AutocompleteIterablesView.as_view(),
            name="autocomplete-iterables-minus-slash",
        ),
        path(
            "autocomplete-iterables/",
            AutocompleteIterablesView.as_view(),
            name="autocomplete-iterables",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
