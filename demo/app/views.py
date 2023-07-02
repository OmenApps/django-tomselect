from django.http import HttpResponse

from django_tomselect.views import AutocompleteView


class DemoAutocompleteView(AutocompleteView):
    def has_add_permission(self, request):
        return True  # no auth in this demo app


def listview_view(request):
    return HttpResponse("This is a dummy listview page.")


def add_view(request):
    return HttpResponse("This is a dummy add page.")
