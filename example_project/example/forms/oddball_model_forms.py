"""Forms for the example project testing oddball models."""

from django import forms

from django_tomselect.app_settings import TomSelectConfig
from django_tomselect.forms import (
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)


class UUIDModelForm(forms.Form):
    """Example form using ModelWithUUIDPk."""

    # Using UUID primary key as value_field
    uuid_model_by_id = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-uuid-pk",
            value_field="id",
            label_field="name",
            placeholder="Select a UUID model by ID...",
        ),
        label="UUID Model (by ID)",
        required=False,
    )

    # Using name field as value_field
    uuid_model_by_name = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-uuid-pk",
            value_field="name",
            label_field="name",
            placeholder="Select a UUID model by name...",
        ),
        label="UUID Model (by Name)",
        required=False,
    )

    # Multiple selection with UUID primary key
    multiple_uuid_models = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-uuid-pk",
            value_field="id",
            label_field="name",
            placeholder="Select multiple UUID models...",
            max_items=None,
        ),
        label="Multiple UUID Models",
        required=False,
    )


class PKIDUUIDModelForm(forms.Form):
    """Example form using ModelWithPKIDAndUUIDId."""

    # Using pkid (AutoField primary key) as value_field
    pkid_model_by_pkid = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="pkid",
            label_field="name",
            placeholder="Select by PKID...",
        ),
        label="PKID Model (by PKID)",
        required=False,
    )

    # Using id (UUID field, not primary key) as value_field
    pkid_model_by_uuid = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="id",
            label_field="name",
            placeholder="Select by UUID ID...",
        ),
        label="PKID Model (by UUID)",
        required=False,
    )

    # Multiple selection with pkid
    multiple_pkid_models = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="pkid",
            label_field="name",
            placeholder="Select multiple by PKID...",
        ),
        label="Multiple PKID Models",
        required=False,
    )

    # Multiple selection with UUID id field
    multiple_uuid_id_models = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-pkid-uuid",
            value_field="id",
            label_field="name",
            placeholder="Select multiple by UUID ID...",
        ),
        label="Multiple Models (by UUID ID)",
        required=False,
    )
