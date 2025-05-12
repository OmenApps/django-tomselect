"""Views for handling queries from django-tomselect widgets."""

from typing import Any, TypeVar
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import FieldError, PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Model, Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import NoReverseMatch, reverse
from django.views.generic import View

from django_tomselect.cache import cache_permission, permission_cache
from django_tomselect.constants import EXCLUDEBY_VAR, FILTERBY_VAR, PAGE_VAR, SEARCH_VAR
from django_tomselect.logging import package_logger
from django_tomselect.models import EmptyModel
from django_tomselect.utils import safe_url, sanitize_dict

T = TypeVar("T", bound=Model)
IterableType = list[Any] | tuple[Any, ...] | dict[Any, Any] | type


class AutocompleteModelView(View):
    """Base view for handling autocomplete requests.

    Intended to be flexible enough for many use cases, but can be subclassed for more specific needs.
    """

    model: type[Model] | None = None
    search_lookups: list[str] = []
    ordering: str | list[str] | tuple[str, ...] | None = None
    page_size: int = 20
    value_fields: list[str] = []
    virtual_fields: list[str] = []

    list_url: str | None = None  # URL name for list view
    create_url: str | None = None  # URL name for create view
    detail_url: str | None = None  # URL name for detail view
    update_url: str | None = None  # URL name for update view
    delete_url: str | None = None  # URL name for delete view

    # Permission settings
    permission_required: str | list[str] | tuple[str, ...] | None = None
    allow_anonymous: bool = False  # Whether to allow unauthenticated users
    skip_authorization: bool = False  # Whether to skip all permission checks

    create_field: str = ""  # The field to create a new object with. Set by the request.

    # Instance variables
    request: HttpRequest | Any
    user: User | AnonymousUser | None
    query: str
    page: str | int
    filter_by: str | None
    exclude_by: str | None
    ordering_from_request: str | None

    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialize subclass with default value_fields if not already set."""
        # Check if the subclass has its own value_fields list
        # If not, create a new list object to avoid shared state across subclasses
        if "value_fields" not in cls.__dict__:
            # Explicitly create a new list object for each subclass
            cls.value_fields = []
        if "virtual_fields" not in cls.__dict__:
            # Explicitly create a new list object for each subclass
            cls.virtual_fields = []
        super().__init_subclass__(**kwargs)

    def setup(self, request: HttpRequest | Any, *args: Any, **kwargs: Any) -> None:
        """Set up the view with request parameters."""
        # Save class-level auth settings before calling super()
        skip_auth = getattr(self.__class__, "skip_authorization", False) or getattr(self, "skip_authorization", False)
        allow_anon = getattr(self.__class__, "allow_anonymous", False) or getattr(self, "allow_anonymous", False)

        super().setup(request, *args, **kwargs)

        self.request = request
        self.user = getattr(request, "user", None)

        # Explicitly set instance attributes from class attributes to prevent them from being overridden
        self.skip_authorization = skip_auth
        self.allow_anonymous = allow_anon

        if self.model is None:
            self.model = kwargs.get("model")

            if not self.model or isinstance(self.model, EmptyModel):
                package_logger.error("Model must be specified")
                raise ValueError("Model must be specified")

            if not (isinstance(self.model, type) and issubclass(self.model, Model)):
                package_logger.error("Unknown model type specified in %s", self.__class__.__name__)
                raise ValueError("Unknown model type specified in %s" % self.__class__.__name__)

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

        package_logger.debug("%s setup complete", self.__class__.__name__)

    def hook_queryset(self, queryset: QuerySet[T]) -> QuerySet[T]:
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

        try:
            q_objects = Q()
            for lookup in self.search_lookups:
                q_objects |= Q(**{lookup: query})
            package_logger.debug("Applying search query %s", q_objects)
            return queryset.filter(q_objects)
        except FieldError:
            package_logger.warning("Invalid search lookup field in %s", self.search_lookups)
        except Exception as e:
            package_logger.error("Error applying search query: %s", str(e))
        return queryset

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

        try:
            package_logger.debug("Applying ordering %s", ordering)
            return queryset.order_by(*ordering)
        except FieldError:
            package_logger.warning("Invalid ordering field in %s", ordering)
        except Exception as e:
            package_logger.error("Error applying ordering: %s", str(e))
        return queryset

    def paginate_queryset(self, queryset: QuerySet) -> dict[str, Any]:
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
            # Filter out virtual fields for the database query
            virtual_fields = getattr(self, "virtual_fields", [])
            real_fields = [f for f in self.value_fields if f not in virtual_fields]
            fields.extend(real_fields)
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
        3. Adds view/update/delete URLs if configured
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
            item["can_view"] = self.has_permission(self.request, "view")
            item["can_update"] = self.has_permission(self.request, "update")
            item["can_delete"] = self.has_permission(self.request, "delete")

            if "id" not in item and pk_name in item:
                item["id"] = item[pk_name]

            # Add instance-specific URLs conditionally based on permissions
            if self.detail_url and item["can_view"]:
                try:
                    item["detail_url"] = safe_url(reverse(self.detail_url, args=[item["id"]]))
                except NoReverseMatch:
                    package_logger.warning("Could not reverse detail_url %s", self.detail_url)

            if self.update_url and item["can_update"]:
                try:
                    item["update_url"] = safe_url(reverse(self.update_url, args=[item["id"]]))
                except NoReverseMatch:
                    package_logger.warning("Could not reverse update_url %s", self.update_url)

            if self.delete_url and item["can_delete"]:
                try:
                    item["delete_url"] = safe_url(reverse(self.delete_url, args=[item["id"]]))
                except NoReverseMatch:
                    package_logger.warning("Could not reverse delete_url %s", self.delete_url)

            # Sanitize all values to prevent XSS
            item = sanitize_dict(item)

        # Allow custom processing through hook
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

    def get_permission_required(self) -> list[str]:
        """Get the permissions required for this view.

        If permission_required is None, no permissions are required.
        Otherwise, use the specified permissions or fall back to model-based defaults.
        """
        if self.permission_required is None:
            return []  # No permissions required

        if isinstance(self.permission_required, str):
            return [self.permission_required]

        return list(self.permission_required) if self.permission_required else []

    @cache_permission
    def has_permission(self, request: HttpRequest | Any, action: str = "view") -> bool:
        """Check if user has all required permissions.

        Supports custom auth backends via Django's auth system.
        """
        if hasattr(request, "user"):
            self.user = request.user

        # Get directly from instance first, not from class
        skip_auth = getattr(self.__class__, "skip_authorization", False) or getattr(self, "skip_authorization", False)
        allow_anon = getattr(self.__class__, "allow_anonymous", False) or getattr(self, "allow_anonymous", False)

        # Check for authorization bypass first
        if skip_auth is True:
            package_logger.debug("Skipping authorization checks due to skip_authorization=True")
            return True

        # Then check anonymous access
        if allow_anon is True:
            package_logger.debug("Allowing anonymous access due to allow_anonymous=True")
            return True

        # Standard auth checks
        if not self.user or not self.user.is_authenticated:
            package_logger.debug("User is not authenticated in %s", self.__class__.__name__)
            return False

        # Get base permissions
        perms = self.get_permission_required()
        if not perms:  # No permissions required
            package_logger.debug("No permissions required in %s", self.__class__.__name__)
            return True

        # Handle both string and iterable permission_required
        if isinstance(perms, str):
            perms = [
                perms,
            ]

        # Add action-specific permissions
        opts = self.model._meta
        if action == "create" and getattr(self.__class__, "create_url", ""):
            perms.append(f"{opts.app_label}.add_{opts.model_name}")
        elif action == "update" and getattr(self.__class__, "update_url", ""):
            perms.append(f"{opts.app_label}.change_{opts.model_name}")
        elif action == "delete" and getattr(self.__class__, "delete_url", ""):
            perms.append(f"{opts.app_label}.delete_{opts.model_name}")

        # Check permissions using auth backend
        has_perms = self.user.has_perms(perms)
        package_logger.debug("User has permissions '%s'? %s", perms, has_perms)
        return has_perms

    def has_object_permission(self, request: HttpRequest | Any, obj: Model, action: str = "view") -> bool:
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

    def has_add_permission(self, request: HttpRequest | Any) -> bool:
        """Check if the user has permission to add objects."""
        if not self.user.is_authenticated:
            return False

        opts = self.model._meta
        codename = f"add_{opts.model_name}"
        return self.user.has_perm(f"{opts.app_label}.{codename}")

    @classmethod
    def invalidate_permissions(cls, user: User | None = None) -> None:
        """Invalidate cached permissions.

        If user is provided, only invalidate that user's permissions.
        """
        if user is not None:
            permission_cache.invalidate_user(user.id)
        else:
            permission_cache.invalidate_all()
        package_logger.debug("Invalidated permissions cache")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check permissions before dispatching request."""
        if self.has_permission(request) or self.allow_anonymous:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied("Permission denied. Cannot dispatch request. User does not have required permissions.")

    def handle_no_permission(self, request: HttpRequest) -> HttpResponse:
        """Handle cases where permission is denied.

        Can be overridden to customize behavior.
        """
        if not self.user.is_authenticated:
            package_logger.warning("User is not authenticated. Redirecting to login.")
            return redirect_to_login(request.get_full_path())
        raise PermissionDenied("Permission denied. User does not have any required permissions.")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle GET requests."""
        package_logger.debug("Handling GET request")
        try:
            queryset = self.get_queryset()
            if self.query:
                queryset = self.search(queryset, self.query)
            data = self.paginate_queryset(queryset)
            return JsonResponse(data)
        except Exception as e:
            package_logger.error("Error in autocomplete request: %s", str(e))

            # Create empty results response
            empty_response = {
                "results": [],
                "page": 1,
                "has_more": False,
                "show_create_option": False,
            }

            # Only include error details when DEBUG is True
            if settings.DEBUG:
                empty_response["error"] = str(e)

            return JsonResponse(empty_response, status=200)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle POST requests."""
        package_logger.debug("Handling POST request")
        return JsonResponse({"error": "Method not allowed"}, status=405)


class AutocompleteIterablesView(View):
    """Autocomplete view for iterables and django choices classes."""

    iterable: IterableType | None = None
    page_size: int = 20

    # Instance variables
    query: str
    page: str | int

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
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

            # Handle dictionaries
            if isinstance(self.iterable, dict):
                return [
                    {
                        "value": str(key),
                        "label": str(value),
                    }
                    for key, value in self.iterable.items()
                ]

            # Handle tuple iterables
            if isinstance(self.iterable, (tuple, list)) and isinstance(self.iterable[0], (tuple, list)):
                return [
                    {
                        "value": str(item[0]),
                        "label": str(item[1]),
                    }
                    for item in self.iterable
                ]

            # Handle simple iterables
            return [{"value": str(item), "label": str(item)} for item in self.iterable]
        except Exception as e:
            package_logger.error("Error getting iterable: %s", str(e))  # Fixed error printing format
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

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle GET requests."""
        package_logger.debug("Handling GET request")
        if self.iterable is None:
            return JsonResponse({"results": [], "page": 1, "has_more": False})

        try:
            items = self.get_iterable()
            filtered = self.search(items)
            data = self.paginate_iterable(filtered)
            return JsonResponse(data)
        except Exception as e:
            package_logger.error("Error in autocomplete iterables request: %s", str(e))

            # Create empty results response
            empty_response = {
                "results": [],
                "page": 1,
                "has_more": False,
            }

            # Only include error details when DEBUG is True
            if settings.DEBUG:
                empty_response["error"] = str(e)

            return JsonResponse(empty_response, status=200)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle POST requests."""
        package_logger.debug("Handling POST request")
        return JsonResponse({"error": "Method not allowed"}, status=405)
