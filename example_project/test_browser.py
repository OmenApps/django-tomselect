"""Browser-level regression coverage for django-tomselect."""

from datetime import timedelta
from urllib.parse import parse_qs, unquote, urlparse

import pytest
from django.urls import reverse
from django.utils import timezone

from example_project.example.models import Article, ArticleStatus, Author, Category, Edition, Magazine, PublishingMarket


pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db(transaction=True),
]


FIELD_SELECTOR = "#tomselect-custom-id"


def edition_response_matches(response, *, query, page_number=None):
    """Return whether a Playwright response matches the edition autocomplete request."""
    if not response.ok or "/autocomplete/edition/" not in response.url:
        return False

    params = parse_qs(urlparse(response.url).query, keep_blank_values=True)
    if params.get("q", [""])[0] != query:
        return False

    if page_number is None:
        return "p" not in params

    return params.get("p", [None])[0] == str(page_number)


def response_matches(response, *, path_suffix, query=None, page_number=None, expected_params=None):
    """Return whether a Playwright response matches the expected autocomplete request."""
    if not response.ok or not response.url.endswith(path_suffix) and path_suffix not in response.url:
        return False

    params = parse_qs(urlparse(response.url).query, keep_blank_values=True)
    if query is not None and params.get("q", [""])[0] != query:
        return False

    if page_number is not None and params.get("p", [None])[0] != str(page_number):
        return False

    for key, expected_value in (expected_params or {}).items():
        values = [unquote(value) for value in params.get(key, [])]
        expected_values = expected_value if isinstance(expected_value, (list, tuple, set)) else [expected_value]
        if not all(any(expected in value for value in values) for expected in expected_values):
            return False

    return True


def widget_selector(select_id):
    """Return the CSS selector for a TomSelect-enhanced select."""
    return f"#{select_id}"


def focus_named_widget(page, select_id):
    """Focus a specific TomSelect widget."""
    page.locator(widget_selector(select_id)).evaluate("select => select.tomselect.focus()")


def open_named_widget(page, select_id):
    """Open a specific TomSelect widget."""
    focus_named_widget(page, select_id)
    page.locator(widget_selector(select_id)).evaluate("select => select.tomselect.open()")


def clear_named_widget(page, select_id):
    """Clear the selected value for a specific TomSelect widget."""
    page.locator(widget_selector(select_id)).evaluate("select => select.tomselect.clear()")


def click_named_dropdown_option(page, select_id, text):
    """Click a visible option in a widget's dropdown."""
    page.locator(widget_selector(select_id)).evaluate(
        """(select, expectedText) => {
            const option = Array.from(
                select.tomselect.dropdown_content.querySelectorAll("[data-selectable]")
            ).find(candidate => candidate.textContent.includes(expectedText));

            if (!option) {
                throw new Error(`Dropdown option not found: ${expectedText}`);
            }

            option.click();
        }""",
        arg=text,
    )


def type_query_for_widget(page, select_id, query):
    """Type into a specific TomSelect widget's input."""
    open_named_widget(page, select_id)
    page.locator(widget_selector(select_id)).evaluate("select => select.tomselect.control_input.value = ''")
    page.keyboard.type(query)


def wait_for_widget(page, select_id):
    """Wait until a specific TomSelect instance is initialized."""
    page.wait_for_function(f"document.querySelector('{widget_selector(select_id)}')?.tomselect !== undefined")


def wait_for_dropdown_option(page, select_id, text):
    """Wait until the dropdown for a widget contains an option with the given text."""
    page.wait_for_function(
        """([selector, expectedText]) => {
            const select = document.querySelector(selector);
            if (!select || !select.tomselect) {
                return false;
            }

            return Array.from(
                select.tomselect.dropdown_content.querySelectorAll("[data-selectable]")
            ).some(option => option.textContent.includes(expectedText));
        }""",
        arg=[widget_selector(select_id), text],
    )


def dropdown_text(page, select_id):
    """Return the visible text content for a widget dropdown."""
    return page.locator(widget_selector(select_id)).evaluate(
        """select => select.tomselect.dropdown_content.textContent"""
    )


def choose_named_widget_option(
    page,
    select_id,
    *,
    option_text,
    path_suffix,
    query="",
    expected_params=None,
):
    """Load a widget's remote options and select one by visible text."""
    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix=path_suffix,
            query=query,
            expected_params=expected_params,
        )
    ):
        if query:
            type_query_for_widget(page, select_id, query)
        else:
            open_named_widget(page, select_id)

    wait_for_dropdown_option(page, select_id, option_text)
    click_named_dropdown_option(page, select_id, option_text)


def focus_widget(page):
    """Focus the TomSelect widget's input."""
    page.locator(FIELD_SELECTOR).evaluate("select => select.tomselect.focus()")


def type_query(page, query):
    """Type a search query into the focused TomSelect input."""
    page.keyboard.type(query)


def clear_query(page):
    """Clear the active TomSelect input using keyboard interaction."""
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")


def blur_widget(page):
    """Blur the active TomSelect widget by clicking outside of it."""
    page.get_by_role("heading", name="Default Styling Demo").click()


def scroll_dropdown_to_bottom(page):
    """Scroll the active TomSelect dropdown to trigger virtual scrolling."""
    page.locator(FIELD_SELECTOR).evaluate(
        """select => {
            const content = select.tomselect.dropdown_content;
            content.scrollTop = content.scrollHeight;
            content.dispatchEvent(new Event("scroll", { bubbles: true }));
        }"""
    )


def wait_for_tomselect(page):
    """Wait until the TomSelect instance is initialized."""
    page.wait_for_function(f"document.querySelector('{FIELD_SELECTOR}')?.tomselect !== undefined")


def wait_for_option_count(page, minimum_count):
    """Wait until the dropdown has at least the given number of selectable options."""
    page.wait_for_function(
        """([selector, count]) => {
            const select = document.querySelector(selector);
            if (!select || !select.tomselect) {
                return false;
            }

            return select.tomselect.dropdown_content.querySelectorAll("[data-selectable]").length >= count;
        }""",
        arg=[FIELD_SELECTOR, minimum_count],
    )


@pytest.fixture
def paginated_editions(db):
    """Create enough editions to exercise browser pagination."""
    for index in range(1, 46):
        Edition.objects.create(
            name=f"Edition {index:02d}",
            year="2024",
            pages=str(index),
            pub_num=f"PUB-{index:03d}",
        )


@pytest.fixture
def filtered_editions(db):
    """Create magazines and editions for filter_by browser coverage."""
    alpha = Magazine.objects.create(name="Alpha Magazine")
    beta = Magazine.objects.create(name="Beta Magazine")

    alpha_editions = [
        Edition.objects.create(name="Alpha Edition One", year="2024", pages="100", pub_num="ALPHA-001", magazine=alpha),
        Edition.objects.create(name="Alpha Edition Two", year="2024", pages="110", pub_num="ALPHA-002", magazine=alpha),
    ]
    beta_edition = Edition.objects.create(
        name="Beta Edition One", year="2024", pages="120", pub_num="BETA-001", magazine=beta
    )

    return {
        "alpha_magazine": alpha,
        "beta_magazine": beta,
        "alpha_editions": alpha_editions,
        "beta_edition": beta_edition,
    }


@pytest.fixture
def authors_for_exclusion(db):
    """Create authors for exclude_by browser coverage."""
    primary = Author.objects.create(name="Primary Author", bio="Primary author bio")
    secondary = Author.objects.create(name="Secondary Author", bio="Secondary author bio")
    tertiary = Author.objects.create(name="Tertiary Author", bio="Tertiary author bio")

    return {
        "primary": primary,
        "secondary": secondary,
        "tertiary": tertiary,
    }


@pytest.fixture
def publishing_markets(db):
    """Create a three-level market hierarchy for dependent-field browser coverage."""
    region = PublishingMarket.objects.create(
        name="North Region",
        market_size=1000,
        active_publications=20,
    )
    other_region = PublishingMarket.objects.create(
        name="South Region",
        market_size=800,
        active_publications=12,
    )

    country = PublishingMarket.objects.create(
        name="North Country",
        parent=region,
        market_size=600,
        active_publications=10,
    )
    other_country = PublishingMarket.objects.create(
        name="South Country",
        parent=other_region,
        market_size=500,
        active_publications=8,
    )

    local_market = PublishingMarket.objects.create(
        name="North City",
        parent=country,
        market_size=300,
        active_publications=5,
    )
    other_local_market = PublishingMarket.objects.create(
        name="South City",
        parent=other_country,
        market_size=200,
        active_publications=4,
    )

    return {
        "region": region,
        "other_region": other_region,
        "country": country,
        "other_country": other_country,
        "local_market": local_market,
        "other_local_market": other_local_market,
    }


@pytest.fixture
def rich_articles(db):
    """Create articles with related metadata for the rich article demo."""
    magazine = Magazine.objects.create(name="Feature Monthly")
    other_magazine = Magazine.objects.create(name="Daily Dispatch")
    primary_author = Author.objects.create(name="Ada Lovelace", bio="Analytical engines")
    co_author = Author.objects.create(name="Grace Hopper", bio="Compilers")
    category = Category.objects.create(name="Engineering")
    secondary_category = Category.objects.create(name="Profiles")

    featured_article = Article.objects.create(
        title="Deep Feature Story",
        word_count=1400,
        magazine=magazine,
        status=ArticleStatus.PUBLISHED,
        updated_at=timezone.now() - timedelta(days=3),
    )
    featured_article.authors.add(primary_author, co_author)
    featured_article.categories.add(category, secondary_category)

    supporting_article = Article.objects.create(
        title="Draft Feature Notes",
        word_count=400,
        magazine=other_magazine,
        status=ArticleStatus.DRAFT,
        updated_at=timezone.now() - timedelta(days=20),
    )
    supporting_article.authors.add(primary_author)
    supporting_article.categories.add(category)

    return {
        "featured_article": featured_article,
        "supporting_article": supporting_article,
        "primary_author": primary_author,
        "co_author": co_author,
        "category": category,
    }


@pytest.fixture
def constant_filter_articles(db):
    """Create article data for constant filter browser coverage."""
    alpha_magazine = Magazine.objects.create(name="Alpha Journal")
    beta_magazine = Magazine.objects.create(name="Beta Journal")
    author = Author.objects.create(name="Filter Author", bio="Filter author bio")
    category = Category.objects.create(name="Investigations")

    alpha_published = Article.objects.create(
        title="Alpha Published Piece",
        word_count=900,
        magazine=alpha_magazine,
        status=ArticleStatus.PUBLISHED,
        updated_at=timezone.now() - timedelta(days=2),
    )
    alpha_draft = Article.objects.create(
        title="Alpha Draft Piece",
        word_count=700,
        magazine=alpha_magazine,
        status=ArticleStatus.DRAFT,
        updated_at=timezone.now() - timedelta(days=2),
    )
    beta_published = Article.objects.create(
        title="Beta Published Piece",
        word_count=1100,
        magazine=beta_magazine,
        status=ArticleStatus.PUBLISHED,
        updated_at=timezone.now() - timedelta(days=5),
    )

    for article in [alpha_published, alpha_draft, beta_published]:
        article.authors.add(author)
        article.categories.add(category)

    return {
        "alpha_magazine": alpha_magazine,
        "beta_magazine": beta_magazine,
        "alpha_published": alpha_published,
        "alpha_draft": alpha_draft,
        "beta_published": beta_published,
    }


def test_clearing_query_reloads_empty_search_results(page, live_server, paginated_editions):
    """Deleting a typed query should repopulate results from the empty-query reset path."""
    page.goto(f"{live_server.url}{reverse('demo-default')}")
    wait_for_tomselect(page)

    focus_widget(page)
    with page.expect_response(lambda response: edition_response_matches(response, query="Ed")):
        type_query(page, "Ed")
    wait_for_option_count(page, 1)

    with page.expect_response(lambda response: edition_response_matches(response, query="")):
        clear_query(page)
    wait_for_option_count(page, 20)

    option_count = page.locator(FIELD_SELECTOR).evaluate(
        """select => select.tomselect.dropdown_content.querySelectorAll("[data-selectable]").length"""
    )
    last_value = page.locator(FIELD_SELECTOR).evaluate("select => select.tomselect.lastValue")

    assert last_value == ""
    assert option_count >= 20


def test_virtual_scroll_still_loads_after_dropdown_reopen(page, live_server, paginated_editions):
    """Closing and reopening the dropdown should preserve fresh pagination state."""
    page.goto(f"{live_server.url}{reverse('demo-default')}")
    wait_for_tomselect(page)

    focus_widget(page)
    with page.expect_response(lambda response: edition_response_matches(response, query="Ed")):
        type_query(page, "Ed")
    wait_for_option_count(page, 20)

    with page.expect_response(lambda response: edition_response_matches(response, query="Ed", page_number=2)):
        scroll_dropdown_to_bottom(page)
    wait_for_option_count(page, 21)

    with page.expect_response(lambda response: edition_response_matches(response, query="")):
        blur_widget(page)
    wait_for_option_count(page, 20)

    focus_widget(page)
    with page.expect_response(lambda response: edition_response_matches(response, query="", page_number=2)):
        scroll_dropdown_to_bottom(page)
    wait_for_option_count(page, 21)

    option_count = page.locator(FIELD_SELECTOR).evaluate(
        """select => select.tomselect.dropdown_content.querySelectorAll("[data-selectable]").length"""
    )

    assert option_count >= 21


def test_filter_by_magazine_limits_edition_results(page, live_server, filtered_editions):
    """Selecting a parent magazine should constrain edition results for the dependent field."""
    page.goto(f"{live_server.url}{reverse('filter-by-magazine')}")
    wait_for_widget(page, "id_magazine")
    wait_for_widget(page, "id_edition")

    choose_named_widget_option(
        page,
        "id_magazine",
        option_text="Alpha Magazine",
        path_suffix="/autocomplete/magazine/",
        query="Alpha",
    )

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/edition/",
            query="",
            expected_params={"f": f"magazine_id={filtered_editions['alpha_magazine'].id}"},
        )
    ):
        open_named_widget(page, "id_edition")
    wait_for_dropdown_option(page, "id_edition", "Alpha Edition One")

    options_text = dropdown_text(page, "id_edition")

    assert "Alpha Edition One" in options_text
    assert "Alpha Edition Two" in options_text
    assert "Beta Edition One" not in options_text


def test_clearing_parent_field_restores_unfiltered_dependent_results(page, live_server, filtered_editions):
    """Clearing a parent field should remove the dependent filter from later requests."""
    page.goto(f"{live_server.url}{reverse('filter-by-magazine')}")
    wait_for_widget(page, "id_magazine")
    wait_for_widget(page, "id_edition")

    choose_named_widget_option(
        page,
        "id_magazine",
        option_text="Alpha Magazine",
        path_suffix="/autocomplete/magazine/",
        query="Alpha",
    )

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/edition/",
            query="",
            expected_params={"f": f"magazine_id={filtered_editions['alpha_magazine'].id}"},
        )
    ):
        open_named_widget(page, "id_edition")
    wait_for_dropdown_option(page, "id_edition", "Alpha Edition One")

    clear_named_widget(page, "id_magazine")

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/edition/",
            query="",
        )
    ):
        open_named_widget(page, "id_edition")
    wait_for_dropdown_option(page, "id_edition", "Beta Edition One")

    options_text = dropdown_text(page, "id_edition")

    assert "Alpha Edition One" in options_text
    assert "Beta Edition One" in options_text


def test_exclude_by_primary_author_omits_selected_author(page, live_server, authors_for_exclusion):
    """Selecting a primary author should exclude that author from the contributing field."""
    page.goto(f"{live_server.url}{reverse('exclude-by-primary-author')}")
    wait_for_widget(page, "id_primary_author")
    wait_for_widget(page, "id_contributing_authors")

    choose_named_widget_option(
        page,
        "id_primary_author",
        option_text="Primary Author",
        path_suffix="/autocomplete/author/",
        query="Primary",
    )

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/author/",
            query="",
            expected_params={"e": f"id={authors_for_exclusion['primary'].id}"},
        )
    ):
        open_named_widget(page, "id_contributing_authors")
    wait_for_dropdown_option(page, "id_contributing_authors", "Secondary Author")

    options_text = dropdown_text(page, "id_contributing_authors")

    assert "Secondary Author" in options_text
    assert "Tertiary Author" in options_text
    assert "Primary Author" not in options_text


def test_three_level_filtering_propagates_parent_ids(page, live_server, publishing_markets):
    """Chained dependent fields should pass the selected parent id through each level."""
    page.goto(f"{live_server.url}{reverse('three-level-filter-by')}")
    wait_for_widget(page, "id_region")
    wait_for_widget(page, "id_country")
    wait_for_widget(page, "id_local_market")

    choose_named_widget_option(
        page,
        "id_region",
        option_text="North Region",
        path_suffix="/autocomplete/region/",
        query="North",
    )

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/country/",
            query="",
            expected_params={"f": f"parent_id={publishing_markets['region'].id}"},
        )
    ):
        open_named_widget(page, "id_country")
    wait_for_dropdown_option(page, "id_country", "North Country")

    country_options = dropdown_text(page, "id_country")
    assert "North Country" in country_options
    assert "South Country" not in country_options

    click_named_dropdown_option(page, "id_country", "North Country")

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/local-market/",
            query="",
            expected_params={"f": f"parent_id={publishing_markets['country'].id}"},
        )
    ):
        open_named_widget(page, "id_local_market")
    wait_for_dropdown_option(page, "id_local_market", "North City")

    local_market_options = dropdown_text(page, "id_local_market")
    assert "North City" in local_market_options
    assert "South City" not in local_market_options


def test_rich_article_select_renders_metadata_and_selected_item(page, live_server, rich_articles):
    """Rich article select should render custom metadata in both dropdown and selected item."""
    page.goto(f"{live_server.url}{reverse('rich-article-select')}")
    wait_for_widget(page, "id_article")

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/rich-article/",
            query="Feature",
        )
    ):
        type_query_for_widget(page, "id_article", "Feature")
    wait_for_dropdown_option(page, "id_article", "Deep Feature Story")

    dropdown_html = page.locator(widget_selector("id_article")).evaluate(
        """select => select.tomselect.dropdown_content.innerHTML"""
    )

    assert "article-option" in dropdown_html
    assert "status-badge status-published" in dropdown_html
    assert "Ada Lovelace" in dropdown_html
    assert "Engineering" in dropdown_html

    click_named_dropdown_option(page, "id_article", "Deep Feature Story")

    selected_html = page.locator(widget_selector("id_article")).evaluate(
        """select => select.tomselect.control.innerHTML"""
    )

    assert "selected-article" in selected_html
    assert "Deep Feature Story" in selected_html
    assert "Ada Lovelace" in selected_html
    assert "Grace Hopper" in selected_html


def test_constant_filter_by_always_applies_published_status(page, live_server, constant_filter_articles):
    """Constant filter_by should always include the published-status filter."""
    page.goto(f"{live_server.url}{reverse('constant-filter-by')}")
    wait_for_widget(page, "id_magazine")
    wait_for_widget(page, "id_published_articles")

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/article/",
            query="",
            expected_params={"f": "__const__status=published"},
        )
    ):
        open_named_widget(page, "id_published_articles")
    wait_for_dropdown_option(page, "id_published_articles", "Alpha Published Piece")

    all_options_text = dropdown_text(page, "id_published_articles")
    assert "Alpha Published Piece" in all_options_text
    assert "Beta Published Piece" in all_options_text
    assert "Alpha Draft Piece" not in all_options_text

    choose_named_widget_option(
        page,
        "id_magazine",
        option_text="Alpha Journal",
        path_suffix="/autocomplete/magazine/",
        query="Alpha",
    )

    with page.expect_response(
        lambda response: response_matches(
            response,
            path_suffix="/autocomplete/article/",
            query="",
            expected_params={
                "f": [
                    "__const__status=published",
                    f"magazine_id={constant_filter_articles['alpha_magazine'].id}",
                ]
            },
        )
    ):
        open_named_widget(page, "id_published_articles")
    wait_for_dropdown_option(page, "id_published_articles", "Alpha Published Piece")

    filtered_options_text = dropdown_text(page, "id_published_articles")
    assert "Alpha Published Piece" in filtered_options_text
    assert "Beta Published Piece" not in filtered_options_text
    assert "Alpha Draft Piece" not in filtered_options_text
