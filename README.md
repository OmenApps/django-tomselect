
# Tom Select for Django

Django autocomplete widgets and views using [Tom Select](https://tom-select.js.org/).

This package provides a Django autocomplete widget and view that can be used
together to provide a user interface for selecting a model instance from a
database table.

The package is adapted from the fantastic work of 
[Philip Becker](https://pypi.org/user/actionb/) in 
[mizdb-tomselect](https://www.pypi.org/project/mizdb-tomselect/), with the goal 
of a more generalized solution for Django autocompletion.

<!-- TOC -->
* [Tom Select for Django](#tom-select-for-django)
  * [Installation](#installation)
  * [Usage](#usage)
  * [Widgets](#widgets)
    * [TomSelectWidget](#tomselectwidget)
    * [TomSelectTabularWidget](#tomselecttabularwidget)
      * [Adding more columns](#adding-more-columns-)
  * [Settings](#settings)
    * [TOMSELECT_BOOTSTRAP_VERSION](#tomselectbootstrapversion)
  * [Function & Features](#function--features)
    * [Modifying the initial QuerySet](#modifying-the-initial-queryset)
    * [Searching](#searching)
    * [Option creation](#option-creation)
      * [AJAX request](#ajax-request)
    * [List View link](#list-view-link)
    * [Chained Dropdown Filtering](#chained-dropdown-filtering)
  * [Manually Initializing Tom Select Fields](#manually-initializing-tom-select-fields)
  * [Development & Demo](#development--demo)
<!-- TOC -->

----

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

Configure an endpoint for autocomplete requests:

```python
# urls.py
from django.urls import path

from django_tomselect.views import AutocompleteView

urlpatterns = [
    # ...
    path("autocomplete/", AutocompleteView.as_view(), name="my_autocomplete_view")
]
```

Use the widgets in a form.

```python
from django import forms

from django_tomselect.widgets import TomSelectWidget, TomSelectTabularWidget
from .models import City, Person


class MyForm(forms.Form):
    city = forms.ModelChoiceField(
        City.objects.all(),
        widget=TomSelectWidget(City, url="my_autocomplete_view"),
    )

    # Display results in a table, with additional columns for fields
    # "first_name" and "last_name":
    person = forms.ModelChoiceField(
        Person.objects.all(),
        widget=TomSelectTabularWidget(
            url="my_autocomplete_view",
            search_lookups=[
                "full_name__icontains",
            ],
            # for extra columns pass a mapping of {"model_field": "Column Header Label"}
            extra_columns={"first_name": "First Name", "last_name": "Last Name"},
            # The column header label for the labelField column
            label_field_label="Full Name",
        ),
    )

``` 

NOTE: Make sure to include [bootstrap](https://getbootstrap.com/docs/5.2/getting-started/download/) somewhere. For example in the template:

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

## Widgets

The widgets pass attributes necessary to make autocomplete requests to the
HTML element via the dataset property. The Tom Select element is then initialized
from the attributes in the dataset property.

### TomSelectWidget & TomSelectMultipleWidget

Base autocomplete widgets for `ModelChoiceField` and `ModelMultipleChoiceField`. The arguments of TomSelectWidget & TomSelectMultipleWidget are:

| Argument          | Default value                                                           | Description                                                                        |
|-------------------|-------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| model             | **required**                                                            | the model class that provides the choices                                          |
| url               | `"autocomplete"`                                                        | URL pattern name of the autocomplete view                                          |
| value_field       | `f"{model._meta.pk.name}"`                                              | model field that provides the value of an option                                   |
| label_field       | `getattr(model, "name_field", "name")`                                  | model field that provides the label of an option                                   |
| search_lookups    | `[f"{self.value_field}__icontains", f"{self.label_field}__icontains"]`  | the list of lookups to use when filtering the results                              |
| create_field      | ""                                                                      | model field to create new objects with ([see below](#ajax-request))                ||
| listview_url      | ""                                                                      | URL name of the list view for this model ([see below](#list-view-link))            |
| add_url           | ""                                                                      | URL name of the add view for this model([see below](#option-creation))             |
| edit_url           | ""                                                                      | URL name of the edit view for each instance of this model([see below](#option-edits))             |
| filter_by         | ()                                                                      | a 2-tuple defining an additional filter ([see below](#chained-dropdown-filtering)) |
| bootstrap_version | 5                                                                       | the bootstrap version to use, either `4` or `5`                                    |

### TomSelectTabularWidget & TomSelectTabularMultipleWidget

These widgets displays the results in tabular form. A table header will be added
to the dropdown. By default, the table contains two columns: one column for the choice 
value (commonly the "ID" of the option) and one column for the choice label (the 
human-readable part of the choice).

![Tabular select preview](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/assets/tomselect_tabular.png "Tabular select preview")

TomSelectTabularWidget & TomSelectTabularMultipleWidget have the following additional arguments:

| Argument          | Default value                   | Description                                  |
|-------------------|---------------------------------|----------------------------------------------|
| extra_columns     |                                 | a mapping for additional columns             |
| value_field_label | `f"{value_field.title()}"`      | table header for the value column            |
| label_field_label | `f"{model._meta.verbose_name}"` | table header for the label column            |
| label_field_label | `f"{model._meta.verbose_name}"` | table header for the label column            |
| show_value_field  | `False`                         | show the value field column (typically `id`) |

#### Adding more columns to the tabular widgets

To add more columns, pass a dictionary mapping field names to column labels as
`extra_columns` to the widget's arguments.

```python
from django import forms
from django_tomselect.widgets import TomSelectTabularWidget
from .models import Person


class MyForm(forms.Form):
    person = forms.ModelChoiceField(
        Person.objects.all(),
        widget=TomSelectTabularWidget(
            url="my_autocomplete_view",
            # for extra columns pass a mapping of {"model_field": "Column Header Label"}
            extra_columns={"first_name": "First Name", "last_name": "Last Name"},
        ),
    )

```

The column label is the header label for a given column in the table.  

The attribute name tells Tom Select what value to look up on a result for the column.

**Important**: that means that the result visible to Tom Select must have an attribute
or property with that name or the column will remain empty. 
The results for Tom Select are created by the view calling `values()` on the 
result queryset, so you must make sure that the attribute name is available
on the view's root queryset as either a model field or as an annotation.

----

## Settings

| Setting | Default value | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|---------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TOMSELECT_BOOTSTRAP_VERSION | `5` | The bootstrap version to use. Either `4` or `5`. Defaults to `5`. This sets the project-wide default for the `bootstrap_version` argument of the widgets. <p>You can overwrite the default for a specific widget by passing the `bootstrap_version` argument to the widget. This sets the project-wide default for the `bootstrap_version` argument of the widgets. You can overwrite the default for a specific widget by passing the `bootstrap_version` argument to the widget.</p>                                                                           |
| TOMSELECT_PROXY_REQUEST | `"django_tomselect.utils.DefaultProxyRequest"` | Either a direct reference to a DefaultProxyRequest subclass or the path to the DefaultProxyRequest subclass to use. This class is used to obtain the model details for the autocomplete. <p>In order to simplify the process of creating a custom autocomplete view, django-tomselect provides a `DefaultProxyRequest` class that can be used to obtain the model details from the queryset and the request. This class is used by the widget to obtain the model details for the autocomplete. In most cases, you will not need to use this class directly.</p> |

----

## Function & Features

### Modifying the initial QuerySet

If you want to modify all autocomplete queries for a subclassed AutocompleteView, you can use `super()` with the `get_queryset()` method.

```python
from django_tomselect.views import AutocompleteView


class MyAutocompleteView(AutocompleteView):
    def get_queryset(self):
        """Toy example of filtering all queries in this view to id values less than 10"""
        queryset = super().get_queryset()
        queryset.filter(id__lt=10)
        return queryset
```

### Searching

The AutocompleteView filters the result QuerySet against the `search_lookups`
passed to the widget. The default value for the lookup is `name__icontains`.
Overwrite the `AutocompleteView.search` method to modify the search process.

```python
from django_tomselect.views import AutocompleteView


class MyAutocompleteView(AutocompleteView):
    def search(self, queryset, q):
        # Filter using your own queryset method:
        return queryset.search(q)
```

### Option creation

To enable option creation in the dropdown, pass the URL pattern name of the 
add page of the given model to the widget. This will add an 'Add' button to the
bottom of the dropdown.

```python
# urls.py
from django.urls import path
from django_tomselect.views import AutocompleteView
from django_tomselect.widgets import TomSelectWidget
from .models import City
from .views import CityAddView

urlpatterns = [
    # ...
    path("autocomplete/", AutocompleteView.as_view(), name="my_autocomplete_view"),
    path("city/add/", CityAddView.as_view(), name="city_add"),
]

# forms.py
widget = TomSelectWidget(City, url="my_autocomplete_view", add_url="city_add")
```

Clicking on that button sends the user to the add page of the model.

#### AJAX request

If `create_field` was also passed to the widget, clicking on the button will
create a new object using an AJAX POST request to the autocomplete URL. The
autocomplete view will use the search term that the user put in on the
`create_field` to create the object:

```python
class AutocompleteView:
    
    def create_object(self, data):
        """Create a new object with the given data."""
        return self.model.objects.create(**{self.create_field: data[self.create_field]})
```

Override the view's `create_object` method to change the creation process.

### List View link

The dropdown will include a link to the list view of the given model if you
pass in the URL pattern name of the list view.

```python
# urls.py
from django.urls import path
from django_tomselect.views import AutocompleteView
from django_tomselect.widgets import TomSelectWidget
from .models import City
from .views import CityListView

urlpatterns = [
    # ...
    path("autocomplete/", AutocompleteView.as_view(), name="my_autocomplete_view"),
    path("city/list/", CityListView.as_view(), name="city_listview"),
]

# forms.py
widget = TomSelectWidget(City, url="my_autocomplete_view", listview_url="city_listview")
```

### Chained Dropdown Filtering

Use the `filter_by` argument to restrict the available options of one 
TomSelectWidget to the value selected in another form field. The parameter must 
be a 2-tuple:  `(name_of_the_other_form_field, django_field_lookup)`

```python
# models.py
from django import forms
from django.db import models
from django_tomselect.widgets import TomSelectWidget


class Person(models.Model):
    name = models.CharField(max_length=50)
    city = models.ForeignKey("City", on_delete=models.SET_NULL, blank=True, null=True)


class City(models.Model):
    name = models.CharField(max_length=50)
    is_capitol = models.BooleanField(default=False)


# forms.py
class PersonsFromCapitolsForm(forms.Form):
    capitol = forms.ModelChoiceField(queryset=City.objects.filter(is_capitol=True))
    person = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        widget=TomSelectWidget(Person, filter_by=("capitol", "city_id")),
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
