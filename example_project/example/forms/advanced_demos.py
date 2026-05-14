"""Forms for the example project demonstrating TomSelectConfig usage."""


from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_tomselect.app_settings import (
    Const,
    PluginCheckboxOptions,
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
    TomSelectTokenField,
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
        """Initialize the form and set help text."""
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
        """Initialize the form and set help text."""
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
        """Initialize the form, set help texts, and handle dynamic fields."""
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


def _rich_author_base_config_kwargs():
    """Shared TomSelectConfig kwargs for the three Rich Author Multi-Select widgets."""
    return dict(
        url="autocomplete-rich-author",
        value_field="id",
        label_field="name",
        placeholder=_("Search for authors..."),
        highlight=True,
        preload=True,
        minimum_query_length=1,
        css_framework="bootstrap5",
    )


class RichAuthorMultiSelectForm(forms.Form):
    """Three multi-select widgets backed by the same Rich Author autocomplete.

    All three fields hit the same endpoint and receive the same rich payload, but
    each renders a different subset of that data with a different plugin combo:

    - authors_full: every signal at a glance (avatar, count, activity, top
      categories, magazines, bio snippet, status mix, years active). Plugins:
      Remove + Clear + Dropdown Header.
    - authors_slim: minimal card (avatar, name, count, activity, bio snippet).
      Plugins: Remove only.
    - authors_stats: data-viz-forward (avatar, sparkline SVG, expertise, peer
      rank). Plugins: Remove + Checkbox Options.

    All fields are required=False so partial submissions work.

    Item (selected-chip) templates only reference data.name because the multi-
    widget rehydrates selected items as {value, label} only - other keys would
    render as 'undefined' on a bound form.
    """

    authors_full = TomSelectModelMultipleChoiceField(
        required=False,
        config=TomSelectConfig(
            **_rich_author_base_config_kwargs(),
            plugin_remove_button=PluginRemoveButton(title=_("Remove this author")),
            plugin_clear_button=PluginClearButton(title=_("Clear all authors")),
            attrs={
                "render": {
                    "option": """
                        `<div class="author-option">
                            <div class="author-avatar-rich palette-${Number(data.avatar_palette_index)}"
                                 title="${escape(data.name)}">
                                ${escape(data.initials)}
                            </div>
                            <div class="author-body">
                                <div class="author-headline">
                                    <span class="author-name">${escape(data.name)}</span>
                                    <span class="activity-indicator activity-${escape(data.activity_level)}"
                                          title="${escape(data.last_active_display)}"></span>
                                    <span class="count-badge">
                                        <i class="bi bi-journal-text"></i>
                                        ${Number(data.article_count)} articles
                                    </span>
                                    <span class="magazines-pill">
                                        <i class="bi bi-collection"></i>
                                        ${Number(data.magazines_count)} mag
                                    </span>
                                </div>
                                <div class="author-meta">
                                    ${data.top_categories.map(cat => `
                                        <span class="category-chip" title="${escape(cat.name)}">
                                            ${escape(cat.name)}
                                            <span class="category-count">${Number(cat.count)}</span>
                                        </span>
                                    `).join('')}
                                </div>
                                <div class="author-bio">${escape(data.bio_snippet)}</div>
                                <div class="status-mix-bar" title="Status mix">
                                    ${data.status_mix.map(seg => seg.pct > 0 ? `
                                        <span class="status-mix-segment status-mix-segment-${escape(seg.key)}"
                                              style="flex-basis: ${Number(seg.pct)}%"
                                              title="${escape(seg.label)}: ${Number(seg.pct)}%"></span>
                                    ` : '').join('')}
                                </div>
                                <div class="author-footer">
                                    <span class="text-muted small">${escape(data.last_active_display)}</span>
                                    <span class="text-muted small">${Number(data.years_active)}y active</span>
                                </div>
                            </div>
                        </div>`
                    """,
                    "item": """
                        `<div class="selected-author-chip selected-author-chip-full">
                            <span class="author-avatar-rich author-avatar-chip
                                         palette-${Number(data.avatar_palette_index || 0)}">
                                ${escape(
                                    data.initials
                                    || (data.name || '')
                                        .split(' ')
                                        .map(w => w[0] || '')
                                        .join('')
                                        .slice(0, 2)
                                        .toUpperCase()
                                )}
                            </span>
                            <span class="ms-1">${escape(data.name)}</span>
                        </div>`
                    """,
                }
            },
        ),
        help_text=_(
            "Full kit - avatar, article/magazine counts, activity, top categories, bio, "
            "status mix, years active. Plugins: Remove + Clear."
        ),
    )

    authors_slim = TomSelectModelMultipleChoiceField(
        required=False,
        config=TomSelectConfig(
            **_rich_author_base_config_kwargs(),
            plugin_remove_button=PluginRemoveButton(title=_("Remove this author")),
            attrs={
                "render": {
                    "option": """
                        `<div class="author-option author-option-slim">
                            <div class="author-avatar-rich author-avatar-slim
                                        palette-${Number(data.avatar_palette_index)}">
                                ${escape(data.initials)}
                            </div>
                            <div class="author-body">
                                <div class="author-headline">
                                    <span class="author-name">${escape(data.name)}</span>
                                    <span class="count-badge count-badge-slim">${Number(data.article_count)}</span>
                                    <span class="activity-indicator activity-${escape(data.activity_level)}"
                                          title="${escape(data.last_active_display)}"></span>
                                </div>
                                <div class="author-bio author-bio-slim">${escape(data.bio_snippet)}</div>
                            </div>
                        </div>`
                    """,
                    "item": """
                        `<div class="selected-author-chip selected-author-chip-slim">
                            <span class="author-avatar-rich author-avatar-chip
                                         palette-${Number(data.avatar_palette_index || 0)}">
                                ${escape(
                                    data.initials
                                    || (data.name || '')
                                        .split(' ')
                                        .map(w => w[0] || '')
                                        .join('')
                                        .slice(0, 2)
                                        .toUpperCase()
                                )}
                            </span>
                            <span class="ms-1">${escape(data.name)}</span>
                        </div>`
                    """,
                }
            },
        ),
        help_text=_("Slim - avatar, name, count, activity dot, bio snippet. Plugin: Remove only."),
    )

    authors_stats = TomSelectModelMultipleChoiceField(
        required=False,
        config=TomSelectConfig(
            **_rich_author_base_config_kwargs(),
            plugin_remove_button=PluginRemoveButton(title=_("Remove this author")),
            plugin_checkbox_options=PluginCheckboxOptions(),
            attrs={
                "render": {
                    "option": """
                        `<div class="author-option author-option-stats">
                            <div class="author-avatar-rich palette-${Number(data.avatar_palette_index)}">
                                ${escape(data.initials)}
                            </div>
                            <div class="author-body">
                                <div class="author-headline">
                                    <span class="author-name">${escape(data.name)}</span>
                                    <span class="peer-rank-pill" title="Peer rank by article count">
                                        #${Number(data.peer_rank)}
                                    </span>
                                </div>
                                <div class="author-stats-row">
                                    <svg class="sparkline"
                                         viewBox="0 0 60 24"
                                         preserveAspectRatio="none"
                                         aria-hidden="true">
                                        ${data.sparkline_bars.map((h, i) => `
                                            <rect class="sparkline-bar"
                                                  x="${i * 5}"
                                                  y="${24 - (Number(h) * 22 / 100) - 1}"
                                                  width="4"
                                                  height="${Math.max(1, Number(h) * 22 / 100)}"></rect>
                                        `).join('')}
                                    </svg>
                                    <span class="expertise-badge">${escape(data.expertise)}</span>
                                    <span class="count-badge count-badge-stats">
                                        ${Number(data.article_count)} <small>articles</small>
                                    </span>
                                </div>
                            </div>
                        </div>`
                    """,
                    "item": """
                        `<div class="selected-author-chip selected-author-chip-stats">
                            <span class="author-avatar-rich author-avatar-chip
                                         palette-${Number(data.avatar_palette_index || 0)}">
                                ${escape(
                                    data.initials
                                    || (data.name || '')
                                        .split(' ')
                                        .map(w => w[0] || '')
                                        .join('')
                                        .slice(0, 2)
                                        .toUpperCase()
                                )}
                            </span>
                            <span class="ms-1">${escape(data.name)}</span>
                        </div>`
                    """,
                }
            },
        ),
        help_text=_(
            "Stats-forward - avatar, sparkline of articles per month, top expertise, peer rank. "
            "Plugins: Remove + Checkbox Options."
        ),
    )


class MultipleFilterByForm(forms.Form):
    """Demonstrates filter_by with multiple field-based filters.

    This form shows how to filter articles by both magazine AND status,
    combining multiple filter conditions with AND logic.
    """

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            placeholder=_("Select a magazine..."),
            highlight=True,
            preload="focus",
            minimum_query_length=0,
            plugin_clear_button=PluginClearButton(title=_("Clear magazine")),
        ),
        required=False,
        help_text=_("Filter articles by magazine"),
    )

    status = TomSelectChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article-status",
            value_field="value",
            label_field="label",
            placeholder=_("Select a status..."),
            highlight=True,
            preload="focus",
            minimum_query_length=0,
            plugin_clear_button=PluginClearButton(title=_("Clear status")),
        ),
        required=False,
        help_text=_("Filter articles by status"),
    )

    # Articles filtered by BOTH magazine AND status
    articles = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article",
            value_field="id",
            label_field="title",
            # Multiple field filters - filter by magazine AND status
            filter_by=[
                ("magazine", "magazine_id"),  # Filter by selected magazine
                ("status", "status"),  # AND by selected status
            ],
            placeholder=_("Select articles (filtered by magazine and status)..."),
            highlight=True,
            max_items=None,
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Articles"),
                extra_columns={
                    "status": _("Status"),
                    "magazine_name": _("Magazine"),
                },
            ),
            plugin_clear_button=PluginClearButton(title=_("Clear articles")),
            plugin_remove_button=PluginRemoveButton(),
        ),
        required=False,
        help_text=_("Articles are filtered by both the selected magazine AND status above"),
    )


class ConstantFilterByForm(forms.Form):
    """Demonstrates filter_by with constant values.

    This form shows how to always filter articles to a specific value
    (e.g., only show published articles) while also allowing additional
    field-based filters.
    """

    magazine = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-magazine",
            value_field="id",
            label_field="name",
            placeholder=_("Optionally select a magazine..."),
            highlight=True,
            preload="focus",
            minimum_query_length=0,
            plugin_clear_button=PluginClearButton(title=_("Clear magazine")),
        ),
        required=False,
        help_text=_("Optionally filter published articles by magazine"),
    )

    # Articles always filtered to "published" status, optionally by magazine
    published_articles = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-article",
            value_field="id",
            label_field="title",
            # Mixed filters - field-based AND constant
            filter_by=[
                ("magazine", "magazine_id"),  # Optional magazine filter
                Const("published", "status"),  # Always filter to published
            ],
            placeholder=_("Select published articles..."),
            highlight=True,
            max_items=None,
            plugin_dropdown_header=PluginDropdownHeader(
                title=_("Published Articles"),
                extra_columns={
                    "magazine_name": _("Magazine"),
                    "word_count": _("Words"),
                },
            ),
            plugin_clear_button=PluginClearButton(title=_("Clear articles")),
            plugin_remove_button=PluginRemoveButton(),
        ),
        required=False,
        help_text=_("Only published articles are shown. Optionally filter further by magazine above."),
    )


class ArticleTokenSearchForm(forms.Form):
    """Single-field token-style filter for articles.

    Demonstrates :class:`TomSelectTokenField` against
    :class:`ArticleTokenQueryView` (composite autocomplete view) over the
    Author/Category/Magazine/Status operators with free-text title search.
    """

    q = TomSelectTokenField(
        composite_view="autocomplete-article-token",
        required=False,
        allow_free_text=True,
        max_tokens=20,
        widget_kwargs={"placeholder": _(
            "Filter articles… try author:, category:, magazine:, status:, or free text"
        )},
        help_text=_(
            "Operators: author:, category: (multi), magazine:, status: (multi). "
            "Use commas for multi values: status:draft,review. "
            "Quote phrases for free-text title search: \"long form essay\"."
        ),
    )
