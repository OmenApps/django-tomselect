

# Django TomSelect

A powerful, lightweight Django package for dynamic select inputs with autocomplete, tagging, and more.

[![PyPI version](https://badge.fury.io/py/django-tomselect.png)](https://badge.fury.io/py/django-tomselect.png)
[![License](https://img.shields.io/pypi/l/django-tomselect.png)](https://github.com/OmenApps/django-tomselect/blob/main/LICENSE)

Django TomSelect integrates [Tom Select](https://tom-select.js.org/) into your Django projects, providing beautiful and intuitive select inputs with features like:

- **Live Search & Autocomplete**
    - Real-time filtering and highlighting as you type
    - Server-side search with customizable lookups
    - Automatic pagination for large datasets
	- Customizable minimum query length

- **Rich UI Options**
    - Single and multiple selection modes
    - Tabular display with custom columns
    - Bootstrap 4/5 theming support
	- Clear/remove buttons
	- Dropdown headers & footers
	- Checkbox options
    - Customizable templates

![Tom Select With Single Select](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/docs/images/Single.png)
![Tom Select Tabular With Multiple Select](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/docs/images/Multiple_Tabular.png)

## Quick Start

1. **Install the package:**
```bash
pip install django-tomselect
```

2. **Update settings.py:**
```python
INSTALLED_APPS = [
    ...
    "django_tomselect"
]

MIDDLEWARE = [
    ...
    "django_tomselect.middleware.TomSelectMiddleware",
    ...
]

TEMPLATES = [
    {
        "OPTIONS": {
            "context_processors": [
                ...
                "django_tomselect.context_processors.tomselect",
                ...
            ],
        },
    },
]
```

3. **Create an autocomplete view:**
```python
from django_tomselect.autocompletes import AutocompleteModelView

class PersonAutocompleteView(AutocompleteModelView):
    model = Person
    search_lookups = ["full_name__icontains"]
```

4. **Add URL pattern:**
```python
urlpatterns = [
    path("person-autocomplete/", PersonAutocompleteView.as_view(), name="person_autocomplete"),
]
```

5. **Use in your forms:**
```python
from django_tomselect.forms import TomSelectModelChoiceField

class MyForm(forms.Form):
    person = TomSelectModelChoiceField(
        url="person_autocomplete",
        value_field="id",
        label_field="full_name",
    )
```

6. **Include in your template:**
```html
{{ form.media }}  {# Adds the required CSS/JS #}

{{ form }}
```

## Other Features

### Advanced Filtering
- Dependent/chained select fields
- Field exclusion support
- Custom search implementations
- Hooks for overriding functionality

### Flexible Configuration
- Support for [Tom Select Plugins](https://tom-select.js.org/plugins/)
- Global settings and per-form-field configuration
- Override any template

### Security
- Built-in permission handling
	- including django auth, custom auth, object perms

### Internationalization
- Translation support
- Customizable messages

## Example Project

To see Django TomSelect in action, check out the [Example Project](https://github.com/OmenApps/django-tomselect/tree/main/example_project). It demonstrates a variety of use cases, with **15 different implementations** from basic atocompletion to advanced applications, showing how to use django-tomselect's autocomplete fields in a Django project.

Each of the examples is described in [the Example Project docs](https://django-tomselect.readthedocs.io/en/latest/example_app/introduction.html).

Here are a few screenshots from the example project:

![Rich Content Article Selection](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/docs/images/rich-article-select1.png)

---

![Article List](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/docs/images/article-list.png)

---

![Article Bulk Actions](https://raw.githubusercontent.com/jacklinke/django-tomselect/main/docs/images/article-bulk-action2.png)

## Documentation

- [Complete Usage Guide](https://django-tomselect.readthedocs.io/en/latest/usage.html)
- [Configuration Reference](https://django-tomselect.readthedocs.io/en/latest/api/config.html)
- [Example Project](https://django-tomselect.readthedocs.io/en/latest/example_app/introduction.html)

## Contributing

Contributions are welcome! Check out our [Contributor Guide](https://github.com/OmenApps/django-tomselect/blob/main/CONTRIBUTING.md) to get started.

## License

This project is licensed under the MIT License - see the [License](https://github.com/OmenApps/django-tomselect/blob/main/LICENSE) file for details.

## Acknowledgments

This package builds on the excellent work of [Philip Becker](https://pypi.org/user/actionb/) in [mizdb-tomselect](https://www.pypi.org/project/mizdb-tomselect/), with a focus on generalization, Django templates, translations, and customization.
