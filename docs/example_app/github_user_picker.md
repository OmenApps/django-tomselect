# External API: GitHub User Picker

## Example Overview

The **GitHub User Picker** example demonstrates that an autocomplete source
does not have to be backed by the Django ORM. Any view that returns a
`JsonResponse` matching the package's expected row shape (`results`, `page`,
`has_more`) can drive a Tom Select widget.

This demo subclasses `AutocompleteIterablesView` but overrides `get()`
directly - bypassing `get_iterable`, `search`, and `paginate_iterable`. The
view then proxies GitHub's public `/search/users` REST endpoint via `httpx`,
caching results to soften the rate-limit hit.

**Objective**:
- Show how to swap the autocomplete data source for an external HTTP API.
- Demonstrate rate-limit-aware fetch behaviour (`403`/`429`, `retry-after`,
  `x-ratelimit-remaining`).
- Show that you can store the selected value in a plain `CharField` - no
  model, no foreign key.

**Use Case**:
- "Pick a GitHub user" / "Tag a Twitter handle" / "Look up an ISBN" - any
  reference to an external system whose canonical id you want to remember.
- Vendor / partner pickers backed by an internal microservice instead of a
  shared database.
- Prototyping with a public dataset (Open Library, MusicBrainz, GBIF,
  Wikidata) before you build a local cache.

**Visual Examples**

![Screenshot: GitHub user picker - typing 'omenapps'](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/github-user-picker.png)

---

## Key Code Segments

### Autocomplete view

```python
import time
import httpx
from django.core.cache import cache
from django.http import JsonResponse
from django_tomselect.autocompletes import AutocompleteIterablesView
from django_tomselect.utils import sanitize_dict


class GitHubUserAutocompleteView(AutocompleteIterablesView):
    """Autocompletes against the GitHub /search/users public API."""

    skip_authorization = True
    page_size = 20

    def get(self, request, *args, **kwargs):
        q = (request.GET.get("q") or "").strip()
        page = max(int(request.GET.get("p", 1) or 1), 1)
        if len(q) < 2:
            return JsonResponse({"results": [], "page": page, "has_more": False})

        # Honor a previously-set throttle window.
        throttled_until = cache.get("demo-github-user-search:throttled-until")
        if throttled_until and throttled_until > time.time():
            wait = int(throttled_until - time.time())
            return JsonResponse({
                "results": [], "page": page, "has_more": False,
                "error": f"GitHub rate limit reached. Try again in {wait}s.",
            })

        cache_key = f"demo-github-user-search:{q}:{page}"
        cached = cache.get(cache_key)
        if cached is not None:
            return JsonResponse(cached)

        try:
            payload = self._fetch_github(q, page)
        except Exception:
            payload = {"results": [], "page": page, "has_more": False,
                       "error": "Upstream error contacting GitHub."}

        # Override-get skips the package's automatic sanitization pass -
        # sanitize at the boundary.
        payload["results"] = [sanitize_dict(r) for r in payload.get("results", [])]
        cache.set(cache_key, payload, 300)
        return JsonResponse(payload)
```

### Rate-limit handling

The view treats GitHub's rate-limit responses (`403` / `429`) as non-fatal:

```python
def _fetch_github(self, q, page):
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(GITHUB_URL, params={"q": q, "per_page": self.page_size, "page": page})

    if resp.status_code in (403, 429):
        retry_after = int(resp.headers.get("retry-after") or 60)
        reset_at = int(time.time() + retry_after)
        cache.set("demo-github-user-search:throttled-until", reset_at, max(retry_after, 30))
        return {
            "results": [], "page": page, "has_more": False, "next_page": None,
            "error": f"GitHub rate limit reached. Try again in {retry_after}s.",
        }

    if resp.headers.get("x-ratelimit-remaining") == "0":
        # Preemptively throttle the next request.
        cache.set("demo-github-user-search:throttled-until",
                  int(resp.headers.get("x-ratelimit-reset") or time.time() + 60), 60)

    data = resp.json()
    # Row keys MUST be "value"/"label" (not "id") to match the widget's
    # configured value_field / label_field. Returning "id" would make Tom
    # Select see data.value === undefined and silently treat every row as
    # "No results found" - a 200 status with rows the UI never displays.
    results = [
        {"value": u["login"], "label": u["login"],
         "avatar_url": u.get("avatar_url", ""),
         "bio": (u.get("bio") or "")[:140]}
        for u in (data.get("items") or [])
    ]
    has_more = page * self.page_size < (data.get("total_count") or 0)
    return {
        "results": results, "page": page, "has_more": has_more,
        # The frontend stores the next-page URL only when both has_more
        # AND next_page are truthy. Emit it so scroll-loaded pages work.
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
