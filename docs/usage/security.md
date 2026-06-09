# Security Considerations

`django_tomselect` is designed to integrate seamlessly with Django’s authentication and authorization frameworks. It provides built-in mechanisms for controlling data visibility, validating permissions, and restricting access to autocomplete endpoints. By configuring permissions, employing authorization hooks, and leveraging caching, you can ensure that your autocomplete fields expose only allowed data to authorized users.

## Visualizing Security

```{mermaid}

    stateDiagram-v2
        [*] --> CheckAuth: Request received

        CheckAuth --> SkipAuth: skip_authorization=True
        CheckAuth --> AllowAnon: allow_anonymous=True
        CheckAuth --> ValidateUser: Regular auth flow

        SkipAuth --> ProcessRequest: Allow
        AllowAnon --> ProcessRequest: Allow

        ValidateUser --> CheckCache: User authenticated
        ValidateUser --> RejectRequest: User not authenticated

        CheckCache --> UseCache: Cache hit
        CheckCache --> CheckPerms: Cache miss

        CheckPerms --> CachePerms: Has permission
        CheckPerms --> RejectRequest: No permission

        CachePerms --> ProcessRequest
        UseCache --> ProcessRequest

        ProcessRequest --> [*]: Complete
        RejectRequest --> [*]: Reject
```

## Permission Handling

Security often begins with permission checks. `django_tomselect` supports permission-based restrictions on Model-type autocomplete views, allowing you to define who can see, search, or create new entries. Iterables-type components, on the other hand, do not benefit from built-in permission checks and rely on your custom logic.

### Model-type vs. Iterables-type Components

- **Model-type Components:**
  When using `AutocompleteModelView`, permissions are integrated. You can rely on the model’s defined permissions (e.g., `view`, `add`, `change`, `delete`) to restrict access. Note that built-in view-permission enforcement is opt-in: it only applies when you set `permission_required` on the view (or override `has_permission`). By default `permission_required = None`, in which case `has_permission` returns `True` for any authenticated user, so a user without the `view` permission will still see the model instances. Set `permission_required = "app_label.view_modelname"` to require the `view` permission.

- **Iterables-type Components:**
  For iterables-based autocomplete (`AutocompleteIterablesView`), there are no out-of-the-box permission checks. You must implement your own filtering or conditional logic in the view to ensure only allowed data is returned.

### Request Passing for Authentication

`django_tomselect` automatically receives the `request` object through its views, making it possible to check `request.user` and confirm that the user is authenticated and authorized before returning data. Ensure that your URLs or views are protected by `login_required`, `LoginRequiredMixin`, or custom permission checks so that the `request.user` is set and reliable.

## Class Variable Priority and Usage

`AutocompleteModelView` provides several class-level attributes that let you fine-tune authorization logic. These attributes influence how permissions are enforced and in which order:

- **`permission_required`**: Specifies exact permissions needed. This could be a single permission string or a list of permissions required to access the data.
- **`allow_anonymous`**: If set to `True`, anonymous users are allowed access, bypassing normal permission checks. Use with caution.
- **`skip_authorization`**: Setting this to `True` disables all permission checks entirely, allowing unrestricted access to the autocomplete. Use only in trusted or controlled environments.

**Priority**:
`skip_authorization` (highest)
`allow_anonymous`
`permission_required` (lowest)

If `skip_authorization` is `True`, no checks are performed at all. If it’s `False`, but `allow_anonymous` is `True`, then no authentication is required. Otherwise, `permission_required` is evaluated against `request.user`.

## Django’s Built-in Authorization System

`django_tomselect` integrates naturally with Django’s built-in authentication and authorization system. By using standard model permissions (e.g., `app_label.view_modelname`), you can control who can see, create, update, or delete specific objects:

```python
class AuthorAutocompleteView(AutocompleteModelView):
    model = Author
    search_lookups = ["name__icontains", "bio__icontains"]

    permission_required = "myapp.view_author"

    def has_permission(self, request, action="view"):
        # Uses built-in user.has_perms() behind the scenes
        return super().has_permission(request, action)
```

By aligning autocomplete views with Django’s permission model, you ensure consistent enforcement across your application.

## Object-level Permissions

Override `has_object_permission()` to evaluate access for a single resolved object:

```python
class ArticleAutocompleteView(AutocompleteModelView):
    model = Article

    def has_object_permission(self, request, obj, action="view"):
        # Restrict visibility to objects owned by the current user
        return obj.owner == request.user
```

```{important}
`has_object_permission()` runs when the view resolves specific objects by ID - for example when a `CompositeAutocompleteView` (token search) turns previously-selected IDs back into labels. It is **not** called for every row of the autocomplete suggestion listing. To restrict which objects appear in the dropdown as the user types (e.g. "user A can see only articles they own, while user B can see all"), filter the queryset instead.
```

```python
class ArticleAutocompleteView(AutocompleteModelView):
    model = Article

    def get_queryset(self):
        # Only the current user's own articles appear in the dropdown
        return super().get_queryset().filter(owner=self.request.user)
```

Combine object-level checks with Django’s permission system or third-party packages like `django-guardian` to implement fine-grained access control.

## Custom and Third-party Auth Systems

For more complex scenarios (e.g., OAuth, SSO, or custom backends), subclass `AutocompleteModelView` and integrate with your custom authentication logic. Implement checks in `has_permission()` or `has_object_permission()` to validate tokens, interact with external services, or apply custom roles and policies.

`django_tomselect` does not impose any specific authentication mechanism, allowing you to seamlessly integrate solutions like `django-guardian` for per-object permissions or adapt to enterprise SSO systems.

## Customizing Authorization

If you need complete control over the authorization process, override key methods in `AutocompleteModelView`:

- **`has_permission(request, action="view")`**: Called before processing the request; return `False` to deny access.
- **`has_object_permission(request, obj, action="view")`**: Evaluate permissions on a single object during ID/label resolution (e.g. token-search resolve). It is **not** invoked per row of the suggestion listing - use `get_queryset()` to filter what the dropdown shows.

Both methods accept an `action` argument - one of `"view"`, `"create"`, `"update"`, or `"delete"`. The action-specific Django model permissions (`add_`/`change_`/`delete_`) only apply when `permission_required` is also set. The default `has_permission()` first checks `permission_required`; if no permissions are required (the default `permission_required = None`) it returns `True` before any action permission is considered. So configuring `create_url` alone does not require `app_label.add_modelname` - that permission is only appended (for `action="create"`) when `permission_required` is set as well. The same applies to `update_url`/`change_` and `delete_url`/`delete_`. Override these methods to branch on `action` for finer-grained control.

For instance, to apply a custom logic that checks a user’s organization membership before displaying data:

```python
class OrganizationRestrictedAutocompleteView(AutocompleteModelView):
    model = Magazine

    def has_permission(self, request, action="view"):
        # Check if user belongs to the required organization
        return request.user.is_authenticated and request.user.organization_id == 42
```

## User Permission Caching and Invalidation

Checking permissions repeatedly can be costly. `django_tomselect` provides an optional permission caching mechanism to speed up subsequent checks. When enabled, permissions are cached per user, model, and action, so changes in user roles or memberships require invalidating the cache (via `AutocompleteModelView.invalidate_permissions(user=...)` or the module-level `permission_cache`) to take effect immediately.

For configuration, behavior, cache-backend support, and the full invalidation API, see [Permission Caching](../api/utilities.md).

## Content Security Policy (CSP) Nonce Support

If your application uses a [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP) to restrict inline scripts, `django-tomselect` supports CSP nonces. This allows you to avoid setting `'unsafe-inline'` in your `script-src` directive.

### How It Works

When a CSP nonce is available on the request object, `django-tomselect` automatically adds it to the inline `<script>` tags it renders:

```html
<script nonce="abc123...">
    // TomSelect initialization code
</script>
```

### Setup with django-csp

If you use [django-csp](https://django-csp.readthedocs.io/), the nonce is available automatically. Ensure the `django-csp` middleware is installed and configured:

```python
# settings.py
MIDDLEWARE = [
    # ...
    "csp.middleware.CSPMiddleware",
    "django_tomselect.middleware.TomSelectMiddleware",
    # ...
]

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "script-src": ["'self'", "'nonce'"],  # django-csp will replace 'nonce' with the actual nonce
    },
}
```

No additional configuration in `django-tomselect` is needed - the widget reads the nonce from `request.csp_nonce` (or `request._csp_nonce`) and passes it to the template context automatically.

### Custom CSP Middleware

If you use a custom CSP middleware, ensure it sets `request.csp_nonce` or `request._csp_nonce` to the nonce value. `django-tomselect` will detect and use it.

### Without CSP

If no CSP nonce is present on the request, the `<script>` tags render without a `nonce` attribute, maintaining full backward compatibility.
