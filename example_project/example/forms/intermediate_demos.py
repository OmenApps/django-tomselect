"""Forms for the example project demonstrating TomSelectConfig usage."""

import logging

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_tomselect.app_settings import (
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.forms import (
    TomSelectChoiceField,
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
    TomSelectMultipleChoiceField,
)
from example_project.example.models import PublicationTag

logger = logging.getLogger(__name__)


category_header = PluginDropdownHeader(
    title=_("Category Selection"),
    show_value_field=False,
    extra_columns={
        "parent_name": _("Parent"),
        "direct_articles": _("Direct Articles"),
        "total_articles": _("Total Articles"),
    },
)

author_header = PluginDropdownHeader(
    title=_("Author Selection"),
    show_value_field=False,
    extra_columns={
        "article_count": _("Articles"),
    },
)


class FilterByMagazineForm(forms.Form):
    """Form with dependent fields demonstrating filter_by functionality."""

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
        ),
    )

    edition = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            show_list=True,
            show_create=True,
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),
            css_framework="bootstrap5",
            plugin_dropdown_footer=PluginDropdownFooter(),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )


class FilterByCategoryForm(forms.Form):
    """Form with dependent fields demonstrating filter_by functionality."""

    main_category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
            plugin_dropdown_header=category_header,
        ),
    )

    subcategories = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="full_path",
            filter_by=("main_category", "parent_id"),
            css_framework="bootstrap5",
            placeholder=_("Select subcategories..."),
            highlight=True,
            max_items=None,
            plugin_remove_button=PluginRemoveButton(),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )


class ExcludeByPrimaryAuthorForm(forms.Form):
    """Form with dependent fields demonstrating exclude_by functionality."""

    primary_author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            css_framework="bootstrap5",
        ),
    )

    contributing_authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),
            css_framework="bootstrap5",
            placeholder=_("Select contributing authors..."),
            highlight=True,
            max_items=None,
            plugin_remove_button=PluginRemoveButton(),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )


class DynamicTagField(TomSelectMultipleChoiceField):
    """A custom field that allows new values to be created on the fly."""

    def clean(self, value):
        """Override to allow values that aren't in the autocomplete results yet."""
        if not value:
            if self.required:
                raise ValidationError(self.error_messages["required"], code="required")
            return []

        # Convert all values to strings
        str_values = [str(v) for v in value]
        return str_values


class TaggingForm(forms.Form):
    """Form for managing publication tags with validation."""

    tags = DynamicTagField(
        config=TomSelectConfig(
            url="autocomplete-publication-tag",
            value_field="value",
            label_field="label",
            placeholder="Enter tags...",
            highlight=True,
            create=True,
            minimum_query_length=2,
            max_items=10,
            plugin_dropdown_header=PluginDropdownHeader(
                title="Publication Tags",
                extra_columns={"usage_count": "Usage Count", "created_at": "Created"},
            ),
            plugin_remove_button=PluginRemoveButton(title="Remove tag", label="×", class_name="remove-tag"),
        ),
        help_text=(
            "Enter or select tags. Tags must be 2-50 characters long, "
            "contain only letters, numbers, hyphens, and underscores, "
            "and start/end with letters or numbers."
        ),
    )

    def clean_tags(self):
        """Validate tags and create/update them in the database."""
        tag_names = self.cleaned_data.get("tags", [])

        if len(tag_names) < 1:
            raise ValidationError("Please add at least one tag")

        if len(tag_names) > 10:
            raise ValidationError("Maximum 10 tags allowed")

        # Check for duplicates (case-insensitive)
        lower_names = [name.lower() for name in tag_names]
        if len(lower_names) != len(set(lower_names)):
            raise ValidationError("Duplicate tags are not allowed")

        # Process each tag
        tags = []
        for name in tag_names:
            # Clean the tag name
            name = name.lower().strip()

            # Validate the tag format
            if len(name) < 2:
                raise ValidationError(f"Tag '{name}' is too short")

            if not all(c.isalnum() or c in "-_" for c in name):
                raise ValidationError(f"Tag '{name}' contains invalid characters")

            if "--" in name or "__" in name:
                raise ValidationError(f"Tag '{name}' contains consecutive special characters")

            if not name[0].isalnum() or not name[-1].isalnum():
                raise ValidationError(f"Tag '{name}' must start and end with a letter or number")

            # Try to get existing tag or create new one
            tag, _ = PublicationTag.objects.get_or_create(
                name=name,
                defaults={"is_approved": True},
            )
            tags.append(tag)

        return tags


class RangePreviewForm(forms.Form):
    """Form demonstrating dynamic range selection with live preview."""

    word_count = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-page-count-range",
            value_field="value",
            label_field="label",
            css_framework="bootstrap5",
            placeholder="Select a word count range...",
            preload="focus",
            highlight=True,
            minimum_query_length=0,
        ),
        help_text="Select a word count range to see distribution visualization",
    )


class EmbargoForm(forms.Form):
    """Form for selecting embargo regions and timeframes."""

    region = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-embargo-region",
            value_field="id",
            label_field="name",
            placeholder="Select region...",
            highlight=True,
            preload="focus",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Publishing Regions",
                extra_columns={
                    "market_tier": "Market Tier",
                    "typical_embargo_days": "Typical Days",
                },
            ),
        )
    )

    timeframe = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-embargo-timeframe",
            value_field="value",
            label_field="label",
            placeholder="Select timeframe...",
            highlight=True,
        )
    )


class WeightedAuthorSearchForm(forms.Form):
    """Form demonstrating weighted author search results."""

    author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-weighted-author",
            value_field="id",
            label_field="name",
            placeholder=_("Search for authors..."),
            highlight=True,
            minimum_query_length=1,
            preload=True,
            css_framework="bootstrap5",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Author Search Results"),
                show_value_field=False,
                label_field_label=_("Author"),
                value_field_label=_("ID"),
                extra_columns={
                    "relevance_score": _("Relevance"),
                    "article_count": _("Articles"),
                    "last_active": _("Last Active"),
                },
            ),
        ),
        help_text=_("Results are ordered by name match, article count, and recent activity"),
    )
