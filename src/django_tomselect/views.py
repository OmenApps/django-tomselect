"""Views for handling queries from django-tomselect widgets."""

import logging
from typing import Any, Optional
from urllib.parse import unquote

from django.core.exceptions import FieldError, PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models, transaction
from django.db.models import Q, QuerySet
from django.http import JsonResponse
from django.views.generic import View

from django_tomselect.models import EmptyModel

logger = logging.getLogger(__name__)


SEARCH_VAR = "q"
FILTERBY_VAR = "f"
EXCLUDEBY_VAR = "e"

PAGE_VAR = "p"


class AutocompleteView(View):
    """Base view for handling autocomplete requests.

    Intended to be flexible enough for many use cases, but can be subclassed for more specific needs.
    """

    model: Optional[type[models.Model]] = None
    search_lookups: list[str] = []
    ordering: Optional[str | list[str] | tuple[str]] = None
    page_size: int = 20

    create_field: str = ""  # The field to create a new object with. Set by the request.
    q: str = ""  # The search term. Set by the request.

    def setup(self, request, *args, **kwargs):
        """Set up the view with request parameters."""
        super().setup(request, *args, **kwargs)

        if self.model is None:
            self.model = kwargs.get("model")

            if not self.model or isinstance(self.model, EmptyModel):
                logger.error("Model must be specified")
                raise ValueError("Model must be specified")

            if not (isinstance(self.model, type) and issubclass(self.model, models.Model)):
                logger.error("Unknown model type specified in AutocompleteView")
                raise ValueError("Unknown model type specified in AutocompleteView")

            kwargs.pop("model", None)

        query = unquote(request.GET.get(SEARCH_VAR, ""))
        self.query = query if not query == "undefined" else ""
        self.page = request.GET.get(PAGE_VAR, 1)

        self.filter_by = request.GET.get(FILTERBY_VAR, None)
        self.exclude_by = request.GET.get(EXCLUDEBY_VAR, None)
        self.ordering_from_request = request.GET.get("ordering", None)

        # Handle page size with validation
        try:
            requested_page_size = int(request.GET.get("page_size", self.page_size))
            if requested_page_size > 0:
                self.page_size = requested_page_size
        except (ValueError, TypeError):
            pass  # Keep default page_size for invalid values

    def hook_queryset(self, queryset: QuerySet) -> QuerySet:
        """Hook to allow for additional queryset manipulation before filtering, searching, and ordering.

        For example, this could be used to prefetch related objects or add annotations that will later be used in
        filtering, searching, or ordering.
        """
        return queryset

    def get_queryset(self) -> QuerySet:
        """Get the base queryset for the view."""
        queryset = self.model.objects.all()

        # Allow for additional queryset manipulation
        queryset = self.hook_queryset(queryset)

        # Apply filtering
        queryset = self.apply_filters(queryset)
        queryset = self.search(queryset, self.query)

        # Apply ordering
        queryset = self.order_queryset(queryset)

        return queryset

    def apply_filters(self, queryset: QuerySet) -> QuerySet:
        """Apply additional filters to the queryset.

        The filter_by and exclude_by parameters, if provided, are expected to be in the format:
        'dependent_field__lookup_field=value'
        """
        if not self.filter_by and not self.exclude_by:
            return queryset

        try:
            if self.filter_by:
                lookup, value = unquote(self.filter_by).replace("'", "").split("=")
                dependent_field, dependent_field_lookup = lookup.split("__")
                if not value or not dependent_field or not dependent_field_lookup:
                    logger.warning("Invalid filter_by value (%s)", self.filter_by)
                    return queryset.none()

                filter_dict = {dependent_field_lookup: value}
                return queryset.filter(**filter_dict)

            if self.exclude_by:
                lookup, value = unquote(self.exclude_by).replace("'", "").split("=")
                exclude_field, exclude_field_lookup = lookup.split("__")
                if not value or not exclude_field or not exclude_field_lookup:
                    logger.warning("Invalid exclude_by value (%s)", self.exclude_by)
                    return queryset.none()

                exclude_dict = {exclude_field_lookup: value}
                return queryset.exclude(**exclude_dict)
        except ValueError:
            logger.warning("Invalid filter_by (%s) or exclude_by (%s) value", self.filter_by, self.exclude_by)
        except FieldError:
            logger.warning("Invalid lookup field in filter_by (%s) or exclude_by (%s)", self.filter_by, self.exclude_by)
        return queryset.none()

    def search(self, queryset: QuerySet, query: str) -> QuerySet:
        """Apply search filtering to the queryset."""
        if not query or not self.search_lookups:
            return queryset

        q_objects = Q()
        for lookup in self.search_lookups:
            q_objects |= Q(**{lookup: query})
        return queryset.filter(q_objects)

    def order_queryset(self, queryset: QuerySet) -> QuerySet:
        """Apply ordering to the queryset."""
        ordering = self.ordering_from_request
        if isinstance(ordering, str):
            ordering = [ordering]
        if ordering is None:
            # Use the model's default ordering or the primary key if no specific ordering is set
            ordering = self.model._meta.ordering or [self.model._meta.pk.name]

        if not ordering:
            return queryset

        return queryset.order_by(*ordering)

    def paginate_queryset(self, queryset) -> dict[str, Any]:
        """Paginate the queryset with improved page handling."""
        try:
            page_number = int(self.page)
        except (TypeError, ValueError):
            page_number = 1

        paginator = Paginator(queryset, self.page_size)

        try:
            page = paginator.page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)

        # Create pagination context with clean URL handling
        pagination_context = {
            "results": self.prepare_results(page.object_list),
            "page": page.number,
            "has_more": page.has_next(),
            # Only include next_page if there are more results
            "next_page": page.number + 1 if page.has_next() else None,
            "total_pages": paginator.num_pages,
        }

        return pagination_context

    def prepare_results(self, results: QuerySet) -> list[dict[str, Any]]:
        """Prepare the results for JSON serialization."""
        return list(results.values())

    def has_add_permission(self, request) -> bool:
        """Check if the user has permission to add objects."""
        if not request.user.is_authenticated:
            return False

        opts = self.model._meta
        codename = f"add_{opts.model_name}"
        return request.user.has_perm(f"{opts.app_label}.{codename}")

    def get_create_data(self, request) -> dict[str, Any]:
        """Get the data for creating a new object.

        Raises:
            ValueError: If create_field is empty or the field value is missing from POST data
        """
        if not self.create_field:
            raise ValueError("create_field must be specified for object creation")

        field_value = request.POST.get(self.create_field)
        if not field_value:
            raise ValueError(f"Missing value for create field '{self.create_field}'")

        return {self.create_field: field_value}

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        try:
            queryset = self.get_queryset()
            if self.query:
                queryset = self.search(queryset, self.query)
            data = self.paginate_queryset(queryset)
            data["show_create_option"] = self.has_add_permission(request)
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse(
                {
                    "error": str(e),
                    "results": [],
                    "page": 1,
                    "has_more": False,
                    "show_create_option": False,
                },
                status=200,  # Return 200 even for errors, with error info in response
            )

    @transaction.atomic
    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST requests for object creation."""
        if not self.has_add_permission(request):
            raise PermissionDenied

        try:
            data = self.get_create_data(request)
            instance = self.model.objects.create(**data)
            return JsonResponse(
                {
                    "pk": instance.pk,
                    "text": str(instance),
                }
            )
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
