"""Forms for the example project demonstrating TomSelectConfig usage."""

from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_tomselect.app_settings import (
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.forms import (
    TomSelectChoiceField,
    TomSelectModelChoiceField,
    TomSelectModelMultipleChoiceField,
)
from example_project.example.models import Article

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


class MarketSelectionForm(forms.Form):
    """Form for selecting publishing markets in a three-level hierarchy."""

    region = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-region",
            value_field="id",
            label_field="name",
            placeholder="Select region...",
            highlight=True,
            preload="focus",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Publishing Regions",
                extra_columns={
                    "total_markets": "Markets",
                    "aggregated_readers": "Potential Readers (M)",
                    "aggregated_publications": "Active Publications",
                },
            ),
        ),
        required=True,
    )

    country = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-country",
            value_field="id",
            label_field="name",
            filter_by=("region", "parent_id"),
            placeholder="Select country...",
            highlight=True,
            plugin_dropdown_header=PluginDropdownHeader(
                title="Countries",
                extra_columns={
                    "total_local_markets": "Local Markets",
                    "total_reader_base": "Potential Readers (M)",
                    "total_pub_count": "Publications",
                },
            ),
        ),
        required=False,
    )

    local_market = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-local-market",
            value_field="id",
            label_field="name",
            filter_by=("country", "parent_id"),
            placeholder="Select local market...",
            highlight=True,
            plugin_dropdown_header=PluginDropdownHeader(
                title="Local Markets",
                extra_columns={
                    "market_size": "Potential Readers (M)",
                    "active_publications": "Active Publications",
                },
            ),
        ),
        required=False,
    )


class EditionYearForm(forms.Form):
    """Form for selecting an edition year."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["year"].help_text = "This field is backed by the edition_year list in models.py"

    year = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-edition-year",
            value_field="value",
            label_field="label",
            placeholder=_("Select an edition year..."),
            preload="focus",
            highlight=True,
            minimum_query_length=0,
        ),
    )


class WordCountForm(forms.Form):
    """Form for selecting a word count range."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["word_count"].help_text = "This field is backed by the word_count_range tuple in models.py"

    word_count = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-page-count",
            value_field="value",
            label_field="label",
            placeholder=_("Select a word count range..."),
            preload="focus",
            highlight=True,
            minimum_query_length=0,
            plugin_remove_button=PluginRemoveButton(),
        ),
    )


class DynamicArticleForm(forms.ModelForm):
    """Form for creating and editing articles with dynamic fields and dependencies."""

    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    word_count = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}), min_value=0)

    status = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
            placeholder=_("Select an article status..."),
            preload="focus",
            highlight=True,
            minimum_query_length=0,
        ),
    )

    priority = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article-priority",
            value_field="value",
            label_field="label",
            placeholder=_("Select an article priority..."),
            preload="focus",
            highlight=True,
            minimum_query_length=0,
        ),
    )

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            show_list=True,
            show_create=True,
            show_update=True,
            show_delete=True,
            value_field="id",
            label_field="name",
            placeholder=_("Select a magazine..."),
            preload="focus",
            highlight=True,
            minimum_query_length=0,
            plugin_dropdown_footer=PluginDropdownFooter(),
        ),
    )

    primary_author = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            show_list=True,
            show_create=True,
            show_update=True,
            value_field="id",
            label_field="name",
            placeholder=_("Select primary author..."),
            highlight=True,
            plugin_dropdown_header=author_header,
            plugin_dropdown_footer=PluginDropdownFooter(),
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title=_("Clear primary author")),
        ),
    )

    contributing_authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            exclude_by=("primary_author", "id"),  # Exclude primary author
            placeholder=_("Select contributing authors..."),
            highlight=True,
            max_items=None,
            plugin_dropdown_header=author_header,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title=_("Clear all contributing authors")),
            plugin_remove_button=PluginRemoveButton(),
        ),
    )

    main_category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            show_list=True,
            show_detail=True,
            show_delete=True,
            show_create=True,
            show_update=True,
            value_field="id",
            label_field="name",
            placeholder=_("Select main category..."),
            highlight=True,
            plugin_dropdown_header=category_header,
            plugin_dropdown_footer=PluginDropdownFooter(),
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title=_("Clear main category")),
        ),
    )

    subcategories = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="full_path",
            show_update=True,
            show_delete=True,
            filter_by=("main_category", "parent_id"),
            placeholder=_("Select subcategories..."),
            highlight=True,
            max_items=None,
            plugin_dropdown_header=category_header,
            plugin_dropdown_input=PluginDropdownInput(),
            plugin_clear_button=PluginClearButton(title=_("Clear all subcategories")),
            plugin_remove_button=PluginRemoveButton(),
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set help text for fields
        self.fields["status"].help_text = "This field is backed by ArticleStatus (models.TextChoices) in models.py"
        self.fields[
            "priority"
        ].help_text = "This field is backed by ArticlePriority (models.IntegerChoices) in models.py"
        self.fields["magazine"].help_text = "This field is backed by the Magazine model"
        if "edition" in self.fields.keys():
            self.fields[
                "edition"
            ].help_text = (
                "This field is backed by the Edition model, and is filtered by the currently selected magazine"
            )
        self.fields["primary_author"].help_text = "This field is backed by the Author model"
        self.fields[
            "contributing_authors"
        ].help_text = "This field is backed by the Author model, and excludes the current selection in primary_author"
        self.fields["main_category"].help_text = "This field is backed by the Category model"
        self.fields["subcategories"].help_text = (
            "This field is backed by the Category model, and is filtered by the main_category, but it only allows "
            "selections when the main_category is a 'parent' category (e.g.: has no parent itself)"
        )

        # Only try to set initial values if we have an existing instance with an id
        if self.instance and self.instance.pk:
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

            # Set initial values for authors if they exist
            if self.instance.authors.exists():
                authors = self.instance.authors.all()
                self.fields["primary_author"].initial = authors[0].pk if authors else None
                if len(authors) > 1:
                    self.fields["contributing_authors"].initial = [author.pk for author in authors[1:]]

            # Dynamically add edition field if magazine exists
            if self.instance.magazine:
                self.fields["edition"] = TomSelectModelChoiceField(
                    config=TomSelectConfig(
                        url="autocomplete-edition",
                        show_list=True,
                        show_create=True,
                        show_update=True,
                        show_delete=True,
                        value_field="id",
                        label_field="name",
                        filter_by=("magazine", "magazine_id"),
                        placeholder=_("Select an edition..."),
                        highlight=True,
                        plugin_dropdown_footer=PluginDropdownFooter(),
                    ),
                    initial=(
                        self.instance.edition.pk
                        if hasattr(self.instance, "edition") and hasattr(self.instance.edition, "pk")
                        else None
                    ),
                )

    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()

        # Validate author selections
        primary_author = cleaned_data.get("primary_author")
        contributing_authors = cleaned_data.get("contributing_authors", [])

        if primary_author and primary_author in contributing_authors:
            self.add_error(
                "contributing_authors",
                _("Primary author cannot also be a contributing author"),
            )

        # Validate category hierarchy
        main_category = cleaned_data.get("main_category")
        subcategories = cleaned_data.get("subcategories", [])

        if main_category and subcategories:
            invalid_subcats = [cat for cat in subcategories if cat.parent_id != main_category.id]
            if invalid_subcats:
                self.add_error(
                    "subcategories",
                    _("Selected subcategories must belong to the main category"),
                )

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
            "priority",
            "magazine",
            "primary_author",
            "contributing_authors",
            "main_category",
            "subcategories",
            "word_count",
        ]


class ArticleBulkActionForm(forms.Form):
    """Form for bulk article management."""

    date_range = forms.ChoiceField(
        required=False,
        choices=[
            ("all", _("All Time")),
            ("today", _("Today")),
            ("week", _("Past Week")),
            ("month", _("Past Month")),
            ("quarter", _("Past Quarter")),
            ("year", _("Past Year")),
        ],
        initial="all",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    main_category = TomSelectModelChoiceField(
        required=False,
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            placeholder=_("Filter by category..."),
            highlight=True,
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Categories"),
                extra_columns={
                    "total_articles": _("Total Articles"),
                },
            ),
        ),
    )

    status = TomSelectChoiceField(
        required=False,
        config=TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
            placeholder=_("Filter by status..."),
            highlight=True,
            preload="focus",
        ),
    )

    def __init__(self, *args, **kwargs):
        """Initialize form and update selected_articles config with current filters."""
        super().__init__(*args, **kwargs)

        # Get initial filter values from kwargs or form data
        data = kwargs.get("data") or kwargs.get("initial", {})
        date_range = data.get("date_range", "all")
        main_category = data.get("main_category", "")
        status = data.get("status", "")

        # Build the autocomplete_params string
        params = []
        if date_range and date_range != "all":
            params.append(f"date_range={date_range}")
        if main_category:
            params.append(f"main_category={main_category}")
        if status:
            params.append(f"status={status}")

        autocomplete_params = "&".join(params)

        # Create the selected_articles field with dynamic filtering
        self.fields["selected_articles"] = TomSelectModelMultipleChoiceField(
            required=False,
            config=TomSelectConfig(
                url="autocomplete-article",
                value_field="id",
                label_field="title",
                placeholder=_("Select articles..."),
                highlight=True,
                max_items=None,
                plugin_dropdown_header=PluginDropdownHeader(
                    title=_("Articles"),
                    extra_columns={
                        "status": _("Status"),
                        "category": _("Category"),
                    },
                ),
                # Pass filter parameters via attrs
                attrs={
                    "autocomplete_params": autocomplete_params,
                    "data-depends-on": "date_range,main_category,status",  # Fields this depends on
                    "class": "tomselect-with-filters",  # Class for easy JS targeting
                },
            ),
        )

    action = forms.ChoiceField(
        choices=[
            ("", _("Select action...")),
            ("publish", _("Publish")),
            ("archive", _("Archive")),
            ("change_category", _("Change Category")),
            ("assign_author", _("Assign Author")),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    target_category = TomSelectModelChoiceField(
        required=False,
        config=TomSelectConfig(
            url="autocomplete-category",
            value_field="id",
            label_field="name",
            placeholder=_("Select target category..."),
        ),
    )

    target_author = TomSelectModelChoiceField(
        required=False,
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            placeholder=_("Select target author..."),
        ),
    )

    def clean(self):
        """Validate that the necessary fields are provided based on the selected action."""
        cleaned_data = super().clean()
        action = cleaned_data.get("action")
        selected_articles = cleaned_data.get("selected_articles")

        if action and not selected_articles:
            raise ValidationError(_("Please select at least one article"))

        if action == "change_category" and not cleaned_data.get("target_category"):
            raise ValidationError(_("Please select a target category"))

        if action == "assign_author" and not cleaned_data.get("target_author"):
            raise ValidationError(_("Please select a target author"))

        return cleaned_data


class RichArticleSelectForm(forms.Form):
    """Form demonstrating rich article selection interface."""

    article = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-rich-article",
            value_field="id",
            label_field="title",
            placeholder=_("Search articles..."),
            highlight=True,
            preload=True,
            minimum_query_length=1,
            css_framework="bootstrap5",
            attrs={
                "render": {
                    "option": """
                        `<div class="article-option">
                            <div class="article-avatar">
                                ${data.authors.map(author => `
                                    <div class="author-avatar" title="${escape(author.name)}">
                                        ${escape(author.initials)}
                                    </div>
                                `).join('')}
                            </div>
                            <div class="article-info">
                                <div class="article-title">
                                    ${escape(data.title)}
                                </div>
                                <div class="article-meta">
                                    <span class="status-badge status-${data.status.toLowerCase()}">
                                        ${escape(data.status_display)}
                                    </span>
                                    <span class="freshness-indicator freshness-${data.freshness}"></span>
                                    ${data.categories.map(cat => `
                                        <span class="category-tag">
                                            ${escape(cat.name)}
                                        </span>
                                    `).join('')}
                                    <span>
                                        <i class="bi bi-card-text fs-5 meta-icon"></i>
                                        ${escape(data.word_count)} words
                                    </span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-value" style="width: ${data.completion_score}%"></div>
                                </div>
                            </div>
                        </div>`
                    """,
                    "item": """
                        `<div class="selected-article d-flex align-items-center gap-2">
                            <span class="freshness-indicator freshness-${data.freshness}"></span>
                            <span class="status-badge status-${data.status.toLowerCase()}">
                                ${escape(data.status_display)}
                            </span>
                            ${escape(data.title)}
                            <small class="text-muted ms-2">
                                (${data.authors.map(a => escape(a.name)).join(', ')})
                            </small>
                        </div>`
                    """,
                }
            },
        ),
        help_text=_("Search for articles by title, author, or category"),
    )
