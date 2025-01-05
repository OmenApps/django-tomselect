"""Tests for Form Fields functionality."""

import pytest
from django import forms
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
    TomSelectModelMultipleWidget,
    TomSelectModelWidget,
)
from example_project.example.models import (
    Article,
    ArticlePriority,
    ArticleStatus,
    Author,
    Edition,
    Magazine,
)


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
class TestFormIntegration:
    """Tests for form integration with TomSelect fields."""

    def test_form_validation_with_valid_data(self, editions):
        """Test that form validates with valid data."""

        class TestForm(forms.Form):
            """Test form with both types of TomSelect fields."""

            single = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"), required=False)
            multiple = TomSelectModelMultipleChoiceField(
                config=TomSelectConfig(url="autocomplete-edition"), required=False
            )

        form = TestForm(data={"single": editions[0].pk, "multiple": [e.pk for e in editions[:2]]})
        assert form.is_valid()
        assert form.cleaned_data["single"] == editions[0]
        assert list(form.cleaned_data["multiple"]) == list(editions[:2])

    def test_form_validation_with_invalid_data(self):
        """Test that form validation fails with invalid data."""

        class TestForm(forms.Form):
            """Test form with both types of TomSelect fields."""

            single = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"), required=False)
            multiple = TomSelectModelMultipleChoiceField(
                config=TomSelectConfig(url="autocomplete-edition"), required=False
            )

        form = TestForm(data={"single": 999999, "multiple": [999999]})
        assert not form.is_valid()
        assert "single" in form.errors
        assert "multiple" in form.errors

    def test_form_validation_with_empty_data(self):
        """Test that form validates with empty data when fields are optional."""

        class TestForm(forms.Form):
            """Test form with both types of TomSelect fields."""

            single = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"), required=False)
            multiple = TomSelectModelMultipleChoiceField(
                config=TomSelectConfig(url="autocomplete-edition"), required=False
            )

        form = TestForm(data={})
        assert form.is_valid()
        assert form.cleaned_data["single"] is None
        assert not list(form.cleaned_data["multiple"])

    def test_form_with_dependent_fields(self, editions):
        """Test form with dependent fields using filter_by."""

        class FilterByMagazineForm(forms.Form):
            """Test form with dependent fields."""

            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))
            edition = TomSelectModelChoiceField(
                config=TomSelectConfig(url="autocomplete-edition", filter_by=("magazine", "magazine_id")),
                required=False,
            )

        magazine = editions[0].magazine
        form = FilterByMagazineForm(data={"magazine": magazine.pk, "edition": editions[0].pk})
        assert form.is_valid()
        assert form.cleaned_data["magazine"] == magazine
        assert form.cleaned_data["edition"] == editions[0]

    def test_form_with_dynamic_queryset(self, magazines):
        """Test form with dynamically changing queryset."""
        # Create test editions for the first magazine
        magazine = magazines[0]
        edition1 = Edition.objects.create(
            name="Test Edition 1",
            year="2024",
            pages="100",
            pub_num="TEST-001",
            magazine=magazine,
        )
        edition2 = Edition.objects.create(
            name="Test Edition 2",
            year="2024",
            pages="200",
            pub_num="TEST-002",
            magazine=magazine,
        )

        class DynamicForm(forms.Form):
            """Test form with dynamically changing queryset."""

            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))
            editions = TomSelectModelMultipleChoiceField(
                config=TomSelectConfig(url="autocomplete-edition"), required=False
            )

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

            primary_edition = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-edition"))
            secondary_editions = TomSelectModelMultipleChoiceField(config=TomSelectConfig(url="autocomplete-edition"))

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
        form = CustomValidationForm(
            data={
                "primary_edition": editions[0].pk,
                "secondary_editions": [editions[1].pk],
            }
        )
        assert form.is_valid()

    def test_form_with_multiple_field_types(self):
        """Test form combining multiple TomSelect field types."""

        class CompleteForm(forms.Form):
            """Test form with multiple TomSelect field types."""

            status = TomSelectChoiceField(config=TomSelectConfig(url="autocomplete-article-status"))
            priorities = TomSelectMultipleChoiceField(config=TomSelectConfig(url="autocomplete-article-priority"))

        form_data = {
            "status": ArticleStatus.ACTIVE,
            "priorities": [ArticlePriority.NORMAL, ArticlePriority.HIGH],
        }
        form = CompleteForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data["status"] == ArticleStatus.ACTIVE
        assert form.cleaned_data["priorities"] == [
            ArticlePriority.NORMAL,
            ArticlePriority.HIGH,
        ]

    def test_form_with_conditional_required(self):
        """Test form with conditionally required fields."""

        class ConditionalForm(forms.Form):
            """Test form with conditionally required fields."""

            status = TomSelectChoiceField(
                config=TomSelectConfig(url="autocomplete-article-status"),
                required=False,
            )
            priority = TomSelectChoiceField(
                config=TomSelectConfig(url="autocomplete-article-priority"),
                required=False,
            )

            def clean(self):
                cleaned_data = super().clean()
                status = cleaned_data.get("status")
                priority = cleaned_data.get("priority")

                if status == ArticleStatus.ACTIVE and not priority:
                    raise ValidationError("Priority is required for active status")
                return cleaned_data

        # Test valid case
        form = ConditionalForm(data={"status": ArticleStatus.ACTIVE, "priority": ArticlePriority.HIGH})
        assert form.is_valid()

        # Test invalid case
        form = ConditionalForm(data={"status": ArticleStatus.ACTIVE})
        assert not form.is_valid()
        assert "Priority is required for active status" in str(form.errors["__all__"])

    def test_create_article_with_relations(self, magazines, editions):
        """Test creating an article with related models using TomSelect fields."""
        from example_project.example.models import Article  # pylint: disable=C0415

        class ArticleForm(forms.Form):
            """Form for creating Article with TomSelect fields."""
            title = forms.CharField()
            word_count = forms.IntegerField()
            magazine = TomSelectModelChoiceField(
                config=TomSelectConfig(url="autocomplete-magazine")
            )
            edition = TomSelectModelChoiceField(  # Changed to single select
                config=TomSelectConfig(url="autocomplete-edition")
            )
            status = TomSelectChoiceField(
                config=TomSelectConfig(url="autocomplete-article-status")
            )
            priority = TomSelectChoiceField(
                config=TomSelectConfig(url="autocomplete-article-priority")
            )

        form_data = {
            'title': 'Test Article',
            'word_count': 1000,
            'magazine': magazines[0].pk,
            'edition': editions[0].pk,  # Single edition
            'status': ArticleStatus.ACTIVE,
            'priority': str(ArticlePriority.NORMAL)
        }

        form = ArticleForm(data=form_data)
        assert form.is_valid()
        cleaned_data = form.cleaned_data

        # Create Article instance
        article = Article.objects.create(
            title=cleaned_data['title'],
            word_count=cleaned_data['word_count'],
            magazine=cleaned_data['magazine'],
            edition=cleaned_data['edition'],  # Set edition directly
            status=cleaned_data['status'],
            priority=int(cleaned_data['priority'])
        )

        # Verify created instance
        assert article.pk is not None
        assert article.title == 'Test Article'
        assert article.magazine == magazines[0]
        assert article.edition == editions[0]
        assert article.status == ArticleStatus.ACTIVE
        assert article.priority == ArticlePriority.NORMAL

    def test_model_form_create_with_tomselect(self, magazines):
        """Test creating model instance using ModelForm with TomSelect fields."""
        class EditionModelForm(forms.ModelForm):
            """ModelForm for creating Edition with TomSelect fields."""
            magazine = TomSelectModelChoiceField(
                config=TomSelectConfig(url="autocomplete-magazine")
            )

            class Meta:
                """Meta class for EditionModelForm."""
                model = Edition
                fields = ['name', 'year', 'pages', 'pub_num', 'magazine']

        form_data = {
            'name': 'New Edition',
            'year': '2025',
            'pages': '100',
            'pub_num': 'TEST-002',
            'magazine': magazines[0].pk
        }

        form = EditionModelForm(data=form_data)
        assert form.is_valid()
        edition = form.save()

        # Verify created instance
        assert edition.pk is not None
        assert edition.name == 'New Edition'
        assert edition.magazine == magazines[0]

    def test_update_model_with_tomselect(self, editions, magazines):
        """Test updating model instance using form with TomSelect fields."""
        edition = editions[0]
        new_magazine = magazines[1]  # Different magazine for update

        class EditionUpdateForm(forms.ModelForm):
            """ModelForm for updating Edition with TomSelect fields."""
            magazine = TomSelectModelChoiceField(
                config=TomSelectConfig(url="autocomplete-magazine")
            )

            class Meta:
                """Meta class for EditionUpdateForm."""
                model = Edition
                fields = ['name', 'magazine']

        form_data = {
            'name': 'Updated Edition',
            'magazine': new_magazine.pk
        }

        form = EditionUpdateForm(instance=edition, data=form_data)
        assert form.is_valid()
        updated_edition = form.save()

        # Verify updates
        assert updated_edition.pk == edition.pk  # Same instance
        assert updated_edition.name == 'Updated Edition'
        assert updated_edition.magazine == new_magazine

    def test_form_with_initial_instance(self, editions):
        """Test form initialization with instance and TomSelect fields."""
        edition = editions[0]

        class EditionForm(forms.ModelForm):
            """ModelForm for Edition with TomSelect fields."""
            magazine = TomSelectModelChoiceField(
                config=TomSelectConfig(url="autocomplete-magazine")
            )

            class Meta:
                """Meta class for EditionForm."""
                model = Edition
                fields = ['name', 'magazine']

        form = EditionForm(instance=edition)

        # Verify initial data is correctly set
        assert form.initial['name'] == edition.name
        assert form.initial['magazine'] == edition.magazine.pk

        # Verify widget has selected option
        rendered = form.as_p()
        assert str(edition.magazine.pk) in rendered

    def test_form_with_create_option_and_validation_error(self):
        """Test form submission with create option and validation error."""
        class TestForm(forms.Form):
            """Test form with create option and validation error."""
            edition = TomSelectModelChoiceField(
                config=TomSelectConfig(
                    url="autocomplete-edition",
                    show_create=True,
                    create_field="name",
                ),
                required=True,
            )

        # Simulate form submission with invalid data
        form = TestForm(data={"edition": ""})
        assert not form.is_valid()
        assert "edition" in form.errors

    def test_create_with_dependent_fields_validation(self, magazines, editions):
        """Test validation rules between dependent fields."""
        from example_project.example.models import Article  # pylint: disable=C0415

        class ArticleForm(forms.ModelForm):
            """ModelForm for Article with dependent fields."""
            magazine = TomSelectModelChoiceField(
                config=TomSelectConfig(url="autocomplete-magazine")
            )
            edition = TomSelectModelChoiceField(
                config=TomSelectConfig(
                    url="autocomplete-edition",
                    filter_by=("magazine", "magazine_id")
                )
            )

            def clean(self):
                cleaned_data = super().clean()
                edition = cleaned_data.get('edition')
                magazine = cleaned_data.get('magazine')

                if edition and magazine and edition.magazine != magazine:
                    raise ValidationError("Edition must belong to selected magazine")
                return cleaned_data

            class Meta:
                """Meta class for ArticleForm."""
                model = Article
                fields = ['title', 'magazine', 'edition']

        # Test with mismatched magazine/edition
        form_data = {
            'title': 'Test Article',
            'magazine': magazines[0].pk,
            'edition': editions[1].pk,  # Edition from different magazine
        }

        form = ArticleForm(data=form_data)
        assert not form.is_valid()
        assert "Edition must belong to selected magazine" in str(form.errors)


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
        config = TomSelectConfig(url="test-url", value_field="test_value", label_field="test_label")
        field = TomSelectModelChoiceField(config=config)
        attrs = field.widget.build_attrs({})

        assert "data-autocomplete-url" in attrs
        assert attrs["data-value-field"] == "test_value"
        assert attrs["data-label-field"] == "test_label"

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
class TestFormsetIntegration:
    """Tests for formset integration with TomSelect fields."""

    def test_basic_model_formset(self, magazines):
        """Test basic model formset functionality with TomSelect fields."""
        EditionFormSet = forms.modelformset_factory(  # pylint: disable=C0103
            Edition,
            fields=["name", "magazine"],
            extra=2,
            form=forms.ModelForm,
        )

        # Create a custom form that uses TomSelect
        class EditionForm(forms.ModelForm):
            """Custom form for Edition with TomSelect field."""
            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))

            class Meta:
                """Meta class for EditionForm."""
                model = Edition
                fields = ["name", "magazine"]

        EditionFormSet = forms.modelformset_factory(  # pylint: disable=C0103
            Edition,
            form=EditionForm,
            extra=2,
        )

        # Test formset creation
        formset = EditionFormSet(queryset=Edition.objects.none())
        assert len(formset.forms) == 2
        assert isinstance(formset.forms[0].fields["magazine"].widget, TomSelectModelWidget)

        # Test valid data submission
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-name": "Edition 1",
            "form-0-magazine": magazines[0].pk,
            "form-1-name": "Edition 2",
            "form-1-magazine": magazines[1].pk,
        }

        formset = EditionFormSet(data=data)
        assert formset.is_valid()

        # Save the formset
        instances = formset.save()
        assert len(instances) == 2
        assert all(isinstance(instance, Edition) for instance in instances)
        assert instances[0].magazine == magazines[0]
        assert instances[1].magazine == magazines[1]

    def test_inline_formset(self, magazines):
        """Test inline formset functionality with TomSelect fields."""

        class EditionInlineForm(forms.ModelForm):
            """Custom inline form for Edition with TomSelect field."""
            class Meta:
                """Meta class for EditionInlineForm."""
                model = Edition
                fields = ["name", "year", "pages", "pub_num"]
                # Note: magazine field is handled automatically by the inline formset

        EditionFormSet = forms.inlineformset_factory(  # pylint: disable=C0103
            Magazine,
            Edition,
            form=EditionInlineForm,
            fields=["name", "year", "pages", "pub_num"],
            extra=2,
            can_delete=True,
        )

        magazine = magazines[0]

        # Create some initial editions
        edition = Edition.objects.create(
            name="Existing Edition 1", year="2024", pages="100", pub_num="TEST-001", magazine=magazine
        )

        # Test formset with initial data
        formset = EditionFormSet(instance=magazine)
        assert len(formset.forms) == 3  # 1 existing + 2 extra

        # Get initial count of editions
        initial_count = Edition.objects.filter(magazine=magazine).count()
        assert initial_count == 1

        # Test valid data submission with updates and new additions
        data = {
            "edition_set-TOTAL_FORMS": "3",
            "edition_set-INITIAL_FORMS": "1",
            "edition_set-MIN_NUM_FORMS": "0",
            "edition_set-MAX_NUM_FORMS": "1000",
            "edition_set-0-id": edition.pk,
            "edition_set-0-magazine": magazine.pk,
            "edition_set-0-name": "Updated Edition 1",
            "edition_set-0-year": "2024",
            "edition_set-0-pages": "100",
            "edition_set-0-pub_num": "TEST-001",
            "edition_set-0-DELETE": "",
            "edition_set-1-id": "",
            "edition_set-1-magazine": magazine.pk,
            "edition_set-1-name": "New Edition 2",
            "edition_set-1-year": "2024",
            "edition_set-1-pages": "200",
            "edition_set-1-pub_num": "TEST-002",
            "edition_set-1-DELETE": "",
            "edition_set-2-id": "",
            "edition_set-2-magazine": magazine.pk,
            "edition_set-2-name": "",
            "edition_set-2-year": "",
            "edition_set-2-pages": "",
            "edition_set-2-pub_num": "",
            "edition_set-2-DELETE": "",
        }

        formset = EditionFormSet(data=data, instance=magazine)

        assert formset.is_valid()

        # Save the formset
        formset.save()

        # Verify database state after save
        editions = Edition.objects.filter(magazine=magazine).order_by("id")
        assert editions.count() == 2  # One existing updated + one new

        # Verify the updated edition
        updated_edition = editions.get(id=edition.pk)
        assert updated_edition.name == "Updated Edition 1"
        assert updated_edition.year == "2024"
        assert updated_edition.pages == "100"
        assert updated_edition.pub_num == "TEST-001"
        assert updated_edition.magazine == magazine

        # Verify the new edition
        new_edition = editions.exclude(id=edition.pk).get()
        assert new_edition.name == "New Edition 2"
        assert new_edition.year == "2024"
        assert new_edition.pages == "200"
        assert new_edition.pub_num == "TEST-002"
        assert new_edition.magazine == magazine

    def test_formset_with_dependent_fields(self, magazines):
        """Test formset with dependent TomSelect fields."""

        class ArticleForm(forms.ModelForm):
            """Custom form for Article with dependent fields."""
            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))
            edition = TomSelectModelChoiceField(
                config=TomSelectConfig(url="autocomplete-edition", filter_by=("magazine", "magazine_id"))
            )
            authors = TomSelectModelMultipleChoiceField(config=TomSelectConfig(url="autocomplete-author"))

            class Meta:
                """Meta class for ArticleForm."""
                model = Article
                fields = ["title", "word_count", "magazine", "edition", "authors"]

        ArticleFormSet = forms.formset_factory(ArticleForm, extra=2)  # pylint: disable=C0103

        # Create test authors
        author1 = Author.objects.create(name="Author 1", bio="Test Bio 1")
        author2 = Author.objects.create(name="Author 2", bio="Test Bio 2")

        # Create test edition
        edition = Edition.objects.create(
            name="Test Edition", year="2024", pages="100", pub_num="TEST-001", magazine=magazines[0]
        )

        # Test formset submission
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-title": "Article 1",
            "form-0-word_count": 1000,
            "form-0-magazine": magazines[0].pk,
            "form-0-edition": edition.pk,
            "form-0-authors": [author1.pk],
            "form-1-title": "Article 2",
            "form-1-word_count": 2000,
            "form-1-magazine": magazines[0].pk,
            "form-1-edition": edition.pk,
            "form-1-authors": [author1.pk, author2.pk],
        }

        formset = ArticleFormSet(data=data)
        assert formset.is_valid()

        # Verify form relationships
        assert formset.forms[0].cleaned_data["magazine"] == magazines[0]
        assert formset.forms[0].cleaned_data["edition"] == edition
        assert list(formset.forms[0].cleaned_data["authors"]) == [author1]
        assert list(formset.forms[1].cleaned_data["authors"]) == [author1, author2]

    def test_formset_validation(self, magazines):
        """Test formset validation with TomSelect fields."""

        class EditionForm(forms.ModelForm):
            """Custom form for Edition with TomSelect field."""
            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))

            class Meta:
                """Meta class for EditionForm."""
                model = Edition
                fields = ["name", "year", "pages", "pub_num", "magazine"]

        # Custom formset with validation
        class BaseEditionFormSet(forms.BaseModelFormSet):
            """Custom formset for Edition with validation."""
            def clean(self):
                """Custom validation logic."""
                super().clean()
                names = []
                for form in self.forms:
                    if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                        name = form.cleaned_data.get("name")
                        if name in names:
                            raise ValidationError("Edition names must be unique within the formset.")
                        names.append(name)

        EditionFormSet = forms.modelformset_factory(  # pylint: disable=C0103
            Edition,
            form=EditionForm,
            formset=BaseEditionFormSet,
            extra=2,
        )

        # Test validation failure with duplicate names
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-name": "Same Name",
            "form-0-year": "2024",
            "form-0-pages": "100",
            "form-0-pub_num": "TEST-001",
            "form-0-magazine": magazines[0].pk,
            "form-1-name": "Same Name",  # Duplicate name
            "form-1-year": "2024",
            "form-1-pages": "200",
            "form-1-pub_num": "TEST-002",
            "form-1-magazine": magazines[0].pk,
        }

        formset = EditionFormSet(data=data)
        assert not formset.is_valid()
        assert "Edition names must be unique within the formset." in str(formset.non_form_errors())

    def test_formset_with_required_fields(self, magazines):
        """Test formset with required TomSelect fields."""

        class EditionForm(forms.ModelForm):
            """Custom form for Edition with TomSelect field."""
            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"), required=True)

            class Meta:
                """Meta class for EditionForm."""
                model = Edition
                fields = ["name", "magazine"]

        EditionFormSet = forms.modelformset_factory(  # pylint: disable=C0103
            Edition,
            form=EditionForm,
            extra=1,
            validate_min=True,
            min_num=1
        )

        # Test validation failure with missing required field
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-name": "Test Edition",
            "form-0-magazine": "",  # Missing required field
        }

        formset = EditionFormSet(data=data)
        assert not formset.is_valid()
        assert "magazine" in formset.forms[0].errors

    def test_formset_with_initial_data(self, magazines):
        """Test formset with initial data in TomSelect fields."""
        # Create initial editions
        Edition.objects.create(
            name="Edition 1", year="2024", pages="100", pub_num="TEST-001", magazine=magazines[0]
        )
        Edition.objects.create(
            name="Edition 2", year="2024", pages="200", pub_num="TEST-002", magazine=magazines[1]
        )

        class EditionForm(forms.ModelForm):
            """Custom form for Edition with TomSelect field."""
            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))

            class Meta:
                """Meta class for EditionForm."""
                model = Edition
                fields = ["name", "magazine"]

        EditionFormSet = forms.modelformset_factory(Edition, form=EditionForm, extra=0)  # pylint: disable=C0103

        # Test formset with initial instances
        formset = EditionFormSet(queryset=Edition.objects.all())

        # Verify initial data
        assert len(formset.forms) == 2
        assert formset.forms[0].initial["magazine"] == magazines[0].pk
        assert formset.forms[1].initial["magazine"] == magazines[1].pk

        # Verify widget has selected options
        rendered = formset.as_p()
        assert str(magazines[0].pk) in rendered
        assert str(magazines[1].pk) in rendered

    def test_empty_formset_handling(self, magazines):
        """Test handling of empty formsets with TomSelect fields."""

        class EditionForm(forms.ModelForm):
            """Custom form for Edition with TomSelect field."""
            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))

            class Meta:
                """Meta class for EditionForm."""
                model = Edition
                fields = ["name", "magazine"]

        EditionFormSet = forms.modelformset_factory(  # pylint: disable=C0103
            Edition,
            form=EditionForm,
            extra=1,
            can_delete=True
        )

        # Test submission with empty forms
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-name": "",
            "form-0-magazine": "",
        }

        formset = EditionFormSet(data=data)
        assert formset.is_valid()  # Should be valid if no required fields
        assert len(formset.cleaned_data) == 1
        assert not any(formset.cleaned_data)  # All forms should be empty
