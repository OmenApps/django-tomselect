"""Pytest fixtures for django_tomselect tests."""

import os
from contextlib import suppress

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.urls import reverse

from example_project.example.models import Edition, Magazine, ModelWithPKIDAndUUIDId, ModelWithUUIDPk


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the settings cache before each test."""
    cache.clear()
    yield


def pytest_collection_modifyitems(items):
    """Automatically mark browser test modules so default test runs can skip them."""
    for item in items:
        if item.path.name.startswith("test_browser"):
            item.add_marker(pytest.mark.playwright)


@pytest.fixture
def user():
    """Create and return a test user."""
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def user_with_permissions(user):
    """Create and return a test user with add permissions."""
    # Get the content type for the Edition model
    edition_content_type = ContentType.objects.get_for_model(Edition)

    # Retrieve the permission for adding an Edition for the correct content type
    add_edition_permission = Permission.objects.get(content_type=edition_content_type, codename="add_edition")

    # Assign the permission to the user
    user.user_permissions.add(add_edition_permission)
    return user


@pytest.fixture
def sample_edition():
    """Create a sample Edition instance."""
    return Edition.objects.create(name="Test Edition", year="2024", pages="100", pub_num="TEST-001")


@pytest.fixture
def sample_magazine():
    """Create a sample Magazine instance."""
    return Magazine.objects.create(name="Test Magazine")


@pytest.fixture
def edition_with_magazine(sample_magazine):
    """Create a sample Edition instance with an associated Magazine."""
    return Edition.objects.create(
        name="Magazine Edition",
        year="2024",
        pages="200",
        pub_num="MAG-001",
        magazine=sample_magazine,
    )


@pytest.fixture
def magazines():
    """Create and return a list of test magazines."""
    magazines = [Magazine.objects.create(name=f"Magazine {i}") for i in range(1, 4)]
    return magazines


@pytest.fixture
def editions(magazines):
    """Create and return test editions with specific data for search tests."""
    editions = []

    # Create editions with specific names and years for our tests
    test_data = [
        ("Edition 1", "2021"),
        ("Edition 2", "2022"),
        ("Edition 3", "2023"),
        ("Edition 4", "2024"),
        ("Edition 5", "2025"),
        ("Edition 6", "2026"),
        ("Edition 7", "2027"),
        ("Edition 8", "2028"),
        ("Edition 9", "2029"),
    ]

    for i, (name, year) in enumerate(test_data, 1):
        edition = Edition.objects.create(
            name=name,
            year=year,
            pages=str(i),
            pub_num=f"PUBNUM{i}",
            magazine=magazines[i % len(magazines)],
        )
        editions.append(edition)

    return editions


@pytest.fixture
def test_editions(db, magazines):
    """Create a specific set of test editions with known data.

    Creates exactly 9 Edition objects, all linked to the first magazine,
    with sequential names ("Edition 1"-"Edition 9"), years 2021-2029,
    pages 10-90, and pub_num "PUB-1"-"PUB-9".
    """
    Edition.objects.all().delete()  # Clear any existing editions

    editions = []
    for i in range(1, 10):  # Create exactly 9 editions
        edition = Edition.objects.create(
            name=f"Edition {i}",
            year=f"202{i}",  # 2021-2029
            pages=str(i * 10),
            pub_num=f"PUB-{i}",
            magazine=magazines[0] if magazines else None,
        )
        editions.append(edition)

    return editions


@pytest.fixture
def autocomplete_url():
    """Return the URL for the edition autocomplete view."""
    return reverse("autocomplete-edition")


@pytest.fixture
def mock_request():
    """Create a mock request with authentication."""

    class MockUser:
        """Mock user class with authentication and permissions."""

        id = 1
        is_authenticated = True

        def has_perms(self, perms):
            """Mock has_perms method."""
            return True

    class MockRequest:
        """Mock request class with user and method attributes."""

        user = MockUser()
        method = "GET"
        GET = {}

        def get_full_path(self):
            """Mock get_full_path method."""
            return "/test/"

    return MockRequest()


@pytest.fixture
def sample_uuid_model():
    """Create a sample ModelWithUUIDPk instance."""
    return ModelWithUUIDPk.objects.create(name="Test UUID Model")


@pytest.fixture
def sample_pkid_uuid_model():
    """Create a sample ModelWithPKIDAndUUIDId instance."""
    return ModelWithPKIDAndUUIDId.objects.create(name="Test PKID UUID Model")


@pytest.fixture
def multiple_uuid_models():
    """Create multiple ModelWithUUIDPk instances."""
    return [ModelWithUUIDPk.objects.create(name=f"UUID Model {i}") for i in range(1, 4)]


@pytest.fixture
def multiple_pkid_uuid_models():
    """Create multiple ModelWithPKIDAndUUIDId instances."""
    return [ModelWithPKIDAndUUIDId.objects.create(name=f"PKID UUID Model {i}") for i in range(1, 4)]


@pytest.fixture
def page(live_server):
    """Create an isolated Playwright page for each end-to-end test."""
    playwright_sync_api = pytest.importorskip(
        "playwright.sync_api",
        reason="Install Playwright with `uv run --extra dev pytest ...`.",
    )
    previous_async_flag = os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE")
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    playwright = playwright_sync_api.sync_playwright().start()

    try:
        browser = playwright.chromium.launch(headless=True)
    except Exception as exc:
        playwright.stop()
        pytest.skip(
            "Playwright Chromium is not installed or could not be launched. "
            "Run `PLAYWRIGHT_BROWSERS_PATH=/tmp/playwright-browsers uv run --extra dev playwright install chromium`. "
            f"Original error: {exc}"
        )

    context = browser.new_context(viewport={"width": 1440, "height": 1200})
    page = context.new_page()

    try:
        yield page
    finally:
        with suppress(Exception):
            context.close()
        with suppress(Exception):
            browser.close()
        playwright.stop()
        if previous_async_flag is None:
            os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
        else:
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = previous_async_flag
