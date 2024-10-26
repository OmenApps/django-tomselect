"""URL configuration for example project."""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie

from django_tomselect.views import AutocompleteView


@ensure_csrf_cookie
def csrf_cookie_view(request):
    """View to set the CSRF cookie."""
    return HttpResponse()


def stub_view(request):
    """Stub view."""
    return HttpResponse()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("csrf/", csrf_cookie_view, name="csrf"),
    path("stub/url/", lambda r: HttpResponse(), name="stub_url"),
    path("autocomplete/", AutocompleteView.as_view(), name="autocomplete"),
    path("example/", include("example_project.example.urls")),
]
