"""Test the setup and configuration of the example project."""

import importlib
import json

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError

import django_tomselect.app_settings as app_settings
from django_tomselect.app_settings import (
    DEFAULT_CSS_FRAMEWORK,
    AllowedCSSFrameworks,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    TomSelectConfig,
    bool_or_callable,
    currently_in_production_mode,
    merge_configs,
    validate_json_encoder_class,
    validate_proxy_request_class,
)
from django_tomselect.request import DefaultProxyRequest
from example_project.example.models import Edition, Magazine


@pytest.mark.django_db
class TestModelFixtures:
    """Test the model fixtures used throughout the test suite."""

    def test_sample_edition_creation(self, sample_edition):
        """Test that the sample_edition fixture creates an Edition correctly."""
        assert isinstance(sample_edition, Edition)
        assert sample_edition.name == "Test Edition"
        assert sample_edition.year == "2024"
        assert sample_edition.pages == "100"
        assert sample_edition.pub_num == "TEST-001"
        assert sample_edition.magazine is None

    def test_sample_magazine_creation(self, sample_magazine):
        """Test that the sample_magazine fixture creates a Magazine correctly."""
        assert isinstance(sample_magazine, Magazine)
        assert sample_magazine.name == "Test Magazine"

    def test_edition_with_magazine_creation(self, edition_with_magazine, sample_magazine):
        """Test that the edition_with_magazine fixture creates related objects correctly."""
        assert isinstance(edition_with_magazine, Edition)
        assert edition_with_magazine.magazine == sample_magazine
        assert edition_with_magazine.name == "Magazine Edition"


@pytest.mark.django_db
class TestAppSettings:
    """Test the app settings functionality."""

    @pytest.mark.parametrize(
        "debug_value,expected",
        [
            (True, False),
            (False, True),
        ],
    )
    def test_production_mode_detection(self, monkeypatch, debug_value, expected):
        """Test that production mode is correctly detected based on DEBUG setting."""
        monkeypatch.setattr(settings, "DEBUG", debug_value)
        # No reload needed since currently_in_production_mode reads settings.DEBUG directly
        assert currently_in_production_mode() == expected

    def test_merge_configs_with_nested_plugins(self):
        """Test merging configs with nested plugin structures."""
        base = TomSelectConfig(
            plugin_dropdown_header=PluginDropdownHeader(title="Base", extra_columns={"key1": "Value1"}),
            plugin_dropdown_footer=PluginDropdownFooter(title="Base Footer"),
        )
        override = TomSelectConfig(
            plugin_dropdown_header=PluginDropdownHeader(title="Override", extra_columns={"key2": "Value2"})
        )
        result = merge_configs(base, override)
        assert result.plugin_dropdown_header.title == "Override"
        assert result.plugin_dropdown_header.extra_columns == {"key2": "Value2"}
        assert result.plugin_dropdown_footer.title == "Base Footer"

    def test_filter_exclude_validation(self):
        """Test validation of filter_by and exclude_by combinations."""
        # Test that exactly same field and value raises error
        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=("field", "value"), exclude_by=("field", "value"))

        # However, different fields should be allowed
        config = TomSelectConfig(filter_by=("field1", "value1"), exclude_by=("field2", "value2"))
        assert config.filter_by == ("field1", "value1")
        assert config.exclude_by == ("field2", "value2")

    def test_tom_select_config_max_options_validation(self):
        """Test validation of max_options parameter."""
        with pytest.raises(ValidationError):
            TomSelectConfig(max_options=0)

        config = TomSelectConfig(max_options=10)
        assert config.max_options == 10

    def test_css_framework_validation(self):
        """Test CSS framework validation with valid and invalid values."""
        # Test valid frameworks
        for framework in AllowedCSSFrameworks:
            config = TomSelectConfig(css_framework=framework.value)
            assert config.css_framework == framework.value

        # Test invalid framework - now raises ValidationError
        with pytest.raises(ValidationError) as exc_info:
            TomSelectConfig(css_framework="invalid_framework")
        assert "css_framework must be one of" in str(exc_info.value)
        assert "invalid_framework" in str(exc_info.value)

        # Test default value when css_framework is not provided
        config = TomSelectConfig()  # Don't specify css_framework at all
        assert config.css_framework == DEFAULT_CSS_FRAMEWORK

        # Test that None is passed through
        config = TomSelectConfig(css_framework=None)
        assert config.css_framework is None

    def test_label_field_dunder_rejected(self):
        """label_field must be a queryable field, not a Python dunder like __str__.

        A dunder exists on every instance (hasattr is always True) but is not
        selectable via QuerySet.values(), so it would render an empty label. The
        config rejects it loudly and points the implementer at a real field or an
        annotation.
        """
        with pytest.raises(ImproperlyConfigured) as exc_info:
            TomSelectConfig(label_field="__str__")
        message = str(exc_info.value)
        assert "__str__" in message
        assert "annotate" in message  # guidance points at a real field / annotation

        # Any dunder shares the same non-queryable failure mode and is rejected.
        with pytest.raises(ImproperlyConfigured):
            TomSelectConfig(label_field="__repr__")

        # Real fields, relation lookups, and the default all remain valid.
        assert TomSelectConfig(label_field="name").label_field == "name"
        assert TomSelectConfig(label_field="author__name").label_field == "author__name"
        assert TomSelectConfig().label_field == "name"

    def test_plugin_dropdown_header_extra_columns_empty(self):
        """Test PluginDropdownHeader with empty extra columns."""
        config = PluginDropdownHeader(extra_columns={})
        assert not config.extra_columns
        assert config.as_dict()["extra_columns"] == {}

    def test_merge_configs_with_none_values(self):
        """Test merging configs when override contains None values."""
        base = TomSelectConfig(
            url="base-url", highlight=True, plugin_dropdown_header=PluginDropdownHeader(title="Base Title")
        )
        override = TomSelectConfig(
            url=None,  # Should not override
            highlight=False,  # Should override
            plugin_dropdown_header=None,  # Should not override
        )
        result = merge_configs(base, override)
        assert result.url == "base-url"  # Maintained from base
        assert result.highlight is False  # Updated from override
        assert result.plugin_dropdown_header.title == "Base Title"  # Maintained from base

    @pytest.mark.parametrize(
        "preload_value,expected",
        [
            ("focus", "focus"),
            (True, True),
            (False, False),
            (None, None),  # Current behavior - None is passed through
            ("invalid", "invalid"),  # Current behavior - no validation
        ],
    )
    def test_preload_validation(self, preload_value, expected):
        """Test preload parameter behavior with various values."""
        config = TomSelectConfig(preload=preload_value)
        assert config.preload == expected

    def test_preload_default_value(self):
        """Test default value for preload when not specified."""
        config = TomSelectConfig()
        assert config.preload == "focus"  # Default value from class definition

    def test_plugin_configuration_inheritance(self):
        """Test that plugin configurations properly inherit and override."""
        base_config = TomSelectConfig(
            plugin_clear_button=PluginClearButton(title="Base Clear", class_name="base-clear")
        )

        # Create new config inheriting from base
        merged = merge_configs(
            base_config,
            TomSelectConfig(
                plugin_clear_button=PluginClearButton(
                    title="New Clear",
                    class_name="base-clear",  # Override title  # Keep same class
                )
            ),
        )

        assert merged.plugin_clear_button.title == "New Clear"
        assert merged.plugin_clear_button.class_name == "base-clear"

    def test_complex_plugin_configuration(self):
        """Test configuration with multiple plugins and complex settings."""
        config = TomSelectConfig(
            url="test-url",
            value_field="custom_id",
            label_field="custom_name",
            filter_by=("category", "type"),
            plugin_dropdown_header=PluginDropdownHeader(
                title="Header", show_value_field=True, extra_columns={"status": "Status"}
            ),
            plugin_clear_button=PluginClearButton(title="Clear All"),
            plugin_checkbox_options=PluginCheckboxOptions(),
            use_htmx=True,
        )

        assert config.url == "test-url"
        assert config.value_field == "custom_id"
        assert config.label_field == "custom_name"
        assert config.filter_by == ("category", "type")
        assert config.plugin_dropdown_header.show_value_field is True
        assert config.plugin_dropdown_header.extra_columns == {"status": "Status"}
        assert config.plugin_clear_button.title == "Clear All"
        assert isinstance(config.plugin_checkbox_options, PluginCheckboxOptions)
        assert config.use_htmx is True

    def test_merge_configs_preserves_default_settings(self):
        """Test that merge_configs preserves global settings not explicitly overridden."""
        # Create a config with non-default values
        base = TomSelectConfig(
            url="base-url",
            value_field="base_value_field",
            use_htmx=True,
            highlight=False,
            create=True,
        )

        # Create an override config with some fields explicitly set
        override = TomSelectConfig(
            url="override-url",  # Explicitly override just URL
        )

        # Merge configs
        result = merge_configs(base, override)

        # The explicitly set field should be overridden
        assert result.url == "override-url"

        # Fields not explicitly set should be preserved from base
        assert result.value_field == "base_value_field"
        assert result.use_htmx is True
        assert result.highlight is False
        assert result.create is True

    def test_merge_configs_handles_default_values_correctly(self):
        """Test that merge_configs doesn't override with default values."""
        # Create a config with non-default values
        base = TomSelectConfig(
            url="base-url",
            highlight=False,  # Non-default value
            preload=False,  # Non-default value
            use_htmx=True,  # Non-default value
        )

        # Create an override with default values
        # When instantiating TomSelectConfig without specifying values,
        # it will initialize fields with their defaults
        override = TomSelectConfig()

        # Merge configs
        result = merge_configs(base, override)

        # Default values from override should not replace explicit values from base
        assert result.url == "base-url"
        assert result.highlight is False  # Should not be overridden with default (True)
        assert result.preload is False  # Should not be overridden with default ("focus")
        assert result.use_htmx is True  # Should not be overridden with default (False)

    def test_merge_configs_preserves_nested_plugin_settings(self):
        """Test that merge_configs preserves nested plugin settings."""
        # Create a config with plugin settings
        base = TomSelectConfig(
            plugin_clear_button=PluginClearButton(title="Base Title", class_name="base-class"),
            plugin_dropdown_header=PluginDropdownHeader(title="Base Header", show_value_field=True),
        )

        # Create an override that only specifies one plugin partially
        override = TomSelectConfig(
            # Only override title of the clear button
            plugin_clear_button=PluginClearButton(
                title="Override Title"
                # class_name not specified, should keep base value
            )
            # plugin_dropdown_header not specified, should keep all base values
        )

        # Merge configs
        result = merge_configs(base, override)

        # Explicitly overridden plugin field should be updated
        assert result.plugin_clear_button.title == "Override Title"

        # Non-overridden plugin field should be preserved
        assert result.plugin_clear_button.class_name == "base-class"

        # Entire plugin not specified in override should be preserved
        assert result.plugin_dropdown_header.title == "Base Header"
        assert result.plugin_dropdown_header.show_value_field is True

    def test_merge_configs_issue_specific_case(self):
        """Test the specific case from Issues with use_htmx setting."""
        # Simulate global default with use_htmx=True (like what would set in settings.py)
        global_config = TomSelectConfig(use_htmx=True)

        # Create a config that specifies other settings but *not* use_htmx
        field_config = TomSelectConfig(
            url="autocomplete:gender",
            placeholder="Select a Gender",
            # use_htmx is not specified, inherit from global_config
        )

        # Merge configs
        result = merge_configs(global_config, field_config)

        # Field-specific settings should be applied
        assert result.url == "autocomplete:gender"
        assert result.placeholder == "Select a Gender"

        # Global use_htmx setting should be keps
        assert result.use_htmx is True

    def test_merge_configs_explicit_equals_default(self):
        """Test handling when override value equals the default value but is explicitly set."""
        # Create a config with non-default values
        base = TomSelectConfig(
            highlight=False,  # Non-default
            minimum_query_length=5,  # Non-default
        )

        # Create class to track if __init__ was called with specific values
        class TrackedConfig(TomSelectConfig):
            def __init__(self, **kwargs):
                self._explicit_keys = set(kwargs.keys())
                super().__init__(**kwargs)

            def is_explicit(self, key):
                return key in self._explicit_keys

        # Create override with explicit setting that equals the default (highlight=True is default), but explicitly set
        override = TrackedConfig(
            highlight=True  # Default value, explicitly set
        )

        assert override.is_explicit("highlight")

        # Merge configs with custom version of the function that checks explicitness
        def custom_merge(base, override):
            combined = base.__dict__.copy()

            for field_name in override.__dataclass_fields__:
                val = getattr(override, field_name)

                # Check if the value was explicitly provided in init
                if hasattr(override, "is_explicit") and override.is_explicit(field_name):
                    combined[field_name] = val

            return TomSelectConfig(**combined)

        result = custom_merge(base, override)

        # highlight should be overridden even though it is same as default value,
        # because it was explicitly specified
        assert result.highlight is True

        # minimum_query_length should be the same as base since it wasn't overridden
        assert result.minimum_query_length == 5


@pytest.mark.django_db
class TestBasicModelOperations:
    """Test basic model operations to ensure fixtures work correctly."""

    def test_edition_str_representation(self, sample_edition):
        """Test the string representation of Edition model."""
        assert str(sample_edition) == "Test Edition"

    def test_magazine_str_representation(self, sample_magazine):
        """Test the string representation of Magazine model."""
        assert str(sample_magazine) == "Test Magazine"

    def test_edition_magazine_relationship(self, edition_with_magazine, sample_magazine):
        """Test the relationship between Edition and Magazine models."""
        assert Edition.objects.filter(magazine=sample_magazine).exists()
        assert edition_with_magazine in sample_magazine.edition_set.all()


@pytest.mark.django_db
class TestSearchQueryset:
    """Test the SearchQueryset functionality."""

    @pytest.mark.parametrize(
        "search_term,expected_count",
        [
            ("Test", 1),
            ("Edition", 2),
            ("Magazine", 1),
            ("NonExistent", 0),
        ],
    )
    def test_search_method(self, sample_edition, edition_with_magazine, search_term, expected_count):
        """Test the search method of SearchQueryset."""
        results = Edition.objects.search(search_term)
        assert results.count() == expected_count


class TestBoolOrCallable:
    """Test the bool_or_callable function."""

    def test_bool_values(self):
        """Test bool_or_callable with boolean values."""
        assert bool_or_callable(True) is True
        assert bool_or_callable(False) is False

    def test_callable_values(self):
        """Test bool_or_callable with callable values."""

        def true_func():
            return True

        def false_func():
            return False

        assert bool_or_callable(true_func) is True
        assert bool_or_callable(false_func) is False

    def test_other_values(self):
        """Test bool_or_callable with non-boolean values."""
        assert bool_or_callable(1) is True
        assert bool_or_callable(0) is False
        assert bool_or_callable("") is False
        assert bool_or_callable("True") is True


class TestProxyRequestClass:
    """Test the proxy request class configuration."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, settings):
        """Setup and teardown for each test."""
        # Store original settings
        self.original_tomselect = getattr(settings, "TOMSELECT", {})

        yield

        # Restore original settings
        settings.TOMSELECT = self.original_tomselect
        # Reload app_settings module to reset state
        importlib.reload(app_settings)

    def test_default_proxy_request(self):
        """Test that default proxy request class is used when not configured."""
        proxy_request_class = validate_proxy_request_class()
        assert issubclass(proxy_request_class, DefaultProxyRequest)
        assert proxy_request_class == DefaultProxyRequest

    def test_invalid_proxy_request_string(self, settings):
        """Test handling of invalid proxy request class string."""
        settings.TOMSELECT = {"PROXY_REQUEST_CLASS": "invalid.module.path"}
        with pytest.raises(ImportError) as exc_info:
            importlib.reload(app_settings)  # Reload to pick up new settings
            # validate_proxy_request_class gets called during import
        assert "Failed to import PROXY_REQUEST_CLASS" in str(exc_info.value)

    def test_invalid_proxy_request_type(self, settings):
        """Test handling of invalid proxy request class type."""

        class InvalidProxyRequest:
            """Invalid proxy request class."""

        settings.TOMSELECT = {"PROXY_REQUEST_CLASS": InvalidProxyRequest}
        with pytest.raises(TypeError) as exc_info:
            importlib.reload(app_settings)  # Reload to pick up new settings
            # validate_proxy_request_class gets called during import
        assert "must be a subclass of DefaultProxyRequest" in str(exc_info.value)

    def test_valid_proxy_request_class(self, settings):
        """Test handling of valid proxy request class."""

        class ValidProxyRequest(DefaultProxyRequest):
            """Valid proxy request class."""

        settings.TOMSELECT = {"PROXY_REQUEST_CLASS": ValidProxyRequest}
        importlib.reload(app_settings)  # Reload to pick up new settings

        proxy_request_class = validate_proxy_request_class()
        assert issubclass(proxy_request_class, DefaultProxyRequest)
        assert proxy_request_class is ValidProxyRequest  # Use 'is' to check identity


class TestJSONEncoderClass:
    """Test the JSON encoder class configuration."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, settings):
        """Setup and teardown for each test."""
        # Store original settings
        self.original_tomselect = getattr(settings, "TOMSELECT", {})

        yield

        # Restore original settings
        settings.TOMSELECT = self.original_tomselect
        # Reload app_settings module to reset state
        importlib.reload(app_settings)

    def test_default_json_encoder_none(self):
        """Test that DEFAULT_JSON_ENCODER is None when not configured."""
        encoder_class = validate_json_encoder_class()
        # When not configured, should return None
        assert encoder_class is None

    def test_valid_json_encoder_class(self, settings):
        """Test handling of valid JSON encoder class."""

        class ValidEncoder(json.JSONEncoder):
            """Valid JSON encoder class."""

        settings.TOMSELECT = {"DEFAULT_JSON_ENCODER": ValidEncoder}
        importlib.reload(app_settings)

        encoder_class = validate_json_encoder_class()
        assert issubclass(encoder_class, json.JSONEncoder)
        assert encoder_class is ValidEncoder

    def test_valid_json_encoder_string(self, settings):
        """Test handling of valid JSON encoder class as string."""
        settings.TOMSELECT = {"DEFAULT_JSON_ENCODER": "json.JSONEncoder"}
        importlib.reload(app_settings)

        encoder_class = validate_json_encoder_class()
        assert encoder_class is json.JSONEncoder

    def test_invalid_json_encoder_string(self, settings):
        """Test handling of invalid JSON encoder class string."""
        settings.TOMSELECT = {"DEFAULT_JSON_ENCODER": "invalid.module.path"}
        with pytest.raises(ImportError) as exc_info:
            importlib.reload(app_settings)
            # validate_json_encoder_class gets called during import
        assert "Failed to import DEFAULT_JSON_ENCODER" in str(exc_info.value)

    def test_invalid_json_encoder_type(self, settings):
        """Test handling of invalid JSON encoder class type."""

        class InvalidEncoder:
            """Invalid encoder class (not a JSONEncoder subclass)."""

        settings.TOMSELECT = {"DEFAULT_JSON_ENCODER": InvalidEncoder}
        with pytest.raises(TypeError) as exc_info:
            importlib.reload(app_settings)
            # validate_json_encoder_class gets called during import
        assert "must be a subclass of json.JSONEncoder" in str(exc_info.value)
