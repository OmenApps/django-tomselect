// Verifies that when findSimilarConfig clones a config for a new formset row,
// the cloned config's per-widget load() actually reads its NEW resetVarName /
// originalFirstUrl from this.settings - not the source widget's closure.
//
// This file complements tests/js/smoke/config-cloning.test.js by exercising
// the real per-widget load() defined in tomselect.html (rendered via
// renderWidgetTemplate in the harness), not just findSimilarConfig in
// isolation. See the prior dead-wrapper test removal in config-cloning.test.js.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  injectWidgetScript,
  IntegrationTomSelectStub
} from '../helpers/harness.js'

describe('integration: cloned-instance load reads settings, not closure', () => {
  let dts
  let realWindow
  let originalFetch
  let fetchMock

  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()

    // The unqualified fetch(url, ...) call in the per-widget load() resolves
    // against JSDOM's window, not Node's globalThis. Stub on realWindow.
    originalFetch = realWindow.fetch
    fetchMock = vi.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ results: [], has_more: false, page: 1, total_pages: 1 })
    }))
    realWindow.fetch = fetchMock

    // JSDOM provides AbortController; spot-verify so a future env regression is loud.
    if (typeof realWindow.AbortController !== 'function') {
      throw new Error('JSDOM environment does not expose AbortController')
    }
  })

  afterEach(() => {
    realWindow.fetch = originalFetch
  })

  function setupOriginalWidget () {
    // Source row's <select> + sibling filter input must exist before the IIFE runs
    // because the IIFE's `if (!element) return` bails on null lookup.
    const select0 = realWindow.document.createElement('select')
    select0.id = 'id_formset-0-recipients'
    select0.setAttribute('data-tomselect', 'true')
    realWindow.document.body.appendChild(select0)

    const filter0 = realWindow.document.createElement('input')
    filter0.id = 'id_formset-0-magazine'
    filter0.value = '42'
    realWindow.document.body.appendChild(filter0)

    injectWidgetScript({
      id: 'id_formset-0-recipients',
      autocompleteUrl: '/autocomplete/recipients/',
      filters: [{ source: 'magazine', lookup: 'exact', sourceType: 'field', levelsUp: 0 }]
    })

    return select0
  }

  function setupClonedRow () {
    const select1 = realWindow.document.createElement('select')
    select1.id = 'id_formset-1-recipients'
    select1.setAttribute('data-tomselect', 'true')
    realWindow.document.body.appendChild(select1)

    const filter1 = realWindow.document.createElement('input')
    filter1.id = 'id_formset-1-magazine'
    filter1.value = '99'
    realWindow.document.body.appendChild(filter1)

    return select1
  }

  it('issues fetch with the cloned row prefix on reset path', async () => {
    setupOriginalWidget()
    const select1 = setupClonedRow()

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    expect(cloned).toBeTruthy()
    expect(cloned.resetVarName).toBe('wasReset_id_formset_1_recipients')

    const instance = new IntegrationTomSelectStub(select1, cloned)

    // Force the reset path: the cloned widget's reset flag is set BEFORE load().
    realWindow[cloned.resetVarName] = true

    const cb = vi.fn()
    instance.load('', cb)

    // load() doesn't return the fetch chain; wait for the user callback.
    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 2000 })

    expect(fetchMock).toHaveBeenCalled()
    const fetchedUrl = fetchMock.mock.calls[0][0]

    // Reset path uses originalFirstUrl with the NEW prefix - so the
    // magazine filter should pick up id_formset-1-magazine ("99"), not the source
    // widget's id_formset-0-magazine ("42").
    expect(fetchedUrl).toContain('magazine__exact%3D99')
    expect(fetchedUrl).not.toContain('magazine__exact%3D42')
  })

  it('clears the cloned reset flag, not the source widget flag', async () => {
    setupOriginalWidget()
    const select1 = setupClonedRow()

    const sourceResetVar = 'wasReset_id_formset_0_recipients'
    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    const instance = new IntegrationTomSelectStub(select1, cloned)

    // Source widget seeded its own flag at IIFE init time.
    expect(realWindow[sourceResetVar]).toBe(false)

    realWindow[cloned.resetVarName] = true

    const cb = vi.fn()
    instance.load('', cb)
    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 2000 })

    // Cloned load() cleared its OWN flag.
    expect(realWindow[cloned.resetVarName]).toBe(false)
    // And did NOT touch the source widget's flag (still its initial false seed).
    expect(realWindow[sourceResetVar]).toBe(false)
  })

  it('shouldLoad reads this.settings.resetVarName, not the source closure', () => {
    setupOriginalWidget()
    const select1 = setupClonedRow()

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    const instance = new IntegrationTomSelectStub(select1, cloned)

    // Source widget's flag set true; cloned widget's flag false.
    realWindow['wasReset_id_formset_0_recipients'] = true
    realWindow[cloned.resetVarName] = false

    // Empty query and source flag true would cause shouldLoad to return true if
    // the cloned widget were reading the source closure. With the settings-based
    // read, the cloned widget reads its OWN flag (false) and falls through to the
    // length-vs-minimum-query-length check - which returns false for empty input.
    const result = instance.shouldLoad('')
    expect(result).toBe(false)

    // Now set the cloned widget's own flag true; same empty query should return true.
    realWindow[cloned.resetVarName] = true
    const resultWithReset = instance.shouldLoad('')
    expect(resultWithReset).toBe(true)
  })
})
