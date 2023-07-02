import json
from unittest.mock import Mock, patch
from urllib.parse import quote, urlencode

import pytest
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import Permission
from django.db.models.sql.where import NothingNode
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.test import Client
from django.urls import reverse
from testapp.models import Edition

from django_tomselect.views import (
    FILTERBY_VAR,
    PAGE_SIZE,
    PAGE_VAR,
    SEARCH_LOOKUP_VAR,
    SEARCH_VAR,
    VALUES_VAR,
    AutocompleteView,
)


@pytest.fixture
def obj():
    return Edition.objects.create(name="Test", pages="1", pub_num="2", year="3")


@pytest.fixture(autouse=True)
def not_found():
    # Add a 'control' object that should never be included in the search results.
    return Edition.objects.create(name="Not Found")


@pytest.fixture
def pages():
    # Create enough data for multiple pages.
    return [
        Edition.objects.create(name=f"2022-{i + 1:02}", pages=i + 1, pub_num=100 + i, year="2022")
        for i in range(PAGE_SIZE * 2)
    ]


@pytest.fixture
def perms_user():
    # Create a user that has 'add' permission for model Edition
    user = get_user_model().objects.create_user(username="perms", password="foo")
    user.user_permissions.add(Permission.objects.get(codename=get_permission_codename("add", Edition._meta)))
    return user


@pytest.fixture
def noperms_user():
    return get_user_model().objects.create_user(username="noperms", password="bar")


@pytest.mark.django_db
class TestAutocompleteView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("autocomplete")
        self.model_label = f"{Edition._meta.app_label}.{Edition._meta.model_name}"

    def test_get_contains_result(self, admin_client, obj):
        """The response of a search query should contain the expected result."""
        query_string = urlencode(
            {"model": self.model_label, SEARCH_VAR: "test", SEARCH_LOOKUP_VAR: '["name__icontains"]'}
        )
        response = admin_client.get(f"{self.url}?{query_string}")
        data = json.loads(response.content)
        assert data["results"] == list(Edition.objects.filter(pk=obj.pk).values())

    @pytest.mark.parametrize("page_number,has_more", [(1, True), (2, False)])
    def test_context_pagination(self, admin_client, pages, page_number, has_more):
        """
        The response of a search query should contain context items for
        pagination.
        """
        request_data = {
            "model": self.model_label,
            SEARCH_VAR: "2022",
            PAGE_VAR: str(page_number),
            SEARCH_LOOKUP_VAR: '["name__icontains"]',
        }
        response = admin_client.get(self.url, data=request_data)
        data = json.loads(response.content)
        assert data["page"] == page_number
        assert data["has_more"] == has_more

    def test_post_creates_new_object(self, admin_client):
        """A successful POST request should create a new model object."""
        request_data = {"model": self.model_label, "name": "New Edition", "create-field": "name"}
        response = admin_client.post(self.url, data=request_data)
        assert response.status_code == 200
        assert Edition.objects.filter(name="New Edition").exists()

    def test_post_context_contains_object_data(self, admin_client):
        """
        The context of a successful POST request should contain data about the
        created item.
        """
        request_data = {
            "model": self.model_label,
            "name": "New Edition",
            "create-field": "name",
        }
        response = admin_client.post(self.url, data=request_data)
        new = Edition.objects.get(name="New Edition")
        data = json.loads(response.content)
        assert data["pk"] == new.pk
        assert data["text"] == str(new)

    def test_post_no_permission(self, client, noperms_user):
        """
        Users that do not have 'add' permission should have the POST request
        denied.
        """
        client.force_login(noperms_user)
        response = client.post(self.url, data={"model": self.model_label})
        assert isinstance(response, HttpResponseForbidden)

    def test_post_user_not_authenticated(self, client):
        """POST requests by unauthenticated users should be denied."""
        client.logout()
        response = client.post(self.url, data={"model": self.model_label})
        assert isinstance(response, HttpResponseForbidden)

    def test_post_create_field_data_missing(self, admin_client):
        """
        POST requests that do not provide a value for the 'create field' should
        be denied.
        """
        request_data = {
            "model": self.model_label,
            # 'name' is missing
            "create-field": "name",
        }
        response = admin_client.post(self.url, data=request_data)
        assert isinstance(response, HttpResponseBadRequest)

    @pytest.mark.parametrize("has_csrf_token", (True, False))
    def test_post_csrf(self, admin_user, has_csrf_token):
        """Assert that requests without a CSRF token are denied."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(admin_user)
        client.get(reverse("csrf"))  # have the csrf middleware set the cookie
        token = client.cookies["csrftoken"]

        request_data = {
            "model": self.model_label,
            "name": "New Edition",
            "create-field": "name",
            "csrfmiddlewaretoken": token.coded_value if has_csrf_token else "",
        }
        response = client.post(self.url, data=request_data)
        if not has_csrf_token:
            assert response.status_code == 403
        else:
            assert response.status_code == 200

    def test_get_no_search_term(self, client):
        """Assert that a GET request without a search term still returns results."""
        query_string = urlencode({"model": self.model_label, SEARCH_LOOKUP_VAR: '["name__icontains"]'})
        response = client.get(f"{self.url}?{query_string}")
        data = json.loads(response.content)
        assert data["results"]

    def test_get_with_filter_by(self, client, obj):
        """
        Assert that a GET request with a filterBy value returns the expected
        results.
        """
        query_string = urlencode(
            {"model": self.model_label, SEARCH_LOOKUP_VAR: '["name__icontains"]', FILTERBY_VAR: "pub_num=2"}
        )
        response = client.get(f"{self.url}?{query_string}")
        data = json.loads(response.content)
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == obj.pk

    def test_get_no_filter_by(self, client):
        """
        Assert that a GET request returns no results when a required filterBy
        has no value.
        """
        query_string = urlencode(
            {"model": self.model_label, SEARCH_LOOKUP_VAR: '["name__icontains"]', FILTERBY_VAR: "pub_num="}
        )
        response = client.get(f"{self.url}?{query_string}")
        data = json.loads(response.content)
        assert not data["results"]


@pytest.mark.django_db
class TestAutocompleteViewUnitTests:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.model = Edition
        self.queryset = self.model.objects.all()
        self.model_label = f"{self.model._meta.app_label}.{self.model._meta.model_name}"

    @pytest.fixture
    def minimal_request_data(self):
        # Minimal request data required for setting up the view.
        return {"model": self.model_label}

    @pytest.fixture
    def request_data(self):
        return {}

    @pytest.fixture
    def get_request(self, rf, minimal_request_data, request_data):
        return rf.get("/", data={**minimal_request_data, **request_data})

    @pytest.fixture
    def post_request(self, rf, minimal_request_data, request_data):
        return rf.post("/", data={**minimal_request_data, **request_data})

    @pytest.fixture
    def view(self, get_request):
        view = AutocompleteView()
        view.request = get_request
        return view

    @pytest.fixture
    def setup_view(self, view, get_request):
        view.setup(request=get_request)

    def test_setup_sets_model(self, view, setup_view):
        """Assert that setup() sets the `model` attribute."""
        assert view.model == self.model

    @pytest.mark.parametrize("request_data", [{"create-field": "create_field"}])
    def test_setup_sets_create_field(self, view, setup_view, request_data):
        """Assert that setup() sets the `create_field` attribute."""
        assert view.create_field == "create_field"

    @pytest.mark.parametrize("request_data", [{SEARCH_LOOKUP_VAR: '["search_lookups"]'}])
    def test_setup_sets_search_lookups(self, view, setup_view, request_data):
        """Assert that setup() sets the `search_lookups` attribute."""
        assert view.search_lookups == ["search_lookups"]

    @pytest.mark.parametrize("request_data", [{VALUES_VAR: quote(json.dumps(["id", "name", "year", "pages"]))}])
    def test_setup_sets_values_select(self, view, setup_view, request_data):
        """Assert that setup() sets the `values_select` attribute."""
        assert view.values_select == ["id", "name", "year", "pages"]

    @pytest.mark.parametrize("request_data", [{FILTERBY_VAR: quote("magazine_id=1")}])
    def test_apply_filter_by(self, view, request_data):
        """Assert that apply_filter_by applies the expected ^filter to the queryset."""
        queryset = view.apply_filter_by(self.queryset)
        assert len(queryset.query.where.children) == 1
        lookup = queryset.query.where.children[0]
        assert lookup.lhs.target == self.model._meta.get_field("magazine")
        assert lookup.rhs == 1

    @pytest.mark.parametrize("request_data", [{}])
    def test_apply_filter_by_no_filterby_var_in_request(self, view, request_data):
        """
        Assert that apply_filter_by returns the queryset unchanged if the
        request does not contain FILTERBY_VAR.
        """
        queryset = view.apply_filter_by(self.queryset)
        assert len(queryset.query.where.children) == 0

    @pytest.mark.parametrize("request_data", [{FILTERBY_VAR: quote("magazine_id=")}])
    def test_apply_filter_by_no_filter_value(self, view, request_data):
        """
        Assert that apply_filter_by returns an empty queryset if no filter
        value is given.
        """
        queryset = view.apply_filter_by(self.queryset)
        assert len(queryset.query.where.children) == 1
        assert isinstance(queryset.query.where.children[0], NothingNode)

    def test_search(self, view):
        """Assert that search filters the queryset against the given search term."""
        view.search_lookups = ["name__icontains"]
        queryset = view.search(self.queryset, "Test")
        assert len(queryset.query.where.children) == 1
        lookup = queryset.query.where.children[0]
        assert lookup.lhs.target == self.model._meta.get_field("name")
        assert lookup.rhs == "Test"

    def test_order_queryset(self, view, setup_view):
        """Assert that order_queryset applies ordering to the queryset."""
        assert view.order_queryset(self.queryset).query.order_by == ("magazine", "name")

    @pytest.mark.parametrize("request_data", [{SEARCH_VAR: quote("Test"), SEARCH_LOOKUP_VAR: '["name__icontains"]'}])
    def test_get_queryset_calls_search(self, view, setup_view, request_data):
        """Assert that get_queryset calls search if a search term is given."""
        search_mock = Mock()
        with patch.object(view, "apply_filter_by", new=search_mock):
            view.get_queryset()
            search_mock.assert_called()

    @pytest.mark.parametrize(
        "request_data", [{FILTERBY_VAR: quote("magazine_id=1"), SEARCH_LOOKUP_VAR: '["name__icontains"]'}]
    )
    def test_get_queryset_calls_apply_filter_by(self, view, setup_view, request_data):
        """Assert that get_queryset calls apply_filter_by if FILTERBY_VAR is given."""
        apply_filter_by_mock = Mock()
        with patch.object(view, "apply_filter_by", new=apply_filter_by_mock):
            view.get_queryset()
            apply_filter_by_mock.assert_called()

    def test_get_queryset_calls_order_queryset(self, view, setup_view):
        """Assert that get_queryset calls order_queryset."""
        order_queryset_mock = Mock()
        with patch.object(view, "order_queryset", new=order_queryset_mock):
            view.get_queryset()
            order_queryset_mock.assert_called()

    @pytest.mark.parametrize("request_data", [{VALUES_VAR: quote(json.dumps(["id", "name", "year", "pages"]))}])
    def test_get_result_values(self, view, setup_view, request_data, obj):
        """Assert that get_result_values returns a list of queryset values."""
        results = view.get_result_values(self.queryset.filter(pk=obj.pk))
        assert results == [{"id": obj.pk, "name": "Test", "year": "3", "pages": "1"}]

    def test_get(self, view, setup_view, admin_user, obj):
        """Assert that get returns the expected response."""
        view.request.user = admin_user
        response = view.get(view.request)
        assert isinstance(response, JsonResponse)
        data = json.loads(response.content)
        assert "results" in data
        assert "page" in data
        assert "has_more" in data
        assert "show_create_option" in data

    @pytest.mark.parametrize("user_name, has_perm", [("noperms_user", False), ("perms_user", True)])
    def test_has_add_permission(self, request, view, setup_view, get_request, user_name, has_perm):
        """
        Assert that has_add_permission returns whether the user has 'add'
        permission for the given model.
        """
        _request = get_request
        _request.user = request.getfixturevalue(user_name)
        assert view.has_add_permission(_request) == has_perm

    @pytest.mark.parametrize("request_data", [{"create-field": "name"}])
    def test_create_object(self, view, setup_view, request_data):
        """Assert that create_object creates an object."""
        obj = view.create_object({"name": "Test"})
        assert isinstance(obj, self.model)
        assert obj.name == "Test"

    @pytest.mark.parametrize("request_data", [{"create-field": "name", "name": "__anything__"}])
    def test_post(self, view, setup_view, post_request, request_data, obj):
        """Assert that post returns the expected response."""

        class DummyObject:
            pk = 42
            name = "foo"

            def __str__(self):
                return f"{self.name}"

        create_object_mock = Mock(return_value=DummyObject())

        with patch.object(view, "has_add_permission", new=Mock(return_value=True)):
            with patch.object(view, "create_object", new=create_object_mock):
                response = view.post(post_request)
                assert isinstance(response, JsonResponse)
                create_object_mock.assert_called()
                data = json.loads(response.content)
                assert data["pk"] == 42
                assert data["text"] == "foo"

    def test_post_no_permission(self, view, setup_view, noperms_user, post_request):
        """
        Assert that post returns a HttpResponseForbidden response when the user
        does not have permission to add objects.
        """
        request = post_request
        request.user = noperms_user
        assert isinstance(view.post(post_request), HttpResponseForbidden)

    @pytest.mark.parametrize("request_data", [{"create-field": "name"}])
    def test_post_no_create_field_data(self, view, setup_view, post_request, request_data):
        """
        Assert that post returns a HttpResponseBadRequest response when the
        request did not contain data for the create_field.
        """
        with patch.object(view, "has_add_permission", new=Mock(return_value=True)):
            assert isinstance(view.post(post_request), HttpResponseBadRequest)
