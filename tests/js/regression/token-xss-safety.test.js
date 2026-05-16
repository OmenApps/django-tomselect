// Token plugin XSS regression guard.
//
// client/plugins/token/index.js explicitly comments that "All DOM
// construction uses createElement + textContent (no innerHTML) so rendered
// chip/dropdown content is XSS-safe by construction." That contract has
// no test. A well-meaning future PR could swap one of the helpers from
// `text:` (which sets textContent) to setting innerHTML, and the bug
// would ship silently - the chips would still look right for benign
// values, and only weaponized inputs would expose the leak.
//
// This file probes each user/server input surface with classic XSS payloads
// and asserts:
//   1. No <script>/<img>/<iframe>/<svg> elements appear anywhere in the
//      widget root (the payload was NOT parsed as HTML).
//   2. The payload's literal characters DO appear in root.textContent
//      (the payload WAS rendered as text - the assertion isn't passing
//      vacuously because the payload was silently dropped).
//
// Surfaces covered:
//   - Token values from the hidden input (parsed quoted segment)
//   - Free-text chips from the hidden input
//   - Operator menu labels (server-controlled)
//   - Value dropdown labels (server-controlled)
//   - Resolved label from the resolve endpoint (server-controlled)
//   - Free-form hint draft (user-typed in value-mode)

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { init } from '../../../client/plugins/token/index.js'

// ---------------------------------------------------------------------------
// Test scaffolding (mirrors tests/js/integration/token-free-form.test.js)
// ---------------------------------------------------------------------------

const COMPOSITE_URL = '/api/q/'

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

function buildFetchMock ({ operators, valueResults = [], resolveResults = [] }) {
  return vi.fn(async (requestUrl) => {
    const url = new URL(String(requestUrl), 'http://localhost')
    const mode = url.searchParams.get('mode')
    if (mode === 'operators') {
      return { ok: true, status: 200, json: async () => ({ operators, free_text_lookups: [] }) }
    }
    if (mode === 'value') {
      return { ok: true, status: 200, json: async () => ({ results: valueResults }) }
    }
    if (mode === 'resolve') {
      return { ok: true, status: 200, json: async () => ({ results: resolveResults }) }
    }
    return { ok: true, status: 200, json: async () => ({}) }
  })
}

function clearBody () {
  while (document.body.firstChild) document.body.removeChild(document.body.firstChild)
}

function mountWidget ({ initialValue = '', operators, valueResults = [], resolveResults = [] }) {
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
  root.dataset.config = JSON.stringify({})
  document.body.appendChild(root)

  const fetchMock = buildFetchMock({ operators, valueResults, resolveResults })
  window.fetch = fetchMock
  globalThis.fetch = fetchMock

  init(root)
  return { root, hidden, fetchMock }
}

async function flushAsync () {
  for (let i = 0; i < 5; i++) await Promise.resolve()
}

function getDraft (root) { return root.querySelector('.tw-input') }

function typeInto (input, value) {
  input.value = value
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

// Assert that no payload-derived HTML elements snuck in, AND that the
// payload's distinctive substring IS present in textContent (so we know the
// payload was actually rendered and not silently dropped).
function assertXssSafe (root, distinctiveSubstring) {
  expect(root.querySelectorAll('script').length).toBe(0)
  expect(root.querySelectorAll('img').length).toBe(0)
  expect(root.querySelectorAll('iframe').length).toBe(0)
  expect(root.querySelectorAll('svg').length).toBe(0)
  expect(root.querySelectorAll('object').length).toBe(0)
  expect(root.querySelectorAll('embed').length).toBe(0)
  expect(root.textContent).toContain(distinctiveSubstring)
}

const SCRIPT_PAYLOAD = '<script>window.__xss_marker__=1</script>'
const IMG_PAYLOAD = '<img src=x onerror="window.__xss_marker__=1">'
const SVG_PAYLOAD = '<svg onload="window.__xss_marker__=1"></svg>'

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('regression: token plugin XSS safety (createElement + textContent contract)', () => {
  beforeEach(() => {
    clearBody()
    delete window.__xss_marker__
    delete window.__djangoTomSelectTokenHydrationCache
  })

  afterEach(() => {
    delete window.fetch
    delete globalThis.fetch
    delete window.__xss_marker__
    delete window.__djangoTomSelectTokenHydrationCache
  })

  // -------------------------------------------------------------------------
  // 1. Token value rendered into a chip via buildTokenChip().
  //     - The parser only accepts identifier-style keys, so the attack
  //       surface is the VALUE half (after the colon). A quoted segment
  //       lets the user smuggle anything into values[0].
  // -------------------------------------------------------------------------

  it('token value containing <script> is rendered as text, not parsed as HTML', async () => {
    // The hidden input arrives serialized as a quoted "author:<payload>".
    // Backslash-escape the inner quote so the tokenizer accepts it.
    const initialValue = '"author:' + SCRIPT_PAYLOAD + '"'
    const { root } = mountWidget({ initialValue, operators: [REGULAR_OP] })
    await flushAsync()

    assertXssSafe(root, 'window.__xss_marker__=1')
    expect(window.__xss_marker__).toBeUndefined()
  })

  it('token value containing <img onerror> is rendered as text', async () => {
    const initialValue = '"author:' + IMG_PAYLOAD + '"'
    const { root } = mountWidget({ initialValue, operators: [REGULAR_OP] })
    await flushAsync()

    assertXssSafe(root, 'onerror')
    expect(window.__xss_marker__).toBeUndefined()
  })

  // -------------------------------------------------------------------------
  // 2. Free-text chip rendered by buildFreeTextChip().
  //     - Any unquoted-without-colon segment becomes free text. A quoted
  //       segment whose content has no colon is also free text.
  // -------------------------------------------------------------------------

  it('free-text chip containing <svg onload> is rendered as text', async () => {
    const initialValue = '"' + SVG_PAYLOAD.replace(/"/g, '\\"') + '"'
    const { root } = mountWidget({ initialValue, operators: [REGULAR_OP] })
    await flushAsync()

    assertXssSafe(root, 'onload')
    expect(window.__xss_marker__).toBeUndefined()
  })

  // -------------------------------------------------------------------------
  // 3. Operator menu - server-controlled op.label and op.key (the server
  //    is trusted, but the contract is "render-as-text regardless"; a
  //    future regression that switches to innerHTML would also surface
  //    when an admin sets a label that LOOKS like markup, even unintended).
  // -------------------------------------------------------------------------

  it('operator label containing <script> is rendered as text in the dropdown', async () => {
    const malicious = {
      key: 'author',
      label: 'Author ' + SCRIPT_PAYLOAD,
      value_field: 'id',
      label_field: 'name',
      multi: false,
      free_form: false,
      max_count: null,
      min_count: 0
    }
    const { root } = mountWidget({ operators: [malicious] })
    await flushAsync()

    // Open the operator menu by typing a partial operator. The input
    // handler unconditionally calls showOperatorMenu(draft) when the
    // draft has no colon, which is the user-driven trigger that paints
    // op.label into the dropdown.
    const draft = getDraft(root)
    typeInto(draft, 'a')
    await flushAsync()

    assertXssSafe(root, 'window.__xss_marker__=1')
    expect(window.__xss_marker__).toBeUndefined()
  })

  // -------------------------------------------------------------------------
  // 4. Value dropdown - row[label_field] rendered by buildValueDropdown().
  // -------------------------------------------------------------------------

  it('value-dropdown row label containing <script> is rendered as text', async () => {
    const valueResults = [
      { id: 1, name: 'Alice ' + SCRIPT_PAYLOAD }
    ]
    const { root } = mountWidget({
      operators: [REGULAR_OP],
      valueResults
    })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'author:')
    await flushAsync()

    assertXssSafe(root, 'window.__xss_marker__=1')
    expect(window.__xss_marker__).toBeUndefined()
  })

  it('value-dropdown row id containing <img onerror> is rendered as text', async () => {
    // The id field is also rendered via .tw-opt-id - cover it explicitly
    // since renderChips' valueText path also concatenates ids.
    const valueResults = [
      { id: IMG_PAYLOAD, name: 'Alice' }
    ]
    const { root } = mountWidget({
      operators: [REGULAR_OP],
      valueResults
    })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'author:')
    await flushAsync()

    assertXssSafe(root, 'onerror')
    expect(window.__xss_marker__).toBeUndefined()
  })

  // -------------------------------------------------------------------------
  // 5. Resolve endpoint label - written into the hydration cache and read
  //    by buildTokenChip when rendering an existing token.
  // -------------------------------------------------------------------------

  it('resolved label from /api/q/?mode=resolve is rendered as text in the chip', async () => {
    const resolveResults = [
      { op: 'author', id: '42', value: '42', label: 'Alice ' + SCRIPT_PAYLOAD, missing: false }
    ]
    const { root } = mountWidget({
      initialValue: 'author:42',
      operators: [REGULAR_OP],
      resolveResults
    })
    // First renderChips runs before resolve completes; flush microtasks
    // until the resolve.then() chain settles and re-renders the chip with
    // the cached (malicious) label.
    await flushAsync()
    await flushAsync()

    assertXssSafe(root, 'window.__xss_marker__=1')
    expect(window.__xss_marker__).toBeUndefined()
  })

  // -------------------------------------------------------------------------
  // 6. Free-form hint draft - the user types the payload directly.
  // -------------------------------------------------------------------------

  it('free-form hint with <script> in the draft renders it as text', async () => {
    const { root } = mountWidget({ operators: [FREE_FORM_OP] })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'published_after:' + SCRIPT_PAYLOAD)
    await flushAsync()

    assertXssSafe(root, 'window.__xss_marker__=1')
    expect(window.__xss_marker__).toBeUndefined()
  })

  // -------------------------------------------------------------------------
  // 7. End-to-end commit: a free-form value typed with a payload, committed
  //    to the hidden input, and re-rendered as a chip - none of the path
  //    should ever execute the payload.
  // -------------------------------------------------------------------------

  it('end-to-end: typing + committing a malicious free-form value produces a text chip only', async () => {
    const { root, hidden } = mountWidget({ operators: [FREE_FORM_OP] })
    await flushAsync()

    const draft = getDraft(root)
    typeInto(draft, 'published_after:' + IMG_PAYLOAD)
    await flushAsync()

    draft.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }))
    await flushAsync()

    // The hidden input was updated (committed value) AND the chip re-rendered.
    expect(hidden.value).toContain('published_after:')
    assertXssSafe(root, 'onerror')
    expect(window.__xss_marker__).toBeUndefined()
  })
})
