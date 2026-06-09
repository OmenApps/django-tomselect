# External API: GitHub User Picker

## Example Overview

The **GitHub User Picker** example demonstrates that an autocomplete source
does not have to be backed by the Django ORM. Any view that returns a
`JsonResponse` matching the package's expected row shape (`results`, `page`,
`has_more`) can drive a Tom Select widget. This demo subclasses
`AutocompleteIterablesView` but overrides `get()` directly - bypassing
`get_iterable`, `search`, and `paginate_iterable` - to proxy GitHub's public
`/search/users` REST endpoint via `httpx`, with caching and rate-limit-aware
fetch behaviour, while storing the chosen login in a plain `CharField`. Use it
as a template for any picker that references an external system (a vendor API,
an internal microservice, or a public dataset) whose canonical id you want to
remember.

**Visual Examples**

![Screenshot: GitHub user picker - typing 'omenapps'](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/github-user-picker.png)

---

## Key Code Segments

### Autocomplete view

```python
import hashlib
import logging
import time

from django.core.cache import cache as _django_cache
from django.http import JsonResponse as _JsonResponse
from django_tomselect.autocompletes import AutocompleteIterablesView

logger = logging.getLogger(__name__)

_GITHUB_USER_SEARCH_URL = "https://api.github.com/search/users"
_GITHUB_CACHE_PREFIX = "demo-github-user-search:"
_GITHUB_CACHE_TIMEOUT = 300  # seconds
_GITHUB_THROTTLE_KEY = "demo-github-user-search:throttled-until"


class GitHubUserAutocompleteView(AutocompleteIterablesView):
    """Autocompletes against the GitHub /search/users public API.

    Subclasses ``AutocompleteIterablesView`` but overrides ``get()`` to skip
    ``get_iterable``/``search``/``paginate_iterable`` - the upstream API does
    pagination and filtering for us.

    Cache, rate-limit, and error handling notes are intentionally kept inline
    so the demo template can reference them. Cache is per-process
    (``LocMemCache`` in the example project), so the protection is partial.
    """

    skip_authorization = True
    page_size = 20

    def get(self, request, *args, **kwargs):
        """Handle the autocomplete request by querying the GitHub search API."""
        from django_tomselect.utils import sanitize_dict

        q = (request.GET.get("q") or "").strip()
        try:
            page = max(int(request.GET.get("p", 1)), 1)
        except (TypeError, ValueError):
            page = 1

        if not q or len(q) < 2:
            return _JsonResponse({"results": [], "page": page, "has_more": False})

        throttled_until = _django_cache.get(_GITHUB_THROTTLE_KEY)
        if throttled_until and throttled_until > time.time():
            wait = int(throttled_until - time.time())
            return _JsonResponse({
                "results": [], "page": page, "has_more": False,
                "error": f"GitHub rate limit reached. Try again in {wait} seconds.",
            })

        # Hash the cache-key components: the raw query may contain spaces or
        # non-ASCII characters which are forbidden by some cache backends
        # (Memcached restricts keys to printable ASCII with no whitespace).
        # LocMemCache (the example project's default) tolerates anything,
        # but using a hash keeps the demo backend-portable.
        q_digest = hashlib.sha1(q.encode("utf-8")).hexdigest()[:16]
        cache_key = f"{_GITHUB_CACHE_PREFIX}{q_digest}:{page}"
        cached = _django_cache.get(cache_key)
        if cached is not None:
            return _JsonResponse(cached)

        try:
            payload = self._fetch_github(q, page)
        except Exception:  # noqa: BLE001 - we deliberately swallow upstream failures
            logger.exception("GitHub user search failed")
            # Don't cache transient errors - let the next request retry.
            return _JsonResponse({
                "results": [], "page": page, "has_more": False,
                "error": "Upstream error contacting GitHub.",
            })

        # Sanitize every row at the boundary - overriding get() means we skip
        # the package's automatic sanitization pass.
        payload["results"] = [sanitize_dict(r) for r in payload.get("results", [])]
        # Only cache successful payloads. Caching rate-limit/error responses
        # would lock the demo into a 5-minute "stale error" state even after
        # the throttle window expires.
        if not payload.get("error"):
            _django_cache.set(cache_key, payload, _GITHUB_CACHE_TIMEOUT)
        return _JsonResponse(payload)
```

### Rate-limit handling

The view treats GitHub's rate-limit responses (`403` / `429`) as non-fatal:

```python
def _fetch_github(self, q: str, page: int) -> dict[str, Any]:  # noqa: C901
    """Call the GitHub search API and normalize the response shape."""
    import httpx  # imported lazily so the rest of the example app loads fine without it

    params = {"q": q, "per_page": self.page_size, "page": page}
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(_GITHUB_USER_SEARCH_URL, params=params, headers={"Accept": "application/json"})

    # Rate-limit hard-stop: mark a throttle window so we stop hitting the API.
    if resp.status_code in (403, 429):
        retry_after = resp.headers.get("retry-after")
        try:
            wait = int(retry_after) if retry_after else 60
        except ValueError:
            wait = 60
        reset = resp.headers.get("x-ratelimit-reset")
        try:
            reset_at = int(reset) if reset else int(time.time() + wait)
        except ValueError:
            reset_at = int(time.time() + wait)
        _django_cache.set(_GITHUB_THROTTLE_KEY, reset_at, max(wait, 30))
        return {
            "results": [], "page": page, "has_more": False,
            "error": f"GitHub rate limit reached. Try again in {wait} seconds.",
        }

    if resp.status_code >= 400:
        return {
            "results": [], "page": page, "has_more": False,
            "error": f"Upstream error ({resp.status_code}).",
        }

    # If x-ratelimit-remaining is 0, throttle preemptively.
    remaining = resp.headers.get("x-ratelimit-remaining")
    if remaining == "0":
        reset = resp.headers.get("x-ratelimit-reset")
        try:
            reset_at = int(reset) if reset else int(time.time() + 60)
        except ValueError:
            reset_at = int(time.time() + 60)
        _django_cache.set(_GITHUB_THROTTLE_KEY, reset_at, 60)

    data = resp.json()
    items = data.get("items") or []
    total = data.get("total_count") or 0
    results = []
    for u in items:
        login = u.get("login") or ""
        # The row keys MUST match the widget's configured value_field /
        # label_field (here: "value"/"label"). Returning {"id": ...} would
        # make Tom Select see data.value === undefined and silently drop
        # every row to "No results found", even with a 200 response.
        results.append({
            "value": login,
            "label": login,
            "avatar_url": u.get("avatar_url") or "",
            "html_url": u.get("html_url") or "",
            "bio": (u.get("bio") or "")[:140],  # keep dropdown rows compact
        })
    has_more = page * self.page_size < total
    return {
        "results": results,
        "page": page,
        "has_more": has_more,
        # The package's frontend stores the next-page URL only when both
        # ``has_more`` AND ``next_page`` are present. Emit it so the
        # widget can fetch additional pages on scroll.
        "next_page": page + 1 if has_more else None,
    }
```

### Form

The form stores the GitHub login string in a plain `CharField`. Because the
login is emitted as both `value` and `label` in the dropdown rows, the
`TomSelectIterablesWidget`'s default `value == label` fallback renders the
selected chip correctly on form re-submit - no custom widget needed.

```python
from django_tomselect.app_settings import TomSelectConfig, PluginDropdownHeader
from django_tomselect.widgets import TomSelectIterablesWidget


class GitHubUserPickerForm(forms.Form):
    github_user = forms.CharField(
        required=False,
        widget=TomSelectIterablesWidget(
            config=TomSelectConfig(
                url="autocomplete-github-user",
                value_field="value",
                label_field="label",
                placeholder=_("Type a GitHub username - e.g. octo"),
                minimum_query_length=2,
                load_throttle=400,
                plugin_dropdown_header=PluginDropdownHeader(
                    title=_("GitHub users"),
                    show_value_field=False,
                    label_field_label=_("Login"),
                    extra_columns={"bio": _("Bio")},
                ),
            ),
        ),
    )
```

### URL Wiring

```python
path(
    "autocomplete/github-user/",
    autocompletes.GitHubUserAutocompleteView.as_view(),
    name="autocomplete-github-user",
),
path("demo-github-user-picker/", views.github_user_picker_view, name="github-user-picker"),
```

---

## Try It

| Action | Result |
|---|---|
| Type `octo` (2+ chars) | Dropdown shows up to 20 GitHub users. |
| Hover a row | The "Bio" column appears via `PluginDropdownHeader.extra_columns`. |
| Submit the form with a selection | View receives the login as a plain string in `cleaned_data["github_user"]`. |
| Type `a` (1 char) | No request; `minimum_query_length=2` keeps the API call from firing on single characters. |
| Repeat the same query | The second request is a cache hit (300s TTL). |
| Hit the API enough to get throttled | Subsequent requests return immediately with a friendly `error` field, no upstream call. |

---

## Trade-offs and Caveats

1. **Synchronous HTTP inside a view**. `httpx.Client(...)` blocks the worker
   thread for up to 10 s. For a demo this is fine; in production consider
   Django's async views (`async def get`) with `httpx.AsyncClient`.
2. **Per-IP rate limits at GitHub's end**. The cache helps within a single
   process; LocMemCache is not shared across workers. For real workloads use
   a shared cache (Redis / Memcached).
3. **No selected-options resolver**. Because the demo stores the GitHub login
   as both the `value` and the `label`, the iterables widget's `value == label`
   fallback renders the selected chip correctly without a custom widget. If
   your external value were opaque (e.g. an integer id with a label fetched
   separately), you would override `TomSelectIterablesWidget._get_selected_options`
   to resolve labels server-side at render time.
4. **Secrets stay on the server**. Even though this demo doesn't require an
   API token, an authenticated variant would put the token on the autocomplete
   view, never in the browser.

---

## Related

- {doc}`tagging` - the in-database equivalent of "pick a value from a
  dynamic source."
- API reference: `AutocompleteIterablesView`, `TomSelectIterablesWidget`,
  `PluginDropdownHeader`.
