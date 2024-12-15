# Template Tags

The `django_tomselect` template tags provide utilities for including TomSelect's CSS and JavaScript assets in your templates.

## Usage

First, load the template tags in your template:

```django
{% load django_tomselect %}
```

```{eval-rst}
.. automodule:: django_tomselect.templatetags.django_tomselect
   :members:
```

## Media Tags

### tomselect_media

Includes all required CSS and JavaScript files for TomSelect.

```django
{% tomselect_media %}
```

With custom CSS framework:
```django
{% tomselect_media css_framework="bootstrap5" %}
```

With minification control:
```django
{% tomselect_media use_minified=True %}
```

This tag outputs:
```html
<!-- With default framework -->
<link href="/static/django_tomselect/vendor/tom-select/css/tom-select.default.min.css" rel="stylesheet" media="all">
<link href="/static/django_tomselect/css/django-tomselect.css" rel="stylesheet" media="all">
<script src="/static/django_tomselect/js/django-tomselect.min.js"></script>

<!-- With Bootstrap 5 -->
<link href="/static/django_tomselect/vendor/tom-select/css/tom-select.bootstrap5.min.css" rel="stylesheet" media="all">
<link href="/static/django_tomselect/css/django-tomselect.css" rel="stylesheet" media="all">
<script src="/static/django_tomselect/js/django-tomselect.min.js"></script>
```

### tomselect_media_css

Includes only the CSS files for TomSelect.

```django
{% tomselect_media_css %}
```

With custom CSS framework:
```django
{% tomselect_media_css css_framework="bootstrap4" %}
```

This tag outputs:
```html
<link href="/static/django_tomselect/vendor/tom-select/css/tom-select.bootstrap4.min.css" rel="stylesheet" media="all">
<link href="/static/django_tomselect/css/django-tomselect.css" rel="stylesheet" media="all">
```

### tomselect_media_js

Includes only the JavaScript files for TomSelect.

```django
{% tomselect_media_js %}
```

With minification control:
```django
{% tomselect_media_js use_minified=False %}
```

This tag outputs:
```html
<script src="/static/django_tomselect/js/django-tomselect.js"></script>
```

## Common Usage Patterns

### Base Template

Include the assets in your base template:

```django
{% load django_tomselect %}
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{% endblock %}</title>
    {% tomselect_media_css css_framework="bootstrap5" %}
</head>
<body>
    {% block content %}{% endblock %}

    {% tomselect_media_js %}
</body>
</html>
```

## CSS Framework Options

The template tags support the following CSS frameworks:

- `default`: Tom Select's default styling
- `bootstrap4`: Bootstrap 4 compatible styling
- `bootstrap5`: Bootstrap 5 compatible styling

```django
{# Default styling #}
{% tomselect_media %}

{# Bootstrap 4 #}
{% tomselect_media css_framework="bootstrap4" %}

{# Bootstrap 5 #}
{% tomselect_media css_framework="bootstrap5" %}
```

## Development vs Production

In development:
```django
{% tomselect_media use_minified=False %}
```

In production:
```django
{% tomselect_media use_minified=True %}
```

Or use Django's settings:
```python
# settings.py
TOMSELECT = {
    'DEFAULT_USE_MINIFIED': not DEBUG
}
```
