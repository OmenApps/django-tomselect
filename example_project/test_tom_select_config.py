"""Tests for TomSelectConfig and the get_plugin_config helper."""

import pytest
from django.core.exceptions import ValidationError

import django_tomselect.app_settings as app_settings
from django_tomselect.app_settings import (
    AllowedCSSFrameworks,
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
    get_plugin_config,
    merge_configs,
)


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
        # verify_config_types() now raises TypeError for invalid types
        with pytest.raises(TypeError) as exc_info:
            config.verify_config_types()

        error_message = str(exc_info.value)
        assert "plugin_checkbox_options must be PluginCheckboxOptions or None" in error_message
        assert "plugin_clear_button must be PluginClearButton or None" in error_message
        assert "plugin_dropdown_header must be PluginDropdownHeader or None" in error_message
        assert "plugin_dropdown_footer must be PluginDropdownFooter or None" in error_message
        assert "plugin_dropdown_input must be PluginDropdownInput or None" in error_message
        assert "plugin_remove_button must be PluginRemoveButton or None" in error_message

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
