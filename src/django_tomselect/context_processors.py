"""Context processors for django_tomselect."""


def tomselect(request):
    """Add tomselect-related context to the template context.

    Currently just adds the request for use in templates.
    """
    return {
        "tomselect_request": request,
    }
