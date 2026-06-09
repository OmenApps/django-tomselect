# Core Components

`django_tomselect` is built around a few key components that work together to provide a seamless autocomplete and selection experience in your Django forms. Understanding these components will help you configure and customize the behavior of Tom Select in your application.

## Autocompletes

Autocompletes are server-side views that respond to requests from the Tom Select widget. They provide the data-often filtered or searched by the user’s query-that populates the dropdown. Implementing an autocomplete view is crucial for any dynamic search functionality.

### `AutocompleteModelView`

- **Purpose**: Serves as the primary autocomplete endpoint for model-based data.
- **Typical Use Case**: When you want to provide a list of model instances (e.g., `Magazine` objects) to a Tom Select widget, allowing the user to search by name and select one or more items.
- **Key Features**:
  - Configurable `search_lookups` to filter data (e.g., `name__icontains`).
  - Supports pagination, ordering, and filtering by additional parameters.
  - Integrates with Django’s authentication and permission system.
  - Can be subclassed to customize search logic (`search()`, `get_queryset()`), filtering (`apply_filters()`), and result formatting (`prepare_results()`).

### `AutocompleteIterablesView`

- **Purpose**: Provides autocomplete data for simple iterables (lists, tuples, or Django choices), rather than model querysets.
- **Typical Use Case**: When selecting from a static list of values (e.g., a list of countries) without hitting the database.
- **Key Features**:
  - Offers search capabilities over a static set of values.
  - Pagination and incremental loading for large sets of options.
  - Simpler than `AutocompleteModelView`, since no ORM queries are involved.

:::{note}
Could you manually add Tom Select to your project and supply iterables as context to the template? Absolutely. But `django_tomselect` standardizes the process, providing a consistent API, integration with Django forms, and advanced features like filtering and server-side pagination for large datasets.
:::

## Form Fields

Form fields integrate `django_tomselect` widgets into Django’s form system, making it easy to replace traditional `ModelChoiceField` or `ModelMultipleChoiceField` fields with Tom Select-enabled versions.

- **TomSelectModelChoiceField**:
  - Single-select field, wrapping a `ModelChoiceField`.
  - Ideal when the user must pick exactly one model instance.

- **TomSelectModelMultipleChoiceField**:
  - Multi-select field, wrapping a `ModelMultipleChoiceField`.
  - Enables the user to select multiple model instances.

- **TomSelectChoiceField**:
  - Single-select field for static choices (e.g., tuples, lists, or Django choices).
  - Similar to `TomSelectModelChoiceField`, but for non-model data.

- **TomSelectMultipleChoiceField**:
  - Multi-select field for static choices.
  - Similar to `TomSelectModelMultipleChoiceField`, but for non-model data.

**Key Features**:

- Each field type automatically binds to a corresponding Tom Select widget.
- Configurations (e.g., `url`, `placeholder`, `search_lookups`) are provided through `TomSelectConfig`.
- Behaves like a standard Django model field, making it easy to integrate into `ModelForm`s.
- Ensures validation and data integrity: the chosen options must exist in the referenced queryset.

## Widgets

Widgets handle the front-end presentation and behavior of the fields. They render the `<select>` element, attach the appropriate JavaScript initialization code, and integrate with the autocomplete views.

- **TomSelectModelWidget**:
  - For single-select fields.
  - Renders as a Tom Select-enhanced `<select>` field, loading data from a specified autocomplete endpoint.

- **TomSelectModelMultipleWidget**:
  - For multi-select fields.
  - Similar to `TomSelectModelWidget`, but allows multiple item selection.

- **TomSelectWidget**:
  - For static choice fields.
  - Renders a Tom Select-enhanced `<select>` field for static choices.

- **TomSelectMultipleWidget**:
  - For static multiple choice fields.
  - Similar to `TomSelectWidget`, but for multiple selections.

**Key Features**:

- Customize look, feel, and behavior through `TomSelectConfig` and widget attributes.
- Seamless integration with autocomplete views: the widget automatically fetches data based on user input.
- Supports advanced features like dependent/chained fields, custom templates, plugin configurations, and HTMX integration.
- Works well with different CSS frameworks (e.g., Bootstrap) for styling, as well as custom templates for full UI control.
