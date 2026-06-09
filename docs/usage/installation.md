# Installation

`django_tomselect` provides form fields and widgets to integrate [Tom Select](https://tom-select.js.org/) into your Django projects, enabling dynamic and customizable `<select>` elements with advanced features like autocomplete, tagging, and search. Follow the steps below to install and configure the package in your project.

Most of the code samples below are based on the example app provided with the package. You can find the complete example app in the `example_project/example/` directory of the repository.

## Install the Package

You can install `django_tomselect` via pip:

```bash
pip install django-tomselect
```

This installs the latest release of `django_tomselect` and its dependencies.

## Add to `INSTALLED_APPS`

In your Django project's `settings.py`, add `django_tomselect` to the `INSTALLED_APPS` list:

```python
INSTALLED_APPS = [
    ...,
    "django_tomselect",
]
```

## Add the middleware and context processor

The middleware and context processor ensure a request context is provided for each form field (and widget) that requires it.

Add the `django_tomselect.middleware.TomSelectMiddleware` to your middleware list:

```python
MIDDLEWARE = [
    ...,
    "django_tomselect.middleware.TomSelectMiddleware",
]
```

Add the `django_tomselect.context_processors.tomselect` context processor to your template context processors:

```python
TEMPLATES = [
    {
        ...,
        "OPTIONS": {
            "context_processors": [
                ...,
                "django_tomselect.context_processors.tomselect",
            ],
        },
    },
]
```

## Note on Django Management Commands

`django_tomselect` includes an internal `EmptyModel` that serves as a placeholder for widget querysets. This model has `managed = False`, meaning Django does not create a database table for it.

When running `dumpdata`, you may encounter an error like:

```
CommandError: Unable to serialize database: relation "django_tomselect_emptymodel" does not exist
```

To resolve this, exclude the `django_tomselect` app when dumping data:

```bash
python manage.py dumpdata --exclude django_tomselect
```

This is the [recommended approach by Django](https://code.djangoproject.com/ticket/13816) for handling unmanaged models that don't have corresponding database tables.

## Verify Required Dependencies

`django_tomselect` integrates Tom Select with Django forms. Ensure you meet the following minimum requirements:

- **Python**: Version 3.11 or higher is required.
- **Django**: Version 4.2 or higher is required. Django 4.2, 5.1, 5.2, and 6.0 are officially supported.
- **Tom Select**: Bundled via static files. You don't need to separately install Tom Select.

## Static Files

Confirm your static files setup is correct. Run:

```bash
python manage.py collectstatic
```

This collects the CSS, JavaScript, and related assets from `django_tomselect` (including Tom Select’s bundled files) into your static root.

## Include Tom Select in Your HTML

`django_tomselect` uses Django’s form media mechanism to load Tom Select’s CSS and JS. In any template where you plan to use `django_tomselect` widgets, ensure that you include the form’s media.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    {{ form.media }}
</head>
<body>
</body>
</html>
```

This can also be done in a base template using the provided template tags. It is particularly useful if you will be loading one or more forms with tomselect fields via htmx.

```html
{% load django_tomselect %}
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Other head content -->
    {% csrf_token %}
    {% tomselect_media %}
    <!-- Optionally specify a css_framework: {% tomselect_media css_framework="bootstrap5" %} -->
</head>
<body>
</body>
</html>
```

If you prefer manual control, you can include only CSS or JS separately:

```django
{% tomselect_media_css css_framework="bootstrap4" %}
{% tomselect_media_js %}
```

These tags insert the appropriate `<link>` and `<script>` elements for Tom Select assets.

## When to Use Template Tags Over `form.media`

- **Global Availability**: If your layout loads forms after the page is rendered or conditionally via AJAX, having the Tom Select assets already included in the base template ensures the environment is ready before forms appear.
- **Consistent Theming**: Applying a global CSS framework choice or custom Tom Select styling in the base template means all subsequently loaded forms will follow the same look without needing to repeat configuration.
- **Cleaner Templates**: Keeping the media loading logic in a single place (like the base template) can simplify templates that render forms, making it easier to maintain and update.

While `{{ form.media }}` is suitable for inline, one-off usage, the template tags `{% tomselect_media %}`, `{% tomselect_media_css %}`, and `{% tomselect_media_js %}` give you more control and flexibility in how and where you load Tom Select’s assets.

## Optional: Configure CSS Framework

`django_tomselect` supports multiple CSS frameworks for styling. You can choose a default framework in `settings.py`:

```python
TOMSELECT = {
    "DEFAULT_CSS_FRAMEWORK": "bootstrap5",  # Options: "default", "bootstrap4", "bootstrap5"
}
```

You can override this at any point using template tags (e.g., `{% tomselect_media css_framework="bootstrap4" %}`) or by configuring the widget on a per-field basis. For the full list of supported values and how they affect styling, see [CSS Framework Options](configuration.md).

!!! note "Load Bootstrap CSS first"
    When using `bootstrap5` (or `bootstrap4`), include the Bootstrap stylesheet **before** `{% tomselect_media %}`. The Bootstrap 5 theme relies on CSS custom properties that Bootstrap defines. Fallback values are included so the widget renders without Bootstrap, but loading Bootstrap first ensures the most accurate styling.
