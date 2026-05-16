"""Edge cases, bug reproduction, and value_field fix tests for UUID models.

Shared fixtures (``sample_uuid_model``, ``sample_pkid_uuid_model``,
``multiple_uuid_models``) are defined in ``example_project/conftest.py``.
"""

import pytest
from django.core.exceptions import ValidationError

from django_tomselect.app_settings import TomSelectConfig
from django_tomselect.forms import (
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)
from django_tomselect.widgets import TomSelectModelWidget
from example_project.example.models import ModelWithPKIDAndUUIDId, ModelWithUUIDPk


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
        uuid_string_repr = f"{{'id': {sample_uuid_model.id!r}, 'name': {sample_uuid_model.name!r}}}"
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

        pkid_string_repr = f"{{'pkid': {sample_pkid_uuid_model.pkid}, 'name': {sample_pkid_uuid_model.name!r}}}"
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
            f"'{sample_uuid_model.id}'",  # noqa: B907
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
            f"'{sample_pkid_uuid_model.id}'",  # noqa: B907
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
            f"UUID('{sample_uuid_model.id}')",  # noqa: B907
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
