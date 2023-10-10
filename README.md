
# Tom Select for Django

Django autocomplete form fields and views using [Tom Select](https://tom-select.js.org/).

This package provides a Django autocomplete field and view that can be used
together to provide a user interface for selecting a model instance from a
database table.

The package is adapted from the fantastic work of [Philip Becker](https://pypi.org/user/actionb/)
in [mizdb-tomselect](https://www.pypi.org/project/mizdb-tomselect/), with the goal of a more
generalized solution for Django autocompletion and a focus on use of django templates, 
translations, customization, explicitness, and minimal use of custom JavaScript

<!-- TOC -->
* [Tom Select for Django](#tom-select-for-django)
  * [Examples](#examples)
  * [Installation](#installation)
  * [Usage](#usage)
  * [Form Fields](#form-fields)
    * [TomSelectField & TomSelectMultipleField](#tomselectfield--tomselectmultiplefield)
  * [Configuration Objects](#configuration-objects)
    * [GeneralConfig](#generalconfig)
    * [PluginCheckboxOptions](#plugincheckboxoptions)
    * [PluginDropdownInput](#plugindropdowninput)
    * [PluginVirtualScroll](#pluginvirtualscroll)
    * [PluginClearButton](#pluginclearbutton)
    * [PluginRemoveButton](#pluginremovebutton)
    * [PluginDropdownHeader](#plugindropdownheader)
    * [PluginDropdownFooter](#plugindropdownfooter)
      * [Adding more columns to the fields](#adding-more-columns-to-the-fields)
  * [Settings](#settings)
  * [Function & Features](#function--features)
    * [Modifying the initial QuerySet](#modifying-the-initial-queryset)
    * [Searching](#searching)
    * [Option creation](#option-creation)
    * [List View link](#list-view-link)
    * [Chained Dropdown Filtering](#chained-dropdown-filtering)
  * [Advanced Topics](#advanced-topics)
    * [Manually Initializing Tom Select Fields](#manually-initializing-tom-select-fields)
  * [Development & Demo](#development--demo)
    * [Customizing Templates](#customizing-templates)
    * [Translations](#translations)
<!-- TOC -->

----

## Examples

The following examples show the Tom Select fields in action. The first two examples
show the Tom Select fields with single selection, with and without the tabular display.

![Tom Select With Single Select](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/assets/Single.png)

![Tom Select Tabular With Single Select](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/assets/SingleTabular.png)

The next two examples show the Tom Select fields with multiple selection, with and 
without the tabular display.

![Tom Select With Multiple Select](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/assets/Multiple.png)

![Tom Select Tabular With Multiple Select](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/assets/MultipleTabular.png)

## Installation

Install:

```bash
pip install -U django-tomselect
```

## Usage

Add to installed apps:

```python
INSTALLED_APPS = [
    # ...
    "django_tomselect"
]
```

Add an autocomplete view for each model that you want to use with django-tomselect:

```python
# views.py
from django_tomselect.views import AutocompleteView
from .models import City, Person


class CityAutocompleteView(AutocompleteView):
    model = City

class PersonAutocompleteView(AutocompleteView):
    model = Person
    search_lookups = [
        "full_name__icontains",
    ]
```

Configure endpoints for autocomplete requests:

```python
# urls.py
from django.urls import path

from .views import CityAutocompleteView, PersonAutocompleteView

urlpatterns = [
    # ...
    path("autocomplete-person/", PersonAutocompleteView.as_view(), name="person_autocomplete"),
    path("autocomplete-city/", CityAutocompleteView.as_view(), name="city_autocomplete"),
]
```

To make the field display tabular results, create a PluginDropdownHeader configuration object:

```python
from django_tomselect.configs import PluginDropdownHeader

person_plugin_dropdown_header = PluginDropdownHeader(
    # The column header label for the valueField column
    value_field_label="ID",
    # The column header label for the labelField column
    label_field_label="Full Name",
    extra_columns={
        "first_name": "First Name",
        "last_name": "Last Name",
    },
)
```

Use the fields in a form.

```python
from django import forms

from django_tomselect.forms import TomSelectField
from .models import City, Person


class MyForm(forms.Form):
    city = TomSelectField(
        url="my_autocomplete_view",
        value_field="id",
        label_field="name",
    )

    # Display results in a table, with additional columns for fields
    # "first_name" and "last_name":
    person = TomSelectField(
        url="my_autocomplete_view",
        value_field="id",
        label_field="full_name",
        plugin_dropdown_header=person_plugin_dropdown_header,
    )
``` 

NOTE: Make sure to include [bootstrap](https://getbootstrap.com/docs/5.2/getting-started/download/) 
4 or 5, and the form media (or manually add the tomselect css and js files) in your template:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Django Tom Select Demo</title>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4" crossorigin="anonymous"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65" crossorigin="anonymous">
    {{ form.media }}
</head>
<body>
<div class="container">
    <form>
        {% csrf_token %}
        {{ form.as_div }}
        <button type="submit" class="btn btn-success">Save</button>
    </form>
</div>
</body>
</html>
```

----

## Form Fields

The form fields pass attributes necessary to make autocomplete requests to the
HTML element via the dataset property. The Tom Select element is then initialized
from the attributes in the dataset property.

### TomSelectField & TomSelectMultipleField

Base autocomplete fields for `ModelChoiceField` and `ModelMultipleChoiceField`. The arguments of TomSelectField & TomSelectMultipleField are:

| Argument                | Default value                          | Type                   | Description                                                                             |
|-------------------------|----------------------------------------|------------------------|-----------------------------------------------------------------------------------------|
| model                   | **required**                           | Model                  | the model class that provides the choices                                               |
| url                     | `"autocomplete"`                       | str                    | URL pattern name of the autocomplete view                                               |
| value_field             | `f"{model._meta.pk.name}"`             | str                    | model field that provides the value of an option                                        |
| label_field             | `getattr(model, "name_field", "name")` | str                    | model field that provides the label of an option                                        |
| create_field            | ""                                     | str                    | model field name used to create new objects with ([see below](#ajax-request))           |
| listview_url            | ""                                     | str                    | URL name of the list view for this model ([see below](#list-view-link))                 |
| create_url              | ""                                     | str                    | URL name of the create view for this model([see below](#option-creation))               |
| update_url              | ""                                     | str                    | URL name of the update view for each instance of this model([see below](#option-edits)) |
| filter_by               | ()                                     | tuple                  | a 2-tuple defining an additional filter ([see below](#chained-dropdown-filtering))      |
| bootstrap_version       | 5                                      | int (4 or 5)           | the bootstrap version to use, either `4` or `5`                                         |
| general_config          | GeneralConfig()                        | GeneralConfig          | A GeneralConfig object or None                                                          |
| plugin_checkbox_options | PluginCheckboxOptions()                | PluginCheckboxOptions  | A PluginCheckboxOptions object or None                                                  |
| plugin_dropdown_input   | PluginDropdownInput()                  | PluginDropdownInput    | A PluginDropdownInput object or None                                                    |
| plugin_virtual_scroll   | PluginVirtualScroll()                  | PluginVirtualScroll    | A PluginVirtualScroll object or None                                                    |
| plugin_clear_button     | PluginClearButton()                    | PluginClearButton      | A PluginClearButton object or None                                                      |
| plugin_remove_button    | PluginRemoveButton()                   | PluginRemoveButton     | A PluginRemoveButton object or None                                                     |
| plugin_dropdown_header  | PluginDropdownHeader()                 | PluginDropdownHeader   | A PluginDropdownHeader object or None                                                   |
| plugin_dropdown_footer  | PluginDropdownFooter()                 | PluginDropdownFooter   | A PluginDropdownFooter object or None                                                   |

## Configuration Objects

The TomSelect fields can be configured be passing in instances of the following classes from django_tomselect.configs:

| Class                                            | Description                                                                                                 |
|--------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `django_tomselect.configs.GeneralConfig`         | Base class for all configuration objects.                                                                   |
| `django_tomselect.configs.PluginCheckboxOptions` | Configures Tom Select to display results with checkboxes.                                                   |
| `django_tomselect.configs.PluginDropdownInput`   | Configures the Tom Select dropdown to display an input field for searching and displaying selected results. |
| `django_tomselect.configs.PluginVirtualScroll`   | Configures Tom Select to use virtual scrolling, retrieving results as needed.                               |
| `django_tomselect.configs.PluginClearButton`     | Configures Tom Select to display a button to clear all selected values.                                     |
| `django_tomselect.configs.PluginRemoveButton`    | Configures Tom Select to display a button to clear a single selected value.                                 |
| `django_tomselect.configs.PluginDropdownHeader`  | Configures the Tom Select dropdown to display results in a table.                                           |
| `django_tomselect.configs.PluginDropdownFooter`  | Configures the footer to be displayed in the Tom Select dropdown.                                           |

### GeneralConfig

Available arguments:

| Argument           | Default value    | Type            | Description                                                                                                                                                                                                                                                                               |
|--------------------|------------------|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| close_after_select | None             | bool or None    | After a selection is made, the dropdown will remain open if in a multi-selection control or will close in a single-selection control. Setting to True will force the dropdown to close after selections are made. Setting to False will keep the dropdown open after selections are made. |
| hide_placeholder   | None             | bool or None    | If True, the placeholder will be hidden when the control has one or more items (selected options) and is not focused. This defaults to False when in a multi-selection control, and to True otherwise.                                                                                    |
| highlight          | True             | bool            | Toggles match highlighting within the dropdown menu when a search term is entered                                                                                                                                                                                                         |
| load_throttle      | 300              | int             | The number of milliseconds to wait before requesting options from the server or None. If None, throttling is disabled. Useful when loading options dynamically while the user types a search / filter expression.                                                                         |
| loading_class      | "loading"        | str             | The class name added to the wrapper element while awaiting the fulfillment of load requests.                                                                                                                                                                                              |
| max_items          | 50               | int             | The max number of items the user can select. A value of 1 makes the control mono-selection, None allows an unlimited number of items.                                                                                                                                                     |
| max_options        | 50               | int or None     | The max number of options to display in the dropdown. Set to None for an unlimited number of options.                                                                                                                                                                                     |
| open_on_focus      | True             | bool            | Show the dropdown immediately when the control receives focus.                                                                                                                                                                                                                            |
| placeholder        | "Select a value" | str or None     | The placeholder of the field. Defaults to input widget's placeholder, unless this one is specified.                                                                                                                                                                                       |
| preload            | "focus"          | bool or "focus" | If True, the load function will be called upon control initialization (with an empty search). Alternatively it can be set to "focus" to call the load function when control receives focus.                                                                                               |
| create             | False            | bool            | Determines if the user is allowed to create new items that aren't in the initial list of options.                                                                                                                                                                                         |
| create_filter      | None             | str or None     | Specifies a RegExp or a string containing a regular expression that the current search filter must match to be allowed to be created. May also be a predicate function provided as a string that takes the filter text and returns whether it is allowed.                                 |
| create_with_htmx   | False            | bool            | Reserved for future use.                                                                                                                                                                                                                                                                  |
         
### PluginCheckboxOptions

Available arguments: None

### PluginDropdownInput

Available arguments: None

### PluginVirtualScroll

Available arguments: None

### PluginClearButton

Overridable template: `django_tomselect/render/clear_button.html`

Available arguments:

| Argument   | Default value      | Description                                            |
|------------|--------------------|--------------------------------------------------------|
| title      | "Clear Selections" | A string to use as the title of the clear button.      |
| class_name | "clear-button"     | A string to use as the class name of the clear button. |

### PluginRemoveButton

Available arguments:

| Argument   | Default value      | Description                                            |
|------------|--------------------|--------------------------------------------------------|
| title      | "Remove this item" | A string to use as the title of the remove button.     |
| label      | "&times;"          | A string to use as the label of the remove button.     |
| class_name | "remove"           | A string to use as the class name of the clear button. |


### PluginDropdownHeader

Overridable template: `django_tomselect/render/dropdown_header.html`

Adding this configuration object displays the results in tabular form. A table header will be
added to the dropdown. By default, the table contains two columns: one column for the choice 
value (commonly the "ID" of the option) and one column for the choice label (the 
human-readable part of the choice).

Available arguments:

| Argument          | Default value                                                               | Description                                                                                                                    |
|-------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| extra_columns     | {}                                                                          | a dict mapping for additional columns to be displayed, where the key is the model field name and the value is the column label |
| header_class      | "container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header" | the classes to use for the header container                                                                                    |
| title_row_class   | "row"                                                                       | the classes to use for the title row                                                                                           |
| label_class       | "form-label"                                                                | the classes to use for the label column                                                                                        |
| value_field_label | `f"{value_field.title()}"`                                                  | table header for the value column                                                                                              |
| label_field_label | `f"{model._meta.verbose_name}"`                                             | table header for the label column                                                                                              |
| show_value_field  | `False`                                                                     | show the value field column (typically `id`)                                                                                   |

### PluginDropdownFooter

Overridable template: `django_tomselect/render/dropdown_footer.html`

Adding this configuration object includes a footer below the results dropdown. By default, the footer
contains a link to the list view of the model, if the `listview_url` argument is provided to the field.

Available arguments:

| Argument          | Default value                                                               | Description                                                                                                                    |
|-------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| extra_columns     | {}                                                                          | a dict mapping for additional columns to be displayed, where the key is the model field name and the value is the column label |
| header_class      | "container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header" | the classes to use for the header container                                                                                    |
| title_row_class   | "row"                                                                       | the classes to use for the title row                                                                                           |
| label_class       | "form-label"                                                                | the classes to use for the label column                                                                                        |
| value_field_label | `f"{value_field.title()}"`                                                  | table header for the value column                                                                                              |
| label_field_label | `f"{model._meta.verbose_name}"`                                             | table header for the label column                                                                                              |
| show_value_field  | `False`                                                                     | show the value field column (typically `id`)                                                                                   |


#### Adding more columns to the fields

To add more columns, pass a dictionary mapping field names to column labels as
`extra_columns` to the PluginDropdownHeader's arguments.

```python
from django import forms
from django_tomselect.configs import PluginDropdownHeader
from django_tomselect.forms import TomSelectField
from .models import Person


person_plugin_dropdown_header = PluginDropdownHeader(
    extra_columns={
        # field_name: column_label
        "first_name": "First Name",
        "last_name": "Last Name",
    },
)

class MyForm(forms.Form):
    person = TomSelectField(
        url="my_autocomplete_view",
        value_field="id",
        label_field="full_name",
        plugin_dropdown_header=person_plugin_dropdown_header,
    )
```

**Important**: that means that the result visible to Tom Select must have an 
attribute or property with that name or the field's contents will remain empty. 
The results for Tom Select are created by the view calling `values()` on the 
result queryset, so you must make sure that the attribute name is available
on the view's root queryset as either a model field or as an annotation.

----

## Settings

| Setting                                  | Default value                                                  | Type                                          | Description                                                                                                                                                                                                                                                              |
|------------------------------------------|----------------------------------------------------------------|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TOMSELECT_BOOTSTRAP_VERSION              | `5`                                                            | int (4 or 5)                                  | The bootstrap version to use. Either `4` or `5`. Defaults to `5`. This sets the project-wide default for the `bootstrap_version` argument of the fields. <p>You can overwrite the default for a specific field by passing the `bootstrap_version` argument to the field. |
| TOMSELECT_PROXY_REQUEST                  | `"django_tomselect.utils.DefaultProxyRequest"`                 | `DefaultProxyRequest` or subclass             | Either a direct reference to a DefaultProxyRequest subclass or the path to the DefaultProxyRequest subclass to use. See below.                                                                                                                                           |
| DJANGO_TOMSELECT_MINIFIED                | `django_tomselect.app_settings.currently_in_production_mode()` | Boolean or callable                           | Either a boolean or a callable that returns a boolean to determine whether to use minified static files.                                                                                                                                                                 |
| DJANGO_TOMSELECT_GENERAL_CONFIG          | GeneralConfig()                                                | Either a GeneralConfig object or None         | Sets the default for this configuration in all forms (can be overridden per-form). If not provided in settings, forms default to use the version provided in `django_tomselect.configs`.                                                                                 |
| DJANGO_TOMSELECT_PLUGIN_CLEAR_BUTTON     | PluginClearButton()                                            | Either a PluginClearButton object or None     | Sets the default for this configuration in all forms (can be overridden per-form). If not provided in settings, forms default to use the version provided in `django_tomselect.configs`.                                                                                 |
| DJANGO_TOMSELECT_PLUGIN_REMOVE_BUTTON    | PluginRemoveButton()                                           | Either a PluginRemoveButton object or None    | Sets the default for this configuration in all forms (can be overridden per-form). If not provided in settings, forms default to use the version provided in `django_tomselect.configs`.                                                                                 |
| DJANGO_TOMSELECT_PLUGIN_DROPDOWN_INPUT   | PluginDropdownInput()                                          | Either a PluginDropdownInput object or None   | Sets the default for this configuration in all forms (can be overridden per-form). If not provided in settings, forms default to use the version provided in `django_tomselect.configs`.                                                                                 |
| DJANGO_TOMSELECT_PLUGIN_DROPDOWN_HEADER  | PluginDropdownHeader()                                         | Either a PluginDropdownHeader object or None  | Sets the default for this configuration in all forms (can be overridden per-form). If not provided in settings, forms default to use the version provided in `django_tomselect.configs`.                                                                                 |
| DJANGO_TOMSELECT_PLUGIN_DROPDOWN_FOOTER  | PluginDropdownFooter()                                         | Either a PluginDropdownFooter object or None  | Sets the default for this configuration in all forms (can be overridden per-form). If not provided in settings, forms default to use the version provided in `django_tomselect.configs`.                                                                                 |
| DJANGO_TOMSELECT_PLUGIN_VIRTUAL_SCROLL   | PluginVirtualScroll()                                          | Either a PluginVirtualScroll object or None   | Sets the default for this configuration in all forms (can be overridden per-form). If not provided in settings, forms default to use the version provided in `django_tomselect.configs`.                                                                                 |
| DJANGO_TOMSELECT_PLUGIN_CHECKBOX_OPTIONS | PluginCheckboxOptions()                                        | Either a PluginCheckboxOptions object or None | Sets the default for this configuration in all forms (can be overridden per-form). If not provided in settings, forms default to use the version provided in `django_tomselect.configs`.                                                                                 |

**Note**: The DefaultProxyRequest class is used to obtain the model details for the autocomplete. 
In order to simplify the process of creating a custom autocomplete view, django-tomselect provides 
a `DefaultProxyRequest` class that can be used to obtain the model details from the queryset and the 
request. In most cases, you will not need to use this class directly.

----

## Function & Features

### Modifying the initial QuerySet

If you want to modify all autocomplete queries for a subclassed AutocompleteView, 
you can use `super()` with the `get_queryset()` method.

```python
from django_tomselect.views import AutocompleteView


class MyAutocompleteView(AutocompleteView):
    model = MyModel
    search_lookups = [
        "name__icontains",
    ]
    
    def get_queryset(self):
        """Toy example of filtering all queries in this view to id values less than 10"""
        queryset = super().get_queryset()
        queryset.filter(id__lt=10)
        return queryset
```

### Searching

The AutocompleteView filters the result QuerySet against `search_lookups`. 
The default value for the lookup is `[]`. Overwrite the `AutocompleteView.search` 
method to modify the search process.

```python
from django_tomselect.views import AutocompleteView


class MyAutocompleteView(AutocompleteView):
    model = MyModel
    search_lookups = [
        "name__icontains",
    ]
    
    def search(self, queryset, q):
        # Filter using your own queryset method:
        return queryset.search(q)
```

### Option creation

**Important**: This is a work in progress. The API may change in the future.

To enable option creation in the dropdown, pass the URL name of the create view of the given model to the field. 
This will add an 'Add' option to the bottom of the dropdown.


### List View link

The dropdown will include a link to the list view of the given model if you
pass in the URL pattern name of the list view.

```python
# urls.py
from django.urls import path
from django_tomselect.views import AutocompleteView
from django_tomselect.forms import TomSelectField
from .models import City
from .views import CityListView

urlpatterns = [
    # ...
    path("autocomplete/", AutocompleteView.as_view(), name="my_autocomplete_view"),
    path("city/list/", CityListView.as_view(), name="city_listview"),
]

# forms.py
city = TomSelectField(
    url="my_autocomplete_view",
    value_field="id",
    label_field="name",
    listview_url="city_listview",
)
```

### Chained Dropdown Filtering

**Important**: This is a work in progress. The API may change in the future.

Use the `filter_by` argument to restrict the available options of one 
TomSelectField to the value selected in another form field. The parameter must 
be a 2-tuple:  `(name_of_the_other_form_field, django_field_lookup)`

```python
# models.py
from django import forms
from django.db import models
from django_tomselect.forms import TomSelectField


class Person(models.Model):
    name = models.CharField(max_length=50)
    city = models.ForeignKey("City", on_delete=models.SET_NULL, blank=True, null=True)


class City(models.Model):
    name = models.CharField(max_length=50)
    is_capitol = models.BooleanField(default=False)


# forms.py
class PersonsFromCapitolsForm(forms.Form):
    capitol = forms.ModelChoiceField(queryset=City.objects.filter(is_capitol=True))
    person = TomSelectField(
        url="my_autocomplete_view",
        value_field="id",
        label_field="name",
        filter_by=("capitol", "city_id"),
    )
```

This will result in the Person result queryset to be filtered against 
`city_id` for the currently selected `capitol` formfield value.  
NOTE: When using `filter_by`, the declaring element now **requires** that the 
other field provides a value, since its choices are dependent on the other 
field. If the other field does not have a value, the search will not return any 
results.

## Advanced Topics

### Manually Initializing Tom Select Fields

If a form is added dynamically after the page loads (e.g.: with htmx), the new form 
fields will not be initialized as django-tomselect fields. In order to manually 
initialize them, dispatch a `triggerTomSelect` event, providing the id of the 
form field as a value in `detail` as follows.

```javascript
<script>
  window.dispatchEvent(new CustomEvent('triggerTomSelect', {
    detail: {
        elemID: 'id_tomselect_tabular'
    }
  }));
</script>
````

---

## Development & Demo

```bash
python3 -m venv venv
source venv/bin/activate
make init
```

Then see the demo for a preview: `python demo/manage.py runserver`

Run tests with `make test` or `make tox`. To install required browsers for playwright: `playwright install`.
See the makefile for other commands.


### Customizing Templates

All templates are located in [`django_tomselect/templates/django_tomselect/`](https://github.com/jacklinke/django-tomselect/tree/main/src/django_tomselect/templates/django_tomselect).

The base template for the widgets is `select.html`. It contains the HTML structure for the custom widget and form field.

Additionally, each of the [Render Templates](https://tom-select.js.org/docs/#render-templates) has its own template.

The templates are rendered with the following context:

| Variable | Description |
|----------|-------------|
| `ToDo`   | ToDo        |

You can override templates by creating a template with the same name in your project's `templates/django_tomselect/` directory.

### Translations

There are a handful of strings in the default templates that are marked for translation.

Before a new language can be added, the LANGUAGES setting must be updated with the new language code.

```python
LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
    ('de', _('Deutsch')),
)
````

To update translations, from the django_tomselect directory run `python ../../manage.py maketmessages -a`. 
This will update the `.po` files in `django_tomselect/locale/` directory. Once translations files  have been 
updated, compile them with `python ../../manage.py compilemessages`.