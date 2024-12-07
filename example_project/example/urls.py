"""URL Configuration."""

from django.contrib import admin
from django.urls import path
from django.views.generic import FormView

from .autocompletes import (
    AuthorAutocompleteView,
    CategoryAutocompleteView,
    DemoEditionAutocompleteView,
    DemoMagazineAutocompleteView,
)
from .forms import DependentForm, ExampleForm
from .views import (
    article_archive_view,
    article_create_view,
    article_list_view,
    article_publish_view,
    article_update_view,
    create_view,
    edition_list_view,
    htmx_form_fragment_view,
    htmx_view,
    load_coauthors,
    load_subcategories,
    model_form_edit_test_view,
    model_form_test_view,
    update_view,
)

urlpatterns = [
    # ToDo: Add an index page
    path("model/", model_form_test_view, name="demo_with_model"),
    path("model/<int:instance_id>/", model_form_edit_test_view, name="demo_with_model_edit"),
    path("bs4/", FormView.as_view(form_class=ExampleForm, template_name="base4.html"), name="demo-bs4"),
    path("bs5/", FormView.as_view(form_class=ExampleForm, template_name="base5.html"), name="demo-bs5"),
    path("autocomplete-edition/", DemoEditionAutocompleteView.as_view(), name="autocomplete-edition"),
    path("autocomplete-magazine/", DemoMagazineAutocompleteView.as_view(), name="autocomplete-magazine"),
    path("editions/list/<int:page>/", edition_list_view, name="edition-list"),
    path("editions/list/", edition_list_view, name="edition-list"),
    path("create/", create_view, name="create"),
    path("update/<path:pk>/", update_view, name="update"),
    path("dependent/", FormView.as_view(form_class=DependentForm, template_name="base5.html"), name="dependent"),
    path(
        "dependent-bs4/", FormView.as_view(form_class=DependentForm, template_name="base4.html"), name="dependent-bs4"
    ),
    path("htmx/", htmx_view, name="htmx"),
    path("htmx-form-fragment/", htmx_form_fragment_view, name="htmx-form-fragment"),
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
    path("articles/<int:page>/", article_list_view, name="article-list"),
    path("articles/", article_list_view, name="article-list"),
    path(
        "article/create/",
        article_create_view,
        name="article-create",
    ),
    path(
        "article/<int:pk>/update/",
        article_update_view,
        name="article-update",
    ),
    path("article/<int:pk>/publish/", article_publish_view, name="article-publish"),
    path("article/<int:pk>/archive/", article_archive_view, name="article-archive"),
    path(
        "ajax/load-subcategories/",
        load_subcategories,
        name="ajax-load-subcategories",
    ),
    path(
        "ajax/load-coauthors/",
        load_coauthors,
        name="ajax-load-coauthors",
    ),
]
