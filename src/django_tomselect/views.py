import json
import logging
from typing import List, Optional, Tuple, Union
from urllib.parse import unquote

from django import http, views
from django.contrib.auth import get_permission_codename
from django.db import models, transaction
from django.db.models import Q

logger = logging.getLogger(__name__)

SEARCH_VAR = "q"
FILTERBY_VAR = "f"
VALUES_VAR = "vs"

PAGE_VAR = "p"
PAGE_SIZE = 20


class AutocompleteView(views.generic.list.BaseListView):
    """Base list view for queries from TomSelect select elements."""

    model: models.Model = None  # Must be set by subclass
    search_lookups: List[str] = []  # Must be set by subclass
    order_by: Optional[Union[Tuple[str], List[str]]] = None  # Either None, a str, or list/tuple of str
    paginate_by: int = PAGE_SIZE
    page_kwarg: str = PAGE_VAR

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        request_data = getattr(request, request.method)

        self.create_field = request_data.get("create-field", None)

        self.values_select = []
        if VALUES_VAR in request_data:
            values = unquote(request_data[VALUES_VAR])
            self.values_select = json.loads(values)
        self.q = unquote(request_data.get(SEARCH_VAR, ""))

        if isinstance(self.order_by, str):
            self.order_by = (self.order_by,)

    def apply_filter_by(self, queryset):
        """
        Filter the given queryset against values set by other form fields.

        If the widget was set up with a `filter_by` parameter, the request will
        include the `FILTERBY_VAR` parameter, indicating that the results must
        be filtered against the lookup and value provided by `FILTERBY_VAR`.
        If `FILTERBY_VAR` is present but no value is set, return an empty
        queryset.
        """
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
        search_queryset = queryset.filter(Q(**kwargs, _connector=Q.OR))
        return search_queryset

    def order_queryset(self, queryset):
        """Order the result queryset by the provided field, or by the model's default ordering."""
        ordering = self.order_by or self.model._meta.ordering or ["id"]
        return queryset.order_by(*ordering)

    def get_queryset(self):
        """Return a queryset of objects that match the search parameters and filters."""
        queryset = super().get_queryset()
        if self.q or FILTERBY_VAR in self.request.GET:
            queryset = self.apply_filter_by(queryset)
            queryset = self.search(queryset, self.q)
        ordered_queryset = self.order_queryset(queryset)
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
