"""Tests for TomSelect widgets and forms with UUID and non-standard PK models."""

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db.models import Q

from django_tomselect.app_settings import TomSelectConfig
from django_tomselect.autocompletes import AutocompleteModelView
from django_tomselect.forms import (
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)
from django_tomselect.widgets import TomSelectModelMultipleWidget, TomSelectModelWidget
from example_project.example.forms.oddball_model_forms import (
    PKIDUUIDModelForm,
    UUIDModelForm,
)
from example_project.example.models import ModelWithPKIDAndUUIDId, ModelWithUUIDPk


@pytest.fixture
def sample_uuid_model():
    """Create a sample ModelWithUUIDPk instance."""
    return ModelWithUUIDPk.objects.create(name="Test UUID Model")


@pytest.fixture
def sample_pkid_uuid_model():
    """Create a sample ModelWithPKIDAndUUIDId instance."""
    return ModelWithPKIDAndUUIDId.objects.create(name="Test PKID UUID Model")


@pytest.fixture
def multiple_uuid_models():
    """Create multiple ModelWithUUIDPk instances."""
    return [ModelWithUUIDPk.objects.create(name=f"UUID Model {i}") for i in range(1, 4)]


@pytest.fixture
def multiple_pkid_uuid_models():
    """Create multiple ModelWithPKIDAndUUIDId instances."""
    return [ModelWithPKIDAndUUIDId.objects.create(name=f"PKID UUID Model {i}") for i in range(1, 4)]


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


@pytest.mark.django_db
class TestEdgeCasesAndBugReproduction:
    """Tests specifically designed to reproduce and verify edge case bugs."""

    def test_uuid_pk_form_submission_bug(self, sample_uuid_model):
        """Test to reproduce 'Select a valid choice' bug with UUID PK."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Simulate form submission with UUID string (common scenario)
        form_data = str(sample_uuid_model.id)

        try:
            cleaned_value = field.clean(form_data)
            assert cleaned_value == sample_uuid_model
        except ValidationError as e:
            pytest.fail(f"UUID PK validation failed: {e}")

    def test_pkid_uuid_model_form_submission_bug(self, sample_pkid_uuid_model):
        """Test to reproduce 'Select a valid choice' bug with PKID & UUID model."""
        # Test with pkid
        field_pkid = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        try:
            cleaned_value = field_pkid.clean(sample_pkid_uuid_model.pkid)
            assert cleaned_value == sample_pkid_uuid_model
        except ValidationError as e:
            pytest.fail(f"PKID validation failed: {e}")

        # Test with UUID id field
        field_uuid = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        try:
            cleaned_value = field_uuid.clean(str(sample_pkid_uuid_model.id))
            assert cleaned_value == sample_pkid_uuid_model
        except ValidationError as e:
            pytest.fail(f"UUID ID field validation failed: {e}")

    def test_string_representation_parsing(self, sample_uuid_model, sample_pkid_uuid_model):
        """Test widget's ability to parse string representations of model instances."""
        # Test UUID PK model string representation
        uuid_widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Simulate string representation that might come from form data
        uuid_string_repr = f"{{'id': '{sample_uuid_model.id}', 'name': '{sample_uuid_model.name}'}}"
        context = uuid_widget.get_context("test", uuid_string_repr, {})

        # Should handle string representation gracefully
        assert "widget" in context

        # Test PKID & UUID model string representation
        pkid_widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        pkid_string_repr = f"{{'pkid': {sample_pkid_uuid_model.pkid}, 'name': '{sample_pkid_uuid_model.name}'}}"
        context = pkid_widget.get_context("test", pkid_string_repr, {})

        # Should handle string representation gracefully
        assert "widget" in context

    def test_mixed_type_values_in_multiple_selection(self, multiple_uuid_models):
        """Test multiple selection with mixed value types (UUID objects and strings)."""
        field = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Mix of UUID objects and strings
        mixed_values = [
            multiple_uuid_models[0].id,
            str(multiple_uuid_models[1].id),
        ]

        try:
            cleaned_value = field.clean(mixed_values)
            assert len(cleaned_value) == 2
            cleaned_ids = list(cleaned_value.values_list("id", flat=True))
            expected_ids = [multiple_uuid_models[0].id, multiple_uuid_models[1].id]
            assert set(cleaned_ids) == set(expected_ids)
        except ValidationError as e:
            pytest.fail(f"Mixed type validation failed: {e}")

    def test_queryset_filtering_with_uuid_fields(self, sample_uuid_model, sample_pkid_uuid_model):
        """Test that queryset filtering works correctly with UUID fields."""
        # Test UUID PK filtering
        uuid_widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        queryset = uuid_widget.get_queryset()
        if queryset:
            # Should be able to filter by UUID
            filtered = queryset.filter(id=sample_uuid_model.id)
            assert sample_uuid_model in filtered

        # Test PKID & UUID filtering
        pkid_widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        queryset = pkid_widget.get_queryset()
        if queryset:
            # Should be able to filter by UUID field (not PK)
            filtered = queryset.filter(id=sample_pkid_uuid_model.id)
            assert sample_pkid_uuid_model in filtered


@pytest.mark.django_db
class TestQuerysetValidationUUIDModels:
    """Tests specifically for queryset validation issues with UUID models."""

    def test_uuid_pk_queryset_lookup_by_pk(self, sample_uuid_model):
        """Test that UUID PK models can be found using pk lookup."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="pk",
                label_field="name",
            )
        )

        queryset = widget.get_queryset()
        if queryset and queryset.model == ModelWithUUIDPk:
            # Test pk lookup with UUID
            found = queryset.filter(pk=sample_uuid_model.pk).first()
            assert found == sample_uuid_model

            # Test pk lookup with UUID string
            found_str = queryset.filter(pk=str(sample_uuid_model.pk)).first()
            assert found_str == sample_uuid_model

    def test_uuid_pk_queryset_lookup_by_id(self, sample_uuid_model):
        """Test that UUID PK models can be found using id lookup."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        queryset = widget.get_queryset()
        if queryset and queryset.model == ModelWithUUIDPk:
            # Test id lookup with UUID
            found = queryset.filter(id=sample_uuid_model.id).first()
            assert found == sample_uuid_model

            # Test id lookup with UUID string
            found_str = queryset.filter(id=str(sample_uuid_model.id)).first()
            assert found_str == sample_uuid_model

    def test_pkid_uuid_model_queryset_lookups(self, sample_pkid_uuid_model):
        """Test different lookup strategies for PKID & UUID model."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        queryset = widget.get_queryset()
        if queryset and queryset.model == ModelWithPKIDAndUUIDId:
            # Test pk lookup (should use pkid)
            found_pk = queryset.filter(pk=sample_pkid_uuid_model.pk).first()
            assert found_pk == sample_pkid_uuid_model

            # Test pkid lookup
            found_pkid = queryset.filter(pkid=sample_pkid_uuid_model.pkid).first()
            assert found_pkid == sample_pkid_uuid_model

            # Test id lookup (UUID field)
            found_id = queryset.filter(id=sample_pkid_uuid_model.id).first()
            assert found_id == sample_pkid_uuid_model

    def test_form_field_queryset_validation_uuid_pk(self, sample_uuid_model, monkeypatch):
        """Test form field queryset validation with UUID PK."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Mock the widget's get_queryset method to return test queryset
        test_queryset = ModelWithUUIDPk.objects.filter(id=sample_uuid_model.id)
        monkeypatch.setattr(field.widget, "get_queryset", lambda: test_queryset)

        # Test validation with UUID string
        try:
            cleaned_value = field.clean(str(sample_uuid_model.id))
            assert cleaned_value == sample_uuid_model
        except ValidationError as e:
            pytest.fail(f"UUID string validation failed: {e}")

        # Test validation with UUID object
        try:
            cleaned_value = field.clean(sample_uuid_model.id)
            assert cleaned_value == sample_uuid_model
        except ValidationError as e:
            pytest.fail(f"UUID object validation failed: {e}")

    def test_form_field_queryset_validation_pkid_uuid(self, sample_pkid_uuid_model, monkeypatch):
        """Test form field queryset validation with PKID & UUID model."""
        # Test with pkid as value_field
        field_pkid = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        test_queryset = ModelWithPKIDAndUUIDId.objects.filter(pkid=sample_pkid_uuid_model.pkid)
        monkeypatch.setattr(field_pkid.widget, "get_queryset", lambda: test_queryset)

        try:
            cleaned_value = field_pkid.clean(sample_pkid_uuid_model.pkid)
            assert cleaned_value == sample_pkid_uuid_model
        except ValidationError as e:
            pytest.fail(f"PKID validation failed: {e}")

        # Test with UUID id as value_field
        field_uuid = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        test_queryset_uuid = ModelWithPKIDAndUUIDId.objects.filter(id=sample_pkid_uuid_model.id)
        monkeypatch.setattr(field_uuid.widget, "get_queryset", lambda: test_queryset_uuid)

        try:
            cleaned_value = field_uuid.clean(str(sample_pkid_uuid_model.id))
            assert cleaned_value == sample_pkid_uuid_model
        except ValidationError as e:
            pytest.fail(f"UUID ID field validation failed: {e}")

    def test_multiple_field_queryset_validation(self, multiple_uuid_models, monkeypatch):
        """Test multiple choice field queryset validation."""
        field = TomSelectModelMultipleChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Mock queryset to include test models
        test_uuids = [model.id for model in multiple_uuid_models[:2]]
        test_queryset = ModelWithUUIDPk.objects.filter(id__in=test_uuids)
        monkeypatch.setattr(field.widget, "get_queryset", lambda: test_queryset)

        # Test with list of UUID strings
        uuid_strings = [str(uuid_val) for uuid_val in test_uuids]
        try:
            cleaned_value = field.clean(uuid_strings)
            assert len(cleaned_value) == 2
            cleaned_ids = list(cleaned_value.values_list("id", flat=True))
            assert set(cleaned_ids) == set(test_uuids)
        except ValidationError as e:
            pytest.fail(f"Multiple UUID validation failed: {e}")

    def test_value_field_mismatch_detection(self, sample_uuid_model):
        """Test detection of value_field mismatches that cause validation errors."""
        # Create field with wrong value_field
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="wrong_field",
                label_field="name",
            )
        )

        # Should raise a validation error due to field mismatch
        with pytest.raises(ValidationError):
            field.clean(sample_uuid_model.id)

    def test_empty_queryset_validation(self, sample_uuid_model, monkeypatch):
        """Test validation behavior with empty queryset."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Mock empty queryset
        empty_queryset = ModelWithUUIDPk.objects.none()
        monkeypatch.setattr(field.widget, "get_queryset", lambda: empty_queryset)

        # Should raise validation error for any value
        with pytest.raises(ValidationError):
            field.clean(sample_uuid_model.id)

    def test_queryset_filter_by_value_field(self, sample_uuid_model, sample_pkid_uuid_model):
        """Test that queryset filtering works correctly with different value_fields."""
        # Test UUID PK model with id as value_field
        widget_uuid = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Mock the _get_selected_options method to test filtering logic
        selected_values = [sample_uuid_model.id]
        queryset = ModelWithUUIDPk.objects.all()

        # Test Q filter construction
        if widget_uuid.value_field == "pk":
            final_filter = Q(pk__in=selected_values)
        else:
            final_filter = Q(**{f"{widget_uuid.value_field}__in": selected_values})

        filtered_objects = queryset.filter(final_filter)
        assert sample_uuid_model in filtered_objects

        # Test PKID & UUID model with different value_fields
        for value_field, test_value in [("pkid", sample_pkid_uuid_model.pkid), ("id", sample_pkid_uuid_model.id)]:
            widget_pkid = TomSelectModelWidget(
                config=TomSelectConfig(
                    url="autocomplete-pkid-uuid",
                    value_field=value_field,
                    label_field="name",
                )
            )

            queryset = ModelWithPKIDAndUUIDId.objects.all()
            selected_values = [test_value]

            if widget_pkid.value_field == "pk":
                final_filter = Q(pk__in=selected_values)
            else:
                final_filter = Q(**{f"{widget_pkid.value_field}__in": selected_values})

            filtered_objects = queryset.filter(final_filter)
            assert sample_pkid_uuid_model in filtered_objects


@pytest.mark.django_db
class TestAutocompleteViewWithUUIDModels:
    """Tests for autocomplete view behavior with UUID models."""

    def test_mock_autocomplete_view_uuid_pk(self, sample_uuid_model, rf):
        """Test mock autocomplete view for UUID PK model."""

        class MockUUIDAutocompleteView(AutocompleteModelView):
            model = ModelWithUUIDPk
            search_lookups = ["name__icontains"]
            value_fields = ["id", "name"]

        view = MockUUIDAutocompleteView()
        request = rf.get("/")
        view.setup(request, model=ModelWithUUIDPk)

        # Test queryset
        queryset = view.get_queryset()
        assert sample_uuid_model in queryset

        # Test prepare_results
        results = view.prepare_results(queryset.filter(id=sample_uuid_model.id))
        assert len(results) == 1
        assert results[0]["id"] == sample_uuid_model.id
        assert "id" in results[0]
        assert "name" in results[0]

    def test_mock_autocomplete_view_pkid_uuid(self, sample_pkid_uuid_model, rf):
        """Test mock autocomplete view for PKID & UUID model."""

        class MockPKIDUUIDAutocompleteView(AutocompleteModelView):
            model = ModelWithPKIDAndUUIDId
            search_lookups = ["name__icontains"]
            value_fields = ["pkid", "id", "name"]

        view = MockPKIDUUIDAutocompleteView()
        request = rf.get("/")
        view.setup(request, model=ModelWithPKIDAndUUIDId)

        # Test queryset
        queryset = view.get_queryset()
        assert sample_pkid_uuid_model in queryset

        # Test prepare_results
        results = view.prepare_results(queryset.filter(pkid=sample_pkid_uuid_model.pkid))
        assert len(results) == 1
        assert results[0]["pkid"] == sample_pkid_uuid_model.pkid
        assert results[0]["id"] == sample_pkid_uuid_model.id
        assert "pkid" in results[0]
        assert "id" in results[0]
        assert "name" in results[0]

    def test_value_field_handling_in_prepare_results(self, sample_uuid_model, sample_pkid_uuid_model, rf):
        """Test that prepare_results handles different value_fields correctly."""
        # Test UUID PK model
        class UUIDView(AutocompleteModelView):
            model = ModelWithUUIDPk
            value_fields = ["id", "name"]

        uuid_view = UUIDView()
        request = rf.get("/")
        uuid_view.setup(request, model=ModelWithUUIDPk)

        queryset = ModelWithUUIDPk.objects.filter(id=sample_uuid_model.id)
        results = uuid_view.prepare_results(queryset)

        if results:
            # Check that UUID is properly handled
            assert "id" in results[0]
            assert isinstance(results[0]["id"], uuid.UUID) or isinstance(results[0]["id"], str)

        # Test PKID & UUID model with different value_fields
        class PKIDView(AutocompleteModelView):
            model = ModelWithPKIDAndUUIDId
            value_fields = ["pkid", "name"]

        pkid_view = PKIDView()
        request = rf.get("/")
        pkid_view.setup(request, model=ModelWithPKIDAndUUIDId)

        queryset = ModelWithPKIDAndUUIDId.objects.filter(pkid=sample_pkid_uuid_model.pkid)
        results = pkid_view.prepare_results(queryset)

        if results:
            assert "pkid" in results[0]
            assert isinstance(results[0]["pkid"], int)

        # Test with UUID id field
        class UUIDIdView(AutocompleteModelView):
            model = ModelWithPKIDAndUUIDId
            value_fields = ["id", "name"]

        uuid_id_view = UUIDIdView()
        request = rf.get("/")
        uuid_id_view.setup(request, model=ModelWithPKIDAndUUIDId)

        queryset = ModelWithPKIDAndUUIDId.objects.filter(id=sample_pkid_uuid_model.id)
        results = uuid_id_view.prepare_results(queryset)

        if results:
            assert "id" in results[0]
            # UUID should be converted to string or kept as UUID
            assert isinstance(results[0]["id"], (uuid.UUID, str))


@pytest.mark.django_db
class TestBugReproductionScenarios:
    """Specific test scenarios to reproduce the reported bugs."""

    def test_form_post_data_simulation_uuid_pk(self, sample_uuid_model):
        """Simulate form POST data that would cause 'Select a valid choice' error."""
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        # Simulate different kinds of POST data that might be submitted
        test_cases = [
            str(sample_uuid_model.id),
            sample_uuid_model.id,
            f"'{sample_uuid_model.id}'",
            sample_uuid_model.pk,
        ]

        for test_value in test_cases:
            try:
                cleaned_value = field.clean(test_value)
                assert cleaned_value == sample_uuid_model, f"Failed for value: {test_value}"
            except ValidationError as e:
                pytest.fail(f"Validation failed for {test_value}: {e}")

    def test_form_post_data_simulation_pkid_uuid(self, sample_pkid_uuid_model):
        """Simulate form POST data for PKID & UUID model."""
        # Test with pkid as value_field
        field_pkid = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        pkid_test_cases = [
            sample_pkid_uuid_model.pkid,
            str(sample_pkid_uuid_model.pkid),
            sample_pkid_uuid_model.pk,
        ]

        for test_value in pkid_test_cases:
            try:
                cleaned_value = field_pkid.clean(test_value)
                assert cleaned_value == sample_pkid_uuid_model, f"Failed for PKID value: {test_value}"
            except ValidationError as e:
                pytest.fail(f"PKID validation failed for {test_value}: {e}")

        # Test with UUID id as value_field
        field_uuid = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        uuid_test_cases = [
            sample_pkid_uuid_model.id,
            str(sample_pkid_uuid_model.id),
            f"'{sample_pkid_uuid_model.id}'",
        ]

        for test_value in uuid_test_cases:
            try:
                cleaned_value = field_uuid.clean(test_value)
                assert cleaned_value == sample_pkid_uuid_model, f"Failed for UUID value: {test_value}"
            except ValidationError as e:
                pytest.fail(f"UUID validation failed for {test_value}: {e}")

    def test_widget_context_with_problematic_values(self, sample_uuid_model, sample_pkid_uuid_model):
        """Test widget context generation with values that might cause issues."""
        # Test UUID PK widget with various value formats
        uuid_widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        problematic_values = [
            str(sample_uuid_model.id),
            sample_uuid_model.id,
            f"UUID('{sample_uuid_model.id}')",
            sample_uuid_model,
        ]

        for value in problematic_values:
            try:
                context = uuid_widget.get_context("test", value, {})
                assert "widget" in context
            except Exception as e:
                pytest.fail(f"Widget context generation failed for {value}: {e}")

        # Test PKID & UUID widget
        pkid_widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="pkid",
                label_field="name",
            )
        )

        pkid_problematic_values = [
            sample_pkid_uuid_model.pkid,
            str(sample_pkid_uuid_model.pkid),
            sample_pkid_uuid_model,
        ]

        for value in pkid_problematic_values:
            try:
                context = pkid_widget.get_context("test", value, {})
                assert "widget" in context
            except Exception as e:
                pytest.fail(f"PKID widget context generation failed for {value}: {e}")

    def test_serialization_deserialization_issues(self, sample_uuid_model):
        """Test potential serialization/deserialization issues with UUID values."""
        import json

        # Test JSON serialization of UUID values
        uuid_str = str(sample_uuid_model.id)

        # Simulate what might happen during AJAX requests
        serialized_data = json.dumps({"value": uuid_str, "label": sample_uuid_model.name})
        deserialized_data = json.loads(serialized_data)

        # The value should be a string after JSON round-trip
        assert isinstance(deserialized_data["value"], str)
        assert deserialized_data["value"] == uuid_str

        # Test that this value can be used for validation
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="id",
                label_field="name",
            )
        )

        try:
            cleaned_value = field.clean(deserialized_data["value"])
            assert cleaned_value == sample_uuid_model
        except ValidationError as e:
            pytest.fail(f"JSON round-trip validation failed: {e}")


@pytest.mark.django_db
class TestValueFieldFix:
    """Test that value_field configuration works correctly."""

    def test_uuid_pk_with_name_value_field(self):
        """Test that using name as value_field works with UUID PK model."""
        # Create test data
        test_model = ModelWithUUIDPk.objects.create(name="Test Model Name")

        # Create form field with name as value_field
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="name",
                label_field="name",
            )
        )

        try:
            cleaned_value = field.clean("Test Model Name")
            assert cleaned_value == test_model
            print("✓ UUID PK with name value_field works correctly")
        except ValidationError as e:
            pytest.fail(f"Validation failed: {e}")

    def test_pkid_uuid_with_id_value_field(self):
        """Test that using UUID id field as value_field works with PKID & UUID model."""
        # Create test data
        test_model = ModelWithPKIDAndUUIDId.objects.create(name="Test PKID Model")

        # Create form field with UUID id as value_field
        field = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        try:
            cleaned_value = field.clean(test_model.id)
            assert cleaned_value == test_model
            print("✓ PKID & UUID with id value_field works correctly")
        except ValidationError as e:
            pytest.fail(f"Validation failed: {e}")

    def test_to_field_name_is_set_correctly(self):
        """Test that to_field_name is set correctly based on value_field."""
        # Test with name as value_field
        field_name = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-uuid-pk",
                value_field="name",
                label_field="name",
            )
        )

        # Note: Need to trigger the clean method to ensure to_field_name is set
        ModelWithUUIDPk.objects.create(name="Test Name Field")
        field_name.clean("Test Name Field")
        assert field_name.to_field_name == "name"
        print("✓ to_field_name is set correctly for name field")

        # Test with id as value_field
        field_id = TomSelectModelChoiceField(
            config=TomSelectConfig(
                url="autocomplete-pkid-uuid",
                value_field="id",
                label_field="name",
            )
        )

        test_model_pkid = ModelWithPKIDAndUUIDId.objects.create(name="Test ID Field")
        field_id.clean(test_model_pkid.id)
        assert field_id.to_field_name == "id"
        print("✓ to_field_name is set correctly for id field")
