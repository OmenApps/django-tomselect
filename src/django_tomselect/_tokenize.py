r"""Private quote-aware tokenizer.

Used by both ``query.py`` (token parser) and ``autocompletes.py``
(``AutocompleteModelView.search`` when ``split_search=True``). Pure-Python; no
Django imports - safe to import from anywhere in the package without circular
import risk.

Tokenization rules:

- Whitespace splits tokens, EXCEPT inside ``"..."`` or ``'...'`` quoted segments.
- Backslash escapes the next character inside a quoted segment (``\"``, ``\'``,
  ``\\``). Escapes outside quotes are passed through verbatim.
- Unterminated quotes produce an entry in ``UNTERMINATED_QUOTE_TOKENS``.
- Empty input produces an empty list.
"""

from __future__ import annotations

__all__ = [
    "Segment",
    "tokenize",
    "TokenizeError",
    "MAX_RAW_LENGTH_BYTES_DEFAULT",
]

from dataclasses import dataclass

MAX_RAW_LENGTH_BYTES_DEFAULT = 4096


class TokenizeError(ValueError):
    """Raised when the tokenizer encounters input it cannot interpret."""


@dataclass(frozen=True)
class Segment:
    """A single tokenized segment.

    Attributes:
        text: The literal text content of the segment with quotes stripped and
            escapes resolved. ``status:pending`` >> ``"status:pending"``;
            ``"light horse loop"`` >> ``"light horse loop"``.
        was_quoted: Whether the segment was wrapped in matched quotes in the
            source. Phrase-aware consumers (e.g. the bound-view
            ``split_search`` tokenizer) use this to decide whether a segment
            is a phrase that must not be further split.
    """

    text: str
    was_quoted: bool


def _consume_outside_quote(ch: str, buf: list[str], flush) -> str | None:
    """Process one char outside any quoted segment. Returns the new ``in_quote`` state."""
    if ch.isspace():
        flush()
        return None
    if ch in ('"', "'"):
        return ch
    buf.append(ch)
    return None


def _consume_in_quote(raw: str, i: int, in_quote: str, buf: list[str]) -> tuple[int, str | None, bool]:
    """Advance the tokenizer one character while inside a quoted segment.

    Returns ``(new_i, new_in_quote, just_closed)``. ``just_closed=True`` means
    the closing quote was just consumed and the caller should mark the
    in-progress segment as quoted.
    """
    n = len(raw)
    ch = raw[i]
    if ch == "\\" and i + 1 < n:
        nxt = raw[i + 1]
        if nxt in ('"', "'", "\\"):
            buf.append(nxt)
            return i + 2, in_quote, False
        buf.append(ch)
        return i + 1, in_quote, False
    if ch == in_quote:
        return i + 1, None, True
    buf.append(ch)
    return i + 1, in_quote, False


def tokenize(raw: str, *, max_raw_length_bytes: int = MAX_RAW_LENGTH_BYTES_DEFAULT) -> list[Segment]:
    """Tokenize a raw query string into segments.

    Args:
        raw: The raw input string.
        max_raw_length_bytes: Maximum permitted utf-8 byte length. Excess raises
            ``TokenizeError``.

    Returns:
        A list of :class:`Segment` objects.

    Raises:
        TokenizeError: If ``raw`` exceeds ``max_raw_length_bytes`` or contains
            an unterminated quoted segment.
    """
    if raw is None:
        return []
    if len(raw.encode("utf-8")) > max_raw_length_bytes:
        raise TokenizeError(f"Raw query exceeds maximum byte length ({max_raw_length_bytes}).")

    segments: list[Segment] = []
    i = 0
    n = len(raw)
    buf: list[str] = []
    in_quote: str | None = None
    quoted_segment = False

    def flush() -> None:
        nonlocal quoted_segment
        if buf or quoted_segment:
            segments.append(Segment(text="".join(buf), was_quoted=quoted_segment))
            buf.clear()
        quoted_segment = False

    while i < n:
        if in_quote is not None:
            i, in_quote, just_closed = _consume_in_quote(raw, i, in_quote, buf)
            if just_closed:
                quoted_segment = True
            continue
        in_quote = _consume_outside_quote(raw[i], buf, flush)
        i += 1

    if in_quote is not None:
        raise TokenizeError(f"Unterminated quote starting with {in_quote!r}.")

    flush()
    return segments
