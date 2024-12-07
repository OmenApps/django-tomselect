"""Test the setup and configuration of the example project."""

from importlib import reload

import pytest

import django_tomselect.app_settings


@pytest.mark.django_db
class TestModelFixtures:
    """Test the model fixtures used throughout the test suite."""

    def test_sample_edition_creation(self, sample_edition):
        """Test that the sample_edition fixture creates an Edition correctly."""
        from example_project.example.models import Edition

        assert isinstance(sample_edition, Edition)
        assert sample_edition.name == "Test Edition"
        assert sample_edition.year == "2024"
        assert sample_edition.pages == "100"
        assert sample_edition.pub_num == "TEST-001"
        assert sample_edition.magazine is None

    def test_sample_magazine_creation(self, sample_magazine):
        """Test that the sample_magazine fixture creates a Magazine correctly."""
        from example_project.example.models import Magazine

        assert isinstance(sample_magazine, Magazine)
        assert sample_magazine.name == "Test Magazine"

    def test_edition_with_magazine_creation(self, edition_with_magazine, sample_magazine):
        """Test that the edition_with_magazine fixture creates related objects correctly."""
        from example_project.example.models import Edition

        assert isinstance(edition_with_magazine, Edition)
        assert edition_with_magazine.magazine == sample_magazine
        assert edition_with_magazine.name == "Magazine Edition"


@pytest.mark.django_db
class TestAppSettings:
    """Test the app settings functionality."""

    def setup_method(self):
        """Reset app settings before each test."""
        reload(django_tomselect.app_settings)

    @pytest.mark.parametrize(
        "setting_name,default_value,expected",
        [
            ("TOMSELECT_CSS_FRAMEWORK", "default", "default"),
            ("NON_EXISTENT_SETTING", "xyz", "xyz"),
        ],
    )
    def test_get_cached_setting(self, settings, setting_name, default_value, expected):
        """Test that get_cached_setting returns correct values."""
        from django_tomselect.app_settings import get_cached_setting

        result = get_cached_setting(setting_name, default_value)
        assert result == expected

        # The cache key is stored in the _settings_cache dict
        assert django_tomselect.app_settings._settings_cache[setting_name] == expected

    @pytest.mark.parametrize(
        "debug_value,expected",
        [
            (True, False),
            (False, True),
        ],
    )
    def test_production_mode_detection(self, settings, debug_value, expected):
        """Test that production mode is correctly detected based on DEBUG setting."""
        settings.DEBUG = debug_value
        reload(django_tomselect.app_settings)
        assert django_tomselect.app_settings.currently_in_production_mode() == expected


@pytest.mark.django_db
class TestCSSFrameworkValidation:
    """Test CSS framework validation."""

    def setup_method(self):
        """Reset app settings before each test."""
        reload(django_tomselect.app_settings)

    @pytest.mark.parametrize(
        "framework,should_raise",
        [
            ("default", False),
            ("bootstrap4", False),
            ("bootstrap5", False),
            ("other_framework", True),
        ],
    )
    def test_css_framework_validation(self, settings, framework, should_raise):
        """Test that CSS framework validation works correctly for bootstrap versions.

        The "other_framework" value is used to test that the validation error is raised.
        """
        if should_raise:
            with pytest.raises(ValueError) as exc_info:
                settings.TOMSELECT_CSS_FRAMEWORK = framework
                reload(django_tomselect.app_settings)
            assert "must be one of the allowed values" in str(exc_info.value)
        else:
            settings.TOMSELECT_CSS_FRAMEWORK = framework
            reload(django_tomselect.app_settings)
            assert django_tomselect.app_settings.DJANGO_TOMSELECT_CSS_FRAMEWORK == framework

    def test_framework_defaults(self):
        """Test that framework defaults are set correctly when no settings provided."""
        settings = django_tomselect.app_settings
        assert settings.DJANGO_TOMSELECT_CSS_FRAMEWORK == "default"

    def test_settings_override_defaults(self):
        """Test that settings properly override defaults."""
        from django.conf import settings

        settings.TOMSELECT_CSS_FRAMEWORK = "bootstrap4"
        reload(django_tomselect.app_settings)
        assert django_tomselect.app_settings.DJANGO_TOMSELECT_CSS_FRAMEWORK == "bootstrap4"

    def test_invalid_bootstrap_version_at_runtime(self):
        """Test that invalid bootstrap version raises error even after initialization."""
        from django.conf import settings

        # First set valid values
        settings.TOMSELECT_CSS_FRAMEWORK = "bootstrap4"
        reload(django_tomselect.app_settings)

        # Then try to set invalid version
        with pytest.raises(ValueError) as exc_info:
            settings.TOMSELECT_CSS_FRAMEWORK = "x"
            reload(django_tomselect.app_settings)
        assert "must be one of the allowed values" in str(exc_info.value)


@pytest.mark.django_db
class TestMinificationSettings:
    """Test minification settings behavior."""

    def setup_method(self, method):
        """Reset app settings before each test and ensure valid bootstrap version."""
        from django.conf import settings

        # Clear the settings cache
        django_tomselect.app_settings._settings_cache = {}

        # Ensure valid bootstrap settings to avoid validation errors
        settings.TOMSELECT_CSS_FRAMEWORK = "bootstrap5"

        # Now safe to reload
        reload(django_tomselect.app_settings)

    def get_minification_value(self):
        """Helper method to get the actual minification value, handling callables."""
        minified = django_tomselect.app_settings.DJANGO_TOMSELECT_MINIFIED
        if callable(minified):
            return minified()
        return minified

    def test_default_minification_in_debug(self, settings):
        """Test default minification behavior in debug mode."""
        settings.DEBUG = True
        reload(django_tomselect.app_settings)
        assert not self.get_minification_value()

    def test_default_minification_in_production(self, settings):
        """Test default minification behavior in production mode."""
        settings.DEBUG = False
        reload(django_tomselect.app_settings)
        assert self.get_minification_value()

    def test_explicit_minification_setting(self, settings):
        """Test explicit minification setting."""
        settings.TOMSELECT_MINIFIED = True
        reload(django_tomselect.app_settings)
        assert self.get_minification_value()

        settings.TOMSELECT_MINIFIED = False
        reload(django_tomselect.app_settings)
        assert not self.get_minification_value()

    def test_minification_callable(self, settings):
        """Test that minification can be controlled by a callable."""

        def minify_true():
            return True

        settings.TOMSELECT_MINIFIED = minify_true
        reload(django_tomselect.app_settings)
        assert self.get_minification_value()

        def minify_false():
            return False

        settings.TOMSELECT_MINIFIED = minify_false
        reload(django_tomselect.app_settings)
        assert not self.get_minification_value()


@pytest.mark.django_db
class TestBasicModelOperations:
    """Test basic model operations to ensure fixtures work correctly."""

    def test_edition_str_representation(self, sample_edition):
        """Test the string representation of Edition model."""
        assert str(sample_edition) == "Test Edition"

    def test_magazine_str_representation(self, sample_magazine):
        """Test the string representation of Magazine model."""
        assert str(sample_magazine) == "Test Magazine"

    def test_edition_magazine_relationship(self, edition_with_magazine, sample_magazine):
        """Test the relationship between Edition and Magazine models."""
        from example_project.example.models import Edition

        assert Edition.objects.filter(magazine=sample_magazine).exists()
        assert edition_with_magazine in sample_magazine.edition_set.all()


@pytest.mark.django_db
class TestSearchQueryset:
    """Test the SearchQueryset functionality."""

    @pytest.mark.parametrize(
        "search_term,expected_count",
        [
            ("Test", 1),
            ("Edition", 2),
            ("Magazine", 1),
            ("NonExistent", 0),
        ],
    )
    def test_search_method(self, sample_edition, edition_with_magazine, search_term, expected_count):
        """Test the search method of SearchQueryset."""
        from example_project.example.models import Edition

        results = Edition.objects.search(search_term)
        assert results.count() == expected_count
