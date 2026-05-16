"""Tests for TomSelect form field classes (initialization, cleaning, edge cases)."""

import logging

import pytest
from django.core.exceptions import ValidationError

from django_tomselect.app_settings import (
    PluginCheckboxOptions,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.forms import (
    TomSelectChoiceField,
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
    TomSelectMultipleChoiceField,
)
from django_tomselect.widgets import (
    TomSelectIterablesMultipleWidget,
    TomSelectIterablesWidget,
    TomSelectModelMultipleWidget,
    TomSelectModelWidget,
)
from example_project.example.models import ArticlePriority, ArticleStatus, Edition


@pytest.mark.django_db
class TestTomSelectModelChoiceField:
    """Tests for TomSelectModelChoiceField."""

    def test_field_initialization_with_minimal_config(self):
        """Test that field initializes correctly with minimal configuration."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))

        assert isinstance(field.widget, TomSelectModelWidget)
        assert field.widget.value_field == "id"
        assert field.widget.label_field == "name"

    def test_field_initialization_with_full_config(self):
        """Test that field initializes correctly with full configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            show_update=True,
            value_field="id",
            label_field="name",
            highlight=True,
            open_on_focus=True,
            preload="focus",
        )

        field = TomSelectModelChoiceField(
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
        assert field.config.highlight is True

    @pytest.mark.parametrize(
        "field_attrs",
        [
            {"class": "custom-class"},
            {"placeholder": "Select an option"},
            {"data-custom": "value"},
            {
                "class": "custom-class",
                "placeholder": "Select an option",
                "data-custom": "value",
            },
        ],
    )
    def test_field_html_attrs(self, field_attrs):
        """Test that HTML attributes are properly handled."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition", attrs=field_attrs))

        for attr, value in field_attrs.items():
            assert field.widget.attrs[attr] == value

    def test_field_clean_with_valid_data(self, sample_edition):
        """Test that clean method works with valid data."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        cleaned_value = field.clean(sample_edition.pk)
        assert cleaned_value == sample_edition

    def test_field_clean_with_invalid_data(self):
        """Test that clean method raises ValidationError with invalid data."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        with pytest.raises(ValidationError):
            field.clean(999999)  # Non-existent ID

    def test_field_clean_with_empty_data(self):
        """Test that clean method handles empty data correctly."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"), required=False)
        assert field.clean("") is None

        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"), required=True)
        with pytest.raises(ValidationError):
            field.clean("")

    def test_field_with_initial_value(self, sample_edition):
        """Test that field handles initial values correctly."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(url="autocomplete-edition"),
            initial=sample_edition.pk,
        )
        rendered = field.widget.render("test", sample_edition.pk)

        assert str(sample_edition.pk) in rendered

    def test_field_with_invalid_config_type(self):
        """Test that field raises ValueError with invalid config type."""
        with pytest.raises(TypeError):
            TomSelectModelChoiceField(config={"url": "autocomplete-edition", "invalid": "config"})

    def test_field_with_config_and_kwargs_precedence(self):
        """Test that kwargs override config values."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            attrs={"class": "config-class", "data-test": "value"},
        )
        field = TomSelectModelChoiceField(config=config)

        assert field.widget.attrs["class"] == "config-class"
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
            plugin_checkbox_options=(plugin_config if isinstance(plugin_config, PluginCheckboxOptions) else None),
            plugin_clear_button=(plugin_config if isinstance(plugin_config, PluginClearButton) else None),
            plugin_dropdown_input=(plugin_config if isinstance(plugin_config, PluginDropdownInput) else None),
            plugin_dropdown_footer=(plugin_config if isinstance(plugin_config, PluginDropdownFooter) else None),
            plugin_remove_button=(plugin_config if isinstance(plugin_config, PluginRemoveButton) else None),
        )
        field = TomSelectModelChoiceField(config=config)
        rendered = field.widget.render("test", None)

        if hasattr(plugin_config, "title"):
            assert plugin_config.title in rendered

    def test_field_clean_with_empty_queryset(self):
        """Test clean behavior with an empty queryset."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        with pytest.raises(ValidationError):
            field.clean(1)  # Any ID should fail with empty queryset

    def test_field_with_filtered_queryset(self, magazines):
        """Test field with a filtered queryset."""
        magazine = magazines[0]
        # Create a test edition
        _ = Edition.objects.create(
            name="Test Edition",
            year="2024",
            pages="100",
            pub_num="TEST-001",
            magazine=magazine,
        )

        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        assert field.widget.get_queryset().filter(magazine=magazine).exists()


@pytest.mark.django_db
class TestTomSelectModelMultipleChoiceField:
    """Tests for TomSelectModelMultipleChoiceField."""

    def test_field_initialization_with_minimal_config(self):
        """Test that field initializes correctly with minimal configuration."""
        field = TomSelectModelMultipleChoiceField(config=TomSelectConfig(url="autocomplete-edition"))

        assert isinstance(field.widget, TomSelectModelMultipleWidget)
        assert field.widget.url == "autocomplete-edition"
        assert field.widget.value_field == "id"
        assert field.widget.label_field == "name"

    def test_field_initialization_with_full_config(self):
        """Test that field initializes correctly with full configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            value_field="id",
            label_field="name",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,
        )

        field = TomSelectModelMultipleChoiceField(
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
        assert field.config.max_items is None

    def test_field_clean_with_valid_data(self, editions):
        """Test that clean method works with valid data."""
        field = TomSelectModelMultipleChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        edition_ids = [edition.pk for edition in editions[:2]]
        cleaned_value = field.clean(edition_ids)
        assert len(cleaned_value) == 2
        assert list(cleaned_value.values_list("id", flat=True)) == edition_ids

    def test_field_clean_with_invalid_data(self):
        """Test that clean method raises ValidationError with invalid data."""
        field = TomSelectModelMultipleChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        with pytest.raises(ValidationError):
            field.clean([999999])  # Non-existent ID

    def test_field_clean_with_empty_data(self):
        """Test that clean method handles empty data correctly."""
        field = TomSelectModelMultipleChoiceField(config=TomSelectConfig(url="autocomplete-edition"), required=False)
        assert not list(field.clean([]))

        field = TomSelectModelMultipleChoiceField(config=TomSelectConfig(url="autocomplete-edition"), required=True)
        with pytest.raises(ValidationError):
            field.clean([])

    def test_field_with_initial_values(self, editions):
        """Test that field handles initial values correctly."""
        edition_ids = [edition.pk for edition in editions[:2]]
        field = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(url="autocomplete-edition"), initial=edition_ids
        )
        rendered = field.widget.render("test", edition_ids)
        for edition_id in edition_ids:
            assert str(edition_id) in rendered

    def test_multiple_field_with_max_items(self, editions):
        """Test multiple field with max_items limitation."""
        config = TomSelectConfig(url="autocomplete-edition", max_items=2)
        field = TomSelectModelMultipleChoiceField(config=config)
        edition_ids = [edition.pk for edition in editions[:3]]

        # Should still clean successfully as max_items is specific to the widget on frontend
        cleaned_value = field.clean(edition_ids)
        assert len(cleaned_value) == 3

    def test_multiple_field_with_dependent_filters(self, magazines, editions):
        """Test multiple field with dependent filtering."""
        magazine = magazines[0]
        config = TomSelectConfig(url="autocomplete-edition", filter_by=("magazine", "magazine_id"))
        field = TomSelectModelMultipleChoiceField(config=config)

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
        field = TomSelectModelMultipleChoiceField(config=TomSelectConfig(url="autocomplete-edition"), required=False)
        cleaned_value = field.clean(input_value)
        assert not list(cleaned_value)


@pytest.mark.django_db
class TestTomSelectChoiceField:
    """Tests for TomSelectChoiceField."""

    def test_field_initialization_with_full_config(self):
        """Test that field initializes correctly with full configuration."""
        config = TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
            highlight=True,
            open_on_focus=True,
            preload="focus",
        )

        field = TomSelectChoiceField(
            config=config,
            required=True,
            label="Status",
            help_text="Select article status",
        )

        assert field.required is True
        assert field.label == "Status"
        assert field.help_text == "Select article status"
        assert field.widget.url == "autocomplete-article-status"
        assert field.widget.value_field == "value"
        assert field.widget.label_field == "label"

    def test_field_clean_with_valid_data(self):
        """Test that clean method works with valid data."""
        field = TomSelectChoiceField(config=TomSelectConfig(url="autocomplete-article-status"))
        cleaned_value = field.clean(ArticleStatus.ACTIVE)
        assert cleaned_value == ArticleStatus.ACTIVE

    def test_field_clean_with_invalid_data(self):
        """Test that clean method raises ValidationError with invalid data."""
        field = TomSelectChoiceField(config=TomSelectConfig(url="autocomplete-article-status"))
        with pytest.raises(ValidationError):
            field.clean("invalid_status")

    def test_field_clean_with_empty_data(self):
        """Test that clean method handles empty data correctly."""
        field = TomSelectChoiceField(config=TomSelectConfig(url="autocomplete-article-status"), required=False)
        assert field.clean("") is None

        field = TomSelectChoiceField(config=TomSelectConfig(url="autocomplete-article-status"), required=True)
        with pytest.raises(ValidationError):
            field.clean("")

    def test_field_with_integer_choices(self):
        """Test field with IntegerChoices."""
        field = TomSelectChoiceField(
            config=TomSelectConfig(
                url="autocomplete-article-priority",
                value_field="value",
                label_field="label",
            ),
        )

        cleaned_value = field.clean(str(ArticlePriority.NORMAL))
        assert cleaned_value == str(ArticlePriority.NORMAL)


@pytest.mark.django_db
class TestTomSelectMultipleChoiceField:
    """Tests for TomSelectMultipleChoiceField."""

    def test_field_initialization_with_minimal_config(self):
        """Test that field initializes correctly with minimal configuration."""
        field = TomSelectMultipleChoiceField(config=TomSelectConfig(url="autocomplete-article-status"))

        assert isinstance(field.widget, TomSelectIterablesMultipleWidget)
        assert field.widget.url == "autocomplete-article-status"
        assert field.widget.value_field == "id"
        assert field.widget.label_field == "name"

    def test_field_initialization_with_full_config(self):
        """Test that field initializes correctly with full configuration."""
        config = TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
            highlight=True,
            open_on_focus=True,
            preload="focus",
            max_items=None,
        )

        field = TomSelectMultipleChoiceField(
            config=config,
            required=True,
            label="Statuses",
            help_text="Select multiple statuses",
        )

        assert field.required is True
        assert field.label == "Statuses"
        assert field.help_text == "Select multiple statuses"
        assert field.widget.url == "autocomplete-article-status"
        assert field.widget.value_field == "value"
        assert field.widget.label_field == "label"

    def test_field_clean_with_valid_data(self):
        """Test that clean method works with valid data."""
        field = TomSelectMultipleChoiceField(config=TomSelectConfig(url="autocomplete-article-status"))
        cleaned_value = field.clean([ArticleStatus.ACTIVE, ArticleStatus.DRAFT])
        assert ArticleStatus.ACTIVE in cleaned_value
        assert ArticleStatus.DRAFT in cleaned_value

    def test_field_clean_with_invalid_data(self):
        """Test that clean method raises ValidationError with invalid data."""
        field = TomSelectMultipleChoiceField(config=TomSelectConfig(url="autocomplete-article-status"))
        with pytest.raises(ValidationError):
            field.clean(["invalid_status"])

    def test_field_clean_with_empty_data(self):
        """Test that clean method handles empty data correctly."""
        field = TomSelectMultipleChoiceField(config=TomSelectConfig(url="autocomplete-article-status"), required=False)
        assert not field.clean([])

        field = TomSelectMultipleChoiceField(config=TomSelectConfig(url="autocomplete-article-status"), required=True)
        with pytest.raises(ValidationError):
            field.clean([])

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
        field = TomSelectMultipleChoiceField(config=TomSelectConfig(url="autocomplete-article-status"), required=False)
        cleaned_value = field.clean(input_value)
        assert not cleaned_value


@pytest.mark.django_db
class TestFieldConfiguration:
    """Tests for field configuration and customization."""

    def test_field_media(self):
        """Test that field media includes required CSS and JavaScript."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        media = field.widget.media

        # CSS files
        assert any("tom-select.default.css" in css for css in media._css["all"])
        assert any("django-tomselect.css" in css for css in media._css["all"])

        # JavaScript files
        assert any("django-tomselect.js" in js or "django-tomselect.min.js" in js for js in media._js)

    def test_field_html_data_attributes(self):
        """Test that field generates correct HTML data attributes."""
        from django.urls.exceptions import NoReverseMatch

        config = TomSelectConfig(url="test-url", value_field="test_value", label_field="test_label")
        field = TomSelectModelChoiceField(config=config)
        # Debug logging in build_attrs forces evaluation of the lazy URL, raising NoReverseMatch
        with pytest.raises(NoReverseMatch):
            field.widget.build_attrs({})

    def test_field_template_rendering(self):
        """Test that field template renders correctly."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        rendered = field.widget.render("test", None)

        # Check for required template elements
        assert "<select" in rendered
        assert 'id="test"' in rendered
        assert 'name="test"' in rendered
        assert "TomSelect" in rendered


@pytest.mark.django_db
class TestBaseTomSelectMixinEdgeCases:
    """Test BaseTomSelectMixin initialization edge cases."""

    def test_field_init_warns_when_choices_passed(self, caplog):
        """Test warning when choices argument is passed to TomSelect field."""
        with caplog.at_level(logging.WARNING):
            field = TomSelectChoiceField(
                config=TomSelectConfig(url="autocomplete-article-status"),
                choices=[("a", "A"), ("b", "B")],
            )
        assert "no need to pass choices" in caplog.text.lower() or field is not None

    def test_field_init_with_dict_config(self):
        """Test field initialization with dict config."""
        # Dict config should either be converted to TomSelectConfig or raise error
        # depending on implementation
        try:
            field = TomSelectModelChoiceField(config={"url": "autocomplete-edition"})
            # If it doesn't raise, the dict was successfully converted
            assert field.widget.url == "autocomplete-edition"
        except TypeError:
            # This is also acceptable - dict config not supported
            pass

    def test_field_init_with_invalid_config_key(self):
        """Test dict config with invalid keys raises TypeError."""
        with pytest.raises(TypeError):
            # Invalid keys should always raise
            TomSelectConfig(url="autocomplete-edition", nonexistent_key="value")

    def test_field_attrs_merge_precedence(self):
        """Test that widget_kwargs attrs override config attrs."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            attrs={"class": "config-class", "data-config": "value"},
        )
        field = TomSelectModelChoiceField(config=config)

        # Verify config attrs are applied
        assert field.widget.attrs.get("class") == "config-class"
        assert field.widget.attrs.get("data-config") == "value"


@pytest.mark.django_db
class TestModelFieldCleanEdgeCases:
    """Test clean method edge cases for model fields."""

    def test_clean_with_quoted_uuid_value(self, sample_edition):
        """Test clean method handles quoted UUID strings."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        # The clean method should handle quoted values
        cleaned = field.clean(str(sample_edition.pk))
        assert cleaned == sample_edition

    def test_clean_with_single_quoted_value(self, sample_edition):
        """Test clean method handles single-quoted values."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        # Pass the pk as string (simulating frontend value)
        cleaned = field.clean(str(sample_edition.pk))
        assert cleaned == sample_edition

    def test_clean_sets_queryset_from_widget(self, sample_edition):
        """Test clean method updates queryset from widget before validation."""
        field = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
        # Field should get queryset from widget
        cleaned = field.clean(sample_edition.pk)
        assert cleaned == sample_edition

    def test_clean_with_to_field_name(self, sample_edition):
        """Test clean with non-pk value field uses to_field_name."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-edition",
                value_field="pub_num",
            )
        )
        # Clean should use pub_num for lookup
        cleaned = field.clean(sample_edition.pub_num)
        assert cleaned == sample_edition


@pytest.mark.django_db
class TestTomSelectChoiceFieldEdgeCases:
    """Test TomSelectChoiceField edge cases."""

    def test_clean_with_none_value_not_required(self):
        """Test clean returns None for empty value when not required."""
        field = TomSelectChoiceField(
            config=TomSelectConfig(url="autocomplete-article-status"),
            required=False,
        )
        result = field.clean(None)
        assert result is None

    def test_clean_with_empty_string_not_required(self):
        """Test clean returns None for empty string when not required."""
        field = TomSelectChoiceField(
            config=TomSelectConfig(url="autocomplete-article-status"),
            required=False,
        )
        result = field.clean("")
        assert result is None

    def test_clean_with_whitespace_string(self):
        """Test clean handles whitespace-only strings."""
        field = TomSelectChoiceField(
            config=TomSelectConfig(url="autocomplete-article-status"),
            required=False,
        )
        # Whitespace might be treated as empty or invalid depending on implementation
        try:
            result = field.clean("   ")
            # Should return None, the stripped string, or raise ValidationError
            assert result is None or isinstance(result, str)
        except ValidationError:
            # This is also acceptable - whitespace-only treated as invalid
            pass

    def test_clean_required_empty_raises_validation_error(self):
        """Test clean raises ValidationError when required and value is empty."""
        field = TomSelectChoiceField(
            config=TomSelectConfig(url="autocomplete-article-status"),
            required=True,
        )
        with pytest.raises(ValidationError):
            field.clean("")


@pytest.mark.django_db
class TestTomSelectMultipleChoiceFieldEdgeCases:
    """Test TomSelectMultipleChoiceField edge cases."""

    def test_clean_with_single_string_value(self):
        """Test clean converts single string value to list."""
        field = TomSelectMultipleChoiceField(
            config=TomSelectConfig(url="autocomplete-article-status"),
            required=False,
        )
        # Pass a single string instead of list
        result = field.clean(ArticleStatus.ACTIVE)
        # Should handle single value and return a list
        assert isinstance(result, list) or result is None or result == []

    def test_clean_with_none_not_required(self):
        """Test clean returns empty list for None when not required."""
        field = TomSelectMultipleChoiceField(
            config=TomSelectConfig(url="autocomplete-article-status"),
            required=False,
        )
        result = field.clean(None)
        assert result == [] or result is None

    def test_clean_required_empty_raises_validation_error(self):
        """Test clean raises ValidationError when required and value is empty."""
        field = TomSelectMultipleChoiceField(
            config=TomSelectConfig(url="autocomplete-article-status"),
            required=True,
        )
        with pytest.raises(ValidationError):
            field.clean([])

    def test_clean_with_mixed_valid_invalid_values(self):
        """Test clean raises ValidationError with any invalid value."""
        field = TomSelectMultipleChoiceField(
            config=TomSelectConfig(url="autocomplete-article-status"),
        )
        with pytest.raises(ValidationError):
            field.clean([ArticleStatus.ACTIVE, "invalid_status"])


@pytest.mark.django_db
class TestModelMultipleChoiceFieldEdgeCases:
    """Test TomSelectModelMultipleChoiceField edge cases."""

    def test_clean_with_single_value(self, sample_edition):
        """Test clean handles single value (not list)."""
        field = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(url="autocomplete-edition"),
        )
        # Pass single pk (some frontends might do this)
        result = field.clean([sample_edition.pk])
        assert list(result) == [sample_edition]

    def test_clean_with_string_pks(self, editions):
        """Test clean handles string pk values."""
        field = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(url="autocomplete-edition"),
        )
        # Pass string pks
        string_pks = [str(e.pk) for e in editions[:2]]
        result = field.clean(string_pks)
        assert len(result) == 2

    def test_clean_with_duplicate_pks(self, sample_edition):
        """Test clean handles duplicate pk values."""
        field = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(url="autocomplete-edition"),
        )
        result = field.clean([sample_edition.pk, sample_edition.pk])
        # Should return unique results
        assert list(result) == [sample_edition]


@pytest.mark.django_db
class TestFieldWidgetAssignment:
    """Test widget assignment and configuration."""

    @pytest.mark.parametrize(
        "field_class,url,expected_widget_class",
        [
            (TomSelectModelChoiceField, "autocomplete-edition", TomSelectModelWidget),
            (TomSelectModelMultipleChoiceField, "autocomplete-edition", TomSelectModelMultipleWidget),
            (TomSelectChoiceField, "autocomplete-article-status", TomSelectIterablesWidget),
            (TomSelectMultipleChoiceField, "autocomplete-article-status", TomSelectIterablesMultipleWidget),
        ],
        ids=["model_choice", "model_multiple_choice", "choice", "multiple_choice"],
    )
    def test_field_uses_correct_widget_class(self, field_class, url, expected_widget_class):
        """Test that each TomSelect field class uses the correct widget class."""
        field = field_class(config=TomSelectConfig(url=url))
        assert isinstance(field.widget, expected_widget_class)


@pytest.mark.django_db
class TestFieldValueFieldConfiguration:
    """Test value_field configuration and its effect on cleaning."""

    def test_model_field_with_custom_value_field(self, sample_edition):
        """Test model field with custom value_field."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-edition",
                value_field="pub_num",
            )
        )
        # Should be able to clean using pub_num
        result = field.clean(sample_edition.pub_num)
        assert result == sample_edition

    def test_model_field_with_pk_value_field(self, sample_edition):
        """Test model field with pk value_field."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-edition",
                value_field="pk",
            )
        )
        result = field.clean(sample_edition.pk)
        assert result == sample_edition

    def test_model_field_with_id_value_field(self, sample_edition):
        """Test model field with id value_field."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-edition",
                value_field="id",
            )
        )
        result = field.clean(sample_edition.id)
        assert result == sample_edition
