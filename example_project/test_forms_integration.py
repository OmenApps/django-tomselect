"""Tests for form integration with TomSelect fields."""

import pytest
from django import forms
from django.core.exceptions import ValidationError

from django_tomselect.app_settings import TomSelectConfig
from django_tomselect.forms import (
    TomSelectChoiceField,
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
    TomSelectMultipleChoiceField,
)
from example_project.example.models import (
    Article,
    ArticlePriority,
    ArticleStatus,
    Edition,
)


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

        class ArticleForm(forms.Form):
            """Form for creating Article with TomSelect fields."""

            title = forms.CharField()
            word_count = forms.IntegerField()
            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))
            edition = TomSelectModelChoiceField(  # Changed to single select
                config=TomSelectConfig(url="autocomplete-edition")
            )
            status = TomSelectChoiceField(config=TomSelectConfig(url="autocomplete-article-status"))
            priority = TomSelectChoiceField(config=TomSelectConfig(url="autocomplete-article-priority"))

        form_data = {
            "title": "Test Article",
            "word_count": 1000,
            "magazine": magazines[0].pk,
            "edition": editions[0].pk,  # Single edition
            "status": ArticleStatus.ACTIVE,
            "priority": str(ArticlePriority.NORMAL),
        }

        form = ArticleForm(data=form_data)
        assert form.is_valid()
        cleaned_data = form.cleaned_data

        # Create Article instance
        article = Article.objects.create(
            title=cleaned_data["title"],
            word_count=cleaned_data["word_count"],
            magazine=cleaned_data["magazine"],
            edition=cleaned_data["edition"],  # Set edition directly
            status=cleaned_data["status"],
            priority=int(cleaned_data["priority"]),
        )

        # Verify created instance
        assert article.pk is not None
        assert article.title == "Test Article"
        assert article.magazine == magazines[0]
        assert article.edition == editions[0]
        assert article.status == ArticleStatus.ACTIVE
        assert article.priority == ArticlePriority.NORMAL

    def test_model_form_create_with_tomselect(self, magazines):
        """Test creating model instance using ModelForm with TomSelect fields."""

        class EditionModelForm(forms.ModelForm):
            """ModelForm for creating Edition with TomSelect fields."""

            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))

            class Meta:
                """Meta class for EditionModelForm."""

                model = Edition
                fields = ["name", "year", "pages", "pub_num", "magazine"]

        form_data = {
            "name": "New Edition",
            "year": "2025",
            "pages": "100",
            "pub_num": "TEST-002",
            "magazine": magazines[0].pk,
        }

        form = EditionModelForm(data=form_data)
        assert form.is_valid()
        edition = form.save()

        # Verify created instance
        assert edition.pk is not None
        assert edition.name == "New Edition"
        assert edition.magazine == magazines[0]

    def test_update_model_with_tomselect(self, editions, magazines):
        """Test updating model instance using form with TomSelect fields."""
        edition = editions[0]
        new_magazine = magazines[1]  # Different magazine for update

        class EditionUpdateForm(forms.ModelForm):
            """ModelForm for updating Edition with TomSelect fields."""

            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))

            class Meta:
                """Meta class for EditionUpdateForm."""

                model = Edition
                fields = ["name", "magazine"]

        form_data = {"name": "Updated Edition", "magazine": new_magazine.pk}

        form = EditionUpdateForm(instance=edition, data=form_data)
        assert form.is_valid()
        updated_edition = form.save()

        # Verify updates
        assert updated_edition.pk == edition.pk  # Same instance
        assert updated_edition.name == "Updated Edition"
        assert updated_edition.magazine == new_magazine

    def test_form_with_initial_instance(self, editions):
        """Test form initialization with instance and TomSelect fields."""
        edition = editions[0]

        class EditionForm(forms.ModelForm):
            """ModelForm for Edition with TomSelect fields."""

            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))

            class Meta:
                """Meta class for EditionForm."""

                model = Edition
                fields = ["name", "magazine"]

        form = EditionForm(instance=edition)

        # Verify initial data is correctly set
        assert form.initial["name"] == edition.name
        assert form.initial["magazine"] == edition.magazine.pk

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

        class ArticleForm(forms.ModelForm):
            """ModelForm for Article with dependent fields."""

            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))
            edition = TomSelectModelChoiceField(
                config=TomSelectConfig(url="autocomplete-edition", filter_by=("magazine", "magazine_id"))
            )

            def clean(self):
                cleaned_data = super().clean()
                edition = cleaned_data.get("edition")
                magazine = cleaned_data.get("magazine")

                if edition and magazine and edition.magazine != magazine:
                    raise ValidationError("Edition must belong to selected magazine")
                return cleaned_data

            class Meta:
                """Meta class for ArticleForm."""

                model = Article
                fields = ["title", "magazine", "edition"]

        # Test with mismatched magazine/edition
        form_data = {
            "title": "Test Article",
            "magazine": magazines[0].pk,
            "edition": editions[1].pk,  # Edition from different magazine
        }

        form = ArticleForm(data=form_data)
        assert not form.is_valid()
        assert "Edition must belong to selected magazine" in str(form.errors)
