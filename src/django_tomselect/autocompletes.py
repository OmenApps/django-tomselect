"""Views for handling queries from django-tomselect widgets."""

from typing import Any
from urllib.parse import unquote

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import FieldError, PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Model, Q, QuerySet
from django.http import JsonResponse
from django.urls import NoReverseMatch, reverse
from django.views.generic import View

from django_tomselect.cache import cache_permission, permission_cache
from django_tomselect.constants import EXCLUDEBY_VAR, FILTERBY_VAR, PAGE_VAR, SEARCH_VAR
from django_tomselect.logging import package_logger
from django_tomselect.models import EmptyModel


class AutocompleteModelView(View):
    """Base view for handling autocomplete requests.

    Intended to be flexible enough for many use cases, but can be subclassed for more specific needs.
    """

    model: type[Model] | None = None
    search_lookups: list[str] = []
    ordering: str | list[str] | tuple[str] | None = None
    page_size: int = 20
    value_fields: list[str] = []

    list_url: str | None = None  # URL name for list view
    create_url: str | None = None  # URL name for create view
    detail_url: str | None = None  # URL name for detail view
    update_url: str | None = None  # URL name for update view
    delete_url: str | None = None  # URL name for delete view

    # Permission settings
    permission_required = None  # Single permission or tuple of permissions required
    allow_anonymous = False  # Whether to allow unauthenticated users
    skip_authorization = False  # Whether to skip all permission checks

    create_field: str = ""  # The field to create a new object with. Set by the request.
    q: str = ""  # The search term. Set by the request.

    def setup(self, request, *args, **kwargs):
        """Set up the view with request parameters."""
        super().setup(request, *args, **kwargs)
        self.request = request
        self.user = getattr(request, "user", None)

        if self.model is None:
            self.model = kwargs.get("model")

            if not self.model or isinstance(self.model, EmptyModel):
                package_logger.error("Model must be specified")
                raise ValueError("Model must be specified")

            if not (isinstance(self.model, type) and issubclass(self.model, Model)):
                package_logger.error("Unknown model type specified in AutocompleteModelView")
                raise ValueError("Unknown model type specified in AutocompleteModelView")

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

        package_logger.debug("AutocompleteModelView setup complete")

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
                    package_logger.warning("Invalid filter_by value (%s)", self.filter_by)
                    return queryset.none()

                filter_dict = {dependent_field_lookup: value}
                package_logger.debug("Applying filter_by %s", filter_dict)
                queryset = queryset.filter(**filter_dict)

            if self.exclude_by:
                lookup, value = unquote(self.exclude_by).replace("'", "").split("=")
                exclude_field, exclude_field_lookup = lookup.split("__")
                if not value or not exclude_field or not exclude_field_lookup:
                    package_logger.warning("Invalid exclude_by value (%s)", self.exclude_by)
                    return queryset.none()

                exclude_dict = {exclude_field_lookup: value}
                package_logger.debug("Applying exclude_by %s", exclude_dict)
                queryset = queryset.exclude(**exclude_dict)
            return queryset
        except ValueError:
            package_logger.warning(
                "Invalid filter_by (%s) or exclude_by (%s) value",
                self.filter_by,
                self.exclude_by,
            )
        except FieldError:
            package_logger.warning(
                "Invalid lookup field in filter_by (%s) or exclude_by (%s)",
                self.filter_by,
                self.exclude_by,
            )
        return queryset.none()

    def search(self, queryset: QuerySet, query: str) -> QuerySet:
        """Apply search filtering to the queryset."""
        if not query or not self.search_lookups:
            return queryset

        q_objects = Q()
        for lookup in self.search_lookups:
            q_objects |= Q(**{lookup: query})
        package_logger.debug("Applying search query %s", q_objects)
        return queryset.filter(q_objects)

    def order_queryset(self, queryset: QuerySet) -> QuerySet:
        """Apply ordering to the queryset.

        Handles string and list/tuple ordering values correctly.
        For strings: Converts single field string to list
        For lists/tuples: Uses as-is
        If no ordering specified: Falls back to model default
        """
        ordering = self.ordering_from_request or self.ordering

        # Convert string ordering to list
        if isinstance(ordering, str):
            ordering = [ordering]
        elif isinstance(ordering, (list, tuple)):
            # Use as-is if already a sequence
            ordering = ordering
        else:
            # Fall back to model's default ordering or primary key
            ordering = self.model._meta.ordering or [self.model._meta.pk.name]

        if not ordering:
            return queryset

        package_logger.debug("Applying ordering %s", ordering)
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

        package_logger.debug("Paginating queryset with page %s of %s", page.number, paginator.num_pages)
        return pagination_context

    def get_value_fields(self) -> list[str]:
        """Get list of fields to include in values() query."""
        pk_name = self.model._meta.pk.name
        fields = [pk_name]

        if self.value_fields:
            fields.extend(self.value_fields)
        else:
            for field in self.model._meta.fields:
                if field.name in ["name", "title", "label"]:
                    fields.append(field.name)

        value_fields = list(dict.fromkeys(fields))
        package_logger.debug("Getting value fields %s", value_fields)
        return value_fields

    def prepare_results(self, results: QuerySet) -> list[dict[str, Any]]:
        """Prepare the results for JSON serialization.

        This method:
        1. Gets values for specified fields
        2. Ensures each result has an 'id' key
        3. Adds update/delete URLs if configured
        4. Calls hook_prepare_results for any custom processing

        Important: This method should not reorder results, as order is already established by order_queryset.
        """
        # Get values for specified fields
        fields = self.get_value_fields()
        values = list(results.values(*fields))

        # Ensure each result has an 'id' key
        pk_name = self.model._meta.pk.name
        for item in values:
            # Only include URLs if user has relevant permissions
            # item['can_list'] = self.has_permission(self.request, 'list')
            # item['can_create'] = self.has_permission(self.request, 'create')
            item["can_view"] = self.has_permission(self.request, "view")
            item["can_update"] = self.has_permission(self.request, "update")
            item["can_delete"] = self.has_permission(self.request, "delete")

            if "id" not in item and pk_name in item:
                item["id"] = item[pk_name]

            # Add instance-specific URLs conditionally based on permissions
            if self.detail_url and item["can_view"]:
                try:
                    item["detail_url"] = reverse(self.detail_url, args=[item["id"]])
                except NoReverseMatch:
                    package_logger.warning("Could not reverse detail_url %s", self.detail_url)

            if self.update_url and item["can_update"]:
                try:
                    item["update_url"] = reverse(self.update_url, args=[item["id"]])
                except NoReverseMatch:
                    package_logger.warning("Could not reverse update_url %s", self.update_url)

            if self.delete_url and item["can_delete"]:
                try:
                    item["delete_url"] = reverse(self.delete_url, args=[item["id"]])
                except NoReverseMatch:
                    package_logger.warning("Could not reverse delete_url %s", self.delete_url)

        return self.hook_prepare_results(values)

    def hook_prepare_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Hook method for customizing the prepared results.

        This method is called at the end of prepare_results after all standard processing
        is complete. Override this method to modify the results without losing the base
        functionality.

        Args:
            results: List of dictionaries containing the prepared results

        Returns:
            The modified results list
        """
        return results

    def get_permission_required(self):
        """Get the permissions required for this view.

        Can be overridden for dynamic permission requirements.
        """
        if self.permission_required is None:
            # Default permissions based on model and action
            perms = []
            if self.model:
                opts = self.model._meta
                perms.extend(
                    [
                        f"{opts.app_label}.list_{opts.model_name}",  # Basic list permission
                        f"{opts.app_label}.view_{opts.model_name}",  # Basic view permission
                        f"{opts.app_label}.search_{opts.model_name}",  # Optional custom search permission
                    ]
                )
                package_logger.debug("Default permissions %s", perms)
            return perms
        package_logger.debug("Custom permissions %s", self.permission_required)
        return self.permission_required

    @cache_permission
    def has_permission(self, request, action="view"):
        """Check if user has all required permissions.

        Supports custom auth backends via Django's auth system.
        """

        # Skip all checks if configured to do so
        if self.skip_authorization:
            return True

        # Allow anonymous access if configured
        if self.allow_anonymous:
            return True

        # Otherwise use standard permission checking
        if not self.user or not self.user.is_authenticated:
            return False

        # Get base permissions
        perms = self.get_permission_required()
        if not perms:  # No permissions required
            return True

        # Handle both string and iterable permission_required
        if isinstance(perms, str):
            perms = [
                perms,
            ]

        # Add action-specific permissions
        opts = self.model._meta
        if action == "create" and self.create_url:
            perms.append(f"{opts.app_label}.add_{opts.model_name}")
        elif action == "update" and self.update_url:
            perms.append(f"{opts.app_label}.change_{opts.model_name}")
        elif action == "delete" and self.delete_url:
            perms.append(f"{opts.app_label}.delete_{opts.model_name}")

        # Check permissions using auth backend
        has_perms = self.user.has_perms(perms)
        package_logger.debug("Checking permissions %s", has_perms)
        return has_perms

    def has_object_permission(self, request, obj, action="view"):
        """Check object-level permissions.

        Can be overridden for custom object-level permissions.
        """
        # Look for custom object-level permission methods
        handler = getattr(self, f"has_{action}_permission", None)
        if handler:
            package_logger.debug("Using custom object-level permission handler %s", handler)
            return handler(request, obj)
        package_logger.debug("Using default object-level permission handler")
        return True

    def has_add_permission(self, request) -> bool:
        """Check if the user has permission to add objects."""
        if not self.user.is_authenticated:
            return False

        opts = self.model._meta
        codename = f"add_{opts.model_name}"
        return self.user.has_perm(f"{opts.app_label}.{codename}")

    @classmethod
    def invalidate_permissions(cls, user=None):
        """
        Invalidate cached permissions.
        If user is provided, only invalidate that user's permissions.
        """
        if user is not None:
            permission_cache.invalidate_user(user.id)
        else:
            permission_cache.invalidate_all()
        package_logger.debug("Invalidated permissions cache")

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before dispatching request."""
        if not self.has_permission(request):
            if not self.allow_anonymous:
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self, request):
        """Handle cases where permission is denied.

        Can be overridden to customize behavior.
        """
        if not self.user.is_authenticated:
            package_logger.warning("User is not authenticated. Redirecting to login.")
            return redirect_to_login(request.get_full_path())
        raise PermissionDenied

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        package_logger.debug("Handling GET request")
        try:
            queryset = self.get_queryset()
            if self.query:
                queryset = self.search(queryset, self.query)
            data = self.paginate_queryset(queryset)
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
                status=200,
            )

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST requests."""
        package_logger.debug("Handling POST request")
        return JsonResponse({"error": "Method not allowed"}, status=405)


class AutocompleteIterablesView(View):
    """Autocomplete view for iterables and django choices classes."""

    iterable = None
    page_size: int = 20

    def setup(self, request, *args, **kwargs):
        """Set up the view with request parameters."""
        super().setup(request, *args, **kwargs)

        query = unquote(request.GET.get(SEARCH_VAR, ""))
        self.query = query if not query == "undefined" else ""
        self.page = request.GET.get(PAGE_VAR, 1)

        # Handle page size with validation
        try:
            requested_page_size = int(request.GET.get("page_size", self.page_size))
            if requested_page_size > 0:
                self.page_size = requested_page_size
        except (ValueError, TypeError):
            pass  # Keep default page_size for invalid values

    def get_iterable(self) -> list[dict[str, str | int]]:
        """Get the choices from the iterable or choices class."""
        if not self.iterable:
            package_logger.warning("No iterable provided")
            return []

        try:

            # Handle TextChoices and IntegerChoices
            if isinstance(self.iterable, type) and hasattr(self.iterable, "choices"):
                return [
                    {
                        "value": str(choice[0]),  # Convert to string to ensure consistency
                        "label": choice[1],  # Use the display label
                    }
                    for choice in self.iterable.choices
                ]

            # Handle tuple iterables
            if isinstance(self.iterable, (tuple, list)) and self.iterable and isinstance(self.iterable[0], (tuple)):
                return [
                    {
                        "value": str(item),  # Store the full tuple as a string for value
                        "label": f"{item[0]:,} - {item[1]:,} words",  # Format with commas for readability
                    }
                    for item in self.iterable
                ]

            # Handle simple iterables
            return [{"value": str(item), "label": str(item)} for item in self.iterable]
        except Exception as e:
            package_logger.error("Error getting iterable: %s", e)
            return []

    def search(self, items: list[dict[str, str]]) -> list[dict[str, str]]:
        """Apply search filtering to the items."""
        if not self.query:
            package_logger.debug("No query provided")
            return items

        query_lower = self.query.lower()
        search_results = [
            item for item in items if query_lower in item["label"].lower() or query_lower in item["value"].lower()
        ]
        package_logger.debug("Search results %s", search_results)
        return search_results

    def paginate_iterable(self, results: list[dict[str, str]]) -> dict[str, Any]:
        """Paginate the filtered results."""
        try:
            page_number = int(self.page)
            page_number = max(page_number, 1)
        except (TypeError, ValueError):
            page_number = 1  # Convert invalid values to page 1

        start_idx = (page_number - 1) * self.page_size
        end_idx = start_idx + self.page_size

        page_results = results[start_idx:end_idx]
        has_more = len(results) > end_idx

        package_logger.debug("Paginating iterable with page %s of %s", page_number, len(results))

        return {
            "results": page_results,
            "page": page_number,  # Return the corrected page number
            "has_more": has_more,
            "next_page": page_number + 1 if has_more else None,
        }

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        package_logger.debug("Handling GET request")
        if self.iterable is None:
            return JsonResponse({"results": [], "page": 1, "has_more": False})

        items = self.get_iterable()
        filtered = self.search(items)
        data = self.paginate_iterable(filtered)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST requests."""
        package_logger.debug("Handling POST request")
        return JsonResponse({"error": "Method not allowed"}, status=405)
