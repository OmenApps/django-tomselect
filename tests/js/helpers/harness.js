import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const TEMPLATE_PATH = resolve(
  __dirname,
  '../../../src/django_tomselect/templates/django_tomselect/tomselect_setup.html'
)

const WIDGET_TEMPLATE_PATH = resolve(
  __dirname,
  '../../../src/django_tomselect/templates/django_tomselect/tomselect.html'
)

const OPTION_CREATE_TEMPLATE_PATH = resolve(
  __dirname,
  '../../../src/django_tomselect/templates/django_tomselect/render/option_create.html'
)

// Vitest 4's JSDOM environment copies dom.window properties onto Node's
// global, but the test-facing `window` is NOT the same object as JSDOM's
// internal window. Scripts injected via document.head.appendChild execute
// in JSDOM's window context, so `window.foo = ...` inside an injected
// script lands on JSDOM's window - accessible only via window.jsdom.window
// (which Vitest exposes by stashing the JSDOM instance there).
export function getJsdomWindow () {
  if (!window.jsdom || !window.jsdom.window) {
    throw new Error('window.jsdom.window is not available - is the Vitest JSDOM environment active?')
  }
  return window.jsdom.window
}

export function loadTemplateScript () {
  const html = readFileSync(TEMPLATE_PATH, 'utf-8')

  const decommented = html.replace(/\{%\s*comment\s*%\}[\s\S]*?\{%\s*endcomment\s*%\}/g, '')

  const scriptMatches = [...decommented.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)]
  let candidate = null
  for (const sm of scriptMatches) {
    if (sm[1].includes('window.djangoTomSelect')) {
      candidate = sm[1]
    }
  }
  if (!candidate) {
    throw new Error('Could not locate the djangoTomSelect <script> block in ' + TEMPLATE_PATH)
  }
  let js = candidate

  js = js.replace(/\{%\s*if not widget\.use_htmx\s*%\}[\s\S]*?\{%\s*endif\s*%\}/g, '')
  js = js.replace(/\{%[\s\S]*?%\}/g, '')
  js = js.replace(/\{\{[\s\S]*?\}\}/g, '')

  if (!js.includes('prepareElement')) {
    throw new Error('Extracted script does not contain prepareElement; extraction is wrong')
  }
  if (js.includes('Custom global setup code here')) {
    throw new Error('Extracted script came from the {% comment %} example, not the real block')
  }
  if (js.includes('{%') || js.includes('{{')) {
    throw new Error('Extracted script still contains Django template tags')
  }

  return js
}

// Stub mirrors real Tom Select setup() at node_modules/tom-select/src/tom-select.ts:167/173/410/432:
// snapshot input.getAttribute('class'), create wrapper with those classes, insert wrapper as
// sibling AFTER the input, then add tomselected + ts-hidden-accessible to the input.
export class TomSelectStub {
  constructor (element, config) {
    const snapshottedClasses = element.getAttribute('class') || ''
    this.element = element
    // Real Tom Select 2.x exposes the underlying <select> as `this.input` (see
    // node_modules/tom-select/src/tom-select.ts:171). Mirror that so config
    // callbacks reading this.input work under test.
    this.input = element
    this.config = config
    this.destroyed = false

    const wrapper = element.ownerDocument.createElement('div')
    wrapper.className = ('ts-wrapper ' + snapshottedClasses).trim()
    element.insertAdjacentElement('afterend', wrapper)

    element.classList.add('tomselected')
    element.classList.add('ts-hidden-accessible')

    element.tomselect = this
    this.wrapper = wrapper
  }

  destroy () {
    this.destroyed = true
    this.element.classList.remove('tomselected')
    this.element.classList.remove('ts-hidden-accessible')
    if (this.wrapper && this.wrapper.parentNode) {
      this.wrapper.remove()
    }
    delete this.element.tomselect
  }
}

export function setupHarness (options = {}) {
  const { TomSelectClass = TomSelectStub } = options
  const realWindow = getJsdomWindow()

  delete realWindow.djangoTomSelect
  document.body.replaceChildren()
  document.querySelectorAll('script[data-harness="dts"]').forEach(s => s.remove())

  realWindow.TomSelect = TomSelectClass

  const js = loadTemplateScript()
  const script = document.createElement('script')
  script.dataset.harness = 'dts'
  script.textContent = js
  document.head.appendChild(script)

  if (!realWindow.djangoTomSelect) {
    throw new Error('Harness failed to populate window.djangoTomSelect. Check that vitest.config.js sets runScripts: "dangerously".')
  }
  return realWindow.djangoTomSelect
}

export function makeSelect ({ id = 'id_test', className = '' } = {}) {
  const select = document.createElement('select')
  select.id = id
  if (className) select.className = className
  select.setAttribute('data-tomselect', 'true')
  document.body.appendChild(select)
  return select
}

// Mirror of djangoTomSelect.truncatePrefix from tomselect_setup.html. Kept here so
// renderWidgetTemplate can resolve {% load django_tomselect %} truncatePrefix calls
// without importing the global setup. If the template-side helper changes, update both.
function harnessTruncatePrefix (prefix, levelsUp) {
  if (!levelsUp || levelsUp <= 0) return prefix
  const matches = []
  prefix.replace(/-\d+-/g, (m, offset) => {
    matches.push({ end: offset + m.length })
    return m
  })
  if (levelsUp > matches.length) return prefix
  const keepThrough = matches.length - levelsUp - 1
  return keepThrough < 0 ? '' : prefix.slice(0, matches[keepThrough].end)
}

function escapeJsLiteral (s) {
  return String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'")
}

function buildWidgetContext (widgetContext) {
  const ctx = {
    autocompleteUrl: '/autocomplete/',
    autocompleteParams: '',
    valueField: 'id',
    labelField: 'name',
    minimumQueryLength: 2,
    loadingClass: 'loading',
    searchParam: 'q',
    filterParam: 'f',
    excludeParam: 'e',
    pageParam: 'p',
    filters: [],
    excludes: [],
    plugins: {},
    ...widgetContext
  }
  if (!ctx.id) ctx.id = 'id_test'
  if (!ctx.name) ctx.name = ctx.id.replace(/^id_/, '')
  return ctx
}

function computeFormPrefix (name) {
  const lastDash = name.lastIndexOf('-')
  return lastDash !== -1 ? name.slice(0, lastDash + 1) : ''
}

// Render a per-widget IIFE (the {% block tomselect_init %} body of tomselect.html)
// with all Django constructs substituted. Returns the JS string ready to inject.
//
// The substitutions are intentionally narrow rather than a generic strip, because
// tomselect.html has Django expressions in JS-expression positions that would yield
// invalid JS if blindly stripped (booleans, scalar conditionals, plugin blocks,
// selected_options loops, render includes, the use_htmx branch). Each region is
// handled with a region-specific replacement that emits the test-friendly default.
export function renderWidgetTemplate (widgetContext = {}) {
  const ctx = buildWidgetContext(widgetContext)
  const formPrefix = computeFormPrefix(ctx.name)
  let html = readFileSync(WIDGET_TEMPLATE_PATH, 'utf-8')

  // Strip {% comment %}...{% endcomment %} blocks BEFORE locating the block tag,
  // because the file's leading docstring contains an example {% block tomselect_init %}
  // that would otherwise be matched first by the block extractor.
  html = html.replace(/\{%\s*comment\s*%\}[\s\S]*?\{%\s*endcomment\s*%\}/g, '')

  // Extract the IIFE inside {% block tomselect_init %}...{% endblock tomselect_init %}
  const blockMatch = html.match(/\{%\s*block tomselect_init\s*%\}([\s\S]*?)\{%\s*endblock tomselect_init\s*%\}/)
  if (!blockMatch) {
    throw new Error('Could not locate {% block tomselect_init %} in tomselect.html')
  }
  let js = blockMatch[1]

  // 1. elementId conditional at line ~49
  js = js.replace(
    /'\{%\s*if "id" in widget\.attrs\.keys and widget\.attrs\.id\s*%\}\{\{\s*widget\.attrs\.id\|escapejs\s*\}\}\{%\s*else\s*%\}\{\{\s*widget\.name\|escapejs\s*\}\}\{%\s*endif\s*%\}'/,
    `'${escapeJsLiteral(ctx.id)}'`
  )

  // 2. {% if not widget.use_htmx %}...{% else %}...{% endif %} - always pick htmx branch
  // so init runs synchronously regardless of whether DOMContentLoaded already fired.
  js = js.replace(
    /\{%\s*if not widget\.use_htmx\s*%\}[\s\S]*?\{%\s*else\s*%\}([\s\S]*?)\{%\s*endif\s*%\}/g,
    '$1'
  )

  // 3. Boolean |yesno expressions (highlight, openOnFocus, hideSelected)
  js = js.replace(/\{\{\s*widget\.highlight\|yesno:"true,false"\s*\}\}/g, ctx.highlight ? 'true' : 'false')
  js = js.replace(/\{\{\s*widget\.open_on_focus\|yesno:"true,false"\s*\}\}/g, ctx.openOnFocus ? 'true' : 'false')
  js = js.replace(/\{\{\s*widget\.hide_selected\|yesno:"true,false"\s*\}\}/g, ctx.hideSelected ? 'true' : 'false')

  // 4. Scalar number/value conditionals
  // maxOptions: {% if widget.max_options %}{{ widget.max_options }}{% else %}null{% endif %}
  js = js.replace(
    /\{%\s*if widget\.max_options\s*%\}\{\{\s*widget\.max_options\s*\}\}\{%\s*else\s*%\}null\{%\s*endif\s*%\}/g,
    ctx.maxOptions == null ? 'null' : String(ctx.maxOptions)
  )
  // preload: {% if widget.preload == "focus" %}'focus'{% elif widget.preload %}true{% else %}false{% endif %}
  js = js.replace(
    /\{%\s*if widget\.preload == "focus"\s*%\}'focus'\{%\s*elif widget\.preload\s*%\}true\{%\s*else\s*%\}false\{%\s*endif\s*%\}/g,
    ctx.preload === 'focus' ? "'focus'" : ctx.preload ? 'true' : 'false'
  )
  // maxItems: {% if not widget.is_multiple %}1{% else %}{% if widget.max_items %}{{ widget.max_items }}{% else %}null{% endif %}{% endif %}
  js = js.replace(
    /\{%\s*if not widget\.is_multiple\s*%\}1\{%\s*else\s*%\}\{%\s*if widget\.max_items\s*%\}\{\{\s*widget\.max_items\s*\}\}\{%\s*else\s*%\}null\{%\s*endif\s*%\}\{%\s*endif\s*%\}/g,
    ctx.isMultiple ? (ctx.maxItems == null ? 'null' : String(ctx.maxItems)) : '1'
  )
  // showValueField: {% if 'dropdown_header' in widget.plugins.keys and widget.plugins.dropdown_header.show_value_field %}true{% else %}false{% endif %}
  js = js.replace(
    /\{%\s*if 'dropdown_header' in widget\.plugins\.keys and widget\.plugins\.dropdown_header\.show_value_field\s*%\}true\{%\s*else\s*%\}false\{%\s*endif\s*%\}/g,
    'false'
  )
  // create: {% if 'create' in widget.keys and widget.create %}true{% else %}false{% endif %}
  js = js.replace(
    /\{%\s*if 'create' in widget\.keys and widget\.create\s*%\}true\{%\s*else\s*%\}false\{%\s*endif\s*%\}/g,
    ctx.create ? 'true' : 'false'
  )

  // 5+7. filterConfig.filters block (lines 107-117) - anchored on `filters: [`
  // immediately after the opening tag to disambiguate from the filterFields block.
  js = js.replace(
    /\{%\s*if "filters" in widget\.keys\s*%\}\s*filters:[\s\S]*?\{%\s*elif "dependent_field" in widget\.keys\s*%\}[\s\S]*?\{%\s*endif\s*%\}/,
    renderFilterConfigFilters(ctx.filters || [])
  )
  // 6+7. filterConfig.excludes block (lines 118-127) - anchored on `excludes: [`
  js = js.replace(
    /\{%\s*if "excludes" in widget\.keys\s*%\}\s*excludes:[\s\S]*?\{%\s*elif "exclude_field" in widget\.keys\s*%\}[\s\S]*?\{%\s*endif\s*%\}/,
    renderFilterConfigExcludes(ctx.excludes || [])
  )

  // 5b. config.filterFields block (lines 232-236) - anchored on `filterFields: [`
  const filterFieldsJs = renderFieldArray(ctx.filters || [], formPrefix)
  js = js.replace(
    /\{%\s*if "filters" in widget\.keys\s*%\}\s*filterFields:[\s\S]*?\{%\s*elif "dependent_field" in widget\.keys\s*%\}[\s\S]*?\{%\s*endif\s*%\}/,
    filterFieldsJs ? `filterFields: [${filterFieldsJs}],` : ''
  )
  // 6b. config.excludeFields block (lines 237-241) - anchored on `excludeFields: [`
  const excludeFieldsJs = renderFieldArray(ctx.excludes || [], formPrefix)
  js = js.replace(
    /\{%\s*if "excludes" in widget\.keys\s*%\}\s*excludeFields:[\s\S]*?\{%\s*elif "exclude_field" in widget\.keys\s*%\}[\s\S]*?\{%\s*endif\s*%\}/,
    excludeFieldsJs ? `excludeFields: [${excludeFieldsJs}],` : ''
  )

  // 8. autocompleteParams ternary inside filterConfig
  js = js.replace(
    /'\{%\s*if 'autocomplete_params' in widget\.keys and not widget\.autocomplete_params == ""\s*%\}\{\{\s*widget\.autocomplete_params\|escapejs\s*\}\}\{%\s*endif\s*%\}'/,
    `'${escapeJsLiteral(ctx.autocompleteParams || '')}'`
  )

  // 9. plugins block - emit minimal plugins
  js = js.replace(
    /\{%\s*block tomselect_plugins\s*%\}[\s\S]*?\{%\s*endblock tomselect_plugins\s*%\}/,
    'plugins: { virtual_scroll: true },'
  )

  // 10. onInitialize selected-options block (lines 289-313) - take the empty branch.
  // The block contains nested {% if "create_url" in option.keys %}{% endif %} pairs
  // inside a {% for option in widget.selected_options %} loop, so a non-greedy
  // {% if %}...{% endif %} match would stop at the wrong endif. Anchor on
  // {% endfor %} to ensure we consume the full outer if-block.
  js = js.replace(
    /\{%\s*if widget\.value\s*%\}[\s\S]*?\{%\s*endfor\s*%\}[\s\S]*?\{%\s*endif\s*%\}/,
    ''
  )

  // 11. {% block tomselect_render %}...{% endblock %}
  // Default: emit an empty render block (cheaper, avoids loading partials that
  // most tests don't exercise). When widgetContext.optionCreate is provided,
  // splice in the real render/option_create.html partial (substituted) so the
  // cloned config's render.option_create can be exercised end-to-end.
  const renderBlockBody = ctx.optionCreate
    ? `render: { ${renderOptionCreatePartial(ctx.optionCreate)} }`
    : 'render: {}'
  js = js.replace(
    /\{%\s*block tomselect_render\s*%\}[\s\S]*?\{%\s*endblock tomselect_render\s*%\}/,
    () => renderBlockBody  // function form: avoids $-interpretation of ${...} JS template literals
  )

  // 12. {% if 'render' in widget.attrs.keys and widget.attrs.render %}...{% endif %} - omit
  js = js.replace(
    /\{%\s*if 'render' in widget\.attrs\.keys and widget\.attrs\.render\s*%\}[\s\S]*?\{%\s*endif\s*%\}/g,
    ''
  )

  // 13. {% translate "..." %} - replace with literal English string in quotes (already inside quotes in template)
  js = js.replace(/\{%\s*translate "([^"]*)"\s*%\}/g, '$1')

  // 14. Remaining named scalars from widgetContext (escapejs literals)
  js = js.replace(/\{\{\s*widget\.search_param\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.searchParam))
  js = js.replace(/\{\{\s*widget\.filter_param\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.filterParam))
  js = js.replace(/\{\{\s*widget\.exclude_param\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.excludeParam))
  js = js.replace(/\{\{\s*widget\.page_param\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.pageParam))
  js = js.replace(/\{\{\s*widget\.value_field\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.valueField))
  js = js.replace(/\{\{\s*widget\.label_field\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.labelField))
  js = js.replace(/\{\{\s*widget\.loading_class\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.loadingClass))
  js = js.replace(/\{\{\s*widget\.autocomplete_url\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.autocompleteUrl))
  js = js.replace(/\{\{\s*widget\.minimum_query_length\s*\}\}/g, String(ctx.minimumQueryLength))
  // widget.name appears in the _sr_status IDs and the const widgetName declaration
  js = js.replace(/\{\{\s*widget\.name\|escapejs\s*\}\}/g, escapeJsLiteral(ctx.name))

  // 15. csp_nonce attribute - omit (no nonce in test)
  js = js.replace(/\{%\s*if csp_nonce\s*%\}[^{]*?\{%\s*endif\s*%\}/g, '')

  // 16. Inner Django block markers ({% block tomselect_url_setup %}, tomselect_config,
  // etc.) - strip the markers themselves; their bodies are real JS we keep.
  js = js.replace(/\{%\s*block\s+\w+\s*%\}/g, '')
  js = js.replace(/\{%\s*endblock\s+\w*\s*%\}/g, '')

  // Final validation
  if (js.includes('{%') || js.includes('{{')) {
    const leftover = js.match(/\{[%{][^}]{0,80}/)
    throw new Error('renderWidgetTemplate: leftover Django template tags after substitution: ' + (leftover ? leftover[0] : '?'))
  }

  return js
}

function renderFieldArray (fields, formPrefix) {
  return (fields || [])
    .filter(f => f.sourceType === 'field')
    .map(f => {
      const effectivePrefix = harnessTruncatePrefix(formPrefix, f.levelsUp || 0)
      return `'id_${escapeJsLiteral(effectivePrefix + f.source)}'`
    })
    .join(', ')
}

// Render render/option_create.html with widget context substituted.
// optionCreateCtx: { createWithHtmx: boolean, viewCreateUrl: string }
// Returns the JS body (option_create: function(data, escape){...},) ready to
// splice into a `render: { ... }` block. Function-form replacements throughout
// to avoid $-interpretation of ${this.input.id} / ${escape(data.input)} in the
// JS template literals embedded in the partial.
function renderOptionCreatePartial (optionCreateCtx) {
  let partial = readFileSync(OPTION_CREATE_TEMPLATE_PATH, 'utf-8')

  partial = partial.replace(/\{%\s*comment\s*%\}[\s\S]*?\{%\s*endcomment\s*%\}/g, '')
  partial = partial.replace(/\{%\s*load\s+[^%]*%\}/g, '')

  // Resolve the create_with_htmx conditional. Anchored loosely so future
  // additions to the predicate don't break the harness.
  partial = partial.replace(
    /\{%\s*if 'create_with_htmx' in widget\.keys[\s\S]*?widget\.view_create_url\s*%\}([\s\S]*?)\{%\s*else\s*%\}([\s\S]*?)\{%\s*endif\s*%\}/,
    (_, htmxBranch, plainBranch) => optionCreateCtx.createWithHtmx ? htmxBranch : plainBranch
  )

  partial = partial.replace(
    /\{\{\s*widget\.view_create_url\|escapejs\s*\}\}/g,
    () => escapeJsLiteral(optionCreateCtx.viewCreateUrl || '')
  )

  // {% translate "..." %} and {% translate '...' %}
  partial = partial.replace(/\{%\s*translate\s+"([^"]*)"\s*%\}/g, (_, s) => s)
  partial = partial.replace(/\{%\s*translate\s+'([^']*)'\s*%\}/g, (_, s) => s)

  return partial.trim()
}

function renderFilterConfigFilters (filters) {
  if (!filters || filters.length === 0) return ''
  const items = filters.map(f =>
    `{ source: '${escapeJsLiteral(f.source)}', lookup: '${escapeJsLiteral(f.lookup)}', sourceType: '${escapeJsLiteral(f.sourceType)}', levelsUp: ${Number(f.levelsUp || 0)} }`
  ).join(', ')
  return `filters: [${items}],`
}

function renderFilterConfigExcludes (excludes) {
  if (!excludes || excludes.length === 0) return ''
  const items = excludes.map(e =>
    `{ source: '${escapeJsLiteral(e.source)}', lookup: '${escapeJsLiteral(e.lookup)}', sourceType: '${escapeJsLiteral(e.sourceType)}', levelsUp: ${Number(e.levelsUp || 0)} }`
  ).join(', ')
  return `excludes: [${items}],`
}

// Inject a per-widget IIFE script into the JSDOM document. The corresponding <select>
// (and any sibling filter/exclude inputs) must already exist in the DOM, since the
// IIFE bails on `if (!element) return;` when document.getElementById misses.
export function injectWidgetScript (widgetContext) {
  const realWindow = getJsdomWindow()
  const js = renderWidgetTemplate(widgetContext)
  const script = realWindow.document.createElement('script')
  script.dataset.harness = 'dts-widget'
  script.textContent = js
  realWindow.document.head.appendChild(script)
  return script
}

// Stub TomSelect that mirrors enough of tom-select for the per-widget load/shouldLoad/onBlur
// to execute end-to-end. Unlike TomSelectStub (which is just a destroy/wrapper shim),
// this:
// - Stores instance.settings = Object.assign({}, user_settings) (mimics getSettings.ts)
// - Binds load/shouldLoad/onBlur/getUrl from the config so `this === instance`
// - Provides no-op implementations for clearOptions/clearCache/clearPagination/etc.
export class IntegrationTomSelectStub {
  constructor (element, config) {
    this.element = element
    // Real Tom Select 2.x exposes the underlying <select> as `this.input` (see
    // node_modules/tom-select/src/tom-select.ts:171). Mirror that so config
    // callbacks reading this.input work under test.
    this.input = element
    this.config = config
    this.destroyed = false
    this.items = []
    this.options = {}
    this.userOptions = {}
    this.settings = Object.assign({ pagination: {} }, config)
    if (!this.settings.pagination) this.settings.pagination = {}

    // Real TomSelect tracks isFocused; some config methods (notably onBlur) early-return
    // on `!self.isFocused`. Default to false so future tests that drive onBlur don't
    // silently skip the deactivate path - they can opt into focused state explicitly.
    this.isFocused = false

    this.dropdown_content = element.ownerDocument.createElement('div')

    if (typeof config.load === 'function') {
      this.load = config.load.bind(this)
    }
    if (typeof config.shouldLoad === 'function') {
      this.shouldLoad = config.shouldLoad.bind(this)
    }
    if (typeof config.onBlur === 'function') {
      this.onBlur = config.onBlur.bind(this)
    }
    if (typeof config.getUrl === 'function') {
      this.getUrl = config.getUrl.bind(this)
    }

    element.tomselect = this
  }

  // No-op stubs that mirror real TomSelect surface used by load/resetTomSelectState
  clear () {}
  clearOptions () {}
  clearCache () {}
  clearPagination () {}
  setNextUrl (query, url) { this.settings.pagination[query] = url }
  addOption () {}
  addOptions () {}
  setValue () {}
  setActiveItem () {}
  setCaret () {}
  close () {}
  on () {}
  updateOption () {}
  scrollToOption () {}

  destroy () {
    this.destroyed = true
    delete this.element.tomselect
  }
}
