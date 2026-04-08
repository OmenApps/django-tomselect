"""Browser-level regression tests for TomSelect pagination resets."""

import os
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse

from example_project.example.models import Edition, Magazine

# Playwright's sync API drives the browser through an in-process event loop.
# Django's async safety check treats that as an async context even in these
# fully synchronous tests, so we allow ORM access for this module.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

playwright = pytest.importorskip("playwright.sync_api")

Error = playwright.Error
Page = playwright.Page
sync_playwright = playwright.sync_playwright


pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def page() -> Page:
    """Create an isolated browser page for each test."""
    with sync_playwright() as playwright_manager:
        try:
            browser = playwright_manager.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        except Error as exc:
            pytest.skip(f"Playwright Chromium is unavailable. Run `uv run playwright install chromium`. {exc}")

        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
        browser.close()


@pytest.fixture(scope="module", autouse=True)
def collected_static_assets() -> None:
    """Collect static assets so the live server can serve TomSelect JS and CSS."""
    static_root = Path(settings.STATIC_ROOT)
    static_root_preexisting = static_root.exists()

    call_command("collectstatic", interactive=False, verbosity=0)
    yield

    if not static_root_preexisting and static_root.exists():
        shutil.rmtree(static_root)


@pytest.fixture
def paginated_editions() -> None:
    """Create enough editions for virtual-scroll pagination on the default demo page."""
    magazine = Magazine.objects.create(name="Pagination Magazine")
    Edition.objects.bulk_create(
        [
            Edition(
                name=f"Pagination Edition {index:02d}",
                year="2026",
                pages=str(100 + index),
                pub_num=f"PAG-{index:02d}",
                magazine=magazine,
            )
            for index in range(1, 36)
        ]
    )


def _matches_edition_response(response, *, query: str, page_number: int) -> bool:
    """Return True when the response matches the edition autocomplete request we expect."""
    if response.status != 200:
        return False

    parsed = urlparse(response.url)
    if not parsed.path.endswith("/autocomplete/edition/"):
        return False

    params = parse_qs(parsed.query)
    request_query = params.get("q", [""])[0]
    request_page = int(params.get("p", ["1"])[0])
    return request_query == query and request_page == page_number


def _ts_wrapper(page: Page, select_id: str):
    """Return the .ts-wrapper for the given select element.

    TomSelect creates .ts-wrapper as an immediate sibling after the original
    <select>, not as a parent wrapper around it.
    """
    return page.locator(f"select#{select_id} + .ts-wrapper")


def _widget_control(page: Page, select_id: str):
    """Return the clickable control area of the TomSelect widget."""
    return _ts_wrapper(page, select_id).locator(".ts-control")


def _search_input(page: Page, select_id: str):
    """Return the search input for typing queries.

    When the dropdown_input plugin is active, the search input is a
    ``.dropdown-input`` inside the dropdown. Otherwise it is the input
    inside ``.ts-control``.
    """
    wrapper = _ts_wrapper(page, select_id)
    dropdown_input = wrapper.locator(".dropdown-input")
    if dropdown_input.count() > 0:
        return dropdown_input
    return wrapper.locator(".ts-control input")


def _dropdown_content(page: Page, select_id: str):
    """Return the scrollable dropdown content element for the given select id."""
    return _ts_wrapper(page, select_id).locator(".ts-dropdown-content")


def _wait_for_edition_response(page: Page, *, query: str, page_number: int, action) -> None:
    """Run an action and wait for the matching edition autocomplete response."""
    with page.expect_response(
        lambda response: _matches_edition_response(response, query=query, page_number=page_number),
        timeout=15000,
    ):
        action()


def _scroll_to_bottom(locator) -> None:
    """Scroll the dropdown content to the bottom and emit a scroll event."""
    locator.evaluate(
        """(element) => {
            element.scrollTop = element.scrollHeight;
            element.dispatchEvent(new Event('scroll', { bubbles: true }));
        }"""
    )


def _wait_for_widget_ready(page: Page, select_id: str) -> None:
    """Wait until TomSelect has initialized the original select element."""
    page.wait_for_function(
        """(widgetId) => Boolean(document.getElementById(widgetId)?.tomselect)""",
        arg=select_id,
        timeout=15000,
    )


@pytest.mark.parametrize("select_id", ["tomselect-custom-id", "id_tomselect_multiple"])
def test_virtual_scroll_survives_close_and_reopen(
    live_server,
    page: Page,
    paginated_editions,
    select_id: str,
) -> None:
    """Closing and reopening a widget should not destroy fresh pagination state."""
    page.goto(f"{live_server.url}{reverse('demo-default')}")
    _wait_for_widget_ready(page, select_id)

    control = _widget_control(page, select_id)
    dropdown_content = _dropdown_content(page, select_id)

    control.click()
    search = _search_input(page, select_id)
    _wait_for_edition_response(page, query="Pagination", page_number=1, action=lambda: search.fill("Pagination"))
    _wait_for_edition_response(
        page,
        query="",
        page_number=1,
        action=lambda: page.get_by_role("heading", name="Default Styling Demo").click(),
    )

    # Reopen and wait for the preload response before scrolling
    _wait_for_edition_response(page, query="", page_number=1, action=lambda: control.click())
    _wait_for_edition_response(page, query="", page_number=2, action=lambda: _scroll_to_bottom(dropdown_content))


def test_virtual_scroll_survives_reset_to_empty_query(
    live_server,
    page: Page,
    paginated_editions,
) -> None:
    """Clearing a non-empty query should reload page one and still preserve next-page pagination."""
    page.goto(f"{live_server.url}{reverse('demo-default')}")
    _wait_for_widget_ready(page, "tomselect-custom-id")

    control = _widget_control(page, "tomselect-custom-id")
    dropdown_content = _dropdown_content(page, "tomselect-custom-id")

    control.click()
    search = _search_input(page, "tomselect-custom-id")
    _wait_for_edition_response(page, query="Pagination", page_number=1, action=lambda: search.fill("Pagination"))
    _wait_for_edition_response(page, query="", page_number=1, action=lambda: search.fill(""))
    _wait_for_edition_response(page, query="", page_number=2, action=lambda: _scroll_to_bottom(dropdown_content))
