import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from playwright.sync_api import expect
from testapp.models import Edition, Magazine

from django_tomselect.views import PAGE_SIZE

# Mark all tests in this module as end-to-end tests (excluded from running by default):
pytestmark = pytest.mark.e2e


@pytest.fixture
def magazine():
    return Magazine.objects.create(name="Test Magazine")


@pytest.fixture(autouse=True)
def other_magazine():
    return Magazine.objects.create(name="Other")


@pytest.fixture(autouse=True)  # TODO: is autouse=True necessary?
def data(magazine):
    return [
        Edition.objects.create(name=f"2022-{i + 1:02}", pages=i + 1, pub_num=100 + i, year="2022", magazine=magazine)
        for i in range(PAGE_SIZE * 3)
    ]


@pytest.fixture
def first_object(data):
    return data[0]


@pytest.fixture(autouse=True)
def noperms_user():
    return get_user_model().objects.create(username="noperms", password="sadface")


@pytest.fixture
def user(admin_user, username):
    """
    Return the user with the given username.

    If username is empty or 'admin', return a pytest-django admin_user.
    """
    if not username or username == "admin":
        return admin_user
    return get_user_model().objects.get(username=username)


@pytest.fixture
def login(client, user):
    """Log in the given user."""
    client.force_login(user)
    return client


@pytest.fixture
def logged_in(login, context):
    """
    Log in a user and add the session cookie for the logged-in user to the
    current context.
    """
    auth_cookie = login.cookies["sessionid"]
    pw_cookie = {
        "name": auth_cookie.key,
        "value": auth_cookie.value,
        "path": auth_cookie["path"],
        "domain": auth_cookie["domain"] or "localhost",
    }
    context.add_cookies([pw_cookie])


# NOTE: must not override original page fixture or tests can't be run against
# multiple browsers
@pytest.fixture
def _page(page, live_server, view_name):
    page.goto(live_server.url + reverse(view_name))
    return page


@pytest.fixture
def ts_wrapper(_page):
    wrapper = _page.locator(".ts-wrapper")
    wrapper.wait_for()
    return wrapper


@pytest.fixture
def wrapper_focus(_page, ts_wrapper):
    with _page.expect_event("requestfinished"):
        ts_wrapper.click()


@pytest.fixture
def search_input(_page, wrapper_focus):
    search_input = _page.locator(".dropdown-input")
    search_input.wait_for()
    return search_input


@pytest.fixture
def search(_page, search_input):
    with _page.expect_event("requestfinished"):
        search_input.fill("2022")


def get_dropdown_items(_page):
    """Return all elements in the dropdown."""
    return _page.locator(".ts-dropdown-content > *")


def get_select_options(_page):
    """Return all selectable options."""
    return _page.locator("[data-selectable][role=option]")


def get_last_dropdown_item(_page):
    item = None
    for item in get_dropdown_items(_page).all():
        # Have to wait for each option to be attached, otherwise
        # test_virtual_scroll fails for the 'create' view.
        item.wait_for(state="attached")
    return item


@pytest.mark.parametrize("view_name", ["simple"])
def test_initially_empty(_page, view_name):
    """Assert that the list of options is empty initially."""
    expect(get_dropdown_items(_page)).to_have_count(0)


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["simple"])
def test_load_first_results_on_focus(_page, view_name, wrapper_focus):
    """Assert that the first _page of options is loaded when the select gets focus."""
    expect(get_select_options(_page)).to_have_count(PAGE_SIZE)


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["simple", "multiple", "tabular", "create"])
def test_virtual_scroll(_page, view_name, search, data):
    """
    Assert that the user can scroll to the bottom of the options to load more
    options from the backend until there are no more search results to load.
    """
    expect(get_select_options(_page)).to_have_count(PAGE_SIZE)

    # Second _page:
    with _page.expect_event("requestfinished"):
        get_last_dropdown_item(_page).scroll_into_view_if_needed()
    expect(get_select_options(_page)).to_have_count(PAGE_SIZE * 2)

    # Last _page:
    with _page.expect_event("requestfinished"):
        get_last_dropdown_item(_page).scroll_into_view_if_needed()
    expect(get_select_options(_page)).to_have_count(len(data))
    expect(get_last_dropdown_item(_page)).to_have_text("No more results")


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["multiple"])
class TestSelectMultiple:
    @pytest.fixture
    def select_two(self, _page, search):
        """Select the first two options."""
        options = get_select_options(_page).all()
        options[0].click()
        options[1].click()

    @pytest.fixture
    def ts_control(self, _page):
        return _page.locator(".ts-control")

    @pytest.fixture
    def selected(self, _page, select_two, ts_control):
        """Return the locator for the selected options."""
        return ts_control.locator(".item")

    def test_select_multiple(self, _page, selected):
        """Assert that the user can select multiple options."""
        expect(selected).to_have_count(2)

    def test_has_remove_button(self, _page, selected):
        """Assert that each selected option has a remove button."""
        for option in selected.all():
            expect(option.locator(".remove")).to_be_attached()

    def test_has_clear_button(self, _page, ts_control):
        """Assert that the ts control has a clear all button."""
        expect(ts_control.locator(".clear-button")).to_have_count(1)


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["tabular"])
class TestTabularSelect:
    @pytest.fixture
    def dropdown_header(self, _page, wrapper_focus):
        """Return the dropdown header."""
        return _page.locator(".ts-dropdown .dropdown-header")

    @pytest.fixture
    def header_columns(self, _page, dropdown_header):
        """Return the column divs of the dropdown header."""
        return dropdown_header.locator(".row > *")

    @pytest.fixture
    def option_columns(self, _page, wrapper_focus):
        """Return the column divs of a select option."""
        return get_select_options(_page).first.locator("*")

    def test_has_dropdown_header(self, _page, dropdown_header):
        """Assert that the dropdown has the expected table header."""
        expect(dropdown_header).to_be_attached()

    def test_header_columns(self, _page, header_columns):
        """Assert that the dropdown header has the expected columns."""
        expect(header_columns).to_have_count(4)
        label_col, year_col, pages_col, pub_num_col = header_columns.all()
        expect(label_col).to_have_class("col-5")
        expect(label_col).to_have_text("Edition")
        expect(year_col).to_have_class("col")
        expect(year_col).to_have_text("Year")
        expect(pages_col).to_have_class("col")
        expect(pages_col).to_have_text("Pages")
        expect(pub_num_col).to_have_class("col")
        expect(pub_num_col).to_have_text("Publication Number")

    def test_options_have_columns(self, _page, option_columns, first_object):
        """Assert that the data of the options are assigned to columns."""
        expect(option_columns).to_have_count(4)
        label_col, year_col, pages_col, pub_num_col = option_columns.all()
        expect(label_col).to_have_class("col-5")
        expect(label_col).to_have_text(first_object.name)
        expect(year_col).to_have_class("col")
        expect(year_col).to_have_text(str(first_object.year))
        expect(pages_col).to_have_class("col")
        expect(pages_col).to_have_text(str(first_object.pages))
        expect(pub_num_col).to_have_class("col")
        expect(pub_num_col).to_have_text(str(first_object.pub_num))


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["tabular-with-value-field"])
class TestTabularSelectWithValueField:
    @pytest.fixture
    def dropdown_header(self, _page, wrapper_focus):
        """Return the dropdown header."""
        return _page.locator(".ts-dropdown .dropdown-header")

    @pytest.fixture
    def header_columns(self, _page, dropdown_header):
        """Return the column divs of the dropdown header."""
        return dropdown_header.locator(".row > *")

    @pytest.fixture
    def option_columns(self, _page, wrapper_focus):
        """Return the column divs of a select option."""
        return get_select_options(_page).first.locator("*")

    def test_has_dropdown_header(self, _page, dropdown_header):
        """Assert that the dropdown has the expected table header."""
        expect(dropdown_header).to_be_attached()

    def test_header_columns(self, _page, header_columns):
        """Assert that the dropdown header has the expected columns."""
        expect(header_columns).to_have_count(5)
        id_col, label_col, year_col, pages_col, pub_num_col = header_columns.all()
        expect(id_col).to_have_class("col-1")
        expect(id_col).to_have_text("Id")
        expect(label_col).to_have_class("col-5")
        expect(label_col).to_have_text("Edition")
        expect(year_col).to_have_class("col")
        expect(year_col).to_have_text("Year")
        expect(pages_col).to_have_class("col")
        expect(pages_col).to_have_text("Pages")
        expect(pub_num_col).to_have_class("col")
        expect(pub_num_col).to_have_text("Publication Number")

    def test_options_have_columns(self, _page, option_columns, first_object):
        """Assert that the data of the options are assigned to columns."""
        expect(option_columns).to_have_count(5)
        id_col, label_col, year_col, pages_col, pub_num_col = option_columns.all()
        expect(id_col).to_have_class("col-1")
        expect(id_col).to_have_text(str(first_object.pk))
        expect(label_col).to_have_class("col-5")
        expect(label_col).to_have_text(first_object.name)
        expect(year_col).to_have_class("col")
        expect(year_col).to_have_text(str(first_object.year))
        expect(pages_col).to_have_class("col")
        expect(pages_col).to_have_text(str(first_object.pages))
        expect(pub_num_col).to_have_class("col")
        expect(pub_num_col).to_have_text(str(first_object.pub_num))


################################################################################
# Dropdown Footer
################################################################################


@pytest.fixture
def dropdown_footer(_page, wrapper_focus):
    """Return the dropdown footer."""
    return _page.locator(".dropdown-footer")


@pytest.fixture
def add_button(_page, dropdown_footer):
    """Return the add button in the dropdown footer."""
    return dropdown_footer.locator(".add-btn")


@pytest.fixture
def listview_button(dropdown_footer):
    """Return the listview button in the dropdown footer."""
    return dropdown_footer.locator(".cl-btn")


@pytest.mark.parametrize("view_name,has_footer", [("add", True), ("listview", True), ("simple", False)])
def test_has_footer(view_name, has_footer, dropdown_footer, context):
    """
    Assert that a footer div is added to the dropdown content if the select
    element declares a 'listview' URL or a 'add' URL.
    """
    if has_footer:
        # Note that the footer will be attached for an 'add' URL even if the
        # user has no 'add' permission.
        expect(dropdown_footer).to_be_attached()
    else:
        expect(dropdown_footer).not_to_be_attached()


@pytest.mark.parametrize("view_name", ["add"])
@pytest.mark.parametrize("username", ["noperms"])
def test_add_button_invisible_when_no_permission(
    logged_in,
    add_button,
    view_name,
    username,
):
    """
    Assert that the add button is invisible if the user does not have
    'add' permission.
    """
    expect(add_button).not_to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["add"])
@pytest.mark.parametrize("username", ["admin"])
class TestFooterAddButton:
    def test_has_visible_add_button(self, logged_in, add_button):
        """Assert that the dropdown footer contains a visible 'add' button."""
        expect(add_button).to_be_visible()

    def test_add_button_text_changes_on_typing(self, logged_in, _page, add_button, search_input):
        """
        Assert that the text of the add button updates along with the user
        typing in a search term.
        """
        expect(add_button).to_have_text("Add value")
        with _page.expect_event("requestfinished"):
            search_input.fill("202")
        expect(add_button).to_have_text("Add value '202'")
        with _page.expect_event("requestfinished"):
            search_input.fill("2022")
        expect(add_button).to_have_text("Add value '2022'")

    def test_add_button_click_no_search_term(self, logged_in, _page, add_button, live_server):
        """
        Assert that clicking the add button with no search term given opens the
        'add' _page in a new tab.
        """

        def requests_add_page(request):
            """Return whether the request is for the add _page."""
            return request.url == live_server.url + reverse("add_page")

        with _page.expect_popup(requests_add_page):
            add_button.click()

    def test_add_button_click_with_search_term(self, logged_in, _page, add_button, search_input, live_server):
        """
        Assert that clicking the add button with a search term given starts a
        POST request to create a new object instead of opening the 'add' _page.
        """
        with _page.expect_request_finished():
            search_input.fill("2022-99")
        with _page.expect_response(live_server.url + reverse("ac")) as response_info:
            add_button.click()
        response = response_info.value
        data = response.json()
        assert data["text"] == "2022-99"
        assert data["pk"]

    def test_add_button_successful_creation(self, logged_in, _page, add_button, search_input):
        """
        If the POST request to create a new object was successful, the created
        item should be immediately selected.
        """
        with _page.expect_request_finished():
            search_input.fill("2022-99")
        with _page.expect_request_finished():
            add_button.click()
        expect(_page.locator(".ts-control .item")).to_have_text("2022-99")
        expect(_page.locator(".dropdown-content")).not_to_be_visible()

    def test_add_button_hidden_for_unauthenticated_user(self, username, add_button):
        """The 'add' button should be hidden if the user is not logged in."""
        expect(add_button).to_be_hidden()

    def test_footer_not_shown_when_add_btn_invisible(self, username, dropdown_footer):
        """The footer div should not be shown when the 'add' button is invisible."""
        expect(dropdown_footer).to_be_hidden()


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["listview"])
class TestFooterListviewButton:
    def test_has_visible_listview_button(self, listview_button):
        """Assert that the dropdown footer contains a visible 'listview' button."""
        expect(listview_button).to_be_visible()

    def test_listview_query_string_contains_search_term(self, _page, listview_button, search_input):
        """
        Assert that the URL to the listview contains the current search term
        in the query string.
        """
        assert listview_button.get_attribute("href") == reverse("listview_page")
        with _page.expect_request_finished():
            search_input.fill("2022")
        assert "q=2022" in listview_button.get_attribute("href")


@pytest.fixture
def magazine_select(_page):
    select = _page.get_by_label("Magazine")
    select.wait_for()
    return select


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["filtered"])
def test_options_filtered(_page, magazine_select, magazine, other_magazine, ts_wrapper, view_name):
    """
    Assert that the options of the 'edition' field are filtered with the values
    of the forwarded field 'magazine'.
    """
    magazine_select.select_option(value=str(other_magazine.pk))
    with _page.expect_request_finished():
        ts_wrapper.click()
    expect(get_select_options(_page)).to_have_count(0)
    magazine_select.focus()
    magazine_select.select_option(value=str(magazine.pk))
    with _page.expect_request_finished():
        ts_wrapper.click()
    expect(get_select_options(_page)).not_to_have_count(0)
