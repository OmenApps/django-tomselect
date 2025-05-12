"""Test the setup and configuration of the example project."""

import importlib

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

import django_tomselect.app_settings as app_settings
from django_tomselect.app_settings import (
    DEFAULT_CSS_FRAMEWORK,
    AllowedCSSFrameworks,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
    bool_or_callable,
    currently_in_production_mode,
    get_plugin_config,
    merge_configs,
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

        # Test invalid framework - currently accepts any string
        config = TomSelectConfig(css_framework="invalid_framework")
        assert config.css_framework == "invalid_framework"  # Current behavior

        # Test default value when css_framework is not provided
        config = TomSelectConfig()  # Don't specify css_framework at all
        assert config.css_framework == DEFAULT_CSS_FRAMEWORK

        # Test that None is passed through
        config = TomSelectConfig(css_framework=None)
        assert config.css_framework is None

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


class TestBaseConfigValidation:
    """Test validation in BaseConfig and its subclasses."""

    def test_plugin_dropdown_header_validation(self):
        """Test validation of PluginDropdownHeader configuration."""
        with pytest.raises(ValidationError):
            PluginDropdownHeader(extra_columns="invalid")  # Should be dict

    def test_tom_select_config_validation(self):
        """Test validation of TomSelectConfig."""
        with pytest.raises(ValidationError):
            TomSelectConfig(filter_by=("field",))  # Should be 2-tuple
        with pytest.raises(ValidationError):
            TomSelectConfig(exclude_by=("field",))  # Should be 2-tuple
        with pytest.raises(ValidationError):
            # Same field for filter and exclude
            TomSelectConfig(filter_by=("field", "value"), exclude_by=("field", "value"))


@pytest.mark.django_db
class TestPluginConfiguration:
    """Test plugin configuration handling."""

    def test_get_plugin_config_with_instance(self, monkeypatch):
        """Test get_plugin_config with plugin instance."""
        # No plugin config in TOMSELECT
        monkeypatch.setattr(app_settings, "PROJECT_TOMSELECT", {"PLUGINS": {}})
        monkeypatch.setattr(app_settings, "PROJECT_PLUGINS", {})

        plugin_instance = PluginClearButton(title="Custom")
        plugin_config = get_plugin_config(PluginClearButton, "clear_button", plugin_instance)
        assert isinstance(plugin_config, PluginClearButton)
        assert plugin_config.title == "Custom"

    def test_get_plugin_config_default(self, monkeypatch):
        """Test get_plugin_config returns default when no config is found."""
        monkeypatch.setattr(app_settings, "PROJECT_TOMSELECT", {"PLUGINS": {}})
        monkeypatch.setattr(app_settings, "PROJECT_PLUGINS", {})

        default_config = PluginClearButton(title="Default")
        plugin_config = get_plugin_config(PluginClearButton, "clear_button", default_config)
        assert isinstance(plugin_config, PluginClearButton)
        assert plugin_config.title == "Default"

    def test_get_plugin_config_with_dict(self, monkeypatch):
        """Test get_plugin_config with dictionary configuration."""
        plugin_dict = {"title": "Custom Title", "class_name": "custom-class"}
        monkeypatch.setattr(app_settings, "PROJECT_PLUGINS", {"clear_button": plugin_dict})

        result = get_plugin_config(PluginClearButton, "clear_button", PluginClearButton())
        assert isinstance(result, PluginClearButton)
        assert result.title == "Custom Title"
        assert result.class_name == "custom-class"

    def test_get_plugin_config_with_invalid_type(self, monkeypatch):
        """Test get_plugin_config with invalid configuration type."""
        invalid_config = 123  # Not a dict or proper instance
        monkeypatch.setattr(app_settings, "PROJECT_PLUGINS", {"clear_button": invalid_config})

        default = PluginClearButton(title="Default")
        result = get_plugin_config(PluginClearButton, "clear_button", default)
        assert result == default


@pytest.mark.django_db
class TestTomSelectConfig:
    """Test TomSelectConfig functionality."""

    def test_as_dict_conversion(self):
        """Test conversion of TomSelectConfig to dictionary."""
        config = TomSelectConfig(
            highlight=False,
            plugin_clear_button=PluginClearButton(title="Clear"),
        )
        config_dict = config.as_dict()
        assert isinstance(config_dict, dict)

        # Now plugin_clear_button is a dict itself
        assert config_dict["plugin_clear_button"]["title"] == "Clear"

    def test_verify_config_types(self, caplog):
        """Test configuration type verification with invalid types."""
        # Provide invalid types for all plugin configs
        config = TomSelectConfig(
            plugin_checkbox_options="not a PluginCheckboxOptions",
            plugin_clear_button="not a PluginClearButton",
            plugin_dropdown_header="not a PluginDropdownHeader",
            plugin_dropdown_footer="not a PluginDropdownFooter",
            plugin_dropdown_input="not a PluginDropdownInput",
            plugin_remove_button="not a PluginRemoveButton",
        )
        assert config.verify_config_types()  # Should return True but log warnings

        warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
        expected_warnings = [
            "PluginCheckboxOptions is not of type PluginCheckboxOptions",
            "PluginClearButton is not of type PluginClearButton",
            "PluginDropdownHeader is not of type PluginDropdownHeader",
            "PluginDropdownFooter is not of type PluginDropdownFooter",
            "PluginDropdownInput is not of type PluginDropdownInput",
            "PluginRemoveButton is not of type PluginRemoveButton",
        ]
        assert all(warn in warning_messages for warn in expected_warnings)

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = TomSelectConfig()
        assert config.url == "autocomplete"
        assert config.show_list is False
        assert config.show_create is False
        assert config.show_detail is False
        assert config.show_update is False
        assert config.show_delete is False
        assert config.value_field == "id"
        assert config.label_field == "name"
        assert config.create_field == ""
        assert not config.filter_by
        assert not config.exclude_by
        assert config.use_htmx is False
        assert config.css_framework == "default"
        assert config.plugin_checkbox_options is None
        assert config.plugin_clear_button is None
        assert config.plugin_dropdown_header is None
        assert config.plugin_dropdown_footer is None
        assert config.plugin_dropdown_input is None
        assert config.plugin_remove_button is None

    @pytest.mark.parametrize(
        "filter_by,should_raise",
        [
            ((), False),
            (("field", "lookup"), False),
            (("single",), True),
            (("one", "two", "three"), True),
        ],
    )
    def test_filter_by_validation(self, filter_by, should_raise):
        """Test filter_by validation."""
        if should_raise:
            with pytest.raises(ValidationError):
                TomSelectConfig(filter_by=filter_by)
        else:
            config = TomSelectConfig(filter_by=filter_by)
            assert config.filter_by == filter_by

    def test_plugin_configurations(self):
        """Test that plugin configurations are properly handled."""
        config = TomSelectConfig(
            plugin_checkbox_options=PluginCheckboxOptions(),
            plugin_clear_button=PluginClearButton(title="Clear"),
            plugin_dropdown_header=PluginDropdownHeader(title="Header"),
            plugin_dropdown_footer=PluginDropdownFooter(title="Footer"),
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_remove_button=PluginRemoveButton(title="Remove"),
        )

        assert isinstance(config.plugin_checkbox_options, PluginCheckboxOptions)
        assert isinstance(config.plugin_clear_button, PluginClearButton)
        assert isinstance(config.plugin_dropdown_header, PluginDropdownHeader)
        assert isinstance(config.plugin_dropdown_footer, PluginDropdownFooter)
        assert isinstance(config.plugin_dropdown_input, PluginDropdownInput)
        assert isinstance(config.plugin_remove_button, PluginRemoveButton)

    def test_update_method(self):
        """Test updating TomSelectConfig values.

        Since TomSelectConfig is a frozen dataclass, we have to create a new instance
        with updated values rather than modifying an existing one.
        """
        base_config = TomSelectConfig()
        new_config = TomSelectConfig(**{**base_config.__dict__, "url": "new-url", "highlight": False})
        assert new_config.url == "new-url"
        assert new_config.highlight is False
        # Verify original config remains unchanged
        assert base_config.url == "autocomplete"
        assert base_config.highlight is True

    def test_merge_configs_with_none(self):
        """Test merging configs when override is None."""
        base = TomSelectConfig(url="test-url", highlight=True)
        result = merge_configs(base, None)
        assert result == base
        assert result.url == "test-url"
        assert result.highlight is True

    def test_load_throttle_validation(self):
        """Test validation of load_throttle parameter."""
        with pytest.raises(ValidationError):
            TomSelectConfig(load_throttle=-1)

    def test_max_items_validation(self):
        """Test validation of max_items parameter."""
        with pytest.raises(ValidationError):
            TomSelectConfig(max_items=0)

    def test_minimum_query_length_validation(self):
        """Test validation of minimum_query_length parameter."""
        with pytest.raises(ValidationError):
            TomSelectConfig(minimum_query_length=-1)

    def test_merge_configs_with_dropdown_header(self):
        """Test merging configs with dropdown header plugin."""
        base = TomSelectConfig(
            plugin_dropdown_header=PluginDropdownHeader(title="Base Title", extra_columns={"base": "Base Column"})
        )
        override = TomSelectConfig(
            plugin_dropdown_header=PluginDropdownHeader(
                title="Override Title", extra_columns={"override": "Override Column"}
            )
        )
        result = merge_configs(base, override)
        assert result.plugin_dropdown_header.title == "Override Title"
        assert result.plugin_dropdown_header.extra_columns == {"override": "Override Column"}

    def test_merge_configs_partial_override(self):
        """Test merging configs with partial override."""
        base = TomSelectConfig(url="base-url", highlight=True, create=False)
        override = TomSelectConfig(url="override-url")
        result = merge_configs(base, override)
        assert result.url == "override-url"
        assert result.highlight is True  # Maintained from base
        assert result.create is False  # Maintained from base


class TestPluginIntegration:
    """Test integration of multiple plugins and configurations."""

    def test_complete_config_setup(self):
        """Test setting up a complete configuration with multiple plugins."""
        config = TomSelectConfig(
            url="test-url",
            highlight=True,
            load_throttle=500,
            css_framework=AllowedCSSFrameworks.BOOTSTRAP5.value,
            plugin_clear_button=PluginClearButton(title="Clear All", class_name="clear-all"),
            plugin_dropdown_header=PluginDropdownHeader(title="Select Option", extra_columns={"status": "Status"}),
            plugin_checkbox_options=PluginCheckboxOptions(),
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_dropdown_footer=PluginDropdownFooter(title="Footer", footer_class="custom-footer"),
            plugin_remove_button=PluginRemoveButton(title="Remove", label="X"),
        )

        assert config.url == "test-url"
        assert config.highlight is True
        assert config.load_throttle == 500
        assert config.css_framework == "bootstrap5"
        assert config.plugin_clear_button.title == "Clear All"
        assert config.plugin_dropdown_header.extra_columns == {"status": "Status"}
        assert isinstance(config.plugin_checkbox_options, PluginCheckboxOptions)
        assert isinstance(config.plugin_dropdown_input, PluginDropdownInput)
        assert config.plugin_dropdown_footer.title == "Footer"
        assert config.plugin_remove_button.label == "X"


@pytest.mark.django_db
class TestPluginCheckboxOptions:
    """Tests for the PluginCheckboxOptions class."""

    def test_instantiation(self):
        """Test that the class can be instantiated."""
        config = PluginCheckboxOptions()
        assert isinstance(config, PluginCheckboxOptions)


@pytest.mark.django_db
class TestPluginDropdownInput:
    """Tests for the PluginDropdownInput class."""

    def test_instantiation(self):
        """Test that the class can be instantiated."""
        config = PluginDropdownInput()
        assert isinstance(config, PluginDropdownInput)


@pytest.mark.django_db
class TestPluginClearButton:
    """Tests for the PluginClearButton class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = PluginClearButton()
        assert config.title == "Clear Selections"
        assert config.class_name == "clear-button"

    def test_custom_values(self):
        """Test that custom values are accepted."""
        config = PluginClearButton(title="Custom Clear", class_name="custom-clear-button")
        assert config.title == "Custom Clear"
        assert config.class_name == "custom-clear-button"


@pytest.mark.django_db
class TestPluginDropdownHeader:
    """Tests for the PluginDropdownHeader class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = PluginDropdownHeader()
        assert config.title == "Autocomplete"
        assert config.header_class == "container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header"
        assert config.title_row_class == "row"
        assert config.label_class == "form-label"
        assert config.value_field_label == "Value"
        assert config.label_field_label == "Label"
        assert config.label_col_class == "col-6"
        assert config.show_value_field is False
        assert not config.extra_columns

    def test_extra_columns_validation(self):
        """Test that extra_columns validation works correctly."""
        # Valid extra columns
        config = PluginDropdownHeader(extra_columns={"field": "Label"})
        assert config.extra_columns == {"field": "Label"}

        # Invalid extra columns
        with pytest.raises(ValidationError):
            PluginDropdownHeader(extra_columns="invalid")

    def test_custom_values(self):
        """Test that custom values are accepted."""
        config = PluginDropdownHeader(
            title="Custom Header",
            header_class="custom-header",
            title_row_class="custom-row",
            label_class="custom-label",
            value_field_label="ID",
            label_field_label="Name",
            label_col_class="col-4",
            show_value_field=True,
            extra_columns={"field1": "Label 1", "field2": "Label 2"},
        )
        assert config.title == "Custom Header"
        assert config.header_class == "custom-header"
        assert config.title_row_class == "custom-row"
        assert config.label_class == "custom-label"
        assert config.value_field_label == "ID"
        assert config.label_field_label == "Name"
        assert config.label_col_class == "col-4"
        assert config.show_value_field is True
        assert config.extra_columns == {"field1": "Label 1", "field2": "Label 2"}

    def test_property_methods(self):
        """Test the property methods for translations."""
        config = PluginDropdownHeader(
            title="Test Title",
            value_field_label="Test Value",
            label_field_label="Test Label",
            extra_columns={"key": "Test Column"},
        )
        assert config._title == "Test Title"
        assert config._value_field_label == "Test Value"
        assert config._label_field_label == "Test Label"
        assert config._extra_columns == {"key": "Test Column"}

    def test_as_dict_method(self):
        """Test the as_dict method with translations."""
        config = PluginDropdownHeader(
            title="Test Title",
            value_field_label="Test Value",
            label_field_label="Test Label",
            extra_columns={"key": "Test Column"},
        )
        result = config.as_dict()
        assert result["title"] == "Test Title"
        assert result["value_field_label"] == "Test Value"
        assert result["label_field_label"] == "Test Label"
        assert result["extra_columns"] == {"key": "Test Column"}


@pytest.mark.django_db
class TestPluginDropdownFooter:
    """Tests for the PluginDropdownFooter class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = PluginDropdownFooter()
        assert config.title == "Autocomplete Footer"
        assert config.footer_class == "container-fluid mt-1 px-2 border-top dropdown-footer"

    def test_custom_values(self):
        """Test that custom values are accepted."""
        config = PluginDropdownFooter(title="Custom Footer", footer_class="custom-footer")
        assert config.title == "Custom Footer"
        assert config.footer_class == "custom-footer"


@pytest.mark.django_db
class TestPluginRemoveButton:
    """Tests for the PluginRemoveButton class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = PluginRemoveButton()
        assert config.title == "Remove this item"
        assert config.label == "&times;"
        assert config.class_name == "remove"

    def test_custom_values(self):
        """Test that custom values are accepted."""
        config = PluginRemoveButton(title="Custom Remove", label="X", class_name="custom-remove")
        assert config.title == "Custom Remove"
        assert config.label == "X"
        assert config.class_name == "custom-remove"
