# Changelog

## django-tomselect 2024.10.1


## django-tomselect 0.5.1b0

- Rewrote large portions of the package
- Implemented templates for each renderable callback
- Now uses form fields vice widgets to allow updating the queryset correctly
- Simplified from 4 wigets to 2 fields
- Implemented configuration objects to customize behavior

## django-tomselect 0.4.2

- Add ability to trigger tomselect creation on individual elements

## django-tomselect 0.4.2

- Add ability to specify the bootstrap version to use at project & widget level

## django-tomselect 0.4.1

- Minor linting improvements
- Expand and correct text in README
- Correct licence header

## django-tomselect 0.4.0

- Rename package to `django-tomselect`
- Add ability to turn on/off the value field in tabular widget
- Change `search_lookup` to `search_lookups` to allow multiple lookups
- Improve documentation

---

## mizdb-tomselect [unreleased]

- assign search term as AutocompleteView instance variable 'q'
- wrap create_object in an atomic block

## mizdb-tomselect 0.3.3 (2023-06-29)

- fix dropdown footer being visible when it has no content (#2)
- set sensible defaults for widget attributes (#3, #4)

## mizdb-tomselect 0.3.2 (2023-06-28)

- AutocompleteView: unquote search var string
- call values() on result queryset with fields specified on the widget only
  - this reduces query overhead 
  - allows including values from many-to-one relations

## mizdb-tomselect 0.3.1 (2023-06-20)

- fix handling of undefined column data

## mizdb-tomselect 0.3.0 (2023-06-20)

- refactor filterBy filtering in autocomplete view 
- add `search_lookup` argument to MIZSelect widget
- AutocompleteView now uses the `search_lookup` to filter the results

## mizdb-tomselect 0.2.0 (2023-06-20)

- initial release