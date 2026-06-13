"""Selected-option resolution when a UUID value_field receives an integer pk.

A model whose real primary key is a separate integer column (``pkid``) while it exposes an
opaque ``UUIDField`` as ``value_field`` (``value_field="id"``) can be handed the integer pk as
the incoming widget value. This happens whenever a bound ``ModelForm`` renders a ``ForeignKey``
to such a model: Django's ``model_to_dict`` reduces the FK initial to the related object's
integer pk, and ``ModelChoiceField.prepare_value`` passes that scalar through unchanged (it only
honors ``to_field_name`` for model instances). The widget then has to build its selected-option
filter from an integer while ``value_field`` points at a ``UUIDField``.

These tests pin down that:

- such an integer initial (as an ``int`` or its digit-string form) resolves to the correct row and
  renders the UUID (never the integer) as the option value, and
- the narrow guard that enables this does not disturb any other configuration: a UUID or
  UUID-string initial, an integer ``value_field`` (a real integer column), the ``pkid`` pk used
  directly as ``value_field``, or - critically - a model whose primary key *is* a ``UUIDField``
  (the common ``id = UUIDField(primary_key=True)`` pattern), which is never rerouted.
"""

import uuid

import pytest

from django_tomselect.app_settings import TomSelectConfig
from django_tomselect.middleware import _request_local
from django_tomselect.widgets import TomSelectModelMultipleWidget, TomSelectModelWidget
from example_project.example.models import (
    Article,
    ModelWithPKIDAndUUIDId,
    ModelWithUUIDPk,
    PublicationTag,
)


class _StubAutocompleteView:
    """Minimal autocomplete view for driving ``_get_selected_options`` directly.

    All ``show_*`` flags default off, so no permission or URL lookups occur; the view only needs
    to exist and answer ``has_permission``.
    """

    detail_url = None
    update_url = None
    delete_url = None
    create_url = None
    list_url = None

    def has_permission(self, request, action):
        """Deny every action; the widget never renders action URLs in these tests."""
        return False


def _model_widget(value_field, queryset):
    """Build a model widget wired to ``queryset`` with no live request."""
    config = TomSelectConfig(url="autocomplete-pkid-uuid", value_field=value_field, label_field="name")
    widget = TomSelectModelWidget(config=config)
    widget.get_queryset = lambda: queryset
    widget.get_current_request = lambda: None
    return widget


@pytest.mark.django_db
class TestUUIDValueFieldResolvesIntegerPkid:
    """A UUID value_field that receives the integer pkid (the bound-ModelForm-FK edit case)."""

    def test_integer_pkid_initial_resolves_to_uuid_option(self, sample_pkid_uuid_model):
        """An integer pkid initial resolves the row and emits the UUID, not the integer."""
        widget = _model_widget("id", ModelWithPKIDAndUUIDId.objects.all())

        options = widget._get_selected_options(sample_pkid_uuid_model.pkid, _StubAutocompleteView())

        assert len(options) == 1
        assert options[0]["value"] == str(sample_pkid_uuid_model.id)
        assert options[0]["value"] != str(sample_pkid_uuid_model.pkid)
        assert options[0]["label"] == sample_pkid_uuid_model.name

    def test_uuid_initial_still_resolves(self, sample_pkid_uuid_model):
        """A UUID initial keeps resolving through the normal value_field path."""
        widget = _model_widget("id", ModelWithPKIDAndUUIDId.objects.all())

        options = widget._get_selected_options(sample_pkid_uuid_model.id, _StubAutocompleteView())

        assert len(options) == 1
        assert options[0]["value"] == str(sample_pkid_uuid_model.id)

    def test_uuid_string_initial_still_resolves(self, sample_pkid_uuid_model):
        """A stringified UUID initial (the POST/redisplay shape) keeps resolving."""
        widget = _model_widget("id", ModelWithPKIDAndUUIDId.objects.all())

        options = widget._get_selected_options(str(sample_pkid_uuid_model.id), _StubAutocompleteView())

        assert len(options) == 1
        assert options[0]["value"] == str(sample_pkid_uuid_model.id)

    def test_string_integer_pkid_initial_resolves(self, sample_pkid_uuid_model):
        """A digit-string pkid (the data-dict / POST-redisplay shape) resolves to the UUID.

        When a bound form is re-rendered, the widget pulls its value out of the submitted data
        dict, where everything is a string. A bare integer pk therefore arrives as ``"5"`` rather
        than ``5``; it must still resolve, and must never be matched against the UUID column (which
        would raise).
        """
        widget = _model_widget("id", ModelWithPKIDAndUUIDId.objects.all())

        options = widget._get_selected_options(str(sample_pkid_uuid_model.pkid), _StubAutocompleteView())

        assert len(options) == 1
        assert options[0]["value"] == str(sample_pkid_uuid_model.id)
        assert options[0]["value"] != str(sample_pkid_uuid_model.pkid)

    def test_multiple_integer_pkid_initial_resolves_to_uuids(self, multiple_pkid_uuid_models):
        """A list of integer pkids (bound M2M edit) resolves each row to its UUID."""
        widget = _model_widget("id", ModelWithPKIDAndUUIDId.objects.all())

        pkids = [model.pkid for model in multiple_pkid_uuid_models[:2]]
        options = widget._get_selected_options(pkids, _StubAutocompleteView())

        assert len(options) == 2
        assert {opt["value"] for opt in options} == {str(model.id) for model in multiple_pkid_uuid_models[:2]}

    def test_multiple_widget_class_resolves_integer_pkids(self, multiple_pkid_uuid_models):
        """``TomSelectModelMultipleWidget`` (which inherits the resolver) gets the same fix.

        The fix lives on ``TomSelectModelWidget``; the multiple-select subclass relies on plain
        inheritance with no override. Instantiate the subclass directly so a future override that
        breaks this path is caught.
        """
        config = TomSelectConfig(url="autocomplete-pkid-uuid", value_field="id", label_field="name")
        widget = TomSelectModelMultipleWidget(config=config)
        widget.get_queryset = lambda: ModelWithPKIDAndUUIDId.objects.all()
        widget.get_current_request = lambda: None

        pkids = [model.pkid for model in multiple_pkid_uuid_models[:2]]
        options = widget._get_selected_options(pkids, _StubAutocompleteView())

        assert {opt["value"] for opt in options} == {str(model.id) for model in multiple_pkid_uuid_models[:2]}


@pytest.mark.django_db
class TestGuardDoesNotMisrouteOtherConfigurations:
    """The pkid->UUID fallback must not hijack any other value_field configuration."""

    def test_pkid_value_field_unaffected(self, sample_pkid_uuid_model):
        """value_field='pkid' (the integer pk used directly) still emits the integer pk."""
        widget = _model_widget("pkid", ModelWithPKIDAndUUIDId.objects.all())

        options = widget._get_selected_options(sample_pkid_uuid_model.pkid, _StubAutocompleteView())

        assert len(options) == 1
        assert options[0]["value"] == str(sample_pkid_uuid_model.pkid)

    def test_integer_value_field_is_not_routed_to_pk(self):
        """An integer initial against a real integer value_field filters that field, not the pk.

        ``PublicationTag.usage_count`` is an integer column distinct from the pk. Selecting by a
        usage-count value must return the rows with that count, proving the guard does not divert a
        legitimate integer value_field to a primary-key lookup.
        """
        tag_a = PublicationTag.objects.create(name="alpha", usage_count=2)
        tag_b = PublicationTag.objects.create(name="bravo", usage_count=2)
        PublicationTag.objects.create(name="other", usage_count=9)

        config = TomSelectConfig(url="autocomplete-pkid-uuid", value_field="usage_count", label_field="name")
        widget = TomSelectModelWidget(config=config)
        widget.get_queryset = lambda: PublicationTag.objects.all()
        widget.get_current_request = lambda: None

        options = widget._get_selected_options(2, _StubAutocompleteView())

        assert {opt["value"] for opt in options} == {"2"}
        returned_names = {opt["label"] for opt in options}
        assert returned_names == {tag_a.name, tag_b.name}


@pytest.mark.django_db
class TestUUIDPrimaryKeyModelIsUnaffected:
    """A model whose primary key IS a UUIDField must never be rerouted (common pattern).

    ``id = UUIDField(primary_key=True)`` is a widespread setup. The whole point of the fallback is
    the *separate*-column case (integer pk + secondary UUID); it must not touch the UUID-pk case.
    Two layers protect these users: the incoming value is a UUID (not an integer) in the real flow,
    and the guard additionally refuses to reroute unless the model's real pk is an integer column.
    """

    def test_uuid_pk_value_resolves_through_normal_path(self, sample_uuid_model):
        """A UUID-pk model with a UUID value resolves exactly as it always has."""
        widget = _model_widget("id", ModelWithUUIDPk.objects.all())

        options = widget._get_selected_options(sample_uuid_model.id, _StubAutocompleteView())

        assert len(options) == 1
        assert options[0]["value"] == str(sample_uuid_model.id)
        assert options[0]["label"] == sample_uuid_model.name

    def test_uuid_pk_string_value_resolves_through_normal_path(self, sample_uuid_model):
        """The POST/redisplay shape (UUID string) resolves on a UUID-pk model."""
        widget = _model_widget("id", ModelWithUUIDPk.objects.all())

        options = widget._get_selected_options(str(sample_uuid_model.id), _StubAutocompleteView())

        assert len(options) == 1
        assert options[0]["value"] == str(sample_uuid_model.id)

    def test_uuid_pk_guard_never_fires_even_for_an_integer(self):
        """Even a stray integer never reroutes a UUID-pk model (its pk is not an integer column)."""
        assert TomSelectModelWidget._value_field_needs_pk_fallback(ModelWithUUIDPk, "id", [5]) is False


class TestValueFieldNeedsPkFallbackGuard:
    """Unit coverage of the field-type discrimination, independent of the DB."""

    @pytest.mark.parametrize(
        "model, value_field, value, expected",
        [
            # value_field is a UUIDField on an integer-pk model: the fallback target.
            (ModelWithPKIDAndUUIDId, "id", 5, True),
            (ModelWithPKIDAndUUIDId, "id", "5", True),  # digit-string pk (data-dict/POST shape)
            (ModelWithPKIDAndUUIDId, "id", uuid.uuid4(), False),
            (ModelWithPKIDAndUUIDId, "id", str(uuid.uuid4()), False),  # UUID str is not a digit-string
            (ModelWithPKIDAndUUIDId, "id", True, False),  # bool is not a pk
            # A UUID *primary* key must never be rerouted (the real pk is not an integer column).
            (ModelWithUUIDPk, "id", 5, False),
            (ModelWithUUIDPk, "id", uuid.uuid4(), False),
            # Non-UUID value_fields are never rerouted, regardless of value.
            (ModelWithPKIDAndUUIDId, "pkid", 5, False),
            (ModelWithPKIDAndUUIDId, "name", 5, False),
            (Article, "priority", 5, False),
            (PublicationTag, "usage_count", 5, False),
            # Unresolvable field / no model: safe negative.
            (ModelWithPKIDAndUUIDId, "does_not_exist", 5, False),
            (None, "id", 5, False),
        ],
    )
    def test_guard(self, model, value_field, value, expected):
        """The guard fires only for a UUID value_field on an integer-pk model handed an integer pk."""
        result = TomSelectModelWidget._value_field_needs_pk_fallback(model, value_field, [value])
        assert result is expected


class _LiveRequest:
    """A minimal request that satisfies ``get_context`` >> ``_build_full_context``.

    ``ModelWithPKIDAndUUIDIdAutocompleteView`` sets ``allow_anonymous = True``, so an authenticated
    flag is enough; ``_tomselect_global_rendered`` short-circuits the one-time global asset render.
    """

    class _User:
        is_authenticated = True

        def has_perms(self, perms):
            """Grant every permission; the view allows anonymous access regardless."""
            return True

    user = _User()
    method = "GET"
    GET = {}  # noqa: RUF012 - mirrors the attribute shape Django's HttpRequest exposes
    _tomselect_global_rendered = True

    def get_full_path(self):
        """Return a stable path; only its presence matters to the context builder."""
        return "/test/"


@pytest.mark.django_db
class TestGetContextResolvesIntegerPkidEndToEnd:
    """Drive the real ``get_context`` plumbing, not just ``_get_selected_options`` in isolation.

    The other tests stub ``get_queryset``/``get_current_request`` and call the private resolver
    directly. These exercise the full path a rendered widget actually takes: ``get_context`` resolves
    the live autocomplete view from the ``autocomplete-pkid-uuid`` URL, validates the request, and
    only then computes ``selected_options``. This is the layer a bound ``ModelForm`` reaches when it
    hands the widget the related object's integer ``pkid``.
    """

    def _live_widget(self, widget_class=TomSelectModelWidget):
        config = TomSelectConfig(url="autocomplete-pkid-uuid", value_field="id", label_field="name")
        return widget_class(config=config)

    def test_get_context_emits_uuid_for_integer_pkid(self, sample_pkid_uuid_model):
        """A widget rendered with the integer pkid surfaces the UUID as the selected option value."""
        widget = self._live_widget()
        _request_local.request = _LiveRequest()
        try:
            context = widget.get_context("customer", sample_pkid_uuid_model.pkid, {})
        finally:
            del _request_local.request

        selected = context["widget"]["selected_options"]
        assert len(selected) == 1
        assert selected[0]["value"] == str(sample_pkid_uuid_model.id)
        assert selected[0]["value"] != str(sample_pkid_uuid_model.pkid)
        assert selected[0]["label"] == sample_pkid_uuid_model.name

    def test_get_context_multiple_widget_emits_uuids_for_integer_pkids(self, multiple_pkid_uuid_models):
        """The multiple-select widget resolves a list of integer pkids to their UUIDs end-to-end."""
        widget = self._live_widget(TomSelectModelMultipleWidget)
        pkids = [model.pkid for model in multiple_pkid_uuid_models[:2]]
        _request_local.request = _LiveRequest()
        try:
            context = widget.get_context("customers", pkids, {})
        finally:
            del _request_local.request

        selected = context["widget"]["selected_options"]
        assert {opt["value"] for opt in selected} == {str(model.id) for model in multiple_pkid_uuid_models[:2]}
