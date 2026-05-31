# Changelog

## 2026.5.6

- `TomSelectConfig` now raises `ImproperlyConfigured` when `label_field` is a Python dunder (e.g. `label_field="__str__"`). A dunder is not selectable via `QuerySet.values()`, so it silently rendered empty labels. **Potentially breaking:** configs that relied on a dunder `label_field` must switch to a real field, a relation lookup (e.g. `"author__name"`), or a queryable annotation exposed in the view's `hook_queryset()` - see the autocomplete views docs

## 2026.5.5

- Suppress warnings for declared virtual autocomplete fields

## 2026.5.4

- Token widget (`TomSelectTokenWidget`): implement the ARIA combobox/listbox pattern - `role="combobox"` with `aria-expanded`/`aria-controls`/`aria-autocomplete` on the input, an inner `role="listbox"` (named per mode) that owns only `role="option"` elements with `aria-selected`, `aria-activedescendant` tracking during keyboard navigation, context-specific remove-button labels, focus restoration after chip removal, and a polite live region announcing token add/remove
- `remove_button` plugin: render a focusable `<button type="button">` with an item-specific `aria-label` instead of `<a tabindex="-1">`, so selected items can be removed by keyboard (focus returns to the control input after removal). **Potentially breaking for custom CSS/JS:** the remove control is now a `<button>` rather than an `<a>` - selectors that match the element type (e.g. `a.remove`) no longer match; use the class (`.remove`) or `button.remove`. The configured class name is unchanged.

## 2026.5.3

- Fix regression #61 that affected `filter_by` and `exclude_by`
- Implement more advanced token-search functionality and add demos of extended/advanced functionality
- Break up large test files and add more regression tests in vitest

## 2026.5.2

- Fix options jumping to page 2 of results in certain cases
- Fix double-escaping of characters in the tabular dropdown
- Fix cloned/nested formset rows leaking controller state (per-instance `currentLoadController`/`previousQuery`, `findSimilarConfig` closures, cross-level `filterFields` URL desync)
- Allow `Const(value, lookup)` to accept a list/tuple value (comma-joined into the URL param) so it works with list-valued lookups like `__in` and `__range`; the autocomplete view now splits these values back into a list before applying the filter
- Accept tuples (not just lists) of `FilterSpec`/2-tuples in `filter_by` and `exclude_by`; previously a 2-tuple of `FilterSpec` was misinterpreted as the legacy `(field, lookup)` form and any other tuple length was rejected outright
- Add vitest for more consistent JS testing

## 2026.5.1

- Add `CompositeAutocompleteView` to wrap multiple `Autocomplete*View` instances behind a single endpoint, dispatching by source name for unified token-style search across heterogeneous datasets
- Add `TomSelectTokenField` and `TomSelectTokenWidget` for token-based search inputs with a structured query parser (field-scoped tokens, quoted phrases, boolean logic) backed by a new Tom Select token plugin
- Fixes for the two bugs in #59

## 2026.4.1

- Fix htmx outerHTML swaps
- Fix `clear_button` HTML template overwrite not working
- Pass `loading_class` config to TomSelect's `loadingClass` JS option (#53)
- Correct annotations, wrap hard-coded strings with `gettext`, and add translations (#54)
- Add a nox session to patch CSS with backup values; test improvements

## 2026.3.3

- Minor htmx reinitialize cleanup; prevent a redundant `reinitialize()` call

## 2026.3.2

- Skip `reinitialize()` when a live TomSelect instance already exists, fixing htmx double-init (#51)
- Add pt and ru locales; expand de/es coverage (#50)

## 2026.3.1

- Suppress spurious URL warnings when `show_list` or `show_create` are `False` (#46)
- Remove docker compose (not needed for this project) and update tooling
- Standardize README badges

## 2026.1.3

- Update bundled Tom Select static files to latest version
- Fix JSON serialization fallback - was incorrectly falling back to `json.JSONEncoder` instead of `DjangoJSONEncoder`, which couldn't handle common Django objects
- Improve logging, sanitization, and handling of non-model fields in `value_fields`
- Avoid unnecessary escaping of fields that are already JSON-safe when using `DjangoJSONEncoder`

## 2026.1.2

- Extend `filter_by` and `exclude_by` to support multiple filter values
- Add ability to specify a custom JSON encoder globally and per-view
- Add new formset demo with prefix support, and update existing demo to prevent parent==child situations
- Implement `__all__` across modules to clarify the public/internal API boundary
- Calculate and return `total_pages` in autocomplete responses, fixing a paging issue (#42)
- Add note about excluding `EmptyModel` when running `dumpdata` (#36)
- Prevent excessively large page sizes that could cause denial of service
- Prevent negative page numbers (resolve to page 1 instead)
- Improve filter validation and parsing
- Improve logging wrapper implementation
- Finish implementing URL param constants in templates
- Improve template security and formset support
- Update docs to reflect recent changes and correct inaccuracies

## 2026.1.1

- Replace the `safety` package with `pip-audit` for dependency auditing
- Improve how widget configuration is validated
- Improve URL escaping and update permission checks to avoid N+1 queries
- Use safe template replacement instead of `new Function()` for improved security
- Improve how the widget handles resets and data fetches
- Update supported Python & Django version references
- Fix several config file issues (names, config sections)
- Various small code quality improvements (imports, flag cleanup, cache tests)

## 2025.9.1

- Rework i18n URL pattern handling

## 2025.7.1

- Resolve i18n issue (#43)
- Add tests for #41
- Limit lookup field splitting to first occurrence

## 2025.5.7

- Correct form handling for edge cases where the model primary key isn't Django's default `id`
- Add new models and forms to cover these edge cases with tests
- Use ruff exclusively (remove references to isort & black)
- Misc cleanup

## 2025.5.6

- For selected values, filter strictly on the `value_field`

## 2025.5.5

- Ensure correct filtering on `value_field` when identifying selected values

## 2025.5.4

- Make `hide_selected` default to `True` (matches expected behavior)
- Additional robustness improvements to widgets

## 2025.5.3

- Fix form fields displaying incorrect labels when form validation fails for another field

## 2025.5.2

- Add `hide_selected` configuration option
- Introduce `LazyView` to simplify working with autocomplete view/url/model from form fields and widgets
- Fix issue where clearing a search query would stop returning results
- Fix issue where reopening a dropdown sometimes showed no options
- Improve performance when a large number of items are pre-selected (automatically paginate through content)
- Fix double-escaping of content in templates
- Return explicit messages for `PermissionDenied` errors
- Update all logging to use modulo formatting instead of f-strings

## 2025.5.1

- Add `virtual_fields` attribute to autocomplete views, resolving issues #34 and #35
- Handle `value_fields` vs `virtual_fields` correctly via `__init_subclass__`
- Improve mutation observer to handle htmx more explicitly and hide select elements correctly
- Add htmx-in-Bootstrap-tabs demo
- Add formset prefix support in example app
- Prevent error details from leaking to output when `DEBUG` is `False`

## 2025.3.3

- Security fix: escape and sanitize all variables and data passed to JavaScript

## 2025.3.2

- Handle dict as input to `get_iterable` (#28)
- Fix issue caused by optimizing for example instead of general case (#27)

## 2025.3.1

- Improve how merged configs handle defaults (ensure all defaults are included if not explicitly overridden)
- Check that `label_field` is in `value_fields`
- Add htmx re-load button
- Add Security policy
- Update docs for `TomSelectChoiceField` and `TomSelectMultipleChoiceField`
- Update dependencies

## 2025.2.3

- Fix issue where permission checks ran even when `permission_required` was set to `None`

## 2025.2.2

- Improve how list and create view URLs are built and validated
- Add template tags to check whether global config JS has already been loaded by another widget (prevents duplicate script tags)
- Correct code examples in README

## 2025.1.2

- Add formset support - reformulate how TomSelect is initialized to work with formsets
- Add examples for a basic formset and a model formset
- Add formset tests
- Correct form field setup in docs (queryset attribute is not needed)
- Update README form example to use `TomSelectConfig`

## 2025.1.1

- Improve escaping and input handling
- Expand test coverage

## 2024.12.7

- Correct implementation for proxy request class

## 2024.12.6

- Ensure translated strings work in plugin dropdown header

## 2024.12.5

- Use an IIFE to create a new scope and avoid potential variable namespace conflicts in JavaScript

## 2024.12.4

- Improve package logging
- Refactor and re-implement tests for proxy request

## 2024.12.3

- Correct how request proxy is implemented in settings and document its use
- Minor formatting and layout improvements

## 2024.12.2

- Complete refactor of the django_tomselect source with breaking changes
- Major update to example project with ~15 different examples
- Overhaul documentation with new images, consolidated pages, and improved content
- Improvements to static file building - reduced final bundle size by half
- Expanded and updated test suite

## 0.4.3

- Add ability to trigger TomSelect creation on individual elements

## 0.4.2

- Add ability to specify the Bootstrap version at project & widget level

## 0.4.1

- Minor linting improvements
- Expand and correct text in README
- Correct licence header

## 0.4.0 (initial release post-fork from mizdb-tomselect)

- Rename package to `django-tomselect`
- Add ability to turn on/off the value field in tabular widget
- Change `search_lookup` to `search_lookups` to allow multiple lookups
- Improve documentation
