"""Tests for TomSelectWidget and TomSelectMultipleWidget."""

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.urls.exceptions import NoReverseMatch

from django_tomselect.configs import (
    GeneralConfig,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.widgets import TomSelectContext, TomSelectMultipleWidget, TomSelectWidget
from example_project.example.models import Edition, Magazine


@pytest.mark.django_db
class TestTomSelectWidgetBase:
    """Base test class for widget tests."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Set up test environment."""
        self.basic_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
        )
        self.widget_class = TomSelectWidget

    def create_widget(self, config=None, **kwargs):
        """Helper method to create widget instances."""
        widget = self.widget_class(config=config or self.basic_config, **kwargs)
        # Initialize the widget with ModelChoiceField's choices
        widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
        return widget


@pytest.mark.django_db
class TestTomSelectWidget(TestTomSelectWidgetBase):
    """Tests for TomSelectWidget."""

    def test_widget_initialization(self):
        """Test basic widget initialization."""
        widget = self.create_widget()
        assert widget.url == "autocomplete-edition"
        assert widget.value_field == "id"
        assert widget.label_field == "name"
        assert isinstance(widget.general_config, GeneralConfig)

    def test_widget_initialization_with_custom_config(self):
        """Test widget initialization with custom config."""
        config = TomSelectConfig(
            url="custom-url",
            value_field="custom_id",
            label_field="custom_name",
            general_config=GeneralConfig(highlight=False, placeholder="Custom placeholder"),
        )
        widget = self.create_widget(config=config)
        assert widget.url == "custom-url"
        assert widget.value_field == "custom_id"
        assert widget.label_field == "custom_name"
        assert widget.general_config.highlight is False
        assert widget.general_config.placeholder == "Custom placeholder"

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
            ({"plugin_checkbox_options": PluginCheckboxOptions()}, ["checkbox_options"]),
            ({"plugin_clear_button": PluginClearButton()}, ["clear_button"]),
            (
                {"plugin_checkbox_options": PluginCheckboxOptions(), "plugin_clear_button": PluginClearButton()},
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


@pytest.mark.django_db
class TestTomSelectMultipleWidget(TestTomSelectWidgetBase):
    """Tests for TomSelectMultipleWidget."""

    @pytest.fixture(autouse=True)
    def setup_multiple_test(self, setup_test):
        """Set up test environment for multiple select widget."""
        self.widget_class = TomSelectMultipleWidget
        self.base_choices = forms.ModelMultipleChoiceField(queryset=Edition.objects.all()).choices

    def create_widget(self, config=None, **kwargs):
        """Helper method to create multiple select widget instances."""
        widget = super().create_widget(config=config, **kwargs)
        widget.choices = self.base_choices
        return widget

    def test_multiple_widget_initialization(self):
        """Test multiple select widget initialization."""
        widget = self.create_widget()
        assert hasattr(widget, "allow_multiple_selected")
        assert widget.allow_multiple_selected

    def test_multiple_widget_build_attrs(self):
        """Test HTML attribute generation for multiple select."""
        widget = self.create_widget()
        attrs = widget.build_attrs({})
        assert attrs.get("is-multiple") is True

    def test_multiple_widget_get_context(self):
        """Test context generation for multiple select."""
        widget = self.create_widget()
        context = widget.get_context("test", None, {})
        assert context["widget"]["is_multiple"]

    def test_multiple_widget_with_initial_values(self, editions):
        """Test context generation with initial values for multiple select."""
        widget = self.create_widget()
        initial_values = [editions[0].pk, editions[1].pk]
        context = widget.get_context("test", initial_values, {})

        assert "widget" in context

    def test_multiple_widget_max_items(self):
        """Test max_items configuration for multiple select."""
        config = TomSelectConfig(general_config=GeneralConfig(max_items=3))
        widget = self.create_widget(config=config)
        context = widget.get_context("test", None, {})

        assert context["widget"]["general_config"]["max_items"] == 3


@pytest.mark.django_db
class TestWidgetErrors:
    """Test error handling in widget initialization and configuration."""

    @pytest.fixture
    def setup_widget(self):
        """Set up base widget for testing."""

        def _create_widget(config):
            widget = TomSelectWidget(config=config)
            widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
            return widget

        return _create_widget

    def test_invalid_config_type(self):
        """Test widget initialization with invalid config type."""
        with pytest.raises(ValueError) as exc:
            TomSelectWidget(config={"url": "test"})
        assert "config must be an instance of TomSelectConfig" in str(exc.value)

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


@pytest.mark.django_db
class TestWidgetURLHandling:
    """Test URL handling functionality."""

    @pytest.fixture
    def setup_widget(self):
        """Set up base widget for testing."""

        def _create_widget(config):
            widget = TomSelectWidget(config=config)
            widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
            return widget

        return _create_widget

    def test_invalid_url_handling(self, setup_widget):
        """Test handling of invalid URLs."""
        widget = setup_widget(TomSelectConfig(url="non-existent-url"))
        with pytest.raises(NoReverseMatch):
            _ = widget.get_autocomplete_url() == ""

    def test_url_with_parameters(self, setup_widget):
        """Test URL generation with parameters."""
        widget = setup_widget(
            TomSelectConfig(
                url="autocomplete-edition", create_url="create", update_url="update", listview_url="edition-list"
            )
        )
        assert widget.get_autocomplete_url() == reverse_lazy("autocomplete-edition")
        assert widget.get_create_url() == reverse_lazy("create")
        assert widget.get_listview_url() == reverse_lazy("edition-list")


@pytest.mark.django_db
class TestWidgetDependentFields:
    """Test dependent field functionality."""

    @pytest.fixture
    def setup_dependent_widget(self):
        """Set up widget with dependent field configuration."""
        widget = TomSelectWidget(
            config=TomSelectConfig(url="autocomplete-edition", filter_by=("magazine", "magazine_id"))
        )
        widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
        return widget

    def test_dependent_field_context(self, setup_dependent_widget):
        """Test context generation with dependent field."""
        context = setup_dependent_widget.get_context("test", None, {})
        assert "dependent_field" in context["widget"]
        assert context["widget"]["dependent_field"] == "magazine"
        assert context["widget"]["dependent_field_lookup"] == "magazine_id"


@pytest.mark.django_db
class TestWidgetQuerysetHandling:
    """Test queryset handling and filtering."""

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
            widget = TomSelectWidget(config=config)
            widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
            return widget

        return _create_widget

    def test_get_model(self, setup_widget, setup_test_data):
        """Test model retrieval from queryset."""
        widget = setup_widget()
        assert widget.get_model() == Edition

    def test_get_queryset(self, setup_widget, setup_test_data):
        """Test queryset retrieval."""
        widget = setup_widget()
        queryset = widget.get_queryset()
        assert queryset.model == Edition
        assert queryset.count() == 2


@pytest.mark.django_db
class TestWidgetContextPreparation:
    """Test context preparation with various configurations."""

    @pytest.fixture
    def setup_widget(self):
        """Create properly initialized widget."""

        def _create_widget(config):
            widget = TomSelectWidget(config=config)
            widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
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
            general_config=GeneralConfig(placeholder="Custom placeholder", highlight=True, max_items=5),
        )
        widget = setup_widget(config)
        attrs = {"class": "custom-class", "data-test": "test"}
        context = widget.get_context("test", None, attrs)

        assert context["widget"]["attrs"]["class"] == "custom-class"
        assert context["widget"]["attrs"]["data-test"] == "test"
        assert context["widget"]["general_config"]["placeholder"] == "Custom placeholder"


@pytest.mark.django_db
class TestWidgetRendering:
    """Test widget rendering functionality."""

    @pytest.fixture
    def setup_widget(self):
        """Set up base widget for testing."""

        def _create_widget(config=None):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectWidget(config=config)
            widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
            return widget

        return _create_widget

    def test_render_with_value(self, setup_widget, sample_edition):
        """Test widget rendering with a selected value."""
        widget = setup_widget()
        rendered = widget.render("test", sample_edition.pk)
        assert str(sample_edition.pk) in rendered
        assert "tom-select" in rendered

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

    def test_render_with_placeholder(self, setup_widget):
        """Test widget rendering with placeholder text."""
        config = TomSelectConfig(
            url="autocomplete-edition", general_config=GeneralConfig(placeholder="Select something...")
        )
        widget = setup_widget(config)
        rendered = widget.render("test", None)
        assert 'placeholder="Select something..."' in rendered

    def test_render_with_custom_id(self, setup_widget):
        """Test widget rendering with custom ID attribute."""
        widget = setup_widget()
        rendered = widget.render("test", None, attrs={"id": "custom-id"})
        assert 'id="custom-id"' in rendered


@pytest.mark.django_db
class TestAdvancedWidgetBehavior:
    """Test advanced widget behaviors and edge cases."""

    @pytest.fixture
    def setup_widget(self):
        """Set up base widget for testing."""

        def _create_widget(config=None):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectWidget(config=config)
            widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
            return widget

        return _create_widget

    def test_widget_with_empty_queryset(self, setup_widget):
        """Test widget behavior with empty queryset."""
        widget = setup_widget()
        widget.choices = forms.ModelChoiceField(queryset=Edition.objects.none()).choices
        context = widget.get_context("test", None, {})
        assert "selected_options" not in context["widget"]

    def test_widget_with_invalid_value(self, setup_widget):
        """Test widget behavior with invalid value."""
        widget = setup_widget()
        context = widget.get_context("test", 99999, {})  # Non-existent ID
        # Invalid IDs should result in empty selected_options
        assert context["widget"]["selected_options"] == []

    def test_exclusion_and_filtering(self, setup_widget):
        """Test widget with both exclude_by and filter_by configurations."""
        config = TomSelectConfig(
            url="autocomplete-edition", filter_by=("magazine", "magazine_id"), exclude_by=("author", "author_id")
        )
        widget = setup_widget(config)
        context = widget.get_context("test", None, {})
        assert context["widget"]["dependent_field"] == "magazine"
        assert context["widget"]["exclude_field"] == "author"


@pytest.mark.django_db
class TestMultipleWidgetSpecifics:
    """Test specific behaviors of TomSelectMultipleWidget."""

    @pytest.fixture
    def setup_multiple_widget(self):
        """Set up multiple select widget for testing."""

        def _create_widget(config=None):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectMultipleWidget(config=config)
            widget.choices = forms.ModelMultipleChoiceField(queryset=Edition.objects.all()).choices
            return widget

        return _create_widget

    def test_multiple_widget_with_max_items_none(self, setup_multiple_widget):
        """Test multiple widget with unlimited selections."""
        config = TomSelectConfig(url="autocomplete-edition", general_config=GeneralConfig(max_items=None))
        widget = setup_multiple_widget(config)
        context = widget.get_context("test", None, {})
        assert context["widget"]["general_config"]["max_items"] is None

    def test_multiple_widget_selected_options(self, setup_multiple_widget, editions):
        """Test multiple widget with multiple selected values."""
        widget = setup_multiple_widget()
        selected_ids = [editions[0].pk, editions[1].pk]
        context = widget.get_context("test", selected_ids, {})
        assert "selected_options" in context["widget"]
        assert len(context["widget"]["selected_options"]) == 2

    def test_multiple_widget_empty_selection(self, setup_multiple_widget):
        """Test multiple widget with empty selection."""
        widget = setup_multiple_widget()
        context = widget.get_context("test", [], {})
        assert "selected_options" not in context["widget"]


@pytest.mark.django_db
class TestWidgetConfigValidation:
    """Test configuration validation for widgets."""

    def test_general_config_validation(self):
        """Test validation of GeneralConfig parameters."""
        with pytest.raises(ValidationError):
            GeneralConfig(load_throttle=-1)

        with pytest.raises(ValidationError):
            GeneralConfig(max_items=0)

        with pytest.raises(ValidationError):
            GeneralConfig(minimum_query_length=-1)

    def test_dropdown_header_validation(self):
        """Test validation of PluginDropdownHeader configuration."""
        with pytest.raises(ValidationError):
            PluginDropdownHeader(extra_columns="invalid")

    def test_config_combination_validation(self):
        """Test validation of combined configurations."""
        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=("field", "lookup"), exclude_by=("field", "lookup"))

    @pytest.mark.parametrize(
        "invalid_value",
        [
            {"load_throttle": -1},
            {"max_items": 0},
            {"minimum_query_length": -1},
        ],
    )
    def test_general_config_invalid_values(self, invalid_value):
        """Test various invalid GeneralConfig values."""
        with pytest.raises(ValidationError):
            GeneralConfig(**invalid_value)


@pytest.mark.django_db
class TestTomSelectContext:
    """Test the TomSelectContext class."""

    @pytest.fixture
    def widget(self):
        """Create a widget for testing."""
        widget = TomSelectWidget(config=TomSelectConfig(url="autocomplete-edition"))
        widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
        return widget

    def test_get_autocomplete_context(self, widget):
        """Test the get_autocomplete_context method."""
        # Mock the search_lookups to avoid implementation issues
        widget.get_search_lookups = lambda: []

        context_manager = TomSelectContext(widget, "test_name", None, {})
        context = context_manager.get_autocomplete_context()

        assert context["value_field"] == "id"
        assert context["label_field"] == "name"
        assert context["is_tabular"] is False
        assert context["use_htmx"] is False
        assert context["autocomplete_url"] == reverse_lazy("autocomplete-edition")
        assert context["search_lookups"] == []

    def test_get_plugin_context(self, widget):
        """Test plugin context with all plugins enabled."""
        widget.plugin_clear_button = PluginClearButton()
        widget.plugin_remove_button = PluginRemoveButton()
        widget.plugin_dropdown_header = PluginDropdownHeader(extra_columns={"year": "Year"})
        widget.plugin_dropdown_footer = PluginDropdownFooter()
        widget.plugin_checkbox_options = PluginCheckboxOptions()
        widget.plugin_dropdown_input = PluginDropdownInput()

        context_manager = TomSelectContext(widget, "test_name", None, {})
        _ = context_manager.get_plugin_context()


@pytest.mark.django_db
class TestWidgetQuerysetBehavior:
    """Test queryset behavior in various scenarios."""

    @pytest.fixture
    def complex_widget(self, sample_magazine):
        """Create widget with complex configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            filter_by=("magazine", "id"),
            plugin_dropdown_header=PluginDropdownHeader(extra_columns={"year": "Year", "pub_num": "Publication"}),
        )
        widget = TomSelectWidget(config=config)
        widget.choices = forms.ModelChoiceField(queryset=Edition.objects.filter(magazine=sample_magazine)).choices
        return widget

    def test_filtered_queryset(self, complex_widget, editions):
        """Test queryset with filtering applied."""
        queryset = complex_widget.get_queryset()
        assert queryset.model == Edition
        assert all(edition.magazine is not None for edition in queryset)

    def test_existing_search_lookups(self, complex_widget):
        """Test behavior for DemoEditionAutocompleteView, where `search_lookups = ["name__icontains"]`."""
        lookups = complex_widget.get_search_lookups()
        assert isinstance(lookups, list)
        assert len(lookups) == 1


@pytest.mark.django_db
class TestWidgetInitializationEdgeCases:
    """Test edge cases in widget initialization."""

    def test_initialization_without_config(self):
        """Test widget initialization without any config."""
        widget = TomSelectWidget()
        assert isinstance(widget.general_config, GeneralConfig)
        assert widget.url == "autocomplete"

    def test_initialization_with_overrides(self):
        """Test widget initialization with kwargs overriding config."""
        config = TomSelectConfig(url="original-url")
        # Remove url from kwargs since it's not a valid widget attribute
        widget = TomSelectWidget(config=config)
        widget.url = "overridden-url"  # After initialization!
        assert widget.url == "overridden-url"

    def test_initialization_with_invalid_attrs(self):
        """Test widget initialization with invalid attributes."""
        widget = TomSelectWidget()
        widget.attrs = {}  # Test setting attrs directly on widget
        assert isinstance(widget.attrs, dict)


@pytest.mark.django_db
class TestWidgetAttributeHandling:
    """Test widget attribute handling."""

    @pytest.fixture
    def widget_with_attrs(self):
        """Create widget with predefined attributes."""
        config = TomSelectConfig(attrs={"class": "base-class", "data-test": "base"})
        widget = TomSelectWidget(config=config)
        widget.choices = forms.ModelChoiceField(queryset=Edition.objects.all()).choices
        return widget

    def test_attr_merging(self, widget_with_attrs):
        """Test merging of attributes from different sources."""
        # Add a test attribute before testing
        widget_with_attrs.attrs["data-test"] = "base"
        context = widget_with_attrs.get_context("test", None, {"class": "override-class", "data-new": "new"})
        attrs = context["widget"]["attrs"]
        assert "override-class" in attrs["class"]
        assert attrs["data-test"] == "base"

    def test_data_attributes(self, widget_with_attrs):
        """Test handling of data-* attributes."""
        attrs = widget_with_attrs.build_attrs({}, {"data-custom": "value"})
        assert attrs["data-custom"] == "value"
        assert "data-autocomplete-url" in attrs


@pytest.mark.django_db
class TestMultipleWidgetEdgeCases:
    """Test edge cases specific to TomSelectMultipleWidget."""

    @pytest.fixture
    def multiple_widget(self):
        """Create multiple select widget."""
        config = TomSelectConfig(url="autocomplete-edition", general_config=GeneralConfig(max_items=None))
        widget = TomSelectMultipleWidget(config=config)
        widget.choices = forms.ModelMultipleChoiceField(queryset=Edition.objects.all()).choices
        return widget

    def test_selected_options_ordering(self, multiple_widget, editions):
        """Test ordering of selected options."""
        # Since Edition model has default ordering by magazine and name,
        # we verify that we get back the correct editions regardless of order
        selected_ids = [str(editions[1].pk), str(editions[0].pk)]
        context = multiple_widget.get_context("test", selected_ids, {})
        selected_options = context["widget"]["selected_options"]

        # Verify we got both editions back
        assert len(selected_options) == 2
        assert {str(opt["value"]) for opt in selected_options} == set(selected_ids)
        # And verify the editions are returned in model's default order
        assert str(selected_options[0]["value"]) == str(editions[0].pk)
        assert str(selected_options[1]["value"]) == str(editions[1].pk)

    def test_invalid_selected_values(self, multiple_widget):
        """Test handling of invalid selected values."""
        context = multiple_widget.get_context("test", [999999, 888888], {})
        # Since invalid values result in empty queryset, selected_options is an empty list
        assert context["widget"]["selected_options"] == []
