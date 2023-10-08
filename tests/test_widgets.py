import pytest
from django.db import models
from testapp.models import Edition

from django_tomselect.widgets import (
    TomSelectMultipleWidget,
    TomSelectTabularMultipleWidget,
    TomSelectTabularWidget,
    TomSelectWidget,
)


class WidgetTestCase:
    widget_class = None

    @pytest.fixture(autouse=True)
    def make_widget(self):
        def _make_widget(model=Edition, **kwargs):
            return self.widget_class(model, **kwargs)

        self.make_widget = _make_widget


class TestTomSelectWidget(WidgetTestCase):
    widget_class = TomSelectWidget

    def test_init_sets_default_value_field(self):
        """
        Assert that init sets the default for `value_field` to the model's
        primary key.
        """

        class CustomPrimaryKeyModel(models.Model):
            my_primary_key = models.PositiveIntegerField(primary_key=True)

            class Meta:
                app_label = "testapp"

        widget = self.widget_class(CustomPrimaryKeyModel)
        assert widget.value_field == "my_primary_key"

    def test_init_sets_default_label_field_to_name(self):
        """
        Assert that init sets the default for `label_field` to 'name' if the
        model has no `name_field`.
        """

        class NoNameFieldModel(models.Model):
            foo = models.CharField(max_length=1)

            class Meta:
                app_label = "testapp"

        widget = self.widget_class(NoNameFieldModel)
        assert widget.label_field == "name"

    def test_init_sets_default_label_field_to_name_field(self):
        """
        Assert that init sets the default for `label_field` to the model's
        `name_field`.
        """

        class NameFieldModel(models.Model):
            foo = models.CharField(max_length=1)

            name_field = "foo"

            class Meta:
                app_label = "testapp"

        widget = self.widget_class(NameFieldModel)
        assert widget.label_field == "foo"

    def test_init_sets_default_search_lookups_from_label_field(self):
        """
        Assert that init sets the default for `search_lookups` to the value of
        `[f"{self.value_field}__icontains, {self.label_field}__icontains"]`.
        """
        widget = TomSelectWidget(Edition, label_field="foo")
        assert widget.search_lookups == ["id__icontains", "foo__icontains"]

    def test_optgroups_no_initial_choices(self):
        """Assert that the widget is rendered without any options."""
        context = self.make_widget().get_context("output", None, {})
        assert not context["widget"]["optgroups"]

    def test_build_attrs(self):
        """Assert that the required HTML attributes are added."""
        widget = self.make_widget(
            # model=Edition,
            url="dummy_url",
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
        assert attrs["data-autocomplete-url"] == "/dummy/url/"
        assert attrs["data-model"] == f"{Edition._meta.app_label}.{Edition._meta.model_name}"
        assert attrs["data-value-field"] == "pk"
        assert attrs["data-label-field"] == "pages"
        assert attrs["data-create-field"] == "the_create_field"
        assert attrs["data-listview-url"] == "/testapp/listview/"
        assert attrs["data-create-url"] == "/testapp/create/"

    @pytest.mark.parametrize(
        "static_file",
        ("django-tomselect.css", "tom-select.bootstrap5.css", "django-tomselect.js"),
    )
    def test_media(self, static_file):
        """Assert that the necessary static files are included."""
        assert static_file in str(self.make_widget().media)


class TestTabularTomSelectWidget(WidgetTestCase):
    widget_class = TomSelectTabularWidget

    def test_init_sets_label_field_label(self):
        """
        Assert that init sets the default for `label_field_label` to the
        verbose_name of the model.
        """
        widget = self.widget_class(Edition)
        assert widget.label_field_label == "Edition"

    def test_init_sets_value_field_label(self):
        """
        Assert that init sets the default for `value_field_label` to
        value_field.title().
        """
        widget = self.widget_class(Edition)
        assert widget.value_field_label == "Id"

    def test_build_attrs(self):
        """Assert that the required HTML attributes are added."""
        widget = self.make_widget(
            # model=Edition,
            extra_columns={"year": "Year", "pages": "Pages", "pub_num": "Publication Number"},
            value_field_label="Primary Key",
            label_field_label="Edition",
        )
        attrs = widget.build_attrs({})
        assert attrs["is-tabular"]
        assert attrs["data-value-field-label"] == "Primary Key"
        assert attrs["data-label-field-label"] == "Edition"
        assert attrs["data-extra-headers"] == '["Year", "Pages", "Publication Number"]'
        assert attrs["data-extra-columns"] == '["year", "pages", "pub_num"]'
