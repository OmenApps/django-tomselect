"""Tests for the django_tomselect.configs module."""

import pytest
from django.core.exceptions import ValidationError

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


@pytest.mark.django_db
class TestGeneralConfig:
    """Tests for the GeneralConfig class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = GeneralConfig()
        assert config.close_after_select is None
        assert config.hide_placeholder is None
        assert config.highlight is True
        assert config.load_throttle == 300
        assert config.loading_class == "loading"
        assert config.max_items == 50
        assert config.max_options is None
        assert config.open_on_focus is True
        assert config.placeholder == "Select a value"
        assert config.preload == "focus"
        assert config.create is False
        assert config.create_filter is None
        assert config.create_with_htmx is False
        assert config.minimum_query_length == 2

    @pytest.mark.parametrize(
        "field,invalid_value,expected_error",
        [
            ("load_throttle", -1, "load_throttle must be positive"),
            ("max_items", 0, "max_items must be greater than 0"),
            ("max_options", 0, "max_options must be greater than 0"),
            ("minimum_query_length", -1, "minimum_query_length must be positive"),
        ],
    )
    def test_validation_errors(self, field, invalid_value, expected_error):
        """Test that validation errors are raised for invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            GeneralConfig(**{field: invalid_value})
        assert expected_error in str(exc_info.value)

    def test_valid_custom_values(self):
        """Test that valid custom values are accepted."""
        config = GeneralConfig(
            close_after_select=True,
            hide_placeholder=True,
            highlight=False,
            load_throttle=500,
            loading_class="custom-loading",
            max_items=100,
            max_options=50,
            open_on_focus=False,
            placeholder="Custom placeholder",
            preload=True,
            create=True,
            create_filter="^[A-Za-z]+$",
            create_with_htmx=True,
            minimum_query_length=3,
        )
        assert config.close_after_select is True
        assert config.hide_placeholder is True
        assert config.highlight is False
        assert config.load_throttle == 500
        assert config.loading_class == "custom-loading"
        assert config.max_items == 100
        assert config.max_options == 50
        assert config.open_on_focus is False
        assert config.placeholder == "Custom placeholder"
        assert config.preload is True
        assert config.create is True
        assert config.create_filter == "^[A-Za-z]+$"
        assert config.create_with_htmx is True
        assert config.minimum_query_length == 3


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
        assert config.extra_columns == {}

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


@pytest.mark.django_db
class TestTomSelectConfig:
    """Tests for the TomSelectConfig class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = TomSelectConfig()
        assert config.url == "autocomplete"
        assert config.listview_url == ""
        assert config.create_url == ""
        assert config.update_url == ""
        assert config.value_field == "id"
        assert config.label_field == "name"
        assert config.create_field == ""
        assert config.filter_by == ()
        assert config.use_htmx is False
        assert config.css_framework == "default"
        assert isinstance(config.general_config, GeneralConfig)
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

    def test_verify_config_types(self):
        """Test that config type verification works."""
        config = TomSelectConfig(
            general_config=GeneralConfig(),
            plugin_checkbox_options=PluginCheckboxOptions(),
            plugin_clear_button=PluginClearButton(),
            plugin_dropdown_header=PluginDropdownHeader(),
            plugin_dropdown_footer=PluginDropdownFooter(),
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_remove_button=PluginRemoveButton(),
        )
        assert config.verify_config_types() is True
