"""Template tag that renders a link to the Read the Docs page for the current demo."""

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

DOCS_BASE_URL = "https://django-tomselect.readthedocs.io/en/latest/example_app/"

# Maps a URL name (from example_project.example.urls) to a docs page slug
# under docs/example_app/. URL names not in this map render no link.
URL_NAME_TO_DOC_SLUG = {
    # Styling demos all map to the shared styling page
    "demo-default": "styling",
    "demo-bs4": "styling",
    "demo-bs5": "styling",
    # Basic demos
    "demo-htmx": "htmx",
    "demo-htmx-tabs": "htmx_in_tabs",
    "demo-formset-filter": "formset_filter_by",
    # Intermediate demos
    "filter-by-magazine": "filter_by_magazine",
    "filter-by-category": "filter_by_category",
    "exclude-by-primary-author": "exclude_by_primary_author",
    "range-preview": "view_range_based_data",
    "tagging": "tagging",
    "custom-content": "custom_content_display",
    "weighted-author-search": "weighted_author_search",
    # Advanced demos
    "three-level-filter-by": "three_level_filter_by",
    "rich-article-select": "rich_article_select",
    "rich-author-multi-select": "rich_author_multi_select",
    "multiple-filter-by": "multiple_filter_by",
    "constant-filter-by": "constant_filter_by",
    "article-list": "article_list_and_create",
    "article-create": "article_list_and_create",
    "article-update": "article_list_and_create",
    "article-bulk-action": "article_bulk_actions",
    "article-token-search": "article_token_search",
    "article-advanced-token-search": "article_advanced_token_search",
    "github-user-picker": "github_user_picker",
    "inline-create-tag": "inline_create_tag",
    "gfk-picker": "gfk_picker",
}


@register.simple_tag(takes_context=True)
def docs_link(context):
    """Render a Read the Docs link for the current view, if one is mapped."""
    request = context.get("request")
    if request is None or request.resolver_match is None:
        return ""

    slug = URL_NAME_TO_DOC_SLUG.get(request.resolver_match.url_name)
    if not slug:
        return mark_safe("")

    url = f"{DOCS_BASE_URL}{slug}.html"
    return format_html(
        '<div class="mb-3">'
        '<a href="{}" target="_blank" rel="noopener" '
        'class="btn btn-sm btn-outline-primary">'
        "View this demo on Read the Docs "
        '<span aria-hidden="true">&rarr;</span>'
        "</a>"
        "</div>",
        url,
    )
