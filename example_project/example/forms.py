"""Forms for the example project demonstrating TomSelectConfig usage."""

from django import forms
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from django_tomselect.configs import (
    GeneralConfig,
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.forms import TomSelectField, TomSelectMultipleField

from .models import Article, Author, Category, Magazine, ModelFormTestModel

# Define reusable configurations
SINGLE_SELECT_CONFIG = TomSelectConfig(
    url="autocomplete-edition",
    listview_url="edition-list",
    create_url="create",
    update_url="update",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
        placeholder="Select a value",
        minimum_query_length=2,
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_clear_button=PluginClearButton(title="Clear Selection", class_name="clear-button"),
)

SINGLE_SELECT_TABULAR_CONFIG = TomSelectConfig(
    url="autocomplete-edition",
    listview_url="edition-list",
    create_url="create",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
    ),
    plugin_dropdown_header=PluginDropdownHeader(
        show_value_field=False,
        label_field_label="Edition",
        value_field_label="Value",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        },
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_dropdown_footer=PluginDropdownFooter(),
)

MULTIPLE_SELECT_CONFIG = TomSelectConfig(
    url="autocomplete-edition",
    listview_url="edition-list",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
        max_items=None,  # Allow unlimited selections
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_clear_button=PluginClearButton(),
    plugin_remove_button=PluginRemoveButton(),
)

MULTIPLE_SELECT_TABULAR_CONFIG = TomSelectConfig(
    url="autocomplete-edition",
    create_url="create",
    value_field="id",
    label_field="name",
    general_config=GeneralConfig(
        highlight=True,
        open_on_focus=True,
        preload="focus",
        max_items=None,
        placeholder="Select multiple values",
    ),
    plugin_dropdown_header=PluginDropdownHeader(
        show_value_field=False,
        label_field_label="Edition",
        value_field_label="Value",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        },
    ),
    plugin_dropdown_input=PluginDropdownInput(),
    plugin_clear_button=PluginClearButton(),
    plugin_remove_button=PluginRemoveButton(),
)


class ExampleForm(forms.Form):
    """Uses TomSelectField and TomSelectMultipleField fields with TomSelectConfig."""

    tomselect = TomSelectField(
        config=SINGLE_SELECT_CONFIG,
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
            "id": "tomselect-custom-id",
        },
        label="Tomselect Single",
        help_text=(
            "TomSelectField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )

    tomselect_tabular = TomSelectField(
        config=SINGLE_SELECT_TABULAR_CONFIG,
        attrs={"class": "form-control mb-3"},
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    tomselect_multiple = TomSelectMultipleField(
        config=MULTIPLE_SELECT_CONFIG,
        attrs={"class": "form-control mb-3"},
        label="Tomselect Multiple",
        help_text=("TomSelectField with multiple select, dropdown input, dropdown footer, " "clear, and highlighting"),
    )

    tomselect_tabular_multiple_with_value_field = TomSelectMultipleField(
        config=MULTIPLE_SELECT_TABULAR_CONFIG,
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectField with multiple select, placeholder text, dropdown input, " "remove, clear, and highlighting"
        ),
    )


class FormHTMX(ExampleForm):
    """Same as Form but with HTMX enabled."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enable HTMX for all fields
        for _, field in self.fields.items():
            if hasattr(field, "config"):
                field.config.use_htmx = True


class DependentForm(forms.Form):
    """Form with dependent fields demonstrating filter_by functionality."""

    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
        ),
    )

    edition = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-edition",
            listview_url="edition-list",
            create_url="create",
            value_field="id",
            label_field="name",
            filter_by=("magazine", "magazine_id"),
        ),
        attrs={"class": "form-control mb-3"},
        required=False,
    )


class ModelForm(forms.ModelForm):
    """ModelForm using TomSelectField and TomSelectMultipleField with TomSelectConfig."""

    tomselect = TomSelectField(
        config=SINGLE_SELECT_CONFIG,
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select a value",
        },
        label="Tomselect Single",
        help_text=(
            "TomSelectField with single select, placeholder text, checkboxes, dropdown "
            "input, dropdown footer, remove, clear, edit, and highlighting"
        ),
    )

    tomselect_tabular = TomSelectField(
        config=SINGLE_SELECT_TABULAR_CONFIG,
        attrs={"class": "form-control mb-3"},
        label="Tomselect Single Tabular",
        help_text=(
            "TomSelectField with single select, placeholder text, dropdown header, "
            "dropdown input, dropdown footer, remove, clear, and highlighting"
        ),
    )

    tomselect_multiple = TomSelectMultipleField(
        config=MULTIPLE_SELECT_CONFIG,
        attrs={"class": "form-control mb-3"},
        label="Tomselect Multiple",
        help_text=("TomSelectField with multiple select, dropdown input, dropdown footer, " "clear, and highlighting"),
    )

    tomselect_tabular_multiple_with_value_field = TomSelectMultipleField(
        config=MULTIPLE_SELECT_TABULAR_CONFIG,
        attrs={
            "class": "form-control mb-3",
            "placeholder": "Select multiple values",
        },
        label="Tomselect Multiple Tabular",
        help_text=(
            "TomSelectField with multiple select, placeholder text, dropdown input, " "remove, clear, and highlighting"
        ),
    )

    class Meta:
        """Meta options for the model form."""

        model = ModelFormTestModel
        fields = "__all__"


author_header = PluginDropdownHeader(
    title=_("Author Selection"),
    show_value_field=False,
    extra_columns={
        "article_count": _("Articles"),
    },
)

category_header = PluginDropdownHeader(
    title=_("Category Selection"),
    show_value_field=False,
    extra_columns={
        "parent_name": _("Parent"),
        "direct_articles": _("Direct Articles"),
        "total_articles": _("Total Articles"),
    },
)


class DynamicArticleForm(forms.ModelForm):
    """Form for creating and editing articles with dynamic fields and dependencies."""

    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    status = forms.ChoiceField(choices=Article.Status.choices, widget=forms.Select(attrs={"class": "form-control"}))

    magazine = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            general_config=GeneralConfig(
                placeholder=_("Select a magazine..."),
                preload="focus",
                highlight=True,
                minimum_query_length=0,
            ),
        ),
    )

    primary_author = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            general_config=GeneralConfig(
                placeholder=_("Select primary author..."),
                highlight=True,
            ),
            plugin_dropdown_header=author_header,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title=_("Clear primary author")),
        ),
    )

    contributing_authors = TomSelectMultipleField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),  # Exclude primary author
            general_config=GeneralConfig(
                placeholder=_("Select contributing authors..."),
                highlight=True,
                max_items=None,
            ),
            plugin_dropdown_header=author_header,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title=_("Clear all contributing authors")),
            plugin_remove_button=PluginRemoveButton(),
        ),
    )

    main_category = TomSelectField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            general_config=GeneralConfig(
                placeholder=_("Select main category..."),
                highlight=True,
            ),
            plugin_dropdown_header=category_header,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title=_("Clear main category")),
        ),
    )

    subcategories = TomSelectMultipleField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="full_path",
            filter_by=("main_category", "parent_id"),
            general_config=GeneralConfig(
                placeholder=_("Select subcategories..."),
                highlight=True,
                max_items=None,
            ),
            plugin_dropdown_header=category_header,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title=_("Clear all subcategories")),
            plugin_remove_button=PluginRemoveButton(),
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial values for categories if instance exists
        if self.instance.categories.exists():
            categories = self.instance.categories.all()
            # Find main category (parent is None) and subcategories
            main_category = next((cat for cat in categories if cat.parent is None), None)
            subcategories = [cat for cat in categories if cat.parent is not None]

            if main_category:
                self.fields["main_category"].initial = main_category.pk
            if subcategories:
                self.fields["subcategories"].initial = [cat.pk for cat in subcategories]

        # Set initial values for authors
        if self.instance.authors.exists():
            authors = self.instance.authors.all()
            self.fields["primary_author"].initial = authors[0].pk if authors else None
            if len(authors) > 1:
                self.fields["contributing_authors"].initial = [author.pk for author in authors[1:]]

        # Dynamically add edition field if magazine exists
        if self.instance.magazine:
            self.fields["edition"] = TomSelectField(
                config=TomSelectConfig(
                    url="autocomplete-edition",
                    listview_url="edition-list",
                    value_field="id",
                    label_field="name",
                    filter_by=("magazine", "magazine_id"),
                    general_config=GeneralConfig(
                        placeholder=_("Select an edition..."),
                        highlight=True,
                    ),
                ),
                initial=self.instance.edition.pk if hasattr(self.instance, "edition") else None,
            )

    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()

        # Validate author selections
        primary_author = cleaned_data.get("primary_author")
        contributing_authors = cleaned_data.get("contributing_authors", [])

        if primary_author and primary_author in contributing_authors:
            self.add_error("contributing_authors", _("Primary author cannot also be a contributing author"))

        # Validate category hierarchy
        main_category = cleaned_data.get("main_category")
        subcategories = cleaned_data.get("subcategories", [])

        if main_category and subcategories:
            invalid_subcats = [cat for cat in subcategories if cat.parent_id != main_category.id]
            if invalid_subcats:
                self.add_error("subcategories", _("Selected subcategories must belong to the main category"))

        return cleaned_data

    def save(self, commit=True):
        """Save the form, handling the M2M relationships properly."""
        article = super().save(commit=False)

        if commit:
            article.save()

            # Handle authors
            authors = []
            if self.cleaned_data.get("primary_author"):
                authors.append(self.cleaned_data["primary_author"])
            if self.cleaned_data.get("contributing_authors"):
                authors.extend(self.cleaned_data["contributing_authors"])

            # Set the authors
            article.authors.set(authors)

            # Handle categories
            categories = []
            if self.cleaned_data.get("main_category"):
                categories.append(self.cleaned_data["main_category"])
            if self.cleaned_data.get("subcategories"):
                categories.extend(self.cleaned_data["subcategories"])

            # Set the categories
            article.categories.set(categories)

            # Handle edition if it exists in cleaned_data
            if "edition" in self.cleaned_data and self.cleaned_data["edition"]:
                # Need to update this through a direct database update
                #   since edition is not a direct field on the Article model
                Article.objects.filter(pk=article.pk).update(edition=self.cleaned_data["edition"])

        return article

    class Meta:
        """Meta options for the model form."""

        model = Article
        fields = [
            "title",
            "status",
            "magazine",
            "primary_author",
            "contributing_authors",
            "main_category",
            "subcategories",
        ]
