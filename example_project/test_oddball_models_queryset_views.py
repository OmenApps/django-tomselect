"""Tests for queryset validation and autocomplete views with UUID models.

Shared fixtures (``sample_uuid_model``, ``sample_pkid_uuid_model``,
``multiple_uuid_models``) are defined in ``example_project/conftest.py``.
"""

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
from django_tomselect.widgets import TomSelectModelWidget
from example_project.example.models import ModelWithPKIDAndUUIDId, ModelWithUUIDPk


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
