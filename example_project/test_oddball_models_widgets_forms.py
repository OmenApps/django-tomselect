"""Tests for TomSelect widgets and form fields with UUID and non-standard PK models.

Shared fixtures (``sample_uuid_model``, ``sample_pkid_uuid_model``,
``multiple_uuid_models``, ``multiple_pkid_uuid_models``) are defined in
``example_project/conftest.py``.
"""

import uuid

import pytest
from django.core.exceptions import ValidationError

from django_tomselect.app_settings import TomSelectConfig
from django_tomselect.forms import (
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)
from django_tomselect.widgets import TomSelectModelMultipleWidget, TomSelectModelWidget
from example_project.example.forms.oddball_model_forms import (
    PKIDUUIDModelForm,
    UUIDModelForm,
)


@pytest.mark.django_db
class TestFormIntegrationWithUUIDModels:
    """Integration tests for forms with UUID models."""

    def test_uuid_model_form_validation(self, sample_uuid_model):
        """Test that UUID model form validates correctly."""
        form_data = {
            "uuid_model_by_id": str(sample_uuid_model.id),
            "uuid_model_by_name": sample_uuid_model.name,
        }

        form = UUIDModelForm(data=form_data)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            assert cleaned_data["uuid_model_by_id"] == sample_uuid_model
            assert cleaned_data["uuid_model_by_name"] == sample_uuid_model
        else:
            pytest.fail(f"Form validation failed: {form.errors}")

    def test_pkid_uuid_model_form_validation(self, sample_pkid_uuid_model):
        """Test that PKID & UUID model form validates correctly."""
        form_data = {
            "pkid_model_by_pkid": sample_pkid_uuid_model.pkid,
            "pkid_model_by_uuid": str(sample_pkid_uuid_model.id),
        }

        form = PKIDUUIDModelForm(data=form_data)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            assert cleaned_data["pkid_model_by_pkid"] == sample_pkid_uuid_model
            assert cleaned_data["pkid_model_by_uuid"] == sample_pkid_uuid_model
        else:
            pytest.fail(f"Form validation failed: {form.errors}")


@pytest.mark.django_db
class TestModelWithUUIDPkWidget:
    """Tests for TomSelectModelWidget with ModelWithUUIDPk."""

    def test_widget_with_uuid_pk_as_value_field(self, sample_uuid_model):
        """Test widget using UUID primary key as value_field."""
        config = TomSelectConfig(
            url="autocomplete-uuid-pk",
            value_field="id",
            label_field="name",
        )
        widget = TomSelectModelWidget(config=config)

        # Test context generation with UUID
        context = widget.get_context("test", sample_uuid_model.id, {})

        assert context["widget"]["value"] == sample_uuid_model.id
        assert isinstance(sample_uuid_model.id, uuid.UUID)

        # Test selected options
        selected_options = context["widget"].get("selected_options", [])
        if selected_options:
            assert selected_options[0]["value"] == str(sample_uuid_model.id)
            assert selected_options[0]["label"] == sample_uuid_model.name

    def test_widget_with_name_as_value_field(self, sample_uuid_model):
        """Test widget using name field as value_field with UUID PK model."""
        config = TomSelectConfig(
            url="autocomplete-uuid-pk",
            value_field="name",
            label_field="name",
        )
        widget = TomSelectModelWidget(config=config)

        # Test context generation with name value
        context = widget.get_context("test", sample_uuid_model.name, {})

        assert context["widget"]["value"] == sample_uuid_model.name

        # Test selected options
        selected_options = context["widget"].get("selected_options", [])
        if selected_options:
            assert selected_options[0]["value"] == sample_uuid_model.name
            assert selected_options[0]["label"] == sample_uuid_model.name

    def test_widget_uuid_string_conversion(self, sample_uuid_model):
        """Test that UUID values are properly converted to strings in options."""
        config = TomSelectConfig(
            url="autocomplete-uuid-pk",
            value_field="id",
            label_field="name",
        )
        widget = TomSelectModelWidget(config=config)

        # Test with UUID object
        uuid_value = sample_uuid_model.id
        context = widget.get_context("test", uuid_value, {})

        # Verify UUID is converted to string in selected options
        selected_options = context["widget"].get("selected_options", [])
        if selected_options:
            assert isinstance(selected_options[0]["value"], str)
            assert selected_options[0]["value"] == str(uuid_value)

    def test_widget_with_uuid_string_input(self, sample_uuid_model):
        """Test widget behavior when UUID is passed as string."""
        config = TomSelectConfig(
            url="autocomplete-uuid-pk",
            value_field="id",
            label_field="name",
        )
        widget = TomSelectModelWidget(config=config)

        # Test with UUID as string
        uuid_string = str(sample_uuid_model.id)
        context = widget.get_context("test", uuid_string, {})

        assert context["widget"]["value"] == uuid_string

        # Test selected options
        selected_options = context["widget"].get("selected_options", [])
        if selected_options:
            assert selected_options[0]["value"] == uuid_string

    def test_multiple_widget_uuid_pk(self, multiple_uuid_models):
        """Test multiple widget with UUID primary keys."""
        config = TomSelectConfig(
            url="autocomplete-uuid-pk",
            value_field="id",
            label_field="name",
        )
        widget = TomSelectModelMultipleWidget(config=config)

        # Test with list of UUID values
        uuid_values = [model.id for model in multiple_uuid_models[:2]]
        context = widget.get_context("test", uuid_values, {})

        assert context["widget"]["is_multiple"]
        selected_options = context["widget"].get("selected_options", [])

        if selected_options:
            assert len(selected_options) == 2
            selected_values = {opt["value"] for opt in selected_options}
            expected_values = {str(uuid_val) for uuid_val in uuid_values}
            assert selected_values == expected_values


@pytest.mark.django_db
class TestModelWithPKIDAndUUIDIdWidget:
    """Tests for TomSelectModelWidget with ModelWithPKIDAndUUIDId."""

    def test_widget_with_pkid_as_value_field(self, sample_pkid_uuid_model):
        """Test widget using pkid (AutoField) as value_field."""
        config = TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="pkid",
            label_field="name",
        )
        widget = TomSelectModelWidget(config=config)

        # Test context generation with pkid value
        context = widget.get_context("test", sample_pkid_uuid_model.pkid, {})

        assert context["widget"]["value"] == sample_pkid_uuid_model.pkid
        assert isinstance(sample_pkid_uuid_model.pkid, int)

        # Test selected options
        selected_options = context["widget"].get("selected_options", [])
        if selected_options:
            assert selected_options[0]["value"] == str(sample_pkid_uuid_model.pkid)
            assert selected_options[0]["label"] == sample_pkid_uuid_model.name

    def test_widget_with_uuid_id_as_value_field(self, sample_pkid_uuid_model):
        """Test widget using UUID id field (not pk) as value_field."""
        config = TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="id",
            label_field="name",
        )
        widget = TomSelectModelWidget(config=config)

        # Test context generation with UUID id value
        context = widget.get_context("test", sample_pkid_uuid_model.id, {})

        assert context["widget"]["value"] == sample_pkid_uuid_model.id
        assert isinstance(sample_pkid_uuid_model.id, uuid.UUID)

        # Test selected options
        selected_options = context["widget"].get("selected_options", [])
        if selected_options:
            assert selected_options[0]["value"] == str(sample_pkid_uuid_model.id)
            assert selected_options[0]["label"] == sample_pkid_uuid_model.name

    def test_widget_pk_vs_uuid_field_distinction(self, sample_pkid_uuid_model):
        """Test that widget correctly distinguishes between pk and uuid fields."""
        # Test with pkid (actual primary key)
        config_pkid = TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="pkid",
            label_field="name",
        )
        widget_pkid = TomSelectModelWidget(config=config_pkid)
        context_pkid = widget_pkid.get_context("test", sample_pkid_uuid_model.pkid, {})

        # Test with id (UUID field, not primary key)
        config_uuid = TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="id",
            label_field="name",
        )
        widget_uuid = TomSelectModelWidget(config=config_uuid)
        context_uuid = widget_uuid.get_context("test", sample_pkid_uuid_model.id, {})

        # Values should be different
        assert context_pkid["widget"]["value"] != context_uuid["widget"]["value"]
        assert isinstance(context_pkid["widget"]["value"], int)
        assert isinstance(context_uuid["widget"]["value"], uuid.UUID)

    def test_multiple_widget_pkid_uuid_model(self, multiple_pkid_uuid_models):
        """Test multiple widget with PKID & UUID model."""
        # Test with pkid values
        config = TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="pkid",
            label_field="name",
        )
        widget = TomSelectModelMultipleWidget(config=config)

        pkid_values = [model.pkid for model in multiple_pkid_uuid_models[:2]]
        context = widget.get_context("test", pkid_values, {})

        assert context["widget"]["is_multiple"]
        selected_options = context["widget"].get("selected_options", [])

        if selected_options:
            assert len(selected_options) == 2
            selected_values = {int(opt["value"]) for opt in selected_options}
            assert selected_values == set(pkid_values)


@pytest.mark.django_db
class TestModelWithUUIDPkForms:
    """Tests for TomSelect form fields with ModelWithUUIDPk."""

    def test_form_field_uuid_pk_validation(self, sample_uuid_model):
        """Test form field validation with UUID primary key."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Test validation with UUID object
        cleaned_value = field.clean(sample_uuid_model.id)
        assert cleaned_value == sample_uuid_model

        # Test validation with UUID string
        cleaned_value_str = field.clean(str(sample_uuid_model.id))
        assert cleaned_value_str == sample_uuid_model

    def test_form_field_uuid_pk_invalid_validation(self):
        """Test form field validation with invalid UUID."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Test with invalid UUID
        with pytest.raises(ValidationError):
            field.clean("invalid-uuid")

        # Test with non-existent UUID
        with pytest.raises(ValidationError):
            field.clean(str(uuid.uuid4()))

    def test_form_field_name_as_value_field(self, sample_uuid_model):
        """Test form field with name as value_field."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="name",
                label_field="name",
            )
        )

        # Test validation with name value
        cleaned_value = field.clean(sample_uuid_model.name)
        assert cleaned_value == sample_uuid_model

    def test_multiple_form_field_uuid_pk(self, multiple_uuid_models):
        """Test multiple form field with UUID primary keys."""
        field = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Test with list of UUID values
        uuid_values = [model.id for model in multiple_uuid_models[:2]]
        cleaned_value = field.clean(uuid_values)

        assert len(cleaned_value) == 2
        cleaned_ids = list(cleaned_value.values_list("id", flat=True))
        assert set(cleaned_ids) == set(uuid_values)

    def test_multiple_form_field_uuid_strings(self, multiple_uuid_models):
        """Test multiple form field with UUID values as strings."""
        field = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Test with list of UUID strings
        uuid_strings = [str(model.id) for model in multiple_uuid_models[:2]]
        cleaned_value = field.clean(uuid_strings)

        assert len(cleaned_value) == 2
        cleaned_ids = [str(uuid_val) for uuid_val in cleaned_value.values_list("id", flat=True)]
        assert set(cleaned_ids) == set(uuid_strings)


@pytest.mark.django_db
class TestModelWithPKIDAndUUIDIdForms:
    """Tests for TomSelect form fields with ModelWithPKIDAndUUIDId."""

    def test_form_field_pkid_validation(self, sample_pkid_uuid_model):
        """Test form field validation with pkid as value_field."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        # Test validation with pkid value
        cleaned_value = field.clean(sample_pkid_uuid_model.pkid)
        assert cleaned_value == sample_pkid_uuid_model

    def test_form_field_uuid_id_validation(self, sample_pkid_uuid_model):
        """Test form field validation with UUID id as value_field."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        # Test validation with UUID id value
        cleaned_value = field.clean(sample_pkid_uuid_model.id)
        assert cleaned_value == sample_pkid_uuid_model

        # Test validation with UUID id as string
        cleaned_value_str = field.clean(str(sample_pkid_uuid_model.id))
        assert cleaned_value_str == sample_pkid_uuid_model

    def test_form_field_pkid_vs_uuid_distinction(self, sample_pkid_uuid_model):
        """Test that form fields correctly handle pkid vs uuid id fields."""
        # Field configured for pkid
        field_pkid = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        # Field configured for UUID id
        field_uuid = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        # Both should return the same model instance
        cleaned_pkid = field_pkid.clean(sample_pkid_uuid_model.pkid)
        cleaned_uuid = field_uuid.clean(sample_pkid_uuid_model.id)

        assert cleaned_pkid == sample_pkid_uuid_model
        assert cleaned_uuid == sample_pkid_uuid_model
        assert cleaned_pkid == cleaned_uuid

    def test_multiple_form_field_mixed_values(self, multiple_pkid_uuid_models):
        """Test multiple form field with mixed pkid and UUID values."""
        # Test with pkid values
        field_pkid = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        pkid_values = [model.pkid for model in multiple_pkid_uuid_models[:2]]
        cleaned_pkid = field_pkid.clean(pkid_values)

        # Test with UUID values
        field_uuid = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        uuid_values = [model.id for model in multiple_pkid_uuid_models[:2]]
        cleaned_uuid = field_uuid.clean(uuid_values)

        # Both should return the same models
        assert len(cleaned_pkid) == 2
        assert len(cleaned_uuid) == 2
        assert set(cleaned_pkid) == set(cleaned_uuid)
