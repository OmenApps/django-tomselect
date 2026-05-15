// Integration tests for the free-form operator path in the token widget
// plugin (client/plugins/token/index.js). These exercise the staged JS
// changes that ship via src/django_tomselect/static/django_tomselect/js/
// django-tomselect.js (the bundle of the same source).
//
// What's covered:
//   1. renderChips skips the resolve round-trip for free-form tokens.
//   2. showValueDropdown shows the typed-value hint instead of fetching
//      a server-backed value list.
//   3. Pressing Enter on a free-form draft commits `opKey:value`.
//   4. Pressing Space in value-mode for a free-form operator types
//      normally instead of committing free text.
//   5. serializeTokenSegment quotes values containing whitespace so the
//      round-trip through the hidden input stays parseable.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

import { init } from '../../../client/plugins/token/index.js'

// ---------------------------------------------------------------------------
// Test scaffolding
// ---------------------------------------------------------------------------

const COMPOSITE_URL = '/api/q/'

function classifyFetchCall (call) {
  const url = new URL(String(call[0]), 'http://localhost')
  return url.searchParams.get('mode')
}

function buildFetchMock (operators) {
  return vi.fn(async (requestUrl) => {
    const url = new URL(String(requestUrl), 'http://localhost')
    const mode = url.searchParams.get('mode')
    if (mode === 'operators') {
      return {
        ok: true,
        status: 200,
        json: async () => ({ operators, free_text_lookups: [] })
      }
    }
    if (mode === 'value') {
      return {
        ok: true,
        status: 200,
        json: async () => ({ results: [] })
      }
    }
    if (mode === 'resolve') {
      // Should NOT be hit by free-form tests; return empty so an
      // accidental call is still a green resolve, just verifiable
      // via fetchMock.mock.calls.
      return {
        ok: true,
        status: 200,
        json: async () => ({ results: [] })
      }
    }
    return {
      ok: true,
      status: 200,
      json: async () => ({})
    }
  })
}

function clearBody () {
  while (document.body.firstChild) {
    document.body.removeChild(document.body.firstChild)
  }
}

function mountWidget ({ initialValue = '', config = {}, operators }) {
  clearBody()
  const hidden = document.createElement('input')
  hidden.type = 'hidden'
  hidden.name = 'q'
  hidden.setAttribute('data-django-tomselect-token-input', '')
  hidden.value = initialValue
  document.body.appendChild(hidden)

  const root = document.createElement('div')
  root.dataset.targetName = 'q'
  root.dataset.compositeUrl = COMPOSITE_URL
  root.dataset.config = JSON.stringify(config)
  document.body.appendChild(root)

  const fetchMock = buildFetchMock(operators)
  window.fetch = fetchMock
  globalThis.fetch = fetchMock

  init(root)
  return { root, hidden, fetchMock }
}

// init() kicks off fetchOperators() and chains .then(...) which calls
// renderChips(). Flush the microtask queue enough times to settle the
// promise + the renderChips call.
async function flushAsync () {
  for (let i = 0; i < 5; i++) {
    await Promise.resolve()
  }
}

function getDraft (root) {
  return root.querySelector('.tw-input')
}

function getDropdown (root) {
  return root.querySelector('.tw-dropdown')
}

function typeInto (input, value) {
  input.value = value
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

function press (input, key) {
  input.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }))
}

const FREE_FORM_OP = {
  key: 'published_after',
  label: 'Published after',
  value_field: 'id',
  label_field: 'id',
  multi: false,
  free_form: true,
  max_count: 1,
  min_count: 0
}

const REGULAR_OP = {
  key: 'author',
  label: 'Author',
  value_field: 'id',
  label_field: 'name',
  multi: false,
  free_form: false,
  max_count: null,
  min_count: 0
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('token plugin: free-form operator integration', () => {
  beforeEach(() => {
    clearBody()
  })

  afterEach(() => {
    delete window.fetch
    delete globalThis.fetch
    // Reset shared hydration cache between tests (init writes to a global
    // Map so a previously-resolved label could mask scheduleResolve gating).
    delete window.__djangoTomSelectTokenHydrationCache
  })

  it('does not schedule a resolve fetch for free-form tokens already in the hidden input', async () => {
    // A free-form token has no server-side row to resolve to a label - the
    // typed string IS the value. Calling resolve would either return a
    // misleading "missing" or thrash the dropdown.
    const { fetchMock } = mountWidget({
      initialValue: 'published_after:2024-01-01',
      operators: [REGULAR_OP, FREE_FORM_OP]
    })

    await flushAsync()

    const modes = fetchMock.mock.calls.map(classifyFetchCall)
    expect(modes).toContain('operators')
    expect(modes).not.toContain('resolve')
  })

  it('still schedules a resolve fetch for non-free-form tokens (regression guard)', async () => {
    // Negative control: the skip applies only to free-form ops. A regular
    // filter_lookup token must still go through resolve so its label
    // renders in the chip.
    const { fetchMock } = mountWidget({
      initialValue: 'author:42',
      operators: [REGULAR_OP, FREE_FORM_OP]
    })

    await flushAsync()

    const modes = fetchMock.mock.calls.map(classifyFetchCall)
    expect(modes).toContain('operators')
    expect(modes).toContain('resolve')
  })

  it('shows the typed-value hint instead of a loading state when entering value-mode for a free-form op', async () => {
    const { root, fetchMock } = mountWidget({
      operators: [REGULAR_OP, FREE_FORM_OP]
    })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'published_after:')
    await flushAsync()

    const dropdown = getDropdown(root)
    expect(dropdown.hidden).toBe(false)
    // The free-form path renders a heading + a .tw-dropdown-hint and never
    // dispatches a mode=value fetch.
    expect(dropdown.querySelector('.tw-dropdown-hint')).not.toBeNull()
    expect(dropdown.textContent).not.toContain('Loading')

    const modes = fetchMock.mock.calls.map(classifyFetchCall)
    expect(modes).not.toContain('value')
  })

  it('updates the hint text with the current draft so the user sees what Enter will commit', async () => {
    const { root } = mountWidget({ operators: [FREE_FORM_OP] })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'published_after:2024-12-31')
    await flushAsync()

    const hint = getDropdown(root).querySelector('.tw-dropdown-hint')
    expect(hint).not.toBeNull()
    expect(hint.textContent).toContain('published_after:2024-12-31')
  })

  it('commits the draft as `opKey:value` when Enter is pressed in free-form value-mode', async () => {
    const { root, hidden } = mountWidget({ operators: [FREE_FORM_OP] })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'published_after:2024-01-01')
    await flushAsync()

    press(draft, 'Enter')
    await flushAsync()

    expect(hidden.value).toBe('published_after:2024-01-01')
    // After commit the draft must be cleared so the user can type the next
    // token without the previous value bleeding into it.
    expect(draft.value).toBe('')
  })

  it('quotes free-form values that contain whitespace so the parser can re-read them', async () => {
    // serializeTokenSegment is internal but observable via the hidden
    // input's value after a commit. A value with whitespace must be
    // wrapped in double quotes; without that, the next parseQuery would
    // split it into a token + free text.
    const { root, hidden } = mountWidget({ operators: [FREE_FORM_OP] })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'published_after:hello world')
    await flushAsync()

    press(draft, 'Enter')
    await flushAsync()

    expect(hidden.value).toBe('"published_after:hello world"')
  })

  it('does not commit on Space while typing a value for a free-form op', async () => {
    // For regular ops, Space commits the draft as free text (lets users
    // build queries by typing). For free-form ops we explicitly opt out so
    // the value can contain spaces - the user must press Enter/Tab.
    const { root, hidden } = mountWidget({ operators: [FREE_FORM_OP] })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'published_after:hello')
    await flushAsync()

    // Simulate user pressing Space; the handler must NOT call
    // commitFreeText, so the hidden input stays empty.
    const ev = new KeyboardEvent('keydown', { key: ' ', bubbles: true, cancelable: true })
    draft.dispatchEvent(ev)
    await flushAsync()

    expect(ev.defaultPrevented).toBe(false)
    expect(hidden.value).toBe('')
  })

  it('still commits on Space in non-value-mode (regression guard for the free-form opt-out)', async () => {
    // Make sure the new "skip Space-commit" branch is narrow: outside
    // value-mode, Space should keep committing free text as before.
    const { root, hidden } = mountWidget({
      operators: [REGULAR_OP, FREE_FORM_OP],
      config: { allow_free_text: true }
    })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'foo')
    await flushAsync()

    const ev = new KeyboardEvent('keydown', { key: ' ', bubbles: true, cancelable: true })
    draft.dispatchEvent(ev)
    await flushAsync()

    expect(ev.defaultPrevented).toBe(true)
    expect(hidden.value).toBe('foo')
  })
})
