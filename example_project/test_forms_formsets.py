"""Tests for formset integration with TomSelect fields."""

import pytest
from django import forms
from django.core.exceptions import ValidationError

from django_tomselect.app_settings import TomSelectConfig
from django_tomselect.forms import (
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)
from django_tomselect.widgets import TomSelectModelWidget
from example_project.example.models import (
    Article,
    Author,
    Edition,
    Magazine,
)


@pytest.mark.django_db
class TestFormsetIntegration:
    """Tests for formset integration with TomSelect fields."""

    def test_basic_model_formset(self, magazines):
        """Test basic model formset functionality with TomSelect fields."""
        EditionFormSet = forms.modelformset_factory(  # noqa: N806
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

        EditionFormSet = forms.modelformset_factory(  # noqa: N806
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

        EditionFormSet = forms.inlineformset_factory(  # noqa: N806
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

        ArticleFormSet = forms.formset_factory(ArticleForm, extra=2)  # noqa: N806

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

        EditionFormSet = forms.modelformset_factory(  # noqa: N806
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

        EditionFormSet = forms.modelformset_factory(  # noqa: N806
            Edition, form=EditionForm, extra=1, validate_min=True, min_num=1
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
        Edition.objects.create(name="Edition 1", year="2024", pages="100", pub_num="TEST-001", magazine=magazines[0])
        Edition.objects.create(name="Edition 2", year="2024", pages="200", pub_num="TEST-002", magazine=magazines[1])

        class EditionForm(forms.ModelForm):
            """Custom form for Edition with TomSelect field."""

            magazine = TomSelectModelChoiceField(config=TomSelectConfig(url="autocomplete-magazine"))

            class Meta:
                """Meta class for EditionForm."""

                model = Edition
                fields = ["name", "magazine"]

        EditionFormSet = forms.modelformset_factory(Edition, form=EditionForm, extra=0)  # noqa: N806

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

        EditionFormSet = forms.modelformset_factory(  # noqa: N806
            Edition, form=EditionForm, extra=1, can_delete=True
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


@pytest.mark.django_db
class TestEditionWithFilterFormset:
    """Test the EditionWithFilterFormsetForm and formset for filter_by in formsets."""

    def test_form_has_filter_by_config(self):
        """Test that the edition field has filter_by configured."""
        from example_project.example.forms import EditionWithFilterFormsetForm

        form = EditionWithFilterFormsetForm()
        edition_field = form.fields["edition"]

        # Check that the widget has filter_by set (stored as direct attribute)
        assert edition_field.widget.filter_by == ("magazine", "magazine_id")

    def test_formset_creates_multiple_forms(self):
        """Test that the formset creates the expected number of forms."""
        from example_project.example.forms import EditionWithFilterFormset

        formset = EditionWithFilterFormset(prefix="test")

        # Default extra=2, so should have 2 empty forms
        assert len(formset.forms) == 2

    def test_formset_form_prefixes_are_correct(self):
        """Test that formset forms have correct prefixes for filter_by to work."""
        from example_project.example.forms import EditionWithFilterFormset

        formset = EditionWithFilterFormset(prefix="edition_filter")

        # Check that field names have the correct prefix format
        for i, form in enumerate(formset.forms):
            magazine_name = form["magazine"].html_name
            edition_name = form["edition"].html_name

            assert magazine_name == f"edition_filter-{i}-magazine"
            assert edition_name == f"edition_filter-{i}-edition"

    def test_formset_rendered_html_contains_filter_config(self):
        """Test that rendered formset HTML includes filter_by configuration."""
        from example_project.example.forms import EditionWithFilterFormset

        formset = EditionWithFilterFormset(prefix="test")
        html = formset.as_p()

        # The rendered HTML should contain the filter_by configuration
        assert "magazine" in html
        assert "magazine_id" in html

    def test_formset_validation_with_valid_data(self, magazines):
        """Test formset validation with valid magazine/edition data."""
        from example_project.example.forms import EditionWithFilterFormset
        from example_project.example.models import Edition

        edition = Edition.objects.create(
            name="Test Edition", year="2024", pages="100", pub_num="TEST-001", magazine=magazines[0]
        )

        data = {
            "test-TOTAL_FORMS": "2",
            "test-INITIAL_FORMS": "0",
            "test-MIN_NUM_FORMS": "0",
            "test-MAX_NUM_FORMS": "1000",
            "test-0-magazine": magazines[0].pk,
            "test-0-edition": edition.pk,
            "test-1-magazine": "",
            "test-1-edition": "",
        }

        formset = EditionWithFilterFormset(data=data, prefix="test")
        assert formset.is_valid()


@pytest.mark.django_db
class TestCategoryModelFormExcludeBy:
    """Test CategoryModelForm with exclude_by to prevent circular references."""

    def test_form_has_exclude_by_config(self):
        """Test that the parent field has exclude_by configured."""
        from example_project.example.forms import CategoryModelForm

        form = CategoryModelForm()
        parent_field = form.fields["parent"]

        # Check that the widget has exclude_by set to prevent self-reference (stored as direct attribute)
        assert parent_field.widget.exclude_by == ("id", "id")

    def test_exclude_by_context_in_rendered_widget(self):
        """Test that exclude_by configuration is present in rendered widget."""
        from example_project.example.forms import CategoryModelForm
        from example_project.example.models import Category

        category = Category.objects.create(name="Test Category")
        form = CategoryModelForm(instance=category)

        # Render the parent field
        html = form["parent"].as_widget()

        # Should contain exclude configuration
        assert "id" in html  # exclude_field should be 'id'

    def test_model_formset_with_exclude_by(self):
        """Test CategoryModelFormset properly handles exclude_by."""
        from example_project.example.forms import CategoryModelFormset
        from example_project.example.models import Category

        # Create some categories
        parent = Category.objects.create(name="Parent Category")
        child = Category.objects.create(name="Child Category", parent=parent)

        queryset = Category.objects.filter(pk__in=[parent.pk, child.pk])
        formset = CategoryModelFormset(queryset=queryset, prefix="category")

        # Check that forms have exclude_by configured (stored as direct widget attribute)
        for form in formset.forms:
            if hasattr(form, "fields") and "parent" in form.fields:
                assert form.fields["parent"].widget.exclude_by == ("id", "id")
