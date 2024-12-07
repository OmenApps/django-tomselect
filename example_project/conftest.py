"""Pytest fixtures for django_tomselect tests."""

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.urls import reverse

from example_project.example.models import Edition, Magazine


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the settings cache before each test."""
    cache.clear()
    yield


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
        name="Magazine Edition", year="2024", pages="200", pub_num="MAG-001", magazine=sample_magazine
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
            name=name, year=year, pages=str(i), pub_num=f"PUBNUM{i}", magazine=magazines[i % len(magazines)]
        )
        editions.append(edition)

    return editions


@pytest.fixture
def autocomplete_url():
    """Return the URL for the edition autocomplete view."""
    return reverse("autocomplete-edition")
