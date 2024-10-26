"""Request object used by the widget to obtain the initial QuerySet."""

from django.db import models


class DefaultProxyRequest:  # pylint: disable=R0903
    """Used as a stand-in for a real request when obtaining the initial QuerySet for the widget."""

    def __init__(self, *args, model: models.Model = None, **kwargs):  # pylint: disable=W0613
        self.model = model
        self.GET = {"q": "", "model": self.model._meta.label_lower if self.model else ""}  # pylint: disable=C0103
        self.POST = {}  # pylint: disable=C0103
        self.method = "GET"
