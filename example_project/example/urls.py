"""URL Configuration."""

from django.urls import path

from example_project.example import autocompletes, views

urlpatterns = [
    path("", views.index_view, name="index"),
    # Basic Examples
    path("demo-default/", views.default_demo, name="demo-default"),
    path("demo-bs4/", views.bootstrap4_demo, name="demo-bs4"),
    path("demo-bs5/", views.bootstrap5_demo, name="demo-bs5"),
    path("demo-htmx/", views.htmx_view, name="demo-htmx"),
    path("demo-htmx-tabs/", views.htmx_tabs_view, name="demo-htmx-tabs"),
    path(
        "demo-htmx-form-fragment/",
        views.htmx_form_fragment_view,
        name="demo-htmx-form-fragment",
    ),
    path(
        "demo-performance-test/",
        views.performance_test_demo,
        name="demo-performance-test",
    ),
    path("demo-formset/", views.formset_demo, name="demo-formset"),
    path("demo-model-formset/", views.model_formset_demo, name="demo-model-formset"),
    # Intermediate Examples
    path("filter-by-magazine/", views.filter_by_magazine_demo, name="filter-by-magazine"),
    path("filter-by-category/", views.filter_by_category_demo, name="filter-by-category"),
    path(
        "exclude-by-primary-author/",
        views.exclude_by_primary_author_demo,
        name="exclude-by-primary-author",
    ),
    path("tagging/", views.tagging_view, name="tagging"),
    path("range-preview/", views.range_preview_demo, name="range-preview"),
    path("update-range-preview/", views.update_range_preview, name="update-range-preview"),
    path("custom-content/", views.embargo_management_view, name="custom-content"),
    path(
        "weighted-author-search/",
        views.weighted_author_search_demo,
        name="weighted-author-search",
    ),
    # Advanced Examples
    path("three-level-filter-by/", views.market_selection_view, name="three-level-filter-by"),
    path("article-bulk-action/", views.article_bulk_action_view, name="article-bulk-action"),
    path("article-filtered-table/", views.article_filtered_table, name="article-filtered-table"),
    path("rich-article-select/", views.rich_article_select_demo, name="rich-article-select"),
    path("multiple-filter-by/", views.multiple_filter_by_demo, name="multiple-filter-by"),
    path("constant-filter-by/", views.constant_filter_by_demo, name="constant-filter-by"),
    path("articles/<int:page>/", views.article_list_view, name="article-list"),
    path("articles/", views.article_list_view, name="article-list"),
    path("article/create/", views.article_create_view, name="article-create"),
    path("article/<int:pk>/", views.article_detail_view, name="article-detail"),
    path("article/<int:pk>/update/", views.article_update_view, name="article-update"),
    path("article/<int:pk>/publish/", views.article_publish_view, name="article-publish"),
    path("article/<int:pk>/archive/", views.article_archive_view, name="article-archive"),
    path("article/<int:pk>/cancel/", views.article_cancel_view, name="article-cancel"),
    # Crud
    path("categories/<int:page>/", views.category_list_view, name="category-list"),
    path("categories/", views.category_list_view, name="category-list"),
    path("category/create/", views.category_create_view, name="category-create"),
    path("category/<int:pk>/", views.category_detail_view, name="category-detail"),
    path("category/<int:pk>/update/", views.category_update_view, name="category-update"),
    path("category/<int:pk>/delete/", views.category_delete_view, name="category-delete"),
    path("magazines/<int:page>/", views.magazine_list_view, name="magazine-list"),
    path("magazines/", views.magazine_list_view, name="magazine-list"),
    path("magazine/create/", views.magazine_create_view, name="magazine-create"),
    path("magazine/<int:pk>/update/", views.magazine_update_view, name="magazine-update"),
    path("magazine/<int:pk>/delete/", views.magazine_delete_view, name="magazine-delete"),
    path("authors/<int:page>/", views.author_list_view, name="author-list"),
    path("authors/", views.author_list_view, name="author-list"),
    path("author/create/", views.author_create_view, name="author-create"),
    path("author/<int:pk>/update/", views.author_update_view, name="author-update"),
    path("author/<int:pk>/delete/", views.author_delete_view, name="author-delete"),
    path("editions/<int:page>/", views.edition_list_view, name="edition-list"),
    path("editions/", views.edition_list_view, name="edition-list"),
    path("edition/create/", views.edition_create_view, name="edition-create"),
    path("edition/<int:pk>/update/", views.edition_update_view, name="edition-update"),
    path("edition/<int:pk>/delete/", views.edition_delete_view, name="edition-delete"),
    # Autocomplete Views
    path(
        "autocomplete/edition/",
        autocompletes.EditionAutocompleteView.as_view(),
        name="autocomplete-edition",
    ),
    path(
        "autocomplete/magazine/",
        autocompletes.MagazineAutocompleteView.as_view(),
        name="autocomplete-magazine",
    ),
    path(
        "autocomplete/author/",
        autocompletes.AuthorAutocompleteView.as_view(),
        name="autocomplete-author",
    ),
    path(
        "autocomplete/category/",
        autocompletes.CategoryAutocompleteView.as_view(),
        name="autocomplete-category",
    ),
    path(
        "autocomplete/country/",
        autocompletes.CountryAutocompleteView.as_view(),
        name="autocomplete-country",
    ),
    path(
        "autocomplete/region/",
        autocompletes.RegionAutocompleteView.as_view(),
        name="autocomplete-region",
    ),
    path(
        "autocomplete/local-market/",
        autocompletes.LocalMarketAutocompleteView.as_view(),
        name="autocomplete-local-market",
    ),
    path(
        "autocomplete/edition-year/",
        autocompletes.EditionYearAutocompleteView.as_view(),
        name="autocomplete-edition-year",
    ),
    path(
        "autocomplete/publication-tag/",
        autocompletes.PublicationTagAutocompleteView.as_view(),
        name="autocomplete-publication-tag",
    ),
    path(
        "autocomplete/page-count/",
        autocompletes.WordCountAutocompleteView.as_view(),
        name="autocomplete-page-count",
    ),
    path(
        "autocomplete/page-count-range/",
        autocompletes.WordCountRangeAutocompleteView.as_view(),
        name="autocomplete-page-count-range",
    ),
    path(
        "autocomplete/embargo-region/",
        autocompletes.EmbargoRegionAutocompleteView.as_view(),
        name="autocomplete-embargo-region",
    ),
    path(
        "autocomplete/embargo-timeframe/",
        autocompletes.EmbargoTimeframeAutocompleteView.as_view(),
        name="autocomplete-embargo-timeframe",
    ),
    path(
        "autocomplete/article-status/",
        autocompletes.ArticleStatusAutocompleteView.as_view(),
        name="autocomplete-article-status",
    ),
    path(
        "autocomplete/article-priority/",
        autocompletes.ArticlePriorityAutocompleteView.as_view(),
        name="autocomplete-article-priority",
    ),
    path(
        "autocomplete/weighted-author/",
        autocompletes.WeightedAuthorAutocompleteView.as_view(),
        name="autocomplete-weighted-author",
    ),
    path(
        "autocomplete/article/",
        autocompletes.ArticleAutocompleteView.as_view(),
        name="autocomplete-article",
    ),
    path(
        "autocomplete/rich-article/",
        autocompletes.RichArticleAutocompleteView.as_view(),
        name="autocomplete-rich-article",
    ),
    path(
        "autocomplete/uuid-pk/",
        autocompletes.ModelWithUUIDPkAutocompleteView.as_view(),
        name="autocomplete-uuid-pk",
    ),
    path(
        "autocomplete/pkid-uuid/",
        autocompletes.ModelWithPKIDAndUUIDIdAutocompleteView.as_view(),
        name="autocomplete-pkid-uuid",
    ),
]
