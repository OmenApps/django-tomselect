# Inline Create with HTMX

## Example Overview

The **Inline Create with HTMX** example shows how to wire an instant
"create new value" flow into a Tom Select field: type a name that doesn't
exist, click the **Add &lt;name&gt;…** option Tom Select renders in the
dropdown, and the server persists the new value — all without a form submit
or page reload. The created chip appears in the field and in a sidebar list
of "Tags created this session". Picking an existing tag from the dropdown
adds a chip but does not land in the sidebar — only fresh creations do.

It also documents a workaround. The package's `create_with_htmx=True` flag
produces an `option_create.html` markup that currently:

1. Does **not** post the typed value (the `<div>` carrying the `hx-post`
   attribute has no `hx-vals`/`hx-include`).
2. Targets the input itself with `hx-swap="outerHTML"`, so a successful
   response can replace the `<select>`.

Until those are addressed in the package, the demo bypasses that wiring at
the JavaScript layer and uses Tom Select's native `settings.create` callback
to talk to a JSON endpoint. The pattern below is the recommended recipe today.

**Objective**:
- Provide an end-to-end working "create on the fly" recipe.
- Pin down a server response contract for the JSON endpoint:
  `{"action": "select", "value", "label", "is_new"}` on success;
  `{"action": "error", "error"}` on validation failure.
- Show how an HTMX OOB swap can layer onto the JSON-based flow: the JS bridge
  fires a `tag-created` custom event and an out-of-band HTMX `hx-trigger`
  refreshes a "tags created this session" panel.

**Use Case**:
- Tag selectors where the user knowledge is in their head, not in your
  database yet.
- Free-form attribute inputs (skills, technologies, dietary preferences).
- Any "we'll backfill the canonical list as users teach us their vocabulary"
  pattern.

**Visual Examples**

![Screenshot: Typing a new tag shows the 'Add <name>...' option](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/inline-create-tag-1.png)
![Screenshot: 'Tags created this session' sidebar updates via OOB swap](https://raw.githubusercontent.com/OmenApps/django-tomselect/refs/heads/main/docs/images/inline-create-tag-2.png)

---

## Key Code Segments

### Form

Reuses `DynamicTagField` from the simple tagging demo. `DynamicTagField`
subclasses `TomSelectMultipleChoiceField` (not `TomSelectModelMultipleChoiceField`),
so it doesn't set `to_field_name` from `config.value_field` — which would
otherwise reject `name`-valued options.

```python
from django_tomselect.app_settings import TomSelectConfig
from example_project.example.forms.intermediate_demos import DynamicTagField


class InlineCreateTagForm(forms.Form):
    tags = DynamicTagField(
        config=TomSelectConfig(
            url="autocomplete-publication-tag",
            value_field="value",
            label_field="label",
            placeholder="Type a tag — e.g. quantum-computing",
            create=True,
            highlight=True,
            minimum_query_length=1,
        ),
        required=False,
    )
```

### Server response contract

The view consumes structured JSON. `value` is the tag's `name`, not its id —
this keeps the value space consistent with `PublicationTagAutocompleteView`,
which emits `{value: tag.name, label: tag.name}`.

Validation is delegated to the model's own `full_clean()` so the endpoint
cannot persist a row the model would reject. The "Tags created this session"
sidebar is updated **only on genuine creation** (`is_new=True`); typing the
name of an existing tag selects it but does not pollute the sidebar.

```python
from django.core.exceptions import ValidationError as DjangoValidationError


@require_POST
def publication_tag_create_htmx(request):
    name = (request.POST.get("name") or "").strip().lower()
    if not name:
        return JsonResponse({"action": "error", "error": "Please type a tag name."})

    existing = PublicationTag.objects.filter(name=name).first()
    if existing is not None:
        if not existing.is_approved:
            existing.is_approved = True
            existing.save(update_fields=["is_approved", "updated_at"])
        return JsonResponse({
            "action": "select", "value": existing.name,
            "label": existing.name, "is_new": False,
        })

    # All further validation lives on the model.
    tag = PublicationTag(name=name, is_approved=True, usage_count=0)
    try:
        tag.full_clean()
    except DjangoValidationError as exc:
        msgs = list(getattr(exc, "messages", None) or [str(exc)])
        return JsonResponse({"action": "error", "error": msgs[0] if msgs else "Invalid tag."})
    tag.save()

    # Only newly-created tags land in the sidebar.
    session_tags = list(request.session.get("demo_inline_create_tags") or [])
    if name not in session_tags:
        session_tags.append(name)
        request.session["demo_inline_create_tags"] = session_tags

    return JsonResponse({
        "action": "select", "value": tag.name,
        "label": tag.name, "is_new": True,
    })
```

### JavaScript bridge

The demo template installs a small handler that overrides Tom Select's
`settings.create` callback. The bridge fires `htmx.trigger('tag-created')`
after a successful create so the OOB session-panel refresh runs.

```js
document.addEventListener('DOMContentLoaded', function attachCreateHandler() {
    var el = document.getElementById('id_tags');
    if (!el || !el.tomselect) {
        // Tom Select also initializes on DOMContentLoaded — retry next frame.
        requestAnimationFrame(attachCreateHandler);
        return;
    }
    var ts = el.tomselect;
    var valueField = ts.settings.valueField;   // "value"
    var labelField = ts.settings.labelField;   // "label"

    ts.settings.create = function (input, callback) {
        fetch(CREATE_URL, {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken(), 'Accept': 'application/json'},
            body: new URLSearchParams({name: input}),
        })
        .then(r => r.json().then(body => ({ok: r.ok, body})))
        .then(({ok, body}) => {
            if (ok && body.action === 'select') {
                var opt = {};
                opt[valueField] = body.value;
                opt[labelField] = body.label;
                callback(opt);                  // Tom Select adds + selects it
                ts.setTextboxValue('');
                htmx.trigger(document.body, 'tag-created', {detail: body});
            } else {
                showInlineError(body.error || 'Could not create tag.');
                callback();                     // signal failure to Tom Select
            }
        })
        .catch(() => { showInlineError('Network error.'); callback(); });
    };
});
```

### OOB session panel

A small `<div>` next to the field uses HTMX to listen for the JS-fired
`tag-created` event and refresh its own contents:

```html
<div hx-get="{% url 'htmx-tag-session-panel' %}"
     hx-trigger="tag-created from:body"
     hx-target="#session-panel"
     hx-swap="outerHTML">
    {% include "example/advanced_demos/_tag_session_panel.html" %}
</div>
```

### URL Wiring

```python
path("demo-inline-create-tag/", views.inline_create_tag_demo, name="inline-create-tag"),
path(
    "htmx-create-publication-tag/",
    views.publication_tag_create_htmx,
    name="htmx-create-publication-tag",
),
path(
    "htmx-tag-session-panel/",
    views.tag_session_panel_htmx,
    name="htmx-tag-session-panel",
),
```

---

## Try It

| Action | Result |
|---|---|
| Type a new tag (e.g. `quantum-computing`) | Dropdown shows "Add **quantum-computing**…". Click → chip appears, no reload, and the sidebar updates. |
| Type an existing tag and click its "Add" option | Same chip is selected; no duplicate row; sidebar does NOT update (the heading is "Tags **created** this session" and the entry already existed). |
| Pick an existing tag directly from the autocomplete suggestions | Chip appears in the field. Sidebar does NOT update — only fresh creations land there. |
| Type an invalid name (`has spaces!`, `--bad--`, `-x`) | Inline error appears under the field via the model's `clean()` rules; no chip added. |
| Watch the sidebar | Refreshes via OOB swap each time a tag is genuinely created. |
| Submit the form | The view receives `cleaned_data["tags"]` as a list of tag-name strings. |

---

## Why This Bypasses `create_with_htmx`

The plan-review process turned up two concrete issues with the package's
built-in HTMX wiring (`src/django_tomselect/templates/django_tomselect/render/option_create.html`):

1. The `<div>` element carries `hx-post` but no `hx-vals` / `hx-include`, so
   HTMX does not include the typed value in the POST body.
2. The element uses `hx-swap="outerHTML"` with `hx-target` pointing at the
   underlying input, so a 200 response can wipe the `<select>`.

For an instant create flow, you need: typed value posted, response that adds
an option *to the existing Tom Select instance*, and per-failure UX. This
demo delivers all three using `settings.create` and a JSON contract. If the
package later ships a built-in equivalent, the contract here is a reasonable
starting point.

---

## Related

- {doc}`tagging` — the simpler version that persists tags only at form submit
  via `get_or_create` in the field's `clean()`.
- API reference: `TomSelectConfig`, `TomSelectMultipleChoiceField`.
