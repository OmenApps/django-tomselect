"""URL Configuration."""

from django.urls import path

from example_project.example.autocompletes import (
    ArticleAutocompleteView,
    ArticlePriorityAutocompleteView,
    ArticleStatusAutocompleteView,
    AuthorAutocompleteView,
    CategoryAutocompleteView,
    CountryAutocompleteView,
    EditionAutocompleteView,
    EditionYearAutocompleteView,
    EmbargoRegionAutocompleteView,
    EmbargoTimeframeAutocompleteView,
    LocalMarketAutocompleteView,
    MagazineAutocompleteView,
    PublicationTagAutocompleteView,
    RegionAutocompleteView,
    RichArticleAutocompleteView,
    WeightedAuthorAutocompleteView,
    WordCountAutocompleteView,
    WordCountRangeAutocompleteView,
)
from example_project.example.views import (
    article_archive_view,
    article_bulk_action_view,
    article_cancel_view,
    article_create_view,
    article_filtered_table,
    article_list_view,
    article_publish_view,
    article_update_view,
    author_create_view,
    author_delete_view,
    author_list_view,
    author_update_view,
    bootstrap4_demo,
    bootstrap5_demo,
    category_create_view,
    category_delete_view,
    category_list_view,
    category_update_view,
    default_demo,
    edition_create_view,
    edition_delete_view,
    edition_list_view,
    edition_update_view,
    embargo_management_view,
    exclude_by_primary_author_demo,
    filter_by_category_demo,
    filter_by_magazine_demo,
    formset_demo,
    htmx_form_fragment_view,
    htmx_view,
    index_view,
    magazine_create_view,
    magazine_delete_view,
    magazine_list_view,
    magazine_update_view,
    market_selection_view,
    model_formset_demo,
    range_preview_demo,
    rich_article_select_demo,
    tagging_view,
    update_range_preview,
    weighted_author_search_demo,
)

urlpatterns = [
    path("", index_view, name="index"),
    # Basic Examples
    path("demo-default/", default_demo, name="demo-default"),
    path("demo-bs4/", bootstrap4_demo, name="demo-bs4"),
    path("demo-bs5/", bootstrap5_demo, name="demo-bs5"),
    path("demo-htmx/", htmx_view, name="demo-htmx"),
    path(
        "demo-htmx-form-fragment/",
        htmx_form_fragment_view,
        name="demo-htmx-form-fragment",
    ),
    path("demo-formset/", formset_demo, name="demo-formset"),
    path("demo-model-formset/", model_formset_demo, name="demo-model-formset"),
    # Intermediate Examples
    path("filter-by-magazine/", filter_by_magazine_demo, name="filter-by-magazine"),
    path("filter-by-category/", filter_by_category_demo, name="filter-by-category"),
    path(
        "exclude-by-primary-author/",
        exclude_by_primary_author_demo,
        name="exclude-by-primary-author",
    ),
    path("tagging/", tagging_view, name="tagging"),
    path("range-preview/", range_preview_demo, name="range-preview"),
    path("update-range-preview/", update_range_preview, name="update-range-preview"),
    path("custom-content/", embargo_management_view, name="custom-content"),
    path(
        "weighted-author-search/",
        weighted_author_search_demo,
        name="weighted-author-search",
    ),
    # Advanced Examples
    path("three-level-filter-by/", market_selection_view, name="three-level-filter-by"),
    path("article-bulk-action/", article_bulk_action_view, name="article-bulk-action"),
    path("article-filtered-table/", article_filtered_table, name="article-filtered-table"),
    path("rich-article-select/", rich_article_select_demo, name="rich-article-select"),
    path("articles/<int:page>/", article_list_view, name="article-list"),
    path("articles/", article_list_view, name="article-list"),
    path("article/create/", article_create_view, name="article-create"),
    path("article/<int:pk>/update/", article_update_view, name="article-update"),
    path("article/<int:pk>/publish/", article_publish_view, name="article-publish"),
    path("article/<int:pk>/archive/", article_archive_view, name="article-archive"),
    path("article/<int:pk>/cancel/", article_cancel_view, name="article-cancel"),
    # Crud
    path("categories/<int:page>/", category_list_view, name="category-list"),
    path("categories/", category_list_view, name="category-list"),
    path("category/create/", category_create_view, name="category-create"),
    path("category/<int:pk>/update/", category_update_view, name="category-update"),
    path("category/<int:pk>/delete/", category_delete_view, name="category-delete"),
    path("magazines/<int:page>/", magazine_list_view, name="magazine-list"),
    path("magazines/", magazine_list_view, name="magazine-list"),
    path("magazine/create/", magazine_create_view, name="magazine-create"),
    path("magazine/<int:pk>/update/", magazine_update_view, name="magazine-update"),
    path("magazine/<int:pk>/delete/", magazine_delete_view, name="magazine-delete"),
    path("authors/<int:page>/", author_list_view, name="author-list"),
    path("authors/", author_list_view, name="author-list"),
    path("author/create/", author_create_view, name="author-create"),
    path("author/<int:pk>/update/", author_update_view, name="author-update"),
    path("author/<int:pk>/delete/", author_delete_view, name="author-delete"),
    path("editions/<int:page>/", edition_list_view, name="edition-list"),
    path("editions/", edition_list_view, name="edition-list"),
    path("edition/create/", edition_create_view, name="edition-create"),
    path("edition/<int:pk>/update/", edition_update_view, name="edition-update"),
    path("edition/<int:pk>/delete/", edition_delete_view, name="edition-delete"),
    # Autocomplete Views
    path(
        "autocomplete/edition/",
        EditionAutocompleteView.as_view(),
        name="autocomplete-edition",
    ),
    path(
        "autocomplete/magazine/",
        MagazineAutocompleteView.as_view(),
        name="autocomplete-magazine",
    ),
    path(
        "autocomplete/author/",
        AuthorAutocompleteView.as_view(),
        name="autocomplete-author",
    ),
    path(
        "autocomplete/category/",
        CategoryAutocompleteView.as_view(),
        name="autocomplete-category",
    ),
    path(
        "autocomplete/country/",
        CountryAutocompleteView.as_view(),
        name="autocomplete-country",
    ),
    path(
        "autocomplete/region/",
        RegionAutocompleteView.as_view(),
        name="autocomplete-region",
    ),
    path(
        "autocomplete/local-market/",
        LocalMarketAutocompleteView.as_view(),
        name="autocomplete-local-market",
    ),
    path(
        "autocomplete/edition-year/",
        EditionYearAutocompleteView.as_view(),
        name="autocomplete-edition-year",
    ),
    path(
        "autocomplete/publication-tag/",
        PublicationTagAutocompleteView.as_view(),
        name="autocomplete-publication-tag",
    ),
    path(
        "autocomplete/page-count/",
        WordCountAutocompleteView.as_view(),
        name="autocomplete-page-count",
    ),
    path(
        "autocomplete/page-count-range/",
        WordCountRangeAutocompleteView.as_view(),
        name="autocomplete-page-count-range",
    ),
    path(
        "autocomplete/embargo-region/",
        EmbargoRegionAutocompleteView.as_view(),
        name="autocomplete-embargo-region",
    ),
    path(
        "autocomplete/embargo-timeframe/",
        EmbargoTimeframeAutocompleteView.as_view(),
        name="autocomplete-embargo-timeframe",
    ),
    path(
        "autocomplete/article-status/",
        ArticleStatusAutocompleteView.as_view(),
        name="autocomplete-article-status",
    ),
    path(
        "autocomplete/article-priority/",
        ArticlePriorityAutocompleteView.as_view(),
        name="autocomplete-article-priority",
    ),
    path(
        "autocomplete/weighted-author/",
        WeightedAuthorAutocompleteView.as_view(),
        name="autocomplete-weighted-author",
    ),
    path(
        "autocomplete/article/",
        ArticleAutocompleteView.as_view(),
        name="autocomplete-article",
    ),
    path(
        "autocomplete/rich-article/",
        RichArticleAutocompleteView.as_view(),
        name="autocomplete-rich-article",
    ),
]
