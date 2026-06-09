"""Views for handling queries from django-tomselect widgets."""

from __future__ import annotations

__all__ = [
    "AutocompleteModelView",
    "AutocompleteIterablesView",
    "CompositeAutocompleteView",
    "Operator",
    "MAX_PAGE_SIZE",
]

import json
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser, User

    from django_tomselect._types import PaginatedResponse
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import FieldDoesNotExist, FieldError, ImproperlyConfigured, PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model, Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import NoReverseMatch
from django.views.generic import View

from django_tomselect.app_settings import DEFAULT_JSON_ENCODER
from django_tomselect.cache import cache_permission, permission_cache
from django_tomselect.constants import EXCLUDEBY_VAR, FILTERBY_VAR, PAGE_VAR, SEARCH_VAR
from django_tomselect.logging import get_logger
from django_tomselect.models import EmptyModel
from django_tomselect.utils import safe_reverse, safe_url, sanitize_dict

logger = get_logger(__name__)

T = TypeVar("T", bound=Model)
IterableType = list[Any] | tuple[Any, ...] | dict[Any, Any] | type

MAX_PAGE_SIZE = 200  # Maximum allowed page size to prevent DoS

# Lookups whose value is a comma-separated list on the URL side (split before use).
LIST_VALUED_LOOKUPS = frozenset({"in", "range"})


def parse_filter_string(filter_str: str) -> tuple[str, str, bool]:
    """Parse a filter/exclude URL param into ``(lookup_field, value, is_constant)``.

    Shared by both AutocompleteModelView (ORM filtering) and
    AutocompleteIterablesView (dict filtering) so the cross-view URL contract
    stays in one place. Handles field-based filters ('field__lookup=value') and
    constant filters ('__const__lookup=value'). The JS wraps params in single
    quotes, so those are stripped here (a known limitation for values that
    legitimately contain apostrophes).

    Args:
        filter_str: The raw filter string from the URL parameter.

    Returns:
        A tuple of (lookup_field, value, is_constant). ``lookup_field`` is
        everything after the first ``__`` (field form) or after ``__const__``
        (constant form).
    """
    cleaned = unquote(filter_str).replace("'", "")
    lookup, value = cleaned.split("=", 1)

    # Constant filter format: __const__lookup=value
    if lookup.startswith("__const__"):
        return (lookup[9:], value, True)  # Remove '__const__' prefix

    # Regular field filter: field__lookup=value
    _dependent_field, lookup_field = lookup.split("__", 1)
    return (lookup_field, value, False)


class JSONEncoderMixin:
    """Mixin providing custom JSON encoder support for autocomplete views."""

    json_encoder: type[json.JSONEncoder] | str | None = None  # Custom JSON encoder for responses

    def get_json_encoder(self) -> type[json.JSONEncoder] | None:
        """Get the JSON encoder to use for responses.

        Precedence:
        1. View-level `json_encoder` attribute (if set and not None)
        2. Global `DEFAULT_JSON_ENCODER` setting
        3. None (Django's default DjangoJSONEncoder will be used)

        The encoder can be specified as:
        - A class (subclass of json.JSONEncoder)
        - A dotted string path (e.g., "myapp.encoders.CustomEncoder")

        Returns:
            A JSONEncoder subclass or None.
        """
        from django.utils.module_loading import import_string

        encoder = self.json_encoder

        # If not set on the view, fall back to global setting
        if encoder is None:
            encoder = DEFAULT_JSON_ENCODER

        # If still None, return DjangoJSONEncoder. We must NOT return None here
        # because JsonResponse(encoder=None) passes cls=None to json.dumps(),
        # which uses the basic json.JSONEncoder that cannot handle UUID, Decimal,
        # datetime, etc. DjangoJSONEncoder handles all of these correctly.
        if encoder is None:
            return DjangoJSONEncoder

        # Handle dotted string path
        if isinstance(encoder, str):
            try:
                encoder = import_string(encoder)
            except ImportError as e:
                logger.error(
                    "Could not import JSON encoder %s: %s. Falling back to DjangoJSONEncoder.",
                    self.json_encoder,
                    e,
                )
                return DjangoJSONEncoder

        # Validate it's a proper encoder class
        if not (isinstance(encoder, type) and issubclass(encoder, json.JSONEncoder)):
            logger.error(
                "json_encoder must be a subclass of json.JSONEncoder, got %s. Falling back to DjangoJSONEncoder.",
                type(encoder),
            )
            return DjangoJSONEncoder

        return encoder


class AutocompleteModelView(JSONEncoderMixin, View):
    """Base view for handling autocomplete requests.

    Intended to be flexible enough for many use cases, but can be subclassed for more specific needs.

    Attributes:
        model: The Django model class to query for autocomplete results.

        search_lookups: List of field lookups to search against when the user types.
            Uses Django's ORM lookup syntax. Example: ['name__icontains', 'email__icontains']
            Multiple lookups are combined with OR logic.

        ordering: Field(s) to order results by. Can be a string, list, or tuple.
            Example: 'name' or ['-created', 'name']

        page_size: Number of results to return per page. Default: 20

        value_fields: List of model field names to include in the JSON response.
            These fields will be available to JavaScript for custom rendering.
            Example: ['id', 'name', 'email', 'avatar_url']

        virtual_fields: List of non-model field names that will be computed dynamically.
            Use this for calculated/derived values that don't exist on the model.
            To populate virtual fields, override `prepare_results()` or define a
            `prepare_{field_name}` method. Example: ['full_name', 'display_label']

        list_url: URL name for the list view. Rendered as a "View All" link in the dropdown
            footer when ``show_list=True`` and ``PluginDropdownFooter`` are set in the
            widget's ``TomSelectConfig``.
        create_url: URL name for the create view. Used in two contexts:
            (a) rendered as a "Create New" link in the dropdown footer when
            ``show_create=True`` and ``PluginDropdownFooter`` are set in TomSelectConfig;
            (b) used as the HTMX POST target for inline creation when ``create=True`` and
            ``create_with_htmx=True`` are set in TomSelectConfig.
            Both require this attribute to be set to a valid URL name.

        detail_url: URL name for the detail view (used for item detail links)
        update_url: URL name for the update view (used for item edit links)
        delete_url: URL name for the delete view (used for item delete links)

        permission_required: Permission string(s) required to access this view.
            Can be a single string or list/tuple of permission strings.

        allow_anonymous: If True, unauthenticated users can access this view. Default: False

        skip_authorization: If True, skip all permission checks. Default: False

        create_field: The field name used when creating new objects via the autocomplete.

    Note:
        **Filter/Exclude Syntax**

        The ``filter_by`` and ``exclude_by`` URL parameters allow dynamic filtering of results
        based on another form field's value. This is useful for dependent dropdowns.

        Format: ``'dependent_field__lookup_field=value'``

        Where:

        - ``dependent_field``: The name of the form field that triggers filtering
        - ``lookup_field``: The model field to filter on (can include lookups like ``__id``)
        - ``value``: The value to filter by (usually from the dependent field)

        Example URL parameters::

            ?filter_by=category__category_id=5  - Filter where category_id equals 5
            ?exclude_by=author__author_id=3     - Exclude where author_id equals 3

        In JavaScript/HTML, use data attributes on the widget::

            data-filter-by="category__category_id"  - Will filter by selected category
            data-exclude-by="author__author_id"     - Will exclude by selected author
    """

    model: type[Model] | None = None
    search_lookups: list[str] = []
    ordering: str | list[str] | tuple[str, ...] | None = None
    allowed_ordering_fields: list[str] | None = None
    allowed_filter_fields: list[str] | None = None
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

    create_field: str = ""  # Model field populated with the typed value during inline creation. Set by the request.

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
        """Initialize subclass with default mutable attributes if not already set.

        This prevents mutable class attributes (lists) from being shared across subclasses,
        which could cause unexpected behavior when one subclass modifies the list.
        """
        # Check if the subclass has its own list attributes
        # If not, create a new list object to avoid shared state across subclasses
        if "search_lookups" not in cls.__dict__:
            cls.search_lookups = []
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

        self.request = request  # type: ignore[assignment]
        self.user = getattr(request, "user", None)

        # Explicitly set instance attributes from class attributes to prevent them from being overridden
        self.skip_authorization = skip_auth
        self.allow_anonymous = allow_anon

        if self.model is None:
            self.model = kwargs.get("model")

            if not self.model or isinstance(self.model, EmptyModel):
                logger.error("Model must be specified")
                raise ValueError("Model must be specified")

            if not (isinstance(self.model, type) and issubclass(self.model, Model)):
                logger.error("Unknown model type specified in %s", self.__class__.__name__)
                raise ValueError("Unknown model type specified in %s" % self.__class__.__name__)

            kwargs.pop("model", None)

        query = unquote(str(request.GET.get(SEARCH_VAR, "")))
        self.query = query if not query == "undefined" else ""
        self.page = request.GET.get(PAGE_VAR, 1)  # type: ignore[assignment]

        # Support multiple filter/exclude parameters via getlist
        # Handle both QueryDict (has getlist) and regular dict (used in some test scenarios)
        filters_by: list[str]
        excludes_by: list[str]
        if hasattr(request.GET, "getlist"):
            filters_by = request.GET.getlist(FILTERBY_VAR) or []
            excludes_by = request.GET.getlist(EXCLUDEBY_VAR) or []
        else:
            # Fallback for regular dict
            filter_val = request.GET.get(FILTERBY_VAR)
            exclude_val = request.GET.get(EXCLUDEBY_VAR)
            filters_by = [str(filter_val)] if filter_val else []
            excludes_by = [str(exclude_val)] if exclude_val else []
        self.filters_by = filters_by
        self.excludes_by = excludes_by

        # Keep legacy single-value references for backwards compatibility
        self.filter_by = self.filters_by[0] if self.filters_by else None  # type: ignore[assignment]
        self.exclude_by = self.excludes_by[0] if self.excludes_by else None  # type: ignore[assignment]
        self.ordering_from_request = request.GET.get("ordering", None)  # type: ignore[assignment]

        # Track filter errors to include in response (helps with debugging)
        self._filter_error: str | None = None

        # Handle page size with validation
        try:
            requested_page_size = int(request.GET.get("page_size", self.page_size))  # type: ignore[arg-type]
            if 0 < requested_page_size <= MAX_PAGE_SIZE:
                self.page_size = requested_page_size
            elif requested_page_size > MAX_PAGE_SIZE:
                self.page_size = MAX_PAGE_SIZE
                logger.debug(
                    "Requested page_size %d exceeded maximum, clamped to %d", requested_page_size, MAX_PAGE_SIZE
                )
        except (ValueError, TypeError):
            pass  # Keep default page_size for invalid values

        self._validate_value_fields()

        logger.debug("%s setup complete", self.__class__.__name__)

    def _validate_value_fields(self) -> None:
        """Check value_fields for non-database columns and auto-mitigate.

        Fields that are not concrete database columns (properties, annotations, non-existent)
        are automatically moved to virtual_fields so they are excluded from .values() queries.
        """
        if not self.value_fields or not self.model:
            return

        non_concrete = []
        for field_path in self.value_fields:
            if "__" in field_path:
                continue  # FK lookups are resolved by Django ORM
            try:
                field_obj = self.model._meta.get_field(field_path)  # type: ignore[union-attr]
                if not getattr(field_obj, "concrete", True):
                    non_concrete.append(field_path)
            except FieldDoesNotExist:
                non_concrete.append(field_path)

        current_virtual = list(getattr(self, "virtual_fields", []))
        unhandled_non_concrete = [field_name for field_name in non_concrete if field_name not in current_virtual]

        if unhandled_non_concrete:
            logger.warning(
                "%s: value_fields %s are not concrete database columns on %s. "
                "These will be automatically excluded from .values() queries. "
                "Consider adding them to virtual_fields and populating them "
                "in prepare_results() or hook_prepare_results().",
                self.__class__.__name__,
                unhandled_non_concrete,
                self.model.__name__,
            )
            # Auto-mitigate: add to virtual_fields so get_value_fields() excludes them
            for field_name in unhandled_non_concrete:
                if field_name not in current_virtual:
                    current_virtual.append(field_name)
            self.virtual_fields = current_virtual

    def hook_queryset(self, queryset: QuerySet[T]) -> QuerySet[T]:
        """Hook to allow for additional queryset manipulation before filtering, searching, and ordering.

        For example, this could be used to prefetch related objects or add annotations that will later be used in
        filtering, searching, or ordering.
        """
        return queryset

    def get_queryset(self) -> QuerySet:
        """Get the base queryset for the view."""
        if self.model is None:
            raise ImproperlyConfigured(f"{self.__class__.__name__} requires a 'model' attribute.")
        queryset = self.model.objects.all()  # type: ignore[union-attr]

        # Allow for additional queryset manipulation
        queryset = self.hook_queryset(queryset)

        # Apply filtering
        queryset = self.apply_filters(queryset)
        queryset = self.search(queryset, self.query)

        # Apply ordering
        queryset = self.order_queryset(queryset)

        return queryset

    def _validate_filter_field(self, field_lookup: str) -> bool:
        """Validate that a filter field lookup path exists on the model."""
        if not self.model:
            return False

        # Define common Django ORM lookup types to skip in validation
        lookup_types = {
            "exact",
            "iexact",
            "contains",
            "icontains",
            "in",
            "gt",
            "gte",
            "lt",
            "lte",
            "startswith",
            "istartswith",
            "endswith",
            "iendswith",
            "range",
            "date",
            "year",
            "month",
            "day",
            "week",
            "week_day",
            "quarter",
            "time",
            "hour",
            "minute",
            "second",
            "isnull",
            "regex",
            "iregex",
            "search",
        }

        parts = field_lookup.split("__")
        model = self.model

        for i, part in enumerate(parts):
            # If this is the last part and it's a lookup type, skip validation
            if i == len(parts) - 1 and part.lower() in lookup_types:
                break
            try:
                field = model._meta.get_field(part)  # type: ignore[union-attr]
                # Follow foreign key / related field chain
                if hasattr(field, "related_model") and field.related_model:
                    model = field.related_model
            except FieldDoesNotExist:
                return False
        return True

    # Django lookup names whose value is expected to be an iterable.
    _LIST_VALUED_LOOKUPS = frozenset({"in", "range"})

    def _lookup_expects_list(self, lookup_field: str) -> bool:
        """Return True if the lookup ends in a list-valued operator (``__in``/``__range``)."""
        suffix = lookup_field.rsplit("__", 1)[-1].lower()
        return suffix in self._LIST_VALUED_LOOKUPS

    def _parse_filter_string(self, filter_str: str) -> tuple[str, str, bool]:
        """Parse a filter string into lookup field and value.

        Handles both field-based filters ('field__lookup=value') and
        constant filters ('__const__lookup=value').

        Args:
            filter_str: The raw filter string from the URL parameter.

        Returns:
            A tuple of (lookup_field, value, is_constant).
        """
        return parse_filter_string(filter_str)

    def _apply_single_filter(self, queryset: QuerySet, filter_str: str, is_exclude: bool = False) -> QuerySet | None:
        """Apply a single filter or exclude to the queryset.

        Args:
            queryset: The queryset to filter.
            filter_str: The filter string in format 'field__lookup=value' or '__const__lookup=value'.
            is_exclude: If True, exclude instead of filter.

        Returns:
            The filtered queryset, or None if there was an error (queryset.none() should be used).
        """
        try:
            lookup_field, value, is_constant = self._parse_filter_string(filter_str)

            if not value or not value.strip() or not lookup_field:
                action = "exclude_by" if is_exclude else "filter_by"
                self._filter_error = f"Invalid {action} format: {filter_str}"
                logger.warning("Invalid %s value (%s)", action, filter_str)
                return None

            # Validate filter field against allowlist if configured
            if self.allowed_filter_fields is not None:
                base_field = lookup_field.split("__")[0]
                if base_field not in self.allowed_filter_fields:
                    action = "exclude" if is_exclude else "filter"
                    self._filter_error = f"Field {base_field!r} not in allowed_{action}_fields"
                    logger.warning(
                        "Filter field '%s' not in allowed_filter_fields",
                        base_field,
                    )
                    return None

            # Validate that the filter field exists on the model
            if not self._validate_filter_field(lookup_field):
                action = "exclude" if is_exclude else "filter"
                self._filter_error = f"Invalid {action} field: {lookup_field}"
                logger.warning(
                    "Invalid %s field '%s' - field does not exist on model %s",
                    action,
                    lookup_field,
                    self.model.__name__ if self.model else "Unknown",
                )
                return None

            # Lookups whose value is expected to be an iterable (list/tuple) on
            # the Django side. The URL param carries a comma-separated string,
            # so split it here before handing it to ``filter()``.
            if self._lookup_expects_list(lookup_field):
                filter_value: list[str] | str = [v for v in value.split(",") if v != ""]
            else:
                filter_value = value

            filter_dict = {lookup_field: filter_value}
            if is_exclude:
                logger.debug("Applying exclude_by %s (constant=%s)", filter_dict, is_constant)
                return queryset.exclude(**filter_dict)
            else:
                logger.debug("Applying filter_by %s (constant=%s)", filter_dict, is_constant)
                return queryset.filter(**filter_dict)

        except ValueError as e:
            action = "exclude_by" if is_exclude else "filter_by"
            self._filter_error = f"Invalid {action} syntax: {e}"
            logger.error(
                "Invalid %s syntax in %s: %s. "
                "Expected format: 'dependent_field__lookup_field=value' or '__const__lookup=value'. Error: %s",
                action,
                self.__class__.__name__,
                filter_str,
                str(e),
            )
            return None

    def _apply_filter_list(self, queryset: QuerySet, filter_strings: list, is_exclude: bool = False) -> QuerySet | None:
        """Apply a list of filter/exclude strings to the queryset.

        Args:
            queryset: The queryset to filter.
            filter_strings: List of filter strings to apply.
            is_exclude: If True, apply as excludes instead of filters.

        Returns:
            The filtered queryset, or None if any filter returned an empty result.
        """
        for filter_str in filter_strings:
            if not isinstance(filter_str, str):
                continue
            result = self._apply_single_filter(queryset, filter_str, is_exclude=is_exclude)
            if result is None:
                return None
            queryset = result
        return queryset

    def apply_filters(self, queryset: QuerySet) -> QuerySet:
        """Apply additional filters to the queryset.

        Supports multiple filter_by and exclude_by parameters. Each parameter can be in one of:
        - Field filter: 'dependent_field__lookup_field=value'
        - Constant filter: '__const__lookup_field=value'

        Multiple filters are combined with AND logic.
        """
        # Get effective filter lists - support both direct assignment and setup() initialized
        filters_by = getattr(self, "filters_by", []) or []
        excludes_by = getattr(self, "excludes_by", []) or []

        # Also handle direct assignment of filter_by/exclude_by for backwards compatibility
        # (used in some tests that set these directly)
        if not filters_by and getattr(self, "filter_by", None):
            filters_by = [self.filter_by]
        if not excludes_by and getattr(self, "exclude_by", None):
            excludes_by = [self.exclude_by]

        if not filters_by and not excludes_by:
            return queryset

        try:
            result = self._apply_filter_list(queryset, filters_by, is_exclude=False)
            if result is None:
                return queryset.none()
            queryset = result

            result = self._apply_filter_list(queryset, excludes_by, is_exclude=True)
            if result is None:
                return queryset.none()

            return result

        except FieldError as e:
            self._filter_error = f"Invalid lookup field: {e}"
            logger.error(
                "Invalid lookup field in %s (model=%s): filters_by=%s, excludes_by=%s. "
                "The specified field may not exist on the model. Error: %s",
                self.__class__.__name__,
                self.model.__name__ if self.model else "Unknown",
                filters_by,
                excludes_by,
                str(e),
            )
            return queryset.none()

    # Opt-in: when True, search() splits the query on whitespace using a
    # quote-aware tokenizer. Each term is OR'd across `search_lookups`; terms
    # are AND-composed. Quoted phrases (e.g. `"foo bar"`) stay as a single
    # term. Default False preserves existing behavior verbatim.
    split_search: bool = False

    def _split_search_terms(self, query: str) -> list[str]:
        """Tokenize ``query`` for split_search, falling back to single-term."""
        from django_tomselect._tokenize import TokenizeError, tokenize

        try:
            segments = tokenize(query)
        except TokenizeError as exc:
            logger.debug("split_search tokenize failure for %r: %s", query, exc)
            return [query]
        terms = [seg.text for seg in segments if seg.text]
        return terms or [query]

    def _build_split_search_q(self, terms: list[str]) -> Q:
        """AND-compose per-term OR-across-lookups Q objects."""
        q_total = Q()
        first = True
        for term in terms:
            term_q = Q()
            for lookup in self.search_lookups:
                term_q = term_q | Q(**{lookup: term})  # type: ignore[misc]
            q_total = term_q if first else q_total & term_q
            first = False
        return q_total

    def _build_simple_search_q(self, query: str) -> Q:
        """OR-compose ``search_lookups`` against the whole query."""
        q_objects = Q()
        for lookup in self.search_lookups:
            q_objects = q_objects | Q(**{lookup: query})  # type: ignore[misc]
        return q_objects

    def search(self, queryset: QuerySet, query: str) -> QuerySet:
        """Apply search filtering to the queryset.

        With ``split_search=False`` (default) the entire ``query`` is OR'd
        across ``search_lookups`` as a single icontains.

        With ``split_search=True`` the query is whitespace-split via the shared
        quote-aware tokenizer (:mod:`django_tomselect._tokenize`); each term
        is OR'd across ``search_lookups`` and the per-term Qs are ANDed
        together. Quoted phrases remain single terms.
        """
        if not query or not self.search_lookups:
            return queryset

        try:
            if self.split_search:
                q_total = self._build_split_search_q(self._split_search_terms(query))
                logger.debug("Applying split search query %s", q_total)
            else:
                q_total = self._build_simple_search_q(query)
                logger.debug("Applying search query %s", q_total)
            return queryset.filter(q_total)
        except FieldError:
            logger.warning("Invalid search lookup field in %s", self.search_lookups)
        except Exception as e:
            logger.error("Error applying search query: %s", str(e))
        return queryset

    def order_queryset(self, queryset: QuerySet) -> QuerySet:
        """Apply ordering to the queryset.

        Handles string and list/tuple ordering values correctly.
        For strings: Converts single field string to list
        For lists/tuples: Uses as-is
        If no ordering specified: Falls back to model default
        """
        ordering = self.ordering_from_request or self.ordering

        # Validate ordering from request against allowlist
        if self.ordering_from_request and self.allowed_ordering_fields is not None:
            bare_field = self.ordering_from_request.lstrip("-")
            if bare_field not in self.allowed_ordering_fields:
                logger.warning(
                    "Ordering field '%s' not in allowed_ordering_fields, falling back to default ordering",
                    self.ordering_from_request,
                )
                ordering = self.ordering

        # Convert string ordering to list
        if isinstance(ordering, str):
            ordering = [ordering]
        elif isinstance(ordering, (list, tuple)):
            # Use as-is if already a sequence
            ordering = ordering
        else:
            # Fall back to model's default ordering or primary key
            if self.model is None:
                raise ImproperlyConfigured(f"{self.__class__.__name__} requires a 'model' attribute.")
            pk = self.model._meta.pk  # type: ignore[union-attr]
            ordering = self.model._meta.ordering or ([pk.name] if pk else ["pk"])  # type: ignore[union-attr]

        if not ordering:
            return queryset

        try:
            logger.debug("Applying ordering %s", ordering)
            return queryset.order_by(*ordering)
        except FieldError:
            logger.warning("Invalid ordering field in %s", ordering)
        except Exception as e:
            logger.error("Error applying ordering: %s", str(e))
        return queryset

    def paginate_queryset(self, queryset: QuerySet) -> PaginatedResponse:
        """Paginate the queryset with improved page handling."""
        try:
            page_number = int(self.page)
            page_number = max(1, page_number)  # Ensure positive
        except (TypeError, ValueError):
            page_number = 1

        paginator = Paginator(queryset, self.page_size)

        try:
            page = paginator.page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)

        # Create pagination context with clean URL handling
        page_num = int(page.number)
        has_more = bool(page.has_next())
        pagination_context: dict[str, Any] = {
            "results": self.prepare_results(page.object_list),  # type: ignore[arg-type]
            "page": page_num,
            "has_more": has_more,
            # Only include next_page if there are more results
            "next_page": page_num + 1 if has_more else None,
            "total_pages": int(paginator.num_pages),  # type: ignore[arg-type]
        }

        logger.debug("Paginating queryset with page %s of %s", page_num, paginator.num_pages)
        return cast("PaginatedResponse", pagination_context)

    def get_value_fields(self) -> list[str]:
        """Get list of fields to include in values() query."""
        if self.model is None:
            raise ImproperlyConfigured(f"{self.__class__.__name__} requires a 'model' attribute.")
        pk = self.model._meta.pk  # type: ignore[union-attr]
        pk_name = pk.name if pk else "pk"
        fields = [pk_name]

        if self.value_fields:
            # Filter out virtual fields for the database query
            virtual_fields = getattr(self, "virtual_fields", [])
            real_fields = [f for f in self.value_fields if f not in virtual_fields]
            fields.extend(real_fields)
        else:
            for field in self.model._meta.fields:  # type: ignore[union-attr]
                if field.name in ["name", "title", "label"]:
                    fields.append(field.name)

        value_fields = list(dict.fromkeys(fields))
        logger.debug("Getting value fields %s", value_fields)
        return value_fields

    def _add_action_url(self, item: dict[str, Any], url_name: str, url_key: str) -> None:
        """Resolve one action URL and set it on the item dict.

        Args:
            item: The result dict to add the URL to.
            url_name: The URL pattern name to reverse.
            url_key: The key to set on the item dict (e.g. "detail_url").
        """
        try:
            item[url_key] = safe_url(safe_reverse(url_name, args=[item["id"]]))
        except NoReverseMatch:
            logger.warning("Could not reverse %s %s", url_key, url_name)

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

        # Re-include virtual_fields that are actually queryset annotations
        # (e.g. fields added via hook_queryset). These are valid for .values()
        # even though they aren't concrete model columns.
        virtual_fields = getattr(self, "virtual_fields", [])
        if virtual_fields and hasattr(results, "query"):
            annotations = getattr(results.query, "annotations", {})
            for vf in virtual_fields:
                if vf in annotations and vf not in fields:
                    fields.append(vf)

        values = list(results.values(*fields))

        # Pre-compute model-level permissions once before the loop
        can_view = self.has_permission(self.request, "view")
        can_update = self.has_permission(self.request, "update")
        can_delete = self.has_permission(self.request, "delete")

        # Ensure each result has an 'id' key
        if self.model is None:
            raise ImproperlyConfigured(f"{self.__class__.__name__} requires a 'model' attribute.")
        pk = self.model._meta.pk  # type: ignore[union-attr]
        pk_name = pk.name if pk else "pk"
        for i, item in enumerate(values):
            item["can_view"] = can_view
            item["can_update"] = can_update
            item["can_delete"] = can_delete

            if "id" not in item and pk_name in item:
                item["id"] = item[pk_name]

            # Add instance-specific URLs conditionally based on permissions
            if self.detail_url and can_view:
                self._add_action_url(item, self.detail_url, "detail_url")
            if self.update_url and can_update:
                self._add_action_url(item, self.update_url, "update_url")
            if self.delete_url and can_delete:
                self._add_action_url(item, self.delete_url, "delete_url")

            # Sanitize all values to prevent XSS
            # sanitize_dict returns a new dict, so we must update the list
            values[i] = sanitize_dict(item)

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
            self.user = request.user  # type: ignore[has-type]

        # Get directly from instance first, not from class
        skip_auth = getattr(self.__class__, "skip_authorization", False) or getattr(self, "skip_authorization", False)
        allow_anon = getattr(self.__class__, "allow_anonymous", False) or getattr(self, "allow_anonymous", False)

        # Check for authorization bypass first
        if skip_auth is True:
            logger.debug("Skipping authorization checks due to skip_authorization=True")
            return True

        # Then check anonymous access
        if allow_anon is True:
            logger.debug("Allowing anonymous access due to allow_anonymous=True")
            return True

        # Standard auth checks
        if self.user is None or not self.user.is_authenticated:
            logger.debug("User is not authenticated in %s", self.__class__.__name__)
            return False

        # Get base permissions
        perms: list[str] = list(self.get_permission_required())
        if not perms:  # No permissions required
            logger.debug("No permissions required in %s", self.__class__.__name__)
            return True

        # Add action-specific permissions
        if self.model is not None:
            opts = self.model._meta  # type: ignore[union-attr]
            if action == "create" and getattr(self.__class__, "create_url", ""):
                perms.append(f"{opts.app_label}.add_{opts.model_name}")
            elif action == "update" and getattr(self.__class__, "update_url", ""):
                perms.append(f"{opts.app_label}.change_{opts.model_name}")
            elif action == "delete" and getattr(self.__class__, "delete_url", ""):
                perms.append(f"{opts.app_label}.delete_{opts.model_name}")

        # Check permissions using auth backend
        has_perms = self.user.has_perms(perms)
        logger.debug("User has permissions '%s'? %s", perms, has_perms)
        return has_perms

    def has_object_permission(self, request: HttpRequest | Any, obj: Model, action: str = "view") -> bool:
        """Check object-level permissions.

        Can be overridden for custom object-level permissions.
        """
        # Look for custom object-level permission methods
        handler = getattr(self, f"has_{action}_permission", None)
        if handler:
            logger.debug("Using custom object-level permission handler %s", handler)
            return handler(request, obj)
        logger.debug("Using default object-level permission handler")
        return True

    def has_add_permission(self, request: HttpRequest | Any) -> bool:
        """Check if the user has permission to add objects."""
        if self.user is None or not self.user.is_authenticated:
            return False

        if self.model is None:
            raise ImproperlyConfigured(f"{self.__class__.__name__} requires a 'model' attribute.")
        opts = self.model._meta  # type: ignore[union-attr]
        codename = f"add_{opts.model_name}"
        return self.user.has_perm(f"{opts.app_label}.{codename}")

    @classmethod
    def invalidate_permissions(cls, user: User | None = None) -> None:
        """Invalidate cached permissions.

        If user is provided, only invalidate that user's permissions.
        """
        if user is not None:
            permission_cache.invalidate_user(user.id)  # type: ignore[attr-defined]
        else:
            permission_cache.invalidate_all()
        logger.debug("Invalidated permissions cache")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check permissions before dispatching request."""
        if self.has_permission(request):
            return super().dispatch(request, *args, **kwargs)  # type: ignore[return-value]
        return self.handle_no_permission(request)

    def handle_no_permission(self, request: HttpRequest) -> HttpResponse:
        """Handle cases where permission is denied.

        Can be overridden to customize behavior.
        """
        if self.user is None or not self.user.is_authenticated:
            logger.warning("User is not authenticated. Redirecting to login.")
            return redirect_to_login(request.get_full_path())
        raise PermissionDenied("Permission denied. User does not have any required permissions.")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle GET requests."""
        logger.debug("Handling GET request")
        try:
            queryset = self.get_queryset()  # Already includes search() via get_queryset -> search
            data: dict[str, Any] = dict(self.paginate_queryset(queryset))

            # Include filter error in response if one occurred (helps with debugging)
            if self._filter_error:
                logger.debug("Filter error occurred: %s", self._filter_error)
                if settings.DEBUG:
                    data["filter_error"] = self._filter_error

            return JsonResponse(data, encoder=self.get_json_encoder())  # type: ignore[arg-type]
        except Exception:
            logger.exception("Error in autocomplete request")

            # Create empty results response
            empty_response: dict[str, Any] = {
                "results": [],
                "page": 1,
                "has_more": False,
                "show_create_option": False,
            }

            # Only include error details when DEBUG is True
            if settings.DEBUG:
                import traceback

                empty_response["error"] = traceback.format_exc()

            return JsonResponse(empty_response, status=500, encoder=self.get_json_encoder())  # type: ignore[arg-type]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle POST requests."""
        logger.debug("Handling POST request")
        return JsonResponse({"error": "Method not allowed"}, status=405, encoder=self.get_json_encoder())  # type: ignore[arg-type]


class AutocompleteIterablesView(JSONEncoderMixin, View):
    """Autocomplete view for iterables and django choices classes."""

    iterable: IterableType | None = None
    page_size: int = 20

    # Only these item keys can be targeted by filter_by/exclude_by, since an
    # iterable item is just {"value", "label"} with no ORM behind it. Strict
    # allowlist: any other base key fails closed (empty results).
    _FILTERABLE_KEYS = frozenset({"value", "label"})

    # Instance variables
    query: str
    page: str | int

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        """Set up the view with request parameters."""
        super().setup(request, *args, **kwargs)

        query = unquote(str(request.GET.get(SEARCH_VAR, "")))
        self.query = query if not query == "undefined" else ""
        self.page = request.GET.get(PAGE_VAR, 1)  # type: ignore[assignment]

        # filter_by / exclude_by params (mirror AutocompleteModelView.setup).
        # Multiple values combine: filters AND, excludes drop the union.
        # Handle both QueryDict (has getlist) and plain dict (proxy requests from
        # lazy_utils and some test scenarios).
        if hasattr(request.GET, "getlist"):
            self.filters_by = request.GET.getlist(FILTERBY_VAR) or []
            self.excludes_by = request.GET.getlist(EXCLUDEBY_VAR) or []
        else:
            filter_val = request.GET.get(FILTERBY_VAR)
            exclude_val = request.GET.get(EXCLUDEBY_VAR)
            self.filters_by = [str(filter_val)] if filter_val else []
            self.excludes_by = [str(exclude_val)] if exclude_val else []

        # Handle page size with validation
        try:
            requested_page_size = int(request.GET.get("page_size", self.page_size))  # type: ignore[arg-type]
            if 0 < requested_page_size <= MAX_PAGE_SIZE:
                self.page_size = requested_page_size
            elif requested_page_size > MAX_PAGE_SIZE:
                self.page_size = MAX_PAGE_SIZE
                logger.debug(
                    "Requested page_size %d exceeded maximum, clamped to %d", requested_page_size, MAX_PAGE_SIZE
                )
        except (ValueError, TypeError):
            pass  # Keep default page_size for invalid values

    def get_iterable(self) -> list[dict[str, str | int]]:
        """Get the choices from the iterable or choices class."""
        if not self.iterable:
            logger.warning("No iterable provided")
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
            if isinstance(self.iterable, (list, tuple)):
                return [{"value": str(item), "label": str(item)} for item in self.iterable]

            return []
        except Exception as e:
            logger.error("Error getting iterable: %s", str(e))  # Fixed error printing format
            return []

    def search(self, items: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
        """Apply search filtering to the items."""
        if not self.query:
            logger.debug("No query provided")
            return items

        query_lower = self.query.lower()
        search_results = [
            item
            for item in items
            if (query_lower in str(item["label"]).lower() or query_lower in str(item["value"]).lower())
        ]
        logger.debug("Search results %s", search_results)
        return search_results

    def _matches(self, item: dict[str, str | int], lookup_field: str, value: str) -> bool | None:
        """Return whether ``item`` satisfies ``lookup_field``/``value``.

        ``lookup_field`` is ``<key>`` or ``<key>__<op>`` where ``<key>`` must be
        ``value`` or ``label`` and ``<op>`` is a supported string lookup
        (default ``exact``). Returns ``None`` to signal an invalid/unsupported
        config (bad key, unknown op, or empty value), which the caller treats as
        fail-closed.
        """
        parts = lookup_field.split("__", 1)
        key = parts[0]
        op = parts[1] if len(parts) == 2 else "exact"

        if key not in self._FILTERABLE_KEYS:
            logger.warning("Invalid iterable filter key %r (allowed: value, label)", key)
            return None

        item_value = str(item[key])

        if op == "in":
            tokens = [v for v in value.split(",") if v.strip() != ""]
            if not tokens:
                return None  # e.g. ``value__in=,`` or whitespace-only -> fail closed
            return item_value in tokens

        if not value.strip():
            return None  # empty/whitespace value on a scalar lookup -> fail closed

        candidate, target = item_value, value
        if op in {"iexact", "icontains", "istartswith", "iendswith"}:
            candidate, target = candidate.lower(), target.lower()

        comparisons = {
            "exact": lambda: candidate == target,
            "iexact": lambda: candidate == target,
            "contains": lambda: target in candidate,
            "icontains": lambda: target in candidate,
            "startswith": lambda: candidate.startswith(target),
            "istartswith": lambda: candidate.startswith(target),
            "endswith": lambda: candidate.endswith(target),
            "iendswith": lambda: candidate.endswith(target),
        }
        compare = comparisons.get(op)
        if compare is None:
            logger.warning("Unsupported iterable filter lookup %r on key %r", op, key)
            return None
        return compare()

    def apply_filters(self, items: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
        """Apply filter_by / exclude_by params to the iterable items.

        Mirrors AutocompleteModelView.apply_filters semantics for non-ORM items:

        - filter_by: keep items matching ALL filters (AND).
        - exclude_by: drop items matching ANY exclude (the union).
        - Invalid key, unsupported lookup, or empty value fails closed (returns
          ``[]``), matching the model view and the dependent-dropdown contract
          ("empty parent => empty dropdown").

        Supports both setup()-populated ``filters_by``/``excludes_by`` lists and
        legacy direct string assignment to ``filter_by``/``exclude_by``.
        """
        filters_by = getattr(self, "filters_by", []) or []
        excludes_by = getattr(self, "excludes_by", []) or []
        if not filters_by and getattr(self, "filter_by", None):
            filters_by = [self.filter_by]
        if not excludes_by and getattr(self, "exclude_by", None):
            excludes_by = [self.exclude_by]

        if not filters_by and not excludes_by:
            return items

        results = list(items)

        for filter_str in filters_by:
            result = self._apply_one(results, filter_str, is_exclude=False)
            if result is None:
                return []  # invalid config -> fail closed
            results = result

        for exclude_str in excludes_by:
            result = self._apply_one(results, exclude_str, is_exclude=True)
            if result is None:
                return []  # invalid config -> fail closed
            results = result

        return results

    def _apply_one(
        self, items: list[dict[str, str | int]], filter_str: Any, *, is_exclude: bool
    ) -> list[dict[str, str | int]] | None:
        """Apply a single filter/exclude string. Returns the surviving items, or
        ``None`` to signal fail-closed (invalid key/op/value or unparseable param).
        """
        if not isinstance(filter_str, str):
            return items  # non-string config entry: skip, mirror model behavior
        try:
            lookup_field, value, _is_constant = parse_filter_string(filter_str)
        except ValueError:
            logger.warning("Unparseable iterable %s param: %r", "exclude_by" if is_exclude else "filter_by", filter_str)
            return None
        kept = []
        for item in items:
            match = self._matches(item, lookup_field, value)
            if match is None:
                return None
            if match != is_exclude:  # keep on filter-match; keep on exclude-miss
                kept.append(item)
        return kept

    def paginate_iterable(self, results: list[dict[str, str | int]]) -> PaginatedResponse:
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

        # Calculate total pages for virtual_scroll plugin compatibility
        total_items = len(results)
        total_pages = (total_items + self.page_size - 1) // self.page_size if total_items > 0 else 1

        logger.debug("Paginating iterable with page %s of %s", page_number, total_pages)

        result: PaginatedResponse = {
            "results": page_results,  # type: ignore[typeddict-item]
            "page": page_number,
            "has_more": has_more,
            "next_page": page_number + 1 if has_more else None,
            "total_pages": total_pages,
        }
        return result

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle GET requests."""
        logger.debug("Handling GET request")
        if self.iterable is None:
            return JsonResponse({"results": [], "page": 1, "has_more": False}, encoder=self.get_json_encoder())  # type: ignore[arg-type]

        try:
            items = self.get_iterable()
            items = self.apply_filters(items)
            filtered = self.search(items)
            data = self.paginate_iterable(filtered)
            return JsonResponse(data, encoder=self.get_json_encoder())  # type: ignore[arg-type]
        except Exception:
            logger.exception("Error in autocomplete iterables request")

            # Create empty results response
            empty_response: dict[str, Any] = {
                "results": [],
                "page": 1,
                "has_more": False,
            }

            # Only include error details when DEBUG is True
            if settings.DEBUG:
                import traceback

                empty_response["error"] = traceback.format_exc()

            return JsonResponse(empty_response, status=500, encoder=self.get_json_encoder())  # type: ignore[arg-type]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle POST requests."""
        logger.debug("Handling POST request")
        return JsonResponse({"error": "Method not allowed"}, status=405, encoder=self.get_json_encoder())  # type: ignore[arg-type]


@dataclass(frozen=True)
class Operator:
    """One token-key binding for a :class:`CompositeAutocompleteView`.

    See the ``token_widget`` docs page for the full contract. Briefly:

    - ``key``: prefix the user types before the colon (e.g. ``author``).
    - ``view``: bound autocomplete view (class reference or ``app:url-name``).
    - ``value_field`` / ``label_field``: JSON keys returned by the bound view's
      ``prepare_results()`` (model views) or ``get_iterable()`` items (iterables).
      Required, no defaults - for model views typically ``value_field="id"``
      plus a label like ``"name"``; for iterables always ``value_field="value"``,
      ``label_field="label"``.
    - ``bound_lookup``: ORM field path used in the resolve queryset filter.
      Defaults to ``value_field``. Override when ``prepare_results()`` projects
      renamed/computed keys.
    - Filtering: exactly one of ``filter_lookup`` (exact-match field path) or
      ``q_translator`` (callable returning a ``Q``) must be set.
    """

    key: str
    view: type[View] | str
    value_field: str = ""
    label_field: str = ""
    bound_lookup: str | None = None
    filter_lookup: str | list[str] | None = None
    q_translator: Callable[[Operator, list[Any]], Q] | None = None
    label: str | None = None
    multi: bool = False
    # None inherits the bound view's class-level ``search_lookups``;
    # ``[]`` deliberately disables search; non-empty list overrides.
    search_lookups: list[str] | None = None
    max_count: int | None = None
    min_count: int = 0
    # When None, auto-derived from ``q_translator``: free-form operators accept
    # user-typed values without a matching dropdown row. Set explicitly to
    # override (e.g. a q_translator op that still wants suggestion-only commits).
    free_form: bool | None = None

    def __post_init__(self) -> None:
        """Validate required fields and default ``bound_lookup`` to ``value_field``."""
        if not self.value_field:
            raise ImproperlyConfigured(f"Operator(key={self.key!r}) requires value_field.")
        if not self.label_field:
            raise ImproperlyConfigured(f"Operator(key={self.key!r}) requires label_field.")
        has_filter = self.filter_lookup is not None
        has_translator = self.q_translator is not None
        if not has_filter and not has_translator:
            raise ImproperlyConfigured(
                f"Operator(key={self.key!r}) requires filter_lookup or q_translator. "
                "These tell parse_query.apply() how to filter the parent queryset."
            )
        if has_filter and has_translator:
            raise ImproperlyConfigured(
                f"Operator(key={self.key!r}) cannot set both filter_lookup and "
                "q_translator. Pick one - q_translator is the more flexible option."
            )
        # Default bound_lookup to value_field (frozen dataclass; use object.__setattr__).
        if self.bound_lookup is None:
            object.__setattr__(self, "bound_lookup", self.value_field)
        if self.free_form is None:
            object.__setattr__(self, "free_form", has_translator)


class CompositeAutocompleteView(JSONEncoderMixin, View):
    """Multiplex multiple autocomplete views into a single token-aware endpoint.

    Three GET routes by ``mode=`` query param:

    - ``?mode=operators`` - JSON list of registered operator keys + metadata.
    - ``?mode=value&op=<key>&q=...&p=...`` - delegate to bound view's ``get()``.
    - ``?mode=resolve&op=<k>&id=<v>[&op=...&id=...]`` - batch label resolution.

    Subclass and set ``operators`` and ``free_text_lookups``.
    """

    operators: list[Operator] = []
    free_text_lookups: list[str] = []
    max_resolve_ids: int = 64

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Emit a one-time iterables-permission warning on subclass registration."""
        super().__init_subclass__(**kwargs)
        seen_iterables = False
        for op in cls.operators:
            view = op.view
            if isinstance(view, type) and issubclass(view, AutocompleteIterablesView):
                seen_iterables = True
                break
            if isinstance(view, str):
                # URL-name operator. Resolve lazily so import-order issues
                # (URLs not yet wired) don't crash subclass creation.
                try:
                    from django_tomselect.lazy_utils import resolve_view_class

                    resolved, _ = resolve_view_class(view)
                    if issubclass(resolved, AutocompleteIterablesView):
                        seen_iterables = True
                        break
                except Exception as exc:  # noqa: BLE001
                    # URL not reversible at import time. The iterables warning
                    # is best-effort; runtime resolution still works. Log at
                    # debug so users can opt in to seeing it.
                    logger.debug(
                        "%s: could not resolve operator view %r at subclass time: %s",
                        cls.__name__,
                        view,
                        exc,
                    )
        if seen_iterables:
            logger.warning(
                "%s registers operators bound to AutocompleteIterablesView. "
                "Iterables views do NOT enforce per-user permissions - labels are "
                "publicly readable. If sensitive, gate access at the form/view layer.",
                cls.__name__,
            )

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Route the request based on ``?mode=``."""
        mode = request.GET.get("mode", "operators")
        try:
            if mode == "operators":
                return self._list_operators(request)
            if mode == "value":
                return self._delegate_value(request)
            if mode == "resolve":
                return self._resolve_labels(request)
        except Exception:
            logger.exception("CompositeAutocompleteView dispatch failed for mode=%r", mode)
            return JsonResponse(
                {"error": "internal error"},
                status=500,
                encoder=self.get_json_encoder(),  # type: ignore[arg-type]
            )
        return JsonResponse(
            {"error": f"unknown mode {mode!r}"},
            status=400,
            encoder=self.get_json_encoder(),  # type: ignore[arg-type]
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Composite endpoint is GET-only."""
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
            encoder=self.get_json_encoder(),  # type: ignore[arg-type]
        )

    def _operator_for(self, key: str) -> Operator | None:
        for op in self.operators:
            if op.key == key:
                return op
        return None

    def _list_operators(self, request: HttpRequest) -> JsonResponse:
        """Return registered operator metadata for the JS plugin."""
        out = []
        for op in self.operators:
            out.append(
                {
                    "key": op.key,
                    "label": str(op.label) if op.label else op.key,
                    "multi": op.multi,
                    "value_field": op.value_field,
                    "label_field": op.label_field,
                    "max_count": op.max_count,
                    "min_count": op.min_count,
                    "free_form": bool(op.free_form),
                }
            )
        return JsonResponse(
            {"operators": out, "free_text_lookups": list(self.free_text_lookups)},
            encoder=self.get_json_encoder(),  # type: ignore[arg-type]
        )

    def _delegate_value(self, request: HttpRequest) -> JsonResponse:
        """Delegate ``mode=value`` to the operator's bound view."""
        from django_tomselect.lazy_utils import resolve_view_class

        op_key = request.GET.get("op", "")
        op = self._operator_for(op_key)
        if op is None:
            return JsonResponse(
                {"error": f"unknown operator {op_key!r}"},
                status=400,
                encoder=self.get_json_encoder(),  # type: ignore[arg-type]
            )

        view_class, view_initkwargs = resolve_view_class(op.view)

        # Apply per-operator search_lookups override via instance subclass.
        if op.search_lookups is not None:
            override = {"search_lookups": list(op.search_lookups)}
            view_class = type(
                f"_OperatorOverride_{op.key}_{view_class.__name__}",
                (view_class,),
                override,
            )

        return view_class.as_view(**view_initkwargs)(request)

    def _resolve_labels(self, request: HttpRequest) -> JsonResponse:
        """Batch-resolve labels for ``(op, id)`` pairs.

        Permission-safe: routes through the bound view's ``has_permission()``
        when available, catches ``PermissionDenied`` and generic exceptions to
        prevent label leaks. Per-operator try/except so one failing operator
        does not poison resolve for the others.
        """
        ops = request.GET.getlist("op")
        ids = request.GET.getlist("id")
        if len(ops) != len(ids):
            return JsonResponse(
                {"error": "op/id list lengths must match"},
                status=400,
                encoder=self.get_json_encoder(),  # type: ignore[arg-type]
            )
        if len(ops) > self.max_resolve_ids:
            return JsonResponse(
                {"error": f"too many resolve ids (max {self.max_resolve_ids})"},
                status=400,
                encoder=self.get_json_encoder(),  # type: ignore[arg-type]
            )

        grouped: dict[str, list[str]] = defaultdict(list)
        for op_key, id_val in zip(ops, ids, strict=False):
            grouped[op_key].append(id_val)

        out: list[dict[str, Any]] = []
        for op_key, key_ids in grouped.items():
            op = self._operator_for(op_key)
            if op is None:
                out.extend({"op": op_key, "id": i, "missing": True} for i in key_ids)
                continue
            try:
                out.extend(self._resolve_one(request, op, key_ids))
            except PermissionDenied:
                out.extend({"op": op_key, "id": i, "missing": True} for i in key_ids)
            except Exception:
                logger.exception("Resolve failed for operator %r", op_key)
                out.extend({"op": op_key, "id": i, "missing": True} for i in key_ids)

        return JsonResponse(
            {"results": out},
            encoder=self.get_json_encoder(),  # type: ignore[arg-type]
        )

    def _resolve_one(self, request: HttpRequest, op: Operator, key_ids: list[str]) -> list[dict[str, Any]]:
        """Resolve labels for a single operator's id list."""
        from django_tomselect.lazy_utils import resolve_view_class

        view_class, view_initkwargs = resolve_view_class(op.view)
        view = view_class(**view_initkwargs)
        view.setup(request)

        if isinstance(view, AutocompleteModelView):
            return self._resolve_model_view(request, view, op, key_ids)
        if isinstance(view, AutocompleteIterablesView):
            return self._resolve_iterables_view(view, op, key_ids)
        return [{"op": op.key, "id": i, "missing": True} for i in key_ids]

    def _project_resolve(self, op: Operator, key_ids: list[str], found: dict[str, Any]) -> list[dict[str, Any]]:
        """Project the per-id resolve response from a found-label map."""
        out: list[dict[str, Any]] = []
        for i in key_ids:
            s = str(i)
            if s in found:
                out.append({"op": op.key, "id": i, "value": i, "label": found[s]})
            else:
                out.append({"op": op.key, "id": i, "missing": True})
        return out

    def _resolve_model_view(
        self,
        request: HttpRequest,
        view: AutocompleteModelView,
        op: Operator,
        key_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Permission-safe resolve for a model-backed bound view."""
        # has_permission signature is (request, action="view"); passing
        # the model class would poison the permission cache.
        if not view.has_permission(request, "view"):
            return [{"op": op.key, "id": i, "missing": True} for i in key_ids]

        qs = view.get_queryset().filter(**{f"{op.bound_lookup}__in": key_ids})

        # Object-level permission gate: prepare_results() does not apply
        # has_object_permission() to rows, so we apply it ourselves before
        # projecting labels. Bound views without a custom override get the
        # default `return True` and behave as before. Filter the ORIGINAL
        # queryset (with its annotations) by allowed pks so prepare_results()
        # still sees any custom-annotated fields it depends on.
        allowed_pks: list[Any] = []
        for obj in qs:
            try:
                if view.has_object_permission(request, obj, "view"):
                    allowed_pks.append(obj.pk)
            except PermissionDenied:
                continue

        rows = view.prepare_results(qs.filter(pk__in=allowed_pks)) if allowed_pks else []
        found: dict[str, Any] = {}
        for row in rows:
            if op.value_field not in row or op.label_field not in row:
                logger.error(
                    "Operator %r expects keys %r/%r in prepared row but found %r",
                    op.key,
                    op.value_field,
                    op.label_field,
                    list(row.keys()),
                )
                continue
            found[str(row[op.value_field])] = row[op.label_field]
        return self._project_resolve(op, key_ids, found)

    def _resolve_iterables_view(
        self,
        view: AutocompleteIterablesView,
        op: Operator,
        key_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Resolve for an iterables-backed bound view (no permission check)."""
        id_set = {str(i) for i in key_ids}
        found: dict[str, Any] = {}
        for item in view.get_iterable():
            if op.value_field not in item or op.label_field not in item:
                logger.error(
                    "Operator %r expects keys %r/%r in iterable item but found %r",
                    op.key,
                    op.value_field,
                    op.label_field,
                    list(item.keys()),
                )
                continue
            v = str(item[op.value_field])
            if v in id_set:
                found[v] = item[op.label_field]
        return self._project_resolve(op, key_ids, found)
