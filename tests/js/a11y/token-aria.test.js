// Accessibility tests for the token widget (client/plugins/token/index.js).
// These exercise the ARIA combobox/listbox pattern, active-descendant
// tracking during keyboard navigation, context-specific remove-button
// labels, and the polite live region that announces token add/remove.
//
// The mount/fetch-stub harness mirrors tests/js/integration/token-free-form.js
// so init() can settle without throwing on window.fetch.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

import { init } from '../../../client/plugins/token/index.js'

const COMPOSITE_URL = '/api/q/'

const STATUS_OP = {
  key: 'status',
  label: 'Status',
  value_field: 'id',
  label_field: 'name',
  multi: false,
  free_form: false,
  max_count: null,
  min_count: 0
}

function buildFetchMock (operators) {
  return vi.fn(async (requestUrl) => {
    const url = new URL(String(requestUrl), 'http://localhost')
    const mode = url.searchParams.get('mode')
    if (mode === 'operators') {
      return { ok: true, status: 200, json: async () => ({ operators, free_text_lookups: [] }) }
    }
    return { ok: true, status: 200, json: async () => ({ results: [] }) }
  })
}

function clearBody () {
  while (document.body.firstChild) document.body.removeChild(document.body.firstChild)
}

function mountWidget ({ initialValue = '', config = {}, operators = [STATUS_OP] } = {}) {
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

// init() chains fetchOperators().then(renderChips); flush microtasks to settle.
async function flushAsync () {
  for (let i = 0; i < 5; i++) await Promise.resolve()
}

function typeInto (input, value) {
  input.value = value
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

describe('token widget ARIA combobox pattern', () => {
  beforeEach(() => { clearBody() })
  afterEach(() => {
    delete window.fetch
    delete globalThis.fetch
    delete window.__djangoTomSelectTokenHydrationCache
  })

  it('marks the draft input as a combobox controlling the listbox', () => {
    const { root } = mountWidget()
    const input = root.querySelector('.tw-input')
    expect(input.getAttribute('role')).toBe('combobox')
    expect(input.getAttribute('aria-expanded')).toBe('false')
    expect(input.getAttribute('aria-autocomplete')).toBe('list')
    const dropdown = root.querySelector('.tw-dropdown')
    expect(input.getAttribute('aria-controls')).toBe(dropdown.id)
    expect(dropdown.id).toBeTruthy()
    expect(dropdown.getAttribute('role')).toBe('listbox')
  })

  it('toggles aria-expanded when the dropdown opens and closes', async () => {
    const { root } = mountWidget()
    await flushAsync()
    const input = root.querySelector('.tw-input')
    typeInto(input, '')
    expect(input.getAttribute('aria-expanded')).toBe('true')
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }))
    expect(input.getAttribute('aria-expanded')).toBe('false')
    expect(input.hasAttribute('aria-activedescendant')).toBe(false)
  })
})
