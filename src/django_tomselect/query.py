"""Token-style query parser for ``CompositeAutocompleteView``.

Public surface:

- :func:`parse_query` - parse a raw query string into a :class:`ParsedQuery`.
- :class:`ParsedQuery` - parsed result with ``tokens``, ``free_text``,
  ``errors``, and a queryset-aware :meth:`ParsedQuery.apply`.
- :class:`ParsedToken` / :class:`ParseError` - supporting types.

The tokenizer lives in :mod:`django_tomselect._tokenize` (private). This module
deliberately avoids importing :mod:`django_tomselect.autocompletes` at module
scope; ``Operator`` is referenced via :data:`typing.TYPE_CHECKING` only, so the
``Operator``-defining module can also import the tokenizer without a cycle.
"""

from __future__ import annotations

__all__ = [
    "parse_query",
    "ParsedQuery",
    "ParsedToken",
    "ParseError",
    "MAX_RAW_LENGTH_DEFAULT",
    "MAX_TOKENS_DEFAULT",
    "MAX_VALUES_PER_OPERATOR_DEFAULT",
]

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet

from django_tomselect._tokenize import Segment, TokenizeError, tokenize
from django_tomselect.logging import get_logger

if TYPE_CHECKING:
    # Avoid an import cycle with autocompletes.py at module load time.
    from django_tomselect.autocompletes import CompositeAutocompleteView, Operator

logger = get_logger(__name__)

# Operator-key regex: a leading identifier-shaped key (letters, digits, underscore;
# must start with a letter). Case-sensitive lookup against the operator registry,
# so e.g. "Author:42" parses as a candidate but matches no registered key
# (which are URL-canonical lowercase) and surfaces as UNKNOWN_OPERATOR rather
# than silently becoming free text.
_OPERATOR_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*):(.*)$", re.DOTALL)

MAX_RAW_LENGTH_DEFAULT = 4096
MAX_TOKENS_DEFAULT = 32
MAX_VALUES_PER_OPERATOR_DEFAULT = 16


@dataclass(frozen=True)
class ParseError:
    """A single parser error.

    ``code`` is one of: ``UNKNOWN_OPERATOR``, ``UNTERMINATED_QUOTE``,
    ``MAX_RAW_LENGTH_EXCEEDED``, ``MAX_TOKENS_EXCEEDED``,
    ``MAX_VALUES_PER_OPERATOR_EXCEEDED``, ``EMPTY_VALUE``.
    """

    code: str
    message: str
    operator_key: str | None = None
    raw: str | None = None


@dataclass(frozen=True)
class ParsedToken:
    """A successfully parsed operator token.

    Attributes:
        key: The registered operator key (e.g. ``"author"``).
        values: One or more values. Single-value for ``multi=False`` operators;
            comma-split for ``multi=True``.
        was_quoted: Whether the source segment was wrapped in quotes (only the
            first comma-separated value is considered for this signal).
    """

    key: str
    values: tuple[str, ...]
    was_quoted: bool


@dataclass
class ParsedQuery:
    """Parsed query with operator tokens, free-text terms, and errors."""

    tokens: list[ParsedToken] = field(default_factory=list)
    free_text: list[str] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)
    # Composite view passed in at parse time. Stored so apply() can resolve
    # operator metadata (filter_lookup, q_translator, multi) without a second
    # lookup. Type-checked via TYPE_CHECKING import.
    _composite: type[CompositeAutocompleteView] | None = field(default=None, repr=False)
    _free_text_lookups: tuple[str, ...] = field(default=(), repr=False)

    def has(self, op_key: str) -> bool:
        """True if at least one token with the given key was parsed."""
        return any(t.key == op_key for t in self.tokens)

    def get(self, op_key: str) -> list[ParsedToken]:
        """Return all tokens with the given key (empty list if none)."""
        return [t for t in self.tokens if t.key == op_key]

    def format_errors(self) -> list[str]:
        """Return a list of user-facing strings for each :class:`ParseError`.

        Suitable for raising as a list-form :class:`ValidationError`.
        """
        return [_format_error(e) for e in self.errors]

    def apply(self, queryset: QuerySet) -> QuerySet:
        """Apply parsed tokens to ``queryset`` and return the narrowed queryset.

        Refuses to apply if :attr:`errors` is non-empty (raises
        :class:`ValidationError` listing each error).

        ORM coercion errors raised inside ``.filter()`` (e.g. typing
        ``category:tech`` against ``filter_lookup="categories__id"``) are caught
        and re-raised as :class:`ValidationError` with operator/value context.
        """
        if self.errors:
            raise ValidationError(self.format_errors())

        if self._composite is None:
            return queryset

        # Operator tokens: AND-compose across operators. Within multi=True
        # operators, the comma-separated values are OR-combined via __in.
        operators_by_key = {op.key: op for op in self._composite.operators}
        for token in self.tokens:
            op = operators_by_key.get(token.key)
            if op is None:  # defensive - should not happen post-validation
                continue
            try:
                queryset = queryset.filter(_token_q(op, token))
            except (ValueError, TypeError) as exc:
                # ORM coercion failure - typed-but-not-selected value for an
                # id-based filter_lookup is the canonical case. Raise a plain
                # (non-dict) ValidationError so callers can attach it to a
                # specific form field via form.add_error("q", e).
                raise ValidationError(
                    f"Invalid value(s) {list(token.values)!r} for operator "  # nosec B608 - error message, not SQL.
                    f"{token.key!r}: {exc}. If this is a reference operator, "
                    "select an option from the dropdown rather than typing free text."
                ) from exc

        # Free-text: each term OR'd across free_text_lookups; terms ANDed together.
        if self.free_text and self._free_text_lookups:
            for term in self.free_text:
                term_q = Q()
                for lookup in self._free_text_lookups:
                    term_q = term_q | Q(**{lookup: term})
                queryset = queryset.filter(term_q)

        return queryset


def parse_query(
    raw: str,
    composite_view: type[CompositeAutocompleteView] | str,
    *,
    max_raw_length: int = MAX_RAW_LENGTH_DEFAULT,
    max_tokens: int = MAX_TOKENS_DEFAULT,
    max_values_per_operator: int = MAX_VALUES_PER_OPERATOR_DEFAULT,
) -> ParsedQuery:
    """Parse a raw token-style query string against a composite view's operators.

    Unknown operator keys never silently re-route to free-text; they produce
    an :class:`ParseError` with code ``UNKNOWN_OPERATOR`` and downstream
    :meth:`ParsedQuery.apply` refuses to run.
    """
    composite_cls = _resolve_composite(composite_view)
    operators_by_key = {op.key: op for op in composite_cls.operators}
    free_text_lookups = tuple(getattr(composite_cls, "free_text_lookups", ()) or ())

    parsed = ParsedQuery(_composite=composite_cls, _free_text_lookups=free_text_lookups)

    if raw is None:
        return parsed

    try:
        segments = tokenize(raw, max_raw_length_bytes=max_raw_length)
    except TokenizeError as exc:
        msg = str(exc)
        if "exceeds maximum byte length" in msg:
            parsed.errors.append(ParseError(code="MAX_RAW_LENGTH_EXCEEDED", message=msg, raw=raw))
        else:
            parsed.errors.append(ParseError(code="UNTERMINATED_QUOTE", message=msg, raw=raw))
        return parsed

    if len(segments) > max_tokens:
        parsed.errors.append(
            ParseError(
                code="MAX_TOKENS_EXCEEDED",
                message=f"Too many tokens ({len(segments)} > {max_tokens}).",
                raw=raw,
            )
        )
        return parsed

    for seg in segments:
        _process_segment(seg, operators_by_key, parsed, max_values_per_operator)
    return parsed


def _process_segment(
    seg: Segment,
    operators_by_key: dict[str, Operator],
    parsed: ParsedQuery,
    max_values_per_operator: int,
) -> None:
    """Classify a tokenized segment as token / free-text / error and append it."""
    match = _OPERATOR_KEY_RE.match(seg.text)
    if match is None:
        parsed.free_text.append(seg.text)
        return
    key, value = match.group(1), match.group(2)
    op = operators_by_key.get(key)
    if op is None:
        parsed.errors.append(
            ParseError(
                code="UNKNOWN_OPERATOR",
                message=f"Unknown operator {key!r}.",
                operator_key=key,
                raw=seg.text,
            )
        )
        return

    values = _resolve_token_values(op, key, value, seg, parsed, max_values_per_operator)
    if values is not None:
        parsed.tokens.append(ParsedToken(key=key, values=values, was_quoted=seg.was_quoted))


def _resolve_token_values(
    op: Operator,
    key: str,
    value: str,
    seg: Segment,
    parsed: ParsedQuery,
    max_values_per_operator: int,
) -> tuple[str, ...] | None:
    """Split / validate values for a token; append errors and return None on failure."""
    if not op.multi:
        return (value,)

    split = tuple(value.split(",")) if value else ("",)
    if len(split) > max_values_per_operator:
        parsed.errors.append(
            ParseError(
                code="MAX_VALUES_PER_OPERATOR_EXCEEDED",
                message=(f"Operator {key!r} has {len(split)} values (maximum {max_values_per_operator})."),
                operator_key=key,
                raw=seg.text,
            )
        )
        return None
    # Reject inputs like "status:draft," or "category:1,,2" - every
    # comma-separated member must be non-empty for multi=True operators.
    # (For multi=False the whole comma-containing value is kept verbatim
    # and this check does not apply.)
    if len(split) > 1 and any(not v.strip() for v in split):
        parsed.errors.append(
            ParseError(
                code="EMPTY_VALUE",
                message=f"Operator {key!r} has an empty value in {seg.text!r}.",
                operator_key=key,
                raw=seg.text,
            )
        )
        return None
    return split


def _resolve_composite(
    composite_view: type[CompositeAutocompleteView] | str,
) -> type[CompositeAutocompleteView]:
    """Resolve a composite view class reference or URL name to the class.

    When the URL pattern was registered via ``as_view(operators=[...], free_text_lookups=[...])``
    we need to honor those init kwargs because they override the class-level
    defaults. Build a lightweight subclass with the kwargs baked in as class
    attributes so ``parse_query`` and ``apply()`` see the correct registry.
    """
    if isinstance(composite_view, str):
        from django_tomselect.lazy_utils import resolve_view_class

        view_class, view_initkwargs = resolve_view_class(composite_view)
        if view_initkwargs:
            # ``View.as_view(**kwargs)`` sets these on the instance at request
            # dispatch time. For our static parsing/validation use case, build
            # a one-shot subclass that promotes those kwargs to class attrs.
            view_class = type(
                f"_ResolvedComposite_{view_class.__name__}",
                (view_class,),
                dict(view_initkwargs),
            )
        return view_class  # type: ignore[return-value]
    return composite_view


def _token_q(op: Operator, token: ParsedToken) -> Q:
    """Build a Q object for a single parsed token, honoring filter_lookup / q_translator."""
    if op.q_translator is not None:
        result = op.q_translator(op, list(token.values))
        if not isinstance(result, Q):
            raise TypeError(f"q_translator for operator {op.key!r} must return a Q, got {type(result)!r}.")
        return result

    # filter_lookup path. By Operator.__post_init__ contract, exactly one of
    # filter_lookup or q_translator is set when we get here.
    lookup = op.filter_lookup
    if isinstance(lookup, str):
        return _build_q_for_lookups([lookup], op, token)
    return _build_q_for_lookups(list(lookup), op, token)


def _build_q_for_lookups(lookups: list[str], op: Operator, token: ParsedToken) -> Q:
    """OR-compose a Q across multiple filter_lookups, applying multi semantics."""
    q = Q()
    for lookup in lookups:
        if op.multi and len(token.values) > 1:
            q = q | Q(**{f"{lookup}__in": list(token.values)})
        else:
            # Single value; for multi=True with one comma value, fall through to equality.
            value = token.values[0] if token.values else ""
            q = q | Q(**{lookup: value})
    return q


def _format_error(err: ParseError) -> str:
    """Render a ParseError as a user-facing string for ValidationError."""
    if err.code == "UNKNOWN_OPERATOR":
        return f"Unknown operator {err.operator_key!r}."
    if err.code == "UNTERMINATED_QUOTE":
        return "Unterminated quote in query."
    if err.code == "MAX_RAW_LENGTH_EXCEEDED":
        return "Query is too long."
    if err.code == "MAX_TOKENS_EXCEEDED":
        return "Too many tokens in query."
    if err.code == "MAX_VALUES_PER_OPERATOR_EXCEEDED":
        return f"Too many values for operator {err.operator_key!r}."
    if err.code == "EMPTY_VALUE":
        return f"Operator {err.operator_key!r} requires a value."
    return err.message
