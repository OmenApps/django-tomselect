"""Tests for individual plugin configuration dataclasses (defaults, custom values, validation)."""

import pytest
from django.core.exceptions import ValidationError

from django_tomselect.app_settings import (
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
)


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
