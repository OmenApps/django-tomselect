"""Tests for TomSelect widget request handling, permissions, formset prefix support, and accessibility attributes."""

import pytest
from django.core.cache import cache

from django_tomselect.app_settings import (
    PluginDropdownHeader,
    TomSelectConfig,
)
from django_tomselect.cache import permission_cache
from django_tomselect.widgets import TomSelectModelWidget
from example_project.example.models import Edition


@pytest.mark.django_db
class TestWidgetRequestHandlingAndUpdates:
    """Test request handling, field changes and updates in TomSelect widgets."""

    @pytest.fixture
    def setup_widget(self):
        """Create properly initialized widget."""

        def _create_widget(config=None):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectModelWidget(config=config)
            return widget

        return _create_widget

    def test_validate_request_missing_attributes(self, setup_widget):
        """Test request validation with missing attributes."""
        widget = setup_widget()

        class InvalidRequest:
            """Mock request missing required attributes."""

        assert not widget.validate_request(InvalidRequest())

    def test_validate_request_missing_user_auth(self, setup_widget):
        """Test request validation with missing user authentication."""
        widget = setup_widget()

        class PartialRequest:
            """Mock request with incomplete user attributes."""

            method = "GET"
            GET = {}
            user = type("MockUser", (), {})()

            def get_full_path(self):
                """Mock get_full_path method."""
                return "/test/"

        assert not widget.validate_request(PartialRequest())

    def test_validate_request_valid(self, setup_widget):
        """Test request validation with valid request object."""
        widget = setup_widget()

        class ValidRequest:
            """Mock request with all required attributes."""

            method = "GET"
            GET = {}

            class User:
                """Mock user object."""

                is_authenticated = True

            user = User()

            def get_full_path(self):
                """Mock get_full_path method."""
                return "/test/"

        assert widget.validate_request(ValidRequest())

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_full_path",
        ],
    )
    def test_validate_request_missing_methods(self, setup_widget, method_name):
        """Test request validation with missing required methods."""
        widget = setup_widget()

        class RequestMissingMethod:
            """Mock request missing specific methods."""

            method = "GET"
            GET = {}

            class User:
                """Mock user object."""

                is_authenticated = True

            user = User()

        # Add all methods except the one we're testing
        for m in ["get_full_path"]:
            if m != method_name:
                setattr(RequestMissingMethod, m, lambda self: None)

        request = RequestMissingMethod()
        assert not widget.validate_request(request)

    @pytest.mark.parametrize(
        "field,lookup",
        [
            ("magazine", "id"),
            ("category", "parent_id"),
            ("author", "user_id"),
        ],
    )
    def test_filter_by_context_various_fields(self, setup_widget, field, lookup):
        """Test context generation with different filter_by configurations."""
        config = TomSelectConfig(url="autocomplete-edition", filter_by=(field, lookup))
        widget = setup_widget(config)
        context = widget.get_context("test", None, {})

        assert context["widget"]["dependent_field"] == field
        assert context["widget"]["dependent_field_lookup"] == lookup

    def test_get_label_nonexistent_prepare_method(self, setup_widget, sample_edition):
        """Test get_label_for_object when prepare method doesn't exist."""
        widget = setup_widget()
        widget.label_field = "custom_label"

        class MockView:
            """Mock view without prepare method."""

        label = widget.get_label_for_object(sample_edition, MockView())
        assert label == str(sample_edition)

    def test_get_context_without_request(self, setup_widget):
        """Test context generation when no request is available."""
        widget = setup_widget()
        widget.get_current_request = lambda: None
        context = widget.get_context("test", None, {})

        # Should still have basic context without permission-specific data
        assert "widget" in context
        assert "autocomplete_url" in context["widget"]
        assert "plugins" in context["widget"]

    @pytest.mark.parametrize("permission_result", [True, False])
    def test_model_url_context_with_permissions(self, setup_widget, permission_result, monkeypatch):
        """Test URL context generation with different permission results."""
        config = TomSelectConfig(url="autocomplete-edition", show_list=True, show_create=True)
        widget = setup_widget(config)

        def mock_reverse(*args, **kwargs):
            return "/test-url/"

        monkeypatch.setattr("django_tomselect.widgets.safe_reverse", mock_reverse)

        class MockRequest:
            """Mock request for permission checks."""

            user = type("User", (), {"is_authenticated": True})()
            method = "GET"
            GET = {}

            def get_full_path(self):
                """Mock get_full_path method."""
                return "/test/"

        class MockView:
            """Mock view with configurable permissions."""

            list_url = "test-list"
            create_url = "test-create"

            def has_permission(self, request, action):
                """Mock has_permission method."""
                return permission_result

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

        widget.get_current_request = lambda: MockRequest()
        context = widget.get_model_url_context(MockView())

        if permission_result:
            assert context["view_list_url"] == "/test-url/"
            assert context["view_create_url"] == "/test-url/"
        else:
            assert context["view_list_url"] is None
            assert context["view_create_url"] is None


@pytest.mark.django_db
class TestWidgetPermissionsAndURLs:
    """Test permission checks and URL generation in TomSelect widgets."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with authentication."""

        class MockRequest:
            """Mock request with authentication."""

            class User:
                """Mock user object."""

                is_authenticated = True

                def has_perms(self, perms):
                    """Mock has_perms method."""
                    return True

            user = User()
            method = "GET"
            GET = {}

            def get_full_path(self):
                """Mock get_full_path method."""
                return "/test/"

        return MockRequest()

    @pytest.fixture
    def setup_widget(self, mock_request):
        """Create widget with permission configuration."""

        def _create_widget(config=None, **kwargs):
            if config is None:
                config = TomSelectConfig(url="autocomplete-edition")
            widget = TomSelectModelWidget(config=config, **kwargs)
            widget.get_current_request = lambda: mock_request
            return widget

        return _create_widget

    @pytest.mark.parametrize(
        "permission_config",
        [
            {"skip_authorization": True},
            {"allow_anonymous": True},
        ],
    )
    def test_permission_overrides(self, setup_widget, mock_request, permission_config):
        """Test permission override configurations."""
        widget = setup_widget(None, **permission_config)

        class MockView:
            """Mock view with configurable permissions."""

            def has_permission(self, request, action):
                """Mock has_permission method."""
                # Should return True because of overrides
                return (
                    True
                    if permission_config.get("skip_authorization") or permission_config.get("allow_anonymous")
                    else False
                )

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

        mock_view = MockView()
        mock_view.skip_authorization = permission_config.get("skip_authorization", False)
        mock_view.allow_anonymous = permission_config.get("allow_anonymous", False)

        context = widget.get_permissions_context(mock_view)
        assert any(context.values()), "At least one permission should be True"


@pytest.mark.django_db
class TestWidgetValidationAndPermissions:
    """Test validation and permission handling."""

    def test_get_instance_url_context_no_urls(self, sample_edition):
        """Test instance URL context when no URLs are configured."""
        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))

        class MockView:
            """Mock view with no URLs."""

            detail_url = None
            update_url = None
            delete_url = None

            def has_permission(self, request, action):
                """Mock has_permission method."""
                return True

        urls = widget.get_instance_url_context(sample_edition, MockView())
        assert not urls

    def test_get_instance_url_context_2arg_override_compatibility(self, sample_edition):
        """Regression: subclass overrides using the documented 2-arg signature must work.

        `get_instance_url_context(self, obj, autocomplete_view)` is part of the public
        widget API (indexed in the Sphinx docs). Framework call sites must not pass
        extra positional/keyword arguments to it - the cached-permissions hot path uses
        `_compute_instance_url_context` instead so subclass overrides keep working.
        """
        import inspect

        from django_tomselect import widgets as widgets_module

        # Pin the public method signature so framework changes cannot quietly add
        # extra parameters that would break downstream subclass overrides.
        sig = inspect.signature(TomSelectModelWidget.get_instance_url_context)
        param_names = [p for p in sig.parameters if p != "self"]
        assert param_names == ["obj", "autocomplete_view"], (
            f"Public hook signature changed - downstream overrides will break. Got: {param_names}"
        )

        # Pin call sites: every framework call to .get_instance_url_context must pass
        # at most 2 positional args (plus self). The cached-permissions path must use
        # _compute_instance_url_context instead.
        source = inspect.getsource(widgets_module)
        # Strip the method definitions themselves so we only inspect call sites.
        call_sites = [
            line
            for line in source.splitlines()
            if "get_instance_url_context(" in line and "def get_instance_url_context" not in line
        ]
        for line in call_sites:
            assert "cached_permissions" not in line, (
                f"Framework call site passes cached_permissions to public hook: {line!r}"
            )

        # End-to-end behavior check: strict 2-arg override must work via the public hook.
        class OverriddenWidget(TomSelectModelWidget):
            """Widget overriding the public hook with the original 2-arg signature."""

            override_calls: list = []

            def get_instance_url_context(self, obj, autocomplete_view):
                """Strict 2-arg override - calling with extra args would TypeError."""
                OverriddenWidget.override_calls.append((obj, autocomplete_view))
                return {"detail_url": "/custom-detail/"}

        class MockView:
            """Mock view with no URLs."""

            detail_url = None
            update_url = None
            delete_url = None

            def has_permission(self, request, action):
                """Mock has_permission method."""
                return True

        widget = OverriddenWidget(config=TomSelectConfig(url="autocomplete-edition"))
        OverriddenWidget.override_calls = []
        result = widget.get_instance_url_context(sample_edition, MockView())
        assert result == {"detail_url": "/custom-detail/"}
        assert len(OverriddenWidget.override_calls) == 1

    @pytest.mark.parametrize("has_get_full_path", [True, False])
    def test_validate_request_get_full_path(self, has_get_full_path):
        """Test request validation with and without get_full_path method."""
        widget = TomSelectModelWidget()

        class MockRequest:
            """Mock request with or without get_full_path method."""

            method = "GET"
            GET = {}

            class User:
                """Mock user object."""

                is_authenticated = True

            user = User()

        if has_get_full_path:
            MockRequest.get_full_path = lambda self: "/test/"

        request = MockRequest()
        assert widget.validate_request(request) == has_get_full_path

    def test_field_permission_caching(self, mock_request):
        """Test that permissions are properly cached."""
        # Set up caching
        permission_cache.cache = cache
        permission_cache.enabled = True
        permission_cache.timeout = 300
        cache.clear()

        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))

        class MockView:
            """Mock view with permission caching."""

            model = Edition

            def has_permission(self, request, action):
                """Mock has_permission method."""
                return True

            def get_queryset(self):
                """Return all editions."""
                return Edition.objects.all()

            def get_permission_required(self):
                """Return required permissions."""
                return ["view_edition"]

        view = MockView()

        # Set the request on the view
        view.request = mock_request
        widget.request = mock_request

        # First call should cache the permission
        context = widget.get_permissions_context(view)
        assert context["can_view"] is True

        # Set the permission directly using the permission_cache method
        permission_cache.set_permission(user_id=mock_request.user.id, model_name="edition", action="view", value=True)

        # Verify permission was cached correctly
        assert (
            permission_cache.get_permission(user_id=mock_request.user.id, model_name="edition", action="view") is True
        )


@pytest.mark.django_db
class TestWidgetRequestValidation:
    """Test request validation scenarios."""

    class MockUser:
        """Mock user for testing."""

        is_authenticated = True

        def has_perms(self, perms):
            """Mock has_perms method."""
            return True

    class BaseMockRequest:
        """Base request class for testing."""

        _method = "GET"
        _get = {}
        _user = None

        @property
        def method(self):
            """Mock method property."""
            return self._method

        @property
        def GET(self):  # noqa: N802
            """Mock GET property."""
            return self._get

        @property
        def user(self):
            """Mock user property."""
            return self._user

        def get_full_path(self):
            """Mock get_full_path method."""
            return "/test/"

    def create_mock_request(self, include_method=True, include_get=True, include_user=True):
        """Create a mock request with specified attributes."""

        class TestRequest(self.BaseMockRequest):
            """Test request class with optional attributes."""

        request = TestRequest()
        if include_user:
            request._user = self.MockUser()
        if include_method:
            request._method = "GET"
        if include_get:
            request._get = {}
        return request

    def test_validate_request_missing_user(self):
        """Test request validation when user attribute is missing."""
        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))
        request = self.create_mock_request(include_user=False)
        assert not widget.validate_request(request)


@pytest.mark.django_db
class TestWidgetFormsetPrefixSupport:
    """Test that widgets correctly handle formset prefixes for dependent/exclude fields.

    This tests the fix for GitHub issue where filter_by and exclude_by fields
    don't work correctly in formsets because the JavaScript was looking for
    element IDs without the formset prefix (e.g., looking for 'id_magazine'
    instead of 'id_formset-0-magazine').
    """

    @pytest.fixture
    def widget_with_filter_by(self):
        """Create widget with filter_by configuration."""
        return TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                filter_by=("magazine", "magazine_id"),
            )
        )

    @pytest.fixture
    def widget_with_exclude_by(self):
        """Create widget with exclude_by configuration."""
        return TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                exclude_by=("category", "category_id"),
            )
        )

    @pytest.fixture
    def widget_with_both_filter_and_exclude(self):
        """Create widget with both filter_by and exclude_by configuration."""
        return TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                filter_by=("magazine", "magazine_id"),
                exclude_by=("category", "category_id"),
            )
        )

    def test_widget_name_passed_to_context(self, widget_with_filter_by):
        """Test that widget name is available in context for prefix extraction."""
        # When rendering with a formset prefix, the name would be like 'formset-0-edition'
        context = widget_with_filter_by.get_context("formset-0-edition", None, {})
        assert context["widget"]["name"] == "formset-0-edition"

    def test_formset_prefix_extraction_logic(self, widget_with_filter_by):
        """Test that the prefix can be extracted from formset field names."""
        # Simulate formset field names and verify prefix extraction logic
        test_cases = [
            ("formset-0-edition", "formset-0-"),  # Standard formset format
            ("edition-0-child", "edition-0-"),    # Different prefix
            ("myform-5-field", "myform-5-"),      # Higher index
            ("field", ""),                         # No formset prefix
            ("simple-name", ""),                   # Simple name with dash but no number
        ]

        for name, expected_prefix in test_cases:
            last_dash = name.rfind("-")
            if last_dash != -1:
                prefix = name[:last_dash + 1]
                # Check if it looks like a formset prefix (contains -N-)
                import re
                if re.search(r'-\d+-$', prefix):
                    extracted_prefix = prefix
                else:
                    extracted_prefix = ""
            else:
                extracted_prefix = ""

            assert extracted_prefix == expected_prefix, (
                f"For name {name!r}, expected prefix {expected_prefix!r}, got {extracted_prefix!r}"
            )

    def test_filter_config_in_context(self, widget_with_filter_by):
        """Test that filterConfig is properly structured for JavaScript use."""
        context = widget_with_filter_by.get_context("formset-0-edition", None, {})

        # The dependent_field and dependent_field_lookup should be set
        assert context["widget"]["dependent_field"] == "magazine"
        assert context["widget"]["dependent_field_lookup"] == "magazine_id"

    def test_exclude_config_in_context(self, widget_with_exclude_by):
        """Test that exclude configuration is properly structured."""
        context = widget_with_exclude_by.get_context("formset-0-edition", None, {})

        assert context["widget"]["exclude_field"] == "category"
        assert context["widget"]["exclude_field_lookup"] == "category_id"

    def test_both_filter_and_exclude_in_context(self, widget_with_both_filter_and_exclude):
        """Test that both filter and exclude configurations work together."""
        context = widget_with_both_filter_and_exclude.get_context("formset-0-edition", None, {})

        assert context["widget"]["dependent_field"] == "magazine"
        assert context["widget"]["dependent_field_lookup"] == "magazine_id"
        assert context["widget"]["exclude_field"] == "category"
        assert context["widget"]["exclude_field_lookup"] == "category_id"

    def test_rendered_javascript_contains_form_prefix_extraction(self, widget_with_filter_by):
        """Test that rendered HTML includes form prefix extraction JavaScript."""
        # Render the widget to check the generated JavaScript
        html = widget_with_filter_by.render("formset-0-edition", None, attrs={"id": "id_formset-0-edition"})

        # The rendered JavaScript should include logic to extract form prefix
        assert "formset-0-edition" in html
        # Check for the prefix extraction code
        assert "lastDashIndex" in html or "formPrefix" in html

    def test_rendered_javascript_uses_prefix_for_filter_field(self, widget_with_filter_by):
        """Test that rendered JavaScript uses prefix when looking up filter field."""
        html = widget_with_filter_by.render("formset-0-edition", None, attrs={"id": "id_formset-0-edition"})

        # The JavaScript should include code that prepends the form prefix to the dependent field ID
        # Check that the filterConfig is present and references the dependent field
        assert "magazine" in html
        assert "magazine_id" in html

    def test_widget_in_formset_context(self):
        """Test widget behavior when used within a Django formset."""
        from django import forms
        from django.forms import formset_factory
        from django_tomselect.forms import TomSelectModelChoiceField

        class TestForm(forms.Form):
            parent = TomSelectModelChoiceField(
                config=TomSelectConfig(
                    url="autocomplete-magazine",
                    value_field="id",
                    label_field="name",
                )
            )
            child = TomSelectModelChoiceField(
                config=TomSelectConfig(
                    url="autocomplete-edition",
                    value_field="id",
                    label_field="name",
                    filter_by=("parent", "parent_id"),
                )
            )

        TestFormset = formset_factory(TestForm, extra=2)  # noqa: N806
        formset = TestFormset(prefix="myform")

        # Check that the forms in the formset have correct name prefixes
        for i, form in enumerate(formset.forms):
            parent_name = form["parent"].html_name
            child_name = form["child"].html_name

            assert parent_name == f"myform-{i}-parent"
            assert child_name == f"myform-{i}-child"

            # Render the child widget and verify it has the filter configuration
            child_html = form["child"].as_widget()
            assert "parent" in child_html  # dependent_field should reference parent
            assert "parent_id" in child_html  # dependent_field_lookup

    def test_rendered_javascript_emits_levels_up_per_filter(self):
        """Widget with FilterSpec(..., levels_up=1) must render levelsUp:1 in JS.

        Rendered output is consumed by the JS-side createFirstUrlFunction's
        runtime prefix truncation. If this drops to 0 (the default), cross-level
        filters silently stop applying their filter values.
        """
        from django_tomselect.app_settings import FilterSpec

        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                filter_by=FilterSpec(source="customer", lookup="id", levels_up=1),
            )
        )
        html = widget.render(
            "orders-0-items-0-product",
            None,
            attrs={"id": "id_orders-0-items-0-product"},
        )
        # filterConfig.filters[].levelsUp must reach the rendered template.
        assert "levelsUp: 1" in html
        # filterFields builder uses the render-time levels_up literal.
        assert "window.djangoTomSelect.truncatePrefix(formPrefix, 1)" in html

    def test_rendered_javascript_default_levels_up_zero(self):
        """Default config (no levels_up) renders levelsUp:0.

        Regression guard: ensures the ``|default:0`` filter is wired and that
        zero-valued levels_up survives JSON-ish template rendering.
        """
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                filter_by=("magazine", "magazine_id"),
            )
        )
        html = widget.render("edition", None, attrs={"id": "id_edition"})
        assert "levelsUp: 0" in html

    def test_multiple_filters_with_formset_prefix(self):
        """Test widget with multiple filters works correctly with formset prefix."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                filter_by=[
                    ("magazine", "magazine_id"),
                    ("year", "year"),
                ],
            )
        )
        context = widget.get_context("formset-0-edition", None, {})

        # Should have filters array
        assert "filters" in context["widget"]
        filters = context["widget"]["filters"]
        assert len(filters) == 2
        assert filters[0]["source"] == "magazine"
        assert filters[0]["lookup"] == "magazine_id"
        assert filters[1]["source"] == "year"
        assert filters[1]["lookup"] == "year"

    def test_multiple_excludes_with_formset_prefix(self):
        """Test widget with multiple excludes works correctly with formset prefix."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                exclude_by=[
                    ("category", "category_id"),
                    ("status", "status"),
                ],
            )
        )
        context = widget.get_context("formset-0-edition", None, {})

        # Should have excludes array
        assert "excludes" in context["widget"]
        excludes = context["widget"]["excludes"]
        assert len(excludes) == 2
        assert excludes[0]["source"] == "category"
        assert excludes[0]["lookup"] == "category_id"
        assert excludes[1]["source"] == "status"
        assert excludes[1]["lookup"] == "status"


@pytest.mark.django_db
class TestAccessibilityAttributes:
    """Tests for ARIA and accessibility attributes (Fixes 5-10)."""

    def create_widget(self, config=None):
        """Helper to create a TomSelectModelWidget."""
        if config is None:
            config = TomSelectConfig(url="autocomplete-edition")
        return TomSelectModelWidget(config=config)

    # Fix 5: aria-describedby
    def test_build_attrs_auto_sets_aria_describedby(self):
        """Test that build_attrs auto-sets aria-describedby for help text association."""
        widget = self.create_widget()
        attrs = widget.build_attrs({"id": "id_my_field"})
        assert attrs["aria-describedby"] == "id_my_field_helptext"

    def test_build_attrs_preserves_explicit_aria_describedby(self):
        """Test that an explicitly set aria-describedby is not overridden."""
        widget = self.create_widget()
        attrs = widget.build_attrs({"id": "id_my_field", "aria-describedby": "custom_help"})
        assert attrs["aria-describedby"] == "custom_help"

    def test_build_attrs_no_aria_describedby_without_id(self):
        """Test that aria-describedby is not set when widget has no id."""
        widget = self.create_widget()
        attrs = widget.build_attrs({})
        assert "aria-describedby" not in attrs or attrs.get("aria-describedby", "") == ""

    # Fix 6: aria-required
    def test_render_aria_required_when_required(self):
        """Test that aria-required='true' is rendered when widget is required."""
        widget = self.create_widget()
        widget.is_required = True
        rendered = widget.render("test_field", None)
        assert 'aria-required="true"' in rendered

    def test_render_no_aria_required_when_optional(self):
        """Test that aria-required is NOT rendered when widget is optional."""
        widget = self.create_widget()
        widget.is_required = False
        rendered = widget.render("test_field", None)
        assert 'aria-required="true"' not in rendered

    # Fix 7: dynamic aria-label
    def test_context_has_dynamic_aria_label(self):
        """Test that _create_base_context generates aria_label from field name."""
        widget = self.create_widget()
        context = widget.get_context("category_type", None, {})
        assert context["widget"]["aria_label"] == "Category Type"

    def test_context_aria_label_replaces_hyphens(self):
        """Test that hyphens in field name are replaced with spaces and title-cased."""
        widget = self.create_widget()
        context = widget.get_context("my-field-name", None, {})
        assert context["widget"]["aria_label"] == "My Field Name"

    def test_render_dynamic_aria_label_in_html(self):
        """Test that rendered HTML contains the dynamic aria-label."""
        widget = self.create_widget()
        rendered = widget.render("category_type", None)
        assert "Select Category Type" in rendered

    # Fix 8: role="alert" on error div
    def test_render_error_div_has_alert_role(self):
        """Test that the error message div has role='alert' and aria-live='assertive'."""
        widget = self.create_widget()
        rendered = widget.render("test_field", None)
        assert 'role="alert"' in rendered
        assert 'aria-live="assertive"' in rendered

    # Fix 9: live region for selection announcements
    def test_render_has_sr_status_span(self):
        """Test that rendered HTML includes the screen reader status span."""
        widget = self.create_widget()
        rendered = widget.render("test_field", None)
        assert 'id="test_field_sr_status"' in rendered
        assert 'role="status"' in rendered
        assert 'aria-live="polite"' in rendered

    def test_render_has_on_item_add_callback(self):
        """Test that rendered HTML includes onItemAdd callback for SR announcements."""
        widget = self.create_widget()
        rendered = widget.render("test_field", None)
        assert "onItemAdd" in rendered
        assert "test_field_sr_status" in rendered

    def test_render_has_on_item_remove_callback(self):
        """Test that rendered HTML includes onItemRemove callback for SR announcements."""
        widget = self.create_widget()
        rendered = widget.render("test_field", None)
        assert "onItemRemove" in rendered

    # Fix 10: role="presentation" in tabular mode
    def test_tabular_dropdown_header_uses_presentation_role(self):
        """Test that tabular dropdown header uses role='presentation' instead of 'columnheader'."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                show_value_field=True,
                extra_columns={"year": "Year"},
            ),
        )
        widget = self.create_widget(config=config)
        rendered = widget.render("test_field", None)
        assert 'role="columnheader"' not in rendered
        assert 'role="presentation"' in rendered

    def test_tabular_option_uses_presentation_role(self):
        """Test that tabular option columns use role='presentation' instead of 'gridcell'."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                show_value_field=True,
                extra_columns={"year": "Year"},
            ),
        )
        widget = self.create_widget(config=config)
        rendered = widget.render("test_field", None)
        assert 'role="gridcell"' not in rendered

    def test_tabular_option_no_row_role(self):
        """Test that tabular option wrapper does not have role='row'."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                show_value_field=True,
                extra_columns={"year": "Year"},
            ),
        )
        widget = self.create_widget(config=config)
        rendered = widget.render("test_field", None)
        # role="row" should not appear in option template
        # (it was removed from the tabular option wrapper div)
        assert 'role="row"' not in rendered
