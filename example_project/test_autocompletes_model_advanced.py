"""Tests for advanced AutocompleteModelView features.

Covers permission handling and authorization, virtual/annotated field
handling, and the configurable JSON encoder (for both
``AutocompleteModelView`` and ``AutocompleteIterablesView``).
"""


import json
import logging

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder

from django_tomselect.autocompletes import AutocompleteIterablesView, AutocompleteModelView
from example_project.example.models import Edition


@pytest.mark.django_db
class TestAutocompleteModelViewPermissions:
    """Tests for AutocompleteModelView permissions handling."""

    class NoPermissionsView(AutocompleteModelView):
        """Test view with no permissions required."""

        model = Edition
        permission_required = None
        search_lookups = ["name__icontains"]

    class WithPermissionsView(AutocompleteModelView):
        """Test view with explicit permissions required."""

        model = Edition
        permission_required = ["example.view_edition"]
        search_lookups = ["name__icontains"]

    def test_no_permissions_required(self, mock_request):
        """Test that views with permission_required = None don't check permissions."""
        view = self.NoPermissionsView()
        view.setup(mock_request)

        # This should not raise PermissionDenied
        response = view.dispatch(mock_request)
        assert response.status_code == 200

    def test_explicit_permissions_required_with_permission(self, mock_request):
        """Test that views with explicit permissions work when user has permission."""
        view = self.WithPermissionsView()
        view.setup(mock_request)

        # Should not raise PermissionDenied since mock_request user has all permissions
        response = view.dispatch(mock_request)
        assert response.status_code == 200

    def test_explicit_permissions_required_without_permission(self, user):
        """Test that views with explicit permissions fail when user lacks permission."""

        class UnauthorizedRequest:
            """Mock request with unauthorized user."""

            def __init__(self, user):
                self.user = user
                self.method = "GET"
                self.GET = {}

            def get_full_path(self):
                return "/test/"

        request = UnauthorizedRequest(user)
        view = self.WithPermissionsView()
        view.setup(request)

        # Should raise PermissionDenied since user doesn't have permission
        with pytest.raises(PermissionDenied):
            view.dispatch(request)

    def test_get_permission_required_none(self, mock_request):
        """Test that get_permission_required returns empty list when permission_required is None."""
        view = self.NoPermissionsView()
        view.setup(mock_request)
        assert view.get_permission_required() == []

    def test_get_permission_required_list(self, mock_request):
        """Test that get_permission_required returns list for explicit permissions."""
        view = self.WithPermissionsView()
        view.setup(mock_request)
        assert view.get_permission_required() == ["example.view_edition"]

    def test_get_permission_required_string(self, mock_request):
        """Test that get_permission_required handles string permission."""

        class StringPermissionView(AutocompleteModelView):
            """Test view with string permission_required."""

            model = Edition
            permission_required = "example.view_edition"

        view = StringPermissionView()
        view.setup(mock_request)
        assert view.get_permission_required() == ["example.view_edition"]

    @pytest.mark.parametrize(
        "use_no_perm_view,allow_anonymous,skip_authorization",
        [
            (True, False, False),  # NoPermissionsView - no permissions required
            (False, True, False),  # WithPermissionsView with allow_anonymous=True
            (False, False, True),  # WithPermissionsView with skip_authorization=True
        ],
        ids=["no_permissions_required", "allow_anonymous", "skip_authorization"],
    )
    def test_has_permission_grants_access(
        self, mock_request, use_no_perm_view, allow_anonymous, skip_authorization
    ):
        """Test configurations that grant has_permission."""
        if use_no_perm_view:
            view = self.NoPermissionsView()
        else:
            view = self.WithPermissionsView()
            view.allow_anonymous = allow_anonymous
            view.skip_authorization = skip_authorization
        view.setup(mock_request)
        assert view.has_permission(mock_request) is True

    def test_unauthenticated_user(self):
        """Test that has_permission returns False for unauthenticated users."""

        class UnauthenticatedUser:
            """Mock user class for unauthenticated users."""

            id = 1
            is_authenticated = False

        class UnauthenticatedRequest:
            """Mock request class for unauthenticated requests."""

            def __init__(self):
                self.user = UnauthenticatedUser()
                self.method = "GET"
                self.GET = {}

            def get_full_path(self):
                """Mock method to get full path."""
                return "/test/"

        request = UnauthenticatedRequest()
        view = self.WithPermissionsView()
        view.setup(request)
        assert view.has_permission(request) is False

    def test_queryset_with_no_permissions(self, mock_request, editions):
        """Test that queryset is accessible when no permissions are required."""
        view = self.NoPermissionsView()
        view.setup(mock_request)
        queryset = view.get_queryset()
        assert queryset.count() == len(editions)

    def test_queryset_with_permissions(self, mock_request, editions):
        """Test that queryset is accessible with proper permissions."""
        view = self.WithPermissionsView()
        view.setup(mock_request)
        queryset = view.get_queryset()
        assert queryset.count() == len(editions)

    def test_has_permission_anonymous_user(self, rf):
        """Test permission handling for anonymous users."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)

        assert not view.has_permission(request)

    def test_has_permission_skip_authorization(self, rf):
        """Test permission handling when skip_authorization is True."""
        view = AutocompleteModelView()
        view.model = Edition
        view.skip_authorization = True
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)

        assert view.has_permission(request)

    def test_has_permission_allow_anonymous(self, rf):
        """Test permission handling when allow_anonymous is True."""
        view = AutocompleteModelView()
        view.model = Edition
        view.allow_anonymous = True
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)

        assert view.has_permission(request)

    @pytest.mark.parametrize(
        "permission_required",
        [
            "example.view_edition",
            ["example.view_edition", "example.add_edition"],
        ],
        ids=["string_format", "list_format"],
    )
    def test_permission_required_formats(self, rf, user, permission_required):
        """Test handling of string and list permission_required formats."""
        view = AutocompleteModelView()
        view.model = Edition
        view.permission_required = permission_required
        request = rf.get("")
        request.user = user
        view.setup(request)

        assert not view.has_permission(request)  # Should be False since user has no perms

    def test_permission_no_requirements(self, rf, user):
        """Test permission handling when no permissions are required."""
        view = AutocompleteModelView()
        view.model = Edition
        view.permission_required = []
        request = rf.get("")
        request.user = user
        view.setup(request)

        assert view.has_permission(request)

    def test_object_permission_default(self, rf, test_editions):
        """Test default object-level permission handling."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")

        assert view.has_object_permission(request, test_editions[0])

    def test_object_permission_custom_handler(self, rf, test_editions):
        """Test custom object-level permission handler."""

        class CustomView(AutocompleteModelView):
            """Custom view with custom object-level permission handler."""

            def has_view_permission(self, request, obj):
                """Custom permission handler."""
                return obj.year.startswith("202")

        view = CustomView()
        view.model = Edition
        request = rf.get("")

        assert view.has_object_permission(request, test_editions[0], "view")

    def test_dispatch_anonymous_redirects_to_login(self, rf):
        """Test dispatch redirects anonymous users to login page."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("/test/")
        request.user = AnonymousUser()
        view.setup(request)

        response = view.dispatch(request)
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")

    def test_dispatch_authenticated_no_perms_raises(self, rf, user):
        """Test dispatch raises PermissionDenied for authenticated user without permissions."""
        view = AutocompleteModelView()
        view.model = Edition
        view.permission_required = "example.view_edition"
        request = rf.get("")
        request.user = user
        view.setup(request)

        with pytest.raises(PermissionDenied):
            view.dispatch(request)

    def test_handle_no_permission_anonymous(self, rf):
        """Test handle_no_permission for anonymous users."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("/test/")
        request.user = AnonymousUser()
        view.setup(request)  # Add setup so view.user is set

        response = view.handle_no_permission(request)
        assert response.url.startswith("/accounts/login/")

    def test_add_permission_anonymous(self, rf):
        """Test add permission for anonymous users."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        request.user = AnonymousUser()
        view.setup(request)  # Add setup so view.user is set

        assert not view.has_add_permission(request)

    def test_add_permission_authenticated(self, rf, user):
        """Test add permission for authenticated users without permissions."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        request.user = user
        view.setup(request)  # Add setup so view.user is set

        assert not view.has_add_permission(request)

    def test_invalidate_permissions_user(self, rf, user):
        """Test invalidating permissions for specific user."""
        view = AutocompleteModelView()
        view.model = Edition

        # Should not raise any errors
        view.invalidate_permissions(user)

    def test_invalidate_permissions_all(self, rf):
        """Test invalidating all permissions."""
        view = AutocompleteModelView()
        view.model = Edition

        # Should not raise any errors
        view.invalidate_permissions()


@pytest.mark.django_db
class TestVirtualFields:
    """Tests for virtual fields functionality in AutocompleteModelView."""

    def test_init_subclass_creates_new_lists(self):
        """Test that __init_subclass__ creates a new value_fields list for each subclass."""
        # Create two subclasses with different value_fields
        class FirstAutocompleteView(AutocompleteModelView):
            model = Edition
            value_fields = ["id", "name"]

        class SecondAutocompleteView(AutocompleteModelView):
            model = Edition
            value_fields = ["id", "year"]

        # Modify the value_fields of one subclass
        FirstAutocompleteView.value_fields.append("pages")

        # Verify each class has its own value_fields list
        assert FirstAutocompleteView.value_fields == ["id", "name", "pages"]
        assert SecondAutocompleteView.value_fields == ["id", "year"]
        assert AutocompleteModelView.value_fields == []

    def test_ensure_label_field_does_not_mutate_view_class_state(self):
        """Regression: augmenting a missing label field must not mutate the view's
        class-level value_fields/virtual_fields in place.

        _ensure_label_field_in_view runs on a throwaway per-call view instance, but
        value_fields/virtual_fields are class attributes. Appending in place leaked
        into every other instance/request/test sharing the view class (an
        order-dependent failure). It must rebind to fresh, instance-scoped lists.
        """
        from django_tomselect.app_settings import TomSelectConfig
        from django_tomselect.widgets import TomSelectModelWidget

        class LabelAutocompleteView(AutocompleteModelView):
            model = Edition
            value_fields = ["id", "name"]

        original_value_fields = LabelAutocompleteView.value_fields
        original_virtual_fields = list(getattr(LabelAutocompleteView, "virtual_fields", []))

        # A non-column label (e.g. an annotated/computed display field) is not a
        # real database column. Dunders like "__str__" are rejected at config time,
        # so use a representative virtual label here.
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", value_field="id", label_field="display_name"),
        )
        widget.model = Edition
        view = LabelAutocompleteView()

        widget._ensure_label_field_in_view(view)

        # The shared class lists are untouched (the bug appended in place).
        assert LabelAutocompleteView.value_fields == ["id", "name"]
        assert LabelAutocompleteView.value_fields is original_value_fields
        assert list(getattr(LabelAutocompleteView, "virtual_fields", [])) == original_virtual_fields

        # The throwaway instance got the label, and the non-column field was routed
        # to virtual_fields so it is excluded from the .values() query.
        assert "display_name" in view.value_fields
        assert "display_name" in view.virtual_fields

    def test_dunder_label_set_on_widget_is_routed_to_virtual_fields(self):
        """Defense-in-depth: TomSelectConfig rejects dunder label_fields, but a dunder
        can still reach the widget by bypassing config validation (a subclass or caller
        setting widget.label_field directly). _ensure_label_field_in_view must route it
        to virtual_fields so it is excluded from .values() and never raises FieldError.
        """
        from django_tomselect.app_settings import TomSelectConfig
        from django_tomselect.widgets import TomSelectModelWidget

        class LabelAutocompleteView(AutocompleteModelView):
            model = Edition
            value_fields = ["id", "name"]

        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", value_field="id", label_field="name"),
        )
        widget.model = Edition
        # Bypass config validation the way a subclass/caller could.
        widget.label_field = "__str__"
        view = LabelAutocompleteView()

        widget._ensure_label_field_in_view(view)

        # Routed to virtual_fields and therefore excluded from the .values() field
        # list, so the query cannot raise FieldError on the non-column dunder.
        assert "__str__" in view.virtual_fields
        assert "__str__" not in view.get_value_fields()

    def test_virtual_fields_excluded_from_query(self, rf):
        """Test that virtual fields are excluded from database queries."""

        class CustomAutocompleteView(AutocompleteModelView):
            """Custom autocomplete view with virtual field."""
            model = Edition
            value_fields = ["id", "name", "display_name"]
            virtual_fields = ["display_name"]

            def hook_prepare_results(self, results):
                for result in results:
                    result["display_name"] = f"{result['name']} (Edition)"
                return results

        view = CustomAutocompleteView()
        request = rf.get("")
        view.setup(request)

        # This should not raise a FieldError, since display_name should be excluded from the query
        fields = view.get_value_fields()
        assert "display_name" not in fields
        assert set(fields) == {"id", "name"}

    def test_declared_virtual_fields_do_not_log_non_concrete_warning(self, rf, caplog):
        """Test that declared virtual fields do not produce setup warnings."""

        class CustomAutocompleteView(AutocompleteModelView):
            """Custom autocomplete view with an explicitly declared virtual field."""

            model = Edition
            value_fields = ["id", "name", "display_name"]
            virtual_fields = ["display_name"]

        view = CustomAutocompleteView()
        request = rf.get("")

        with caplog.at_level(logging.WARNING, logger="django_tomselect.autocompletes"):
            view.setup(request)

        messages = [record.getMessage() for record in caplog.records]
        assert all("not concrete database columns" not in message for message in messages)

    def test_unhandled_non_concrete_fields_warn_and_become_virtual(self, rf, caplog):
        """Test that undeclared non-concrete value fields still warn and auto-register."""

        class CustomAutocompleteView(AutocompleteModelView):
            """Custom autocomplete view with an undeclared virtual field."""

            model = Edition
            value_fields = ["id", "name", "display_name"]

        view = CustomAutocompleteView()
        request = rf.get("")

        with caplog.at_level(logging.WARNING, logger="django_tomselect.autocompletes"):
            view.setup(request)

        assert "display_name" in view.virtual_fields
        assert "value_fields ['display_name'] are not concrete database columns" in caplog.text

    def test_warning_lists_only_unhandled_non_concrete_fields(self, rf, caplog):
        """Test that setup warnings omit non-concrete fields already declared virtual."""

        class CustomAutocompleteView(AutocompleteModelView):
            """Custom autocomplete view with mixed declared and undeclared virtual fields."""

            model = Edition
            value_fields = ["id", "name", "display_name", "computed_label"]
            virtual_fields = ["display_name"]

        view = CustomAutocompleteView()
        request = rf.get("")

        with caplog.at_level(logging.WARNING, logger="django_tomselect.autocompletes"):
            view.setup(request)

        messages = [record.getMessage() for record in caplog.records]
        non_concrete_messages = [message for message in messages if "not concrete database columns" in message]
        assert len(non_concrete_messages) == 1
        assert "computed_label" in non_concrete_messages[0]
        assert "display_name" not in non_concrete_messages[0]
        assert view.virtual_fields == ["display_name", "computed_label"]

    def test_hook_prepare_results_with_virtual_field(self, rf, test_editions):
        """Test that hook_prepare_results can add virtual fields."""

        class CustomAutocompleteView(AutocompleteModelView):
            """Custom autocomplete view with virtual field."""
            model = Edition
            value_fields = ["id", "name", "year"]
            virtual_fields = ["combined"]

            def hook_prepare_results(self, results):
                for result in results:
                    result["combined"] = f"{result['name']} ({result['year']})"
                return results

        view = CustomAutocompleteView()
        request = rf.get("")
        view.setup(request)

        # Get the results directly from hook_prepare_results
        queryset = view.get_queryset()
        results = list(queryset.values(*view.get_value_fields()))
        modified_results = view.hook_prepare_results(results)

        # Check that the virtual field is added
        assert len(modified_results) > 0
        assert "combined" in modified_results[0]
        assert modified_results[0]["combined"] == f"{modified_results[0]['name']} ({modified_results[0]['year']})"

    def test_annotation_fields_included_in_values(self, rf, db):
        """Test that queryset annotations in value_fields are included in .values() even when auto-detected as virtual.

        Fields that aren't concrete model columns but ARE queryset annotations (added via hook_queryset)
        should be included in the .values() call so they appear in the results.
        """
        from django.db.models import F

        from example_project.example.models import Category

        parent = Category.objects.create(name="Science")
        child = Category.objects.create(name="Physics", parent=parent)

        class AnnotatedAutocompleteView(AutocompleteModelView):
            model = Category
            value_fields = ["id", "name", "parent_id", "parent_name"]
            skip_authorization = True

            def hook_queryset(self, queryset):
                return queryset.annotate(parent_name=F("parent__name"))

        view = AnnotatedAutocompleteView()
        request = rf.get("")
        view.setup(request)

        # parent_name should be auto-detected as non-concrete and moved to virtual_fields
        assert "parent_name" in view.virtual_fields

        # But prepare_results should still include it because it's a queryset annotation
        queryset = view.get_queryset()
        results = view.prepare_results(queryset)

        child_result = next(r for r in results if r["id"] == child.pk)
        assert child_result["parent_name"] == "Science"

        parent_result = next(r for r in results if r["id"] == parent.pk)
        assert parent_result["parent_name"] is None

    def test_annotation_fields_full_prepare_results_pipeline(self, rf, db):
        """Test the full pipeline with annotations through hook_prepare_results.

        Simulates the CategoryAutocompleteView pattern: annotations added in hook_queryset,
        listed in value_fields, and accessed in hook_prepare_results.
        """
        from django.db.models import F

        from example_project.example.models import Category

        parent = Category.objects.create(name="Technology")
        child = Category.objects.create(name="Software", parent=parent)

        class CategoryLikeAutocompleteView(AutocompleteModelView):
            model = Category
            value_fields = ["id", "name", "parent_id", "parent_name"]
            skip_authorization = True

            def hook_queryset(self, queryset):
                return queryset.annotate(parent_name=F("parent__name"))

            def hook_prepare_results(self, results):
                for item in results:
                    # This would raise KeyError before the fix if parent_name was excluded
                    if item["parent_name"]:
                        item["formatted_name"] = f"{item['parent_name']} >> {item['name']}"
                    else:
                        item["formatted_name"] = item["name"]
                return results

        view = CategoryLikeAutocompleteView()
        request = rf.get("")
        view.setup(request)

        queryset = view.get_queryset()
        results = view.prepare_results(queryset)

        child_result = next(r for r in results if r["id"] == child.pk)
        assert child_result["formatted_name"] == "Technology >> Software"
        assert child_result["parent_name"] == "Technology"

        parent_result = next(r for r in results if r["id"] == parent.pk)
        assert parent_result["formatted_name"] == "Technology"

    def test_true_virtual_fields_still_excluded(self, rf, test_editions):
        """Test that fields that are neither concrete nor annotations are still excluded from .values()."""

        class ViewWithTrueVirtual(AutocompleteModelView):
            model = Edition
            value_fields = ["id", "name", "computed_label"]
            virtual_fields = ["computed_label"]
            skip_authorization = True

            def hook_prepare_results(self, results):
                for result in results:
                    result["computed_label"] = f"Label: {result['name']}"
                return results

        view = ViewWithTrueVirtual()
        request = rf.get("")
        view.setup(request)

        # computed_label is not an annotation, so it should stay excluded from .values()
        fields = view.get_value_fields()
        assert "computed_label" not in fields

        # But prepare_results should still work (hook adds it manually)
        queryset = view.get_queryset()
        results = view.prepare_results(queryset)
        assert results[0]["computed_label"].startswith("Label: ")

    def test_category_autocomplete_view_returns_results(self, rf, db):
        """Integration test: the actual CategoryAutocompleteView returns results without errors."""
        from example_project.example.autocompletes import CategoryAutocompleteView
        from example_project.example.models import Category

        parent = Category.objects.create(name="Science")
        Category.objects.create(name="Physics", parent=parent)
        Category.objects.create(name="Chemistry", parent=parent)

        view = CategoryAutocompleteView()
        request = rf.get("", {"q": ""})
        view.setup(request)

        queryset = view.get_queryset()
        results = view.prepare_results(queryset)

        assert len(results) == 3
        # Verify hook_prepare_results ran successfully (it adds formatted_name)
        assert all("formatted_name" in r for r in results)
        # Verify annotation fields are present
        assert all("parent_name" in r for r in results)
        assert all("full_path" in r for r in results)
        assert all("direct_articles" in r for r in results)
        assert all("total_articles" in r for r in results)


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for testing."""

    def default(self, obj):
        """Custom serialization logic."""
        if hasattr(obj, "__str__"):
            return str(obj)
        return super().default(obj)


@pytest.mark.django_db
class TestAutocompleteModelViewJSONEncoder:
    """Tests for JSON encoder support in AutocompleteModelView."""

    def test_default_encoder_when_not_set(self, rf):
        """Test that get_json_encoder returns DjangoJSONEncoder by default."""
        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        view.setup(request)

        assert view.get_json_encoder() is DjangoJSONEncoder

    def test_view_level_encoder_class(self, rf):
        """Test that view-level json_encoder class attribute works."""

        class CustomView(AutocompleteModelView):
            """Custom view with custom JSON encoder."""
            model = Edition
            json_encoder = CustomJSONEncoder

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        encoder = view.get_json_encoder()
        assert encoder is CustomJSONEncoder

    def test_view_level_encoder_string(self, rf):
        """Test that view-level json_encoder as dotted string path works."""

        class CustomView(AutocompleteModelView):
            """Custom view with JSON encoder as string."""
            model = Edition
            json_encoder = "json.JSONEncoder"

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        encoder = view.get_json_encoder()
        assert encoder is json.JSONEncoder

    def test_invalid_encoder_string_falls_back(self, rf, caplog):
        """Test that invalid dotted string path falls back to DjangoJSONEncoder."""

        class CustomView(AutocompleteModelView):
            """Custom view with invalid JSON encoder string."""
            model = Edition
            json_encoder = "nonexistent.module.Encoder"

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        with caplog.at_level(logging.ERROR, logger="django_tomselect.autocompletes"):
            encoder = view.get_json_encoder()
        assert encoder is DjangoJSONEncoder
        assert "Could not import JSON encoder" in caplog.text

    def test_invalid_encoder_type_falls_back(self, rf, caplog):
        """Test that invalid encoder type falls back to DjangoJSONEncoder."""

        class CustomView(AutocompleteModelView):
            """Custom view with invalid JSON encoder type."""
            model = Edition
            json_encoder = "not a class"  # After import fails, this becomes a string

        # Set the encoder directly to a non-encoder class to bypass import
        view = AutocompleteModelView()
        view.model = Edition
        view.json_encoder = str  # str is a class but not a JSONEncoder
        request = rf.get("")
        view.setup(request)

        with caplog.at_level(logging.ERROR, logger="django_tomselect.autocompletes"):
            encoder = view.get_json_encoder()
        assert encoder is DjangoJSONEncoder
        assert "must be a subclass of json.JSONEncoder" in caplog.text

    def test_global_setting_used_when_view_not_set(self, rf, monkeypatch):
        """Test that global DEFAULT_JSON_ENCODER setting is used when view doesn't set one."""
        import django_tomselect.autocompletes as autocompletes_module

        # Mock the global setting
        monkeypatch.setattr(autocompletes_module, "DEFAULT_JSON_ENCODER", CustomJSONEncoder)

        view = AutocompleteModelView()
        view.model = Edition
        request = rf.get("")
        view.setup(request)

        encoder = view.get_json_encoder()
        assert encoder is CustomJSONEncoder

    def test_view_encoder_takes_precedence_over_global(self, rf, monkeypatch):
        """Test that view-level encoder takes precedence over global setting."""
        import django_tomselect.autocompletes as autocompletes_module

        class AnotherEncoder(json.JSONEncoder):
            """Another custom encoder for testing."""
            pass

        # Mock the global setting
        monkeypatch.setattr(autocompletes_module, "DEFAULT_JSON_ENCODER", AnotherEncoder)

        class CustomView(AutocompleteModelView):
            """Custom view with its own JSON encoder."""
            model = Edition
            json_encoder = CustomJSONEncoder

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        encoder = view.get_json_encoder()
        assert encoder is CustomJSONEncoder
        assert encoder is not AnotherEncoder

    def test_json_response_uses_encoder(self, rf, test_editions, user):
        """Test that JsonResponse actually uses the custom encoder."""

        class CustomView(AutocompleteModelView):
            """Custom view with custom JSON encoder."""
            model = Edition
            json_encoder = CustomJSONEncoder

        view = CustomView()
        request = rf.get("")
        request.user = user
        view.setup(request)

        response = view.get(request)
        assert response.status_code == 200

        # Verify response is valid JSON
        data = json.loads(response.content.decode("utf-8"))
        assert "results" in data


@pytest.mark.django_db
class TestAutocompleteIterablesViewJSONEncoder:
    """Tests for JSON encoder support in AutocompleteIterablesView."""

    def test_default_encoder_when_not_set(self, rf):
        """Test that get_json_encoder returns DjangoJSONEncoder by default."""

        class CustomView(AutocompleteIterablesView):
            """Custom view without JSON encoder."""
            iterable = [("a", "A"), ("b", "B")]

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        assert view.get_json_encoder() is DjangoJSONEncoder

    def test_view_level_encoder_class(self, rf):
        """Test that view-level json_encoder class attribute works."""

        class CustomView(AutocompleteIterablesView):
            """Custom view with custom JSON encoder."""
            iterable = [("a", "A"), ("b", "B")]
            json_encoder = CustomJSONEncoder

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        encoder = view.get_json_encoder()
        assert encoder is CustomJSONEncoder

    def test_view_level_encoder_string(self, rf):
        """Test that view-level json_encoder as dotted string path works."""

        class CustomView(AutocompleteIterablesView):
            """Custom view with JSON encoder as string."""
            iterable = [("a", "A"), ("b", "B")]
            json_encoder = "json.JSONEncoder"

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        encoder = view.get_json_encoder()
        assert encoder is json.JSONEncoder

    def test_invalid_encoder_string_falls_back(self, rf, caplog):
        """Test that invalid dotted string path falls back to DjangoJSONEncoder."""

        class CustomView(AutocompleteIterablesView):
            """Custom view with invalid JSON encoder string."""
            iterable = [("a", "A"), ("b", "B")]
            json_encoder = "nonexistent.module.Encoder"

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        with caplog.at_level(logging.ERROR, logger="django_tomselect.autocompletes"):
            encoder = view.get_json_encoder()
        assert encoder is DjangoJSONEncoder
        assert "Could not import JSON encoder" in caplog.text

    def test_global_setting_used_when_view_not_set(self, rf, monkeypatch):
        """Test that global DEFAULT_JSON_ENCODER setting is used when view doesn't set one."""
        import django_tomselect.autocompletes as autocompletes_module

        # Mock the global setting
        monkeypatch.setattr(autocompletes_module, "DEFAULT_JSON_ENCODER", CustomJSONEncoder)

        class CustomView(AutocompleteIterablesView):
            """Custom view without JSON encoder."""
            iterable = [("a", "A"), ("b", "B")]

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        encoder = view.get_json_encoder()
        assert encoder is CustomJSONEncoder

    def test_json_response_uses_encoder(self, rf):
        """Test that JsonResponse actually uses the custom encoder."""

        class CustomView(AutocompleteIterablesView):
            """Custom view with custom JSON encoder."""
            iterable = [("a", "A"), ("b", "B")]
            json_encoder = CustomJSONEncoder

        view = CustomView()
        request = rf.get("")
        view.setup(request)

        response = view.get(request)
        assert response.status_code == 200

        # Verify response is valid JSON
        data = json.loads(response.content.decode("utf-8"))
        assert "results" in data
