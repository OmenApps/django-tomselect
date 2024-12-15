# Context Processors and Middleware

This documentation covers the context processors and middleware components that support TomSelect's functionality.

## Context Processors

```{eval-rst}
.. automodule:: django_tomselect.context_processors
   :members:
   :show-inheritance:
```

### Usage

Add the context processor to your template context processors in settings.py:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                # ... other context processors ...
                'django_tomselect.context_processors.tomselect',
            ],
        },
    },
]
```

This makes the request object available in templates for TomSelect widgets, which is necessary for permission checking and URL generation.

### Example

```django
{# In your template #}
{% if tomselect_request.user.is_authenticated %}
    {{ form.author }}  {# TomSelect widget with proper permissions #}
{% endif %}
```

## Middleware

```{eval-rst}
.. automodule:: django_tomselect.middleware
   :members:
   :show-inheritance:
```

The middleware component manages the request object in thread-local storage, making it available throughout the TomSelect widget rendering process.

### Installation

Add the middleware to your MIDDLEWARE setting:

```python
MIDDLEWARE = [
    # ... other middleware ...
    'django_tomselect.middleware.TomSelectMiddleware',
]
```

### How It Works

The middleware:
1. Stores the request object in thread-local storage
2. Makes it available during widget rendering
3. Cleans up the storage after the response
4. Supports both synchronous and asynchronous requests

### Accessing the Request

You can access the current request using the provided utility function:

```python
from django_tomselect.middleware import get_current_request

def my_function():
    request = get_current_request()
    if request and request.user.is_authenticated:
        # Do something with the request
        pass
```

### ASGI Support

The middleware automatically handles both WSGI and ASGI deployments. For ASGI, it uses the `asgiref.local.Local` implementation instead of `threading.local`.

```python
# No additional configuration needed
from django.core.asgi import get_asgi_application
application = get_asgi_application()
```

### Thread Safety

The middleware ensures thread safety by:
- Using thread-local storage
- Properly cleaning up after each request
- Supporting concurrent requests

### Example Use Case

```python
from django_tomselect.widgets import TomSelectModelWidget
from django_tomselect.middleware import get_current_request

class CustomWidget(TomSelectModelWidget):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        request = get_current_request()
        if request and request.user.is_authenticated:
            context['widget']['show_create'] = request.user.has_perm('app.create_model')
        return context
```
