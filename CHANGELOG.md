# Changelog

## 2026.3.1 (unreleased)

- Suppress spurious URL warnings when `show_list` or `show_create` are `False` (#46)
- Remove docker compose (not needed for this project) and update tooling
- Standardize README badges

## 2026.1.3

- Update bundled Tom Select static files to latest version
- Fix JSON serialization fallback — was incorrectly falling back to `json.JSONEncoder` instead of `DjangoJSONEncoder`, which couldn't handle common Django objects
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

- Add formset support — reformulate how TomSelect is initialized to work with formsets
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
- Improvements to static file building — reduced final bundle size by half
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
