"""Widget tests for the django-tomselect package."""

import pytest
from django.db import models

from django_tomselect.widgets import TomSelectMultipleWidget, TomSelectWidget

# from django_tomselect.widgets import TomSelectTabularWidget
from example_project.example.models import Edition


class WidgetTestCase:  # pylint: disable=R0903
    """Base class for widget tests."""

    widget_class = None

    @pytest.fixture(autouse=True)
    def make_widget(self):
        """Create a widget factory method."""

        def _make_widget(model=Edition, **kwargs):
            return self.widget_class(model, **kwargs)

        self.make_widget = _make_widget


    def test_optgroups_no_initial_choices(self):
        """Assert that the widget is rendered without any options."""
        context = self.make_widget().get_context("output", None, {})
        assert not context["widget"]["optgroups"]

    def test_build_attrs(self):
        """Assert that the required HTML attributes are added."""
        widget = self.make_widget(
            # model=Edition,
            url="stub_url",
            value_field="pk",
            label_field="pages",
            create_field="the_create_field",
            multiple=True,
            listview_url="listview_page",
            create_url="create_page",
        )
        attrs = widget.build_attrs({})
        assert attrs["is-tomselect"]
        assert attrs["is-multiple"]
        assert attrs["data-autocomplete-url"] == "/stub/url/"
        assert attrs["data-model"] == f"{Edition._meta.app_label}.{Edition._meta.model_name}"  # pylint: disable=W0212
        assert attrs["data-value-field"] == "pk"
        assert attrs["data-label-field"] == "pages"
        assert attrs["data-create-field"] == "the_create_field"
        assert attrs["data-listview-url"] == "/example/listview/"
        assert attrs["data-create-url"] == "/example/create/"

    @pytest.mark.parametrize(
        "static_file",
        ("django-tomselect.css", "tom-select.bootstrap5.css", "django-tomselect.js"),
    )
    def test_media(self, static_file):
        """Assert that the necessary static files are included."""
        assert static_file in str(self.make_widget().media)
