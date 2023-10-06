import json
from urllib.parse import unquote

from django import http, views
from django.contrib.auth import get_permission_codename
from django.db import transaction
from django.db.models import Q

SEARCH_VAR = "q"
SEARCH_LOOKUP_VAR = "sl"
FILTERBY_VAR = "f"
VALUES_VAR = "vs"

PAGE_VAR = "p"
PAGE_SIZE = 20


class AutocompleteView(views.generic.list.BaseListView):
    """Base list view for queries from TomSelect select elements."""

    model = None  # Must be set by subclass
    search_lookups = []  # Must be set by subclass
    paginate_by = PAGE_SIZE
    page_kwarg = PAGE_VAR

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        request_data = getattr(request, request.method)

        self.create_field = request_data.get("create-field")

        self.values_select = []
        if VALUES_VAR in request_data:
            values = unquote(request_data[VALUES_VAR])
            self.values_select = json.loads(values)
        self.q = unquote(request_data.get(SEARCH_VAR, ""))

    def apply_filter_by(self, queryset):
        """
        Filter the given queryset against values set by other form fields.

        If the widget was set up with a `filter_by` parameter, the request will
        include the `FILTERBY_VAR` parameter, indicating that the results must
        be filtered against the lookup and value provided by `FILTERBY_VAR`.
        If `FILTERBY_VAR` is present but no value is set, return an empty
        queryset.
        """
        # print(f"apply_filter_by queryset: {queryset}")
        # print(f"apply_filter_by self.request.GET: {self.request.GET}")
        if FILTERBY_VAR not in self.request.GET:
            return queryset
        else:
            lookup, value = unquote(self.request.GET[FILTERBY_VAR]).split("=")
            if not value:
                # A filter was set up for this autocomplete, but no filter value
                # was provided; return an empty queryset.
                return queryset.none()
            return queryset.filter(**{lookup: value})

    def search(self, queryset, q):
        """Filter the result queryset against the search term."""
        kwargs = {item: q for item in self.search_lookups}
        # print(f"search queryset: {queryset}")
        # print(f"search kwargs: {kwargs}")
        # return queryset.filter(Q(**kwargs, _connector=Q.OR))
        search_queryset = queryset.filter(Q(**kwargs, _connector=Q.OR))
        # print(f"search search_queryset: {search_queryset}")
        return search_queryset

    def order_queryset(self, queryset):
        """Order the result queryset."""

        # ToDo: This is something that should be settable from the form field / widget,
        #   falling back to model meta or id if not provided
        ordering = self.model._meta.ordering or ["id"]
        return queryset.order_by(*ordering)

    def get_queryset(self):
        """Return a queryset of objects that match the search parameters and filters."""
        queryset = super().get_queryset()
        # print(f"get_queryset queryset (initial): {queryset}")
        if self.q or FILTERBY_VAR in self.request.GET:
            queryset = self.apply_filter_by(queryset)
            queryset = self.search(queryset, self.q)
        # print(f"get_queryset queryset (after filtering): {queryset}")
        # return self.order_queryset(queryset)
        ordered_queryset = self.order_queryset(queryset)
        # print(f"get_queryset ordered_queryset: {ordered_queryset}")
        return ordered_queryset

    def get_page_results(self, page):
        """Hook for modifying the result queryset for the given page."""
        return page.object_list

    def get_result_values(self, results):
        """Return a JSON-serializable list of values for the given results."""
        return list(results.values(*self.values_select))

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page_size = self.get_paginate_by(queryset)
        paginator, page, object_list, has_other_pages = self.paginate_queryset(queryset, page_size)
        data = {
            "results": self.get_result_values(self.get_page_results(page)),
            "page": page.number,
            "has_more": page.has_next(),
            "show_create_option": self.has_add_permission(request),
        }
        return http.JsonResponse(data)

    def has_add_permission(self, request):
        """Return True if the user has the permission to add a model object."""
        if not request.user.is_authenticated:
            return False

        opts = self.model._meta
        codename = get_permission_codename("add", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def create_object(self, data):
        """Create a new object with the given data."""
        return self.model.objects.create(**{self.create_field: data[self.create_field]})

    def post(self, request, *args, **kwargs):
        if not self.has_add_permission(request):
            return http.HttpResponseForbidden()
        if request.POST.get(self.create_field) is None:
            return http.HttpResponseBadRequest()
        with transaction.atomic():
            obj = self.create_object(request.POST)
        return http.JsonResponse(
            {
                "pk": obj.pk,
                "text": str(obj),
            }
        )
