from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie

from django_tomselect.views import AutocompleteView


@ensure_csrf_cookie
def csrf_cookie_view(request):
    return HttpResponse()


def dummy_view(request):
    return HttpResponse()


urlpatterns = [
    path("csrf/", csrf_cookie_view, name="csrf"),
    path("dummy/url/", lambda r: HttpResponse(), name="dummy_url"),
    path("autocomplete/", AutocompleteView.as_view(), name="autocomplete"),
    path("testapp/", include("testapp.urls")),
]
