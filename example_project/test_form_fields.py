"""Tests for Form Fields functionality."""

import pytest
from django import forms
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
from django_tomselect.forms import TomSelectField, TomSelectMultipleField
from django_tomselect.widgets import TomSelectMultipleWidget, TomSelectWidget
from example_project.example.models import Edition, Magazine, ModelFormTestModel


@pytest.mark.django_db
class TestTomSelectField:
    """Tests for TomSelectField."""

    def test_field_initialization_with_minimal_config(self):
        """Test that field initializes correctly with minimal configuration."""
        field = TomSelectField(queryset=Edition.objects.all())

        assert isinstance(field.widget, TomSelectWidget)
        assert field.widget.url == "autocomplete"
        assert field.widget.value_field == "id"
        assert field.widget.label_field == "name"

    def test_field_initialization_with_full_config(self):
        """Test that field initializes correctly with full configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            listview_url="edition-list",
            create_url="create",
            update_url="update",
            value_field="id",
            label_field="name",
            general_config=GeneralConfig(
                highlight=True,
                open_on_focus=True,
                preload="focus",
            ),
        )

        field = TomSelectField(
            queryset=Edition.objects.all(),
            config=config,
            required=True,
            label="Test Label",
            help_text="Test help text",
        )

        assert field.required is True
        assert field.label == "Test Label"
        assert field.help_text == "Test help text"
        assert field.config.url == "autocomplete-edition"
        assert field.config.value_field == "id"
        assert field.config.label_field == "name"
        assert field.config.general_config.highlight is True

    @pytest.mark.parametrize(
        "field_attrs",
        [
            {"class": "custom-class"},
            {"placeholder": "Select an option"},
            {"data-custom": "value"},
            {"class": "custom-class", "placeholder": "Select an option", "data-custom": "value"},
        ],
    )
    def test_field_html_attrs(self, field_attrs):
        """Test that HTML attributes are properly handled."""
        field = TomSelectField(queryset=Edition.objects.all(), attrs=field_attrs)

        for attr, value in field_attrs.items():
            assert field.widget.attrs[attr] == value

    def test_field_clean_with_valid_data(self, sample_edition):
        """Test that clean method works with valid data."""
        field = TomSelectField(queryset=Edition.objects.all())
        cleaned_value = field.clean(sample_edition.pk)
        assert cleaned_value == sample_edition

    def test_field_clean_with_invalid_data(self):
        """Test that clean method raises ValidationError with invalid data."""
        field = TomSelectField(queryset=Edition.objects.all())
        with pytest.raises(ValidationError):
            field.clean(999999)  # Non-existent ID

    def test_field_clean_with_empty_data(self):
        """Test that clean method handles empty data correctly."""
        field = TomSelectField(queryset=Edition.objects.all(), required=False)
        assert field.clean("") is None

        field = TomSelectField(queryset=Edition.objects.all(), required=True)
        with pytest.raises(ValidationError):
            field.clean("")

    def test_field_with_initial_value(self, sample_edition):
        """Test that field handles initial values correctly."""
        field = TomSelectField(queryset=Edition.objects.all(), initial=sample_edition.pk)
        rendered = field.widget.render("test", sample_edition.pk)

        assert str(sample_edition.pk) in rendered
        assert str(sample_edition.name) in rendered

    @pytest.mark.parametrize(
        "config_kwargs,expected_in_html",
        [
            (
                {"plugin_dropdown_header": PluginDropdownHeader(show_value_field=True)},
                ["dropdown-header", "Value", "Label"],
            ),
            ({"general_config": GeneralConfig(placeholder="Custom placeholder")}, ['placeholder="Custom placeholder"']),
        ],
    )
    def test_field_rendering_with_different_configs(self, config_kwargs, expected_in_html):
        """Test that field renders correctly with different configurations."""
        config = TomSelectConfig(**config_kwargs)
        field = TomSelectField(queryset=Edition.objects.all(), config=config)
        rendered = field.widget.render("test", None)
        for expected in expected_in_html:
            assert expected in rendered


@pytest.mark.django_db
class TestTomSelectMultipleField:
    """Tests for TomSelectMultipleField."""

    def test_field_initialization_with_minimal_config(self):
        """Test that field initializes correctly with minimal configuration."""
        field = TomSelectMultipleField(queryset=Edition.objects.all())

        assert isinstance(field.widget, TomSelectMultipleWidget)
        assert field.widget.url == "autocomplete"
        assert field.widget.value_field == "id"
        assert field.widget.label_field == "name"

    def test_field_initialization_with_full_config(self):
        """Test that field initializes correctly with full configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            listview_url="edition-list",
            create_url="create",
            value_field="id",
            label_field="name",
            general_config=GeneralConfig(
                highlight=True,
                open_on_focus=True,
                preload="focus",
                max_items=None,
            ),
        )

        field = TomSelectMultipleField(
            queryset=Edition.objects.all(),
            config=config,
            required=True,
            label="Test Label",
            help_text="Test help text",
        )

        assert field.required is True
        assert field.label == "Test Label"
        assert field.help_text == "Test help text"
        assert field.config.url == "autocomplete-edition"
        assert field.config.value_field == "id"
        assert field.config.label_field == "name"
        assert field.config.general_config.max_items is None

    def test_field_clean_with_valid_data(self, editions):
        """Test that clean method works with valid data."""
        field = TomSelectMultipleField(queryset=Edition.objects.all())
        edition_ids = [edition.pk for edition in editions[:2]]
        cleaned_value = field.clean(edition_ids)
        assert len(cleaned_value) == 2
        assert list(cleaned_value.values_list("id", flat=True)) == edition_ids

    def test_field_clean_with_invalid_data(self):
        """Test that clean method raises ValidationError with invalid data."""
        field = TomSelectMultipleField(queryset=Edition.objects.all())
        with pytest.raises(ValidationError):
            field.clean([999999])  # Non-existent ID

    def test_field_clean_with_empty_data(self):
        """Test that clean method handles empty data correctly."""
        field = TomSelectMultipleField(queryset=Edition.objects.all(), required=False)
        assert not list(field.clean([]))

        field = TomSelectMultipleField(queryset=Edition.objects.all(), required=True)
        with pytest.raises(ValidationError):
            field.clean([])

    def test_field_with_initial_values(self, editions):
        """Test that field handles initial values correctly."""
        edition_ids = [edition.pk for edition in editions[:2]]
        field = TomSelectMultipleField(queryset=Edition.objects.all(), initial=edition_ids)
        rendered = field.widget.render("test", edition_ids)
        for edition_id in edition_ids:
            assert str(edition_id) in rendered


@pytest.mark.django_db
class TestFormIntegration:
    """Tests for form integration with TomSelect fields."""

    def test_form_validation_with_valid_data(self, editions):
        """Test that form validates with valid data."""

        class TestForm(forms.Form):
            """Test form with both types of TomSelect fields."""

            single = TomSelectField(queryset=Edition.objects.all(), required=False)
            multiple = TomSelectMultipleField(queryset=Edition.objects.all(), required=False)

        form = TestForm(data={"single": editions[0].pk, "multiple": [e.pk for e in editions[:2]]})
        assert form.is_valid()
        assert form.cleaned_data["single"] == editions[0]
        assert list(form.cleaned_data["multiple"]) == list(editions[:2])

    def test_form_validation_with_invalid_data(self):
        """Test that form validation fails with invalid data."""

        class TestForm(forms.Form):
            """Test form with both types of TomSelect fields."""

            single = TomSelectField(queryset=Edition.objects.all(), required=False)
            multiple = TomSelectMultipleField(queryset=Edition.objects.all(), required=False)

        form = TestForm(data={"single": 999999, "multiple": [999999]})
        assert not form.is_valid()
        assert "single" in form.errors
        assert "multiple" in form.errors

    def test_form_validation_with_empty_data(self):
        """Test that form validates with empty data when fields are optional."""

        class TestForm(forms.Form):
            """Test form with both types of TomSelect fields."""

            single = TomSelectField(queryset=Edition.objects.all(), required=False)
            multiple = TomSelectMultipleField(queryset=Edition.objects.all(), required=False)

        form = TestForm(data={})
        assert form.is_valid()
        assert form.cleaned_data["single"] is None
        assert not list(form.cleaned_data["multiple"])

    def test_form_with_dependent_fields(self, editions):
        """Test form with dependent fields using filter_by."""

        class DependentForm(forms.Form):
            """Test form with dependent fields."""

            magazine = TomSelectField(queryset=Magazine.objects.all(), required=False)
            edition = TomSelectField(
                queryset=Edition.objects.all(),
                config=TomSelectConfig(filter_by=("magazine", "magazine_id")),
                required=False,
            )

        magazine = editions[0].magazine
        form = DependentForm(data={"magazine": magazine.pk, "edition": editions[0].pk})
        assert form.is_valid()
        assert form.cleaned_data["magazine"] == magazine
        assert form.cleaned_data["edition"] == editions[0]

    def test_model_form_integration(self, editions):
        """Test integration with Django ModelForm."""

        class TestModelForm(forms.ModelForm):
            """Test model form with TomSelect fields."""

            class Meta:
                """Meta options for the form."""

                model = ModelFormTestModel
                fields = "__all__"
                field_classes = {
                    "tomselect": TomSelectField,
                    "tomselect_multiple": TomSelectMultipleField,
                }

        form = TestModelForm(
            data={"name": "Test Model", "tomselect": editions[0].pk, "tomselect_multiple": [e.pk for e in editions[:2]]}
        )
        assert form.is_valid()
        instance = form.save()
        assert instance.tomselect == editions[0]
        assert list(instance.tomselect_multiple.all()) == list(editions[:2])


@pytest.mark.django_db
class TestFieldConfiguration:
    """Tests for field configuration and customization."""

    def test_field_media(self):
        """Test that field media includes required CSS and JavaScript."""
        field = TomSelectField(queryset=Edition.objects.all())
        media = field.widget.media

        # CSS files
        assert any("tom-select.default.css" in css for css in media._css["all"])
        assert any("django-tomselect.css" in css for css in media._css["all"])

        # JavaScript files
        assert any("django-tomselect.js" in js or "django-tomselect.min.js" in js for js in media._js)

    def test_field_html_data_attributes(self):
        """Test that field generates correct HTML data attributes."""
        config = TomSelectConfig(url="test-url", value_field="test_value", label_field="test_label")
        field = TomSelectField(queryset=Edition.objects.all(), config=config)
        attrs = field.widget.build_attrs({})

        assert "data-autocomplete-url" in attrs
        assert attrs["data-value-field"] == "test_value"
        assert attrs["data-label-field"] == "test_label"

    def test_field_template_rendering(self):
        """Test that field template renders correctly."""
        field = TomSelectField(queryset=Edition.objects.all())
        rendered = field.widget.render("test", None)

        # Check for required template elements
        assert "<select" in rendered
        assert 'id="test"' in rendered
        assert 'name="test"' in rendered
        assert "TomSelect" in rendered


@pytest.mark.django_db
class TestTomSelectFieldAdvanced:
    """Advanced tests for TomSelectField."""

    def test_field_with_invalid_config_type(self):
        """Test that field raises ValueError with invalid config type."""
        # Should raise AttributeError when trying to access config.attrs
        with pytest.raises(AttributeError):
            TomSelectField(queryset=Edition.objects.all(), config={"invalid": "config"})

    def test_field_with_config_and_kwargs_precedence(self):
        """Test that kwargs override config values."""
        config = TomSelectConfig(url="autocomplete-edition", value_field="id", attrs={"class": "config-class"})
        field = TomSelectField(
            queryset=Edition.objects.all(), config=config, attrs={"class": "kwarg-class", "data-test": "value"}
        )

        assert field.widget.attrs["class"] == "kwarg-class"
        assert field.widget.attrs["data-test"] == "value"

    @pytest.mark.parametrize(
        "plugin_config",
        [
            (PluginCheckboxOptions()),
            (PluginClearButton(title="Custom Clear")),
            (PluginDropdownInput()),
            (PluginDropdownFooter(title="Custom Footer")),
            (PluginRemoveButton(title="Custom Remove")),
        ],
    )
    def test_field_with_different_plugins(self, plugin_config):
        """Test field initialization with different plugin configurations."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_checkbox_options=plugin_config if isinstance(plugin_config, PluginCheckboxOptions) else None,
            plugin_clear_button=plugin_config if isinstance(plugin_config, PluginClearButton) else None,
            plugin_dropdown_input=plugin_config if isinstance(plugin_config, PluginDropdownInput) else None,
            plugin_dropdown_footer=plugin_config if isinstance(plugin_config, PluginDropdownFooter) else None,
            plugin_remove_button=plugin_config if isinstance(plugin_config, PluginRemoveButton) else None,
        )
        field = TomSelectField(queryset=Edition.objects.all(), config=config)
        rendered = field.widget.render("test", None)

        if hasattr(plugin_config, "title"):
            assert plugin_config.title in rendered

    def test_field_clean_with_empty_queryset(self):
        """Test clean behavior with an empty queryset."""
        field = TomSelectField(queryset=Edition.objects.none())
        with pytest.raises(ValidationError):
            field.clean(1)  # Any ID should fail with empty queryset

    def test_field_with_filtered_queryset(self, magazines):
        """Test field with a filtered queryset."""
        magazine = magazines[0]
        # Create a test edition
        _ = Edition.objects.create(name="Test Edition", year="2024", pages="100", pub_num="TEST-001", magazine=magazine)

        field = TomSelectField(
            queryset=Edition.objects.filter(magazine=magazine), config=TomSelectConfig(url="autocomplete-edition")
        )
        assert field.widget.get_queryset().filter(magazine=magazine).exists()


@pytest.mark.django_db
class TestTomSelectMultipleFieldAdvanced:
    """Advanced tests for TomSelectMultipleField."""

    def test_multiple_field_with_max_items(self, editions):
        """Test multiple field with max_items limitation."""
        config = TomSelectConfig(url="autocomplete-edition", general_config=GeneralConfig(max_items=2))
        field = TomSelectMultipleField(queryset=Edition.objects.all(), config=config)
        edition_ids = [edition.pk for edition in editions[:3]]

        # Should still clean successfully as max_items is specific to the widget on frontend
        cleaned_value = field.clean(edition_ids)
        assert len(cleaned_value) == 3

    def test_multiple_field_with_dependent_filters(self, magazines, editions):
        """Test multiple field with dependent filtering."""
        magazine = magazines[0]
        config = TomSelectConfig(url="autocomplete-edition", filter_by=("magazine", "magazine_id"))
        field = TomSelectMultipleField(queryset=Edition.objects.all(), config=config)

        # Test that the queryset is properly filtered
        filtered_queryset = field.widget.get_queryset().filter(magazine=magazine)
        assert all(edition.magazine == magazine for edition in filtered_queryset)

    @pytest.mark.parametrize(
        "input_value",
        [
            None,
            [],
            (),
            set(),
        ],
    )
    def test_multiple_field_empty_value_handling(self, input_value):
        """Test multiple field handling of various empty values."""
        field = TomSelectMultipleField(queryset=Edition.objects.all(), required=False)
        cleaned_value = field.clean(input_value)
        assert not list(cleaned_value)


@pytest.mark.django_db
class TestFormIntegrationAdvanced:
    """Advanced tests for form integration."""

    def test_form_with_dynamic_queryset(self, magazines):
        """Test form with dynamically changing queryset."""
        # Create test editions for the first magazine
        magazine = magazines[0]
        edition1 = Edition.objects.create(
            name="Test Edition 1", year="2024", pages="100", pub_num="TEST-001", magazine=magazine
        )
        edition2 = Edition.objects.create(
            name="Test Edition 2", year="2024", pages="200", pub_num="TEST-002", magazine=magazine
        )

        class DynamicForm(forms.Form):
            """Test form with dynamically changing queryset."""

            magazine = TomSelectField(queryset=Magazine.objects.all())
            editions = TomSelectMultipleField(queryset=Edition.objects.none())

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                if self.data.get("magazine"):
                    self.fields["editions"].queryset = Edition.objects.filter(magazine_id=self.data["magazine"])

        # Test with magazine selected
        form = DynamicForm(data={"magazine": magazine.pk})
        assert form.fields["editions"].queryset.filter(magazine=magazine).exists()
        assert list(form.fields["editions"].queryset) == [edition1, edition2]

        # And with no magazine selected
        form = DynamicForm(data={})
        assert not form.fields["editions"].queryset.exists()

    def test_form_with_custom_validation(self, editions):
        """Test form with custom validation rules."""

        class CustomValidationForm(forms.Form):
            """Test form with custom validation rules."""

            primary_edition = TomSelectField(queryset=Edition.objects.all())
            secondary_editions = TomSelectMultipleField(queryset=Edition.objects.all())

            def clean(self):
                """Custom validation logic."""
                cleaned_data = super().clean()
                primary = cleaned_data.get("primary_edition")
                secondary = cleaned_data.get("secondary_editions")

                if primary and secondary and primary in secondary:
                    raise ValidationError("Primary edition cannot be included in secondary editions")
                return cleaned_data

        # Test invalid case
        edition = editions[0]
        form = CustomValidationForm(data={"primary_edition": edition.pk, "secondary_editions": [edition.pk]})
        assert not form.is_valid()
        assert form.errors["__all__"]

        # Test valid case
        form = CustomValidationForm(data={"primary_edition": editions[0].pk, "secondary_editions": [editions[1].pk]})
        assert form.is_valid()
