// Regression: filter_by / exclude_by must keep the dependent dropdown EMPTY
// when the upstream source field has no value.
//
// Documented contract (see docs/example_app/filter_by_magazine.md and
// docs/example_app/exclude_by_primary_author.md):
//
//   "If no magazine is selected, the Edition dropdown remains empty."
//   "If no Primary Author is selected, the Contributing Authors field will
//    remain empty."
//
// Pre-fix bug: createFirstUrlFunction silently skipped the filter URL param
// when the source field was empty (`if (filterValue)` guard at the
// per-filter loop). The backend then received a request with no filter
// constraint and returned the full unfiltered queryset, populating the
// dependent dropdown with rows the user shouldn't be able to choose.
//
// Fix: load() now calls hasUnsatisfiedDependency(prefix, filterCfg) BEFORE
// issuing fetch. When any field-type filter or exclude has an empty source
// value, load() short-circuits with callback([]) and skips the network
// round-trip entirely. Constant filters/excludes (sourceType !== 'field')
// have no DOM source so they never trigger the short-circuit.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  injectWidgetScript,
  IntegrationTomSelectStub
} from '../helpers/harness.js'

function makeFilterInput (id, value) {
  const realWindow = getJsdomWindow()
  const el = realWindow.document.createElement('input')
  el.id = id
  if (value !== undefined) el.value = value
  realWindow.document.body.appendChild(el)
  return el
}

function makeDependentSelect (id) {
  const realWindow = getJsdomWindow()
  const select = realWindow.document.createElement('select')
  select.id = id
  select.setAttribute('data-tomselect', 'true')
  realWindow.document.body.appendChild(select)
  return select
}

describe('regression: dependent dropdown must be empty when upstream source is empty', () => {
  let dts, realWindow, originalFetch, fetchMock

  beforeEach(() => {
    dts = setupHarness({ TomSelectClass: IntegrationTomSelectStub })
    realWindow = getJsdomWindow()

    originalFetch = realWindow.fetch
    fetchMock = vi.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ results: [], has_more: false, page: 1, total_pages: 1 })
    }))
    realWindow.fetch = fetchMock
  })

  afterEach(() => {
    realWindow.fetch = originalFetch
  })

  // ---------------------------------------------------------------------
  // Modern array-based filter / exclude config (filter_by tuple compiles
  // to widget.filters via TomSelectConfig.get_normalized_filters).
  // ---------------------------------------------------------------------

  it('field-type filter: empty source field => no fetch, callback receives []', async () => {
    // Magazine input exists but has no value (user has not selected one yet)
    makeFilterInput('id_magazine', '')
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [{ source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 }]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('field-type filter: populated source field => fetch fires with filter param', async () => {
    makeFilterInput('id_magazine', '42')
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [{ source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 }]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(fetchMock).toHaveBeenCalledOnce()
    const fetchedUrl = fetchMock.mock.calls[0][0]
    expect(fetchedUrl).toContain('magazine__magazine_id%3D42')
  })

  it('field-type exclude: empty source field => no fetch, callback receives []', async () => {
    makeFilterInput('id_primary_author', '')
    const select = makeDependentSelect('id_contributing_authors')

    injectWidgetScript({
      id: 'id_contributing_authors',
      autocompleteUrl: '/autocomplete/author/',
      excludes: [{ source: 'primary_author', lookup: 'id', sourceType: 'field', levelsUp: 0 }]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('field-type exclude: populated source field => fetch fires with exclude param', async () => {
    makeFilterInput('id_primary_author', '7')
    const select = makeDependentSelect('id_contributing_authors')

    injectWidgetScript({
      id: 'id_contributing_authors',
      autocompleteUrl: '/autocomplete/author/',
      excludes: [{ source: 'primary_author', lookup: 'id', sourceType: 'field', levelsUp: 0 }]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(fetchMock).toHaveBeenCalledOnce()
    const fetchedUrl = fetchMock.mock.calls[0][0]
    expect(fetchedUrl).toContain('primary_author__id%3D7')
  })

  it('constant filter alone (no field-type source) => fetch fires regardless of DOM state', async () => {
    const select = makeDependentSelect('id_articles')

    injectWidgetScript({
      id: 'id_articles',
      autocompleteUrl: '/autocomplete/article/',
      // sourceType 'const' = no DOM source, always applied
      filters: [{ source: 'published', lookup: 'status', sourceType: 'const', levelsUp: 0 }]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(fetchMock).toHaveBeenCalledOnce()
    const fetchedUrl = fetchMock.mock.calls[0][0]
    expect(fetchedUrl).toContain('__const__status%3Dpublished')
  })

  it('mixed filters: field-type empty + constant => short-circuit (field unsatisfied)', async () => {
    // The user has a constant filter (always applies) AND a field-type
    // filter (depends on magazine). Magazine is empty, so the contract
    // requires an empty dropdown regardless of the constant.
    makeFilterInput('id_magazine', '')
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [
        { source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 },
        { source: 'published', lookup: 'status', sourceType: 'const', levelsUp: 0 }
      ]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('mixed filters: all field-type sources populated => fetch fires with all params', async () => {
    makeFilterInput('id_magazine', '42')
    makeFilterInput('id_year', '2024')
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [
        { source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 },
        { source: 'year', lookup: 'year', sourceType: 'field', levelsUp: 0 }
      ]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(fetchMock).toHaveBeenCalledOnce()
    const fetchedUrl = fetchMock.mock.calls[0][0]
    expect(fetchedUrl).toContain('magazine__magazine_id%3D42')
    expect(fetchedUrl).toContain('year__year%3D2024')
  })

  it('one of multiple field-type filters empty => short-circuit (any-empty rule)', async () => {
    // Per docs, ALL field-type dependencies must be satisfied.
    makeFilterInput('id_magazine', '42')
    makeFilterInput('id_year', '')  // year is empty -- should short-circuit
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [
        { source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 },
        { source: 'year', lookup: 'year', sourceType: 'field', levelsUp: 0 }
      ]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('filter satisfied + exclude empty => short-circuit (exclude unsatisfied)', async () => {
    makeFilterInput('id_magazine', '42')
    makeFilterInput('id_primary_author', '')
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [{ source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 }],
      excludes: [{ source: 'primary_author', lookup: 'id', sourceType: 'field', levelsUp: 0 }]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('no filter/exclude configured => fetch fires (unchanged baseline)', async () => {
    const select = makeDependentSelect('id_magazine')

    injectWidgetScript({
      id: 'id_magazine',
      autocompleteUrl: '/autocomplete/magazine/'
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(fetchMock).toHaveBeenCalledOnce()
  })

  it('source field missing from DOM entirely => treated as empty, short-circuit', async () => {
    // No id_magazine input exists in DOM at all (parent field not yet
    // rendered, formset clone race, etc.). The contract still requires
    // an empty dropdown rather than an unfiltered one.
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [{ source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 }]
    })

    const cb = vi.fn()
    select.tomselect.load('', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('short-circuit while a prior fetch is in-flight does not render error UI', async () => {
    // Race scenario: user had a value selected upstream, dependent load
    // fetch started, then user cleared the upstream while the fetch was
    // still in flight. The short-circuit must abort cleanly without
    // letting the in-flight catch handler render the "Failed to load
    // options" error message in the dropdown.
    const magazine = makeFilterInput('id_magazine', '42')
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [{ source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 }]
    })

    // Capture fetch options so we can drive the AbortSignal manually.
    let capturedSignal = null
    let rejectFetch = null
    realWindow.fetch = vi.fn((_url, opts) => {
      capturedSignal = opts && opts.signal
      return new Promise((_resolve, reject) => {
        rejectFetch = reject
      })
    })

    // Capture any error UI writes that the in-flight catch might attempt.
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    // 1. First load with upstream populated -- fetch starts and hangs.
    const firstCb = vi.fn()
    select.tomselect.load('', firstCb)
    expect(realWindow.fetch).toHaveBeenCalledOnce()
    expect(capturedSignal).toBeTruthy()
    expect(capturedSignal.aborted).toBe(false)

    // 2. User clears the upstream field.
    magazine.value = ''

    // 3. Second load (e.g. triggered by setupFieldHandlers reset) hits the
    //    short-circuit. The fix nulls _currentLoadController.
    const secondCb = vi.fn()
    select.tomselect.load('', secondCb)
    expect(secondCb).toHaveBeenCalledWith([])
    expect(capturedSignal.aborted).toBe(true)

    // 4. Simulate the in-flight fetch settling with AbortError (what
    //    AbortController.abort() actually causes browsers to emit).
    const abortErr = new Error('The user aborted a request.')
    abortErr.name = 'AbortError'
    rejectFetch(abortErr)

    // Wait a microtask for the catch handler to run.
    await new Promise(resolve => setTimeout(resolve, 10))

    // 5. The catch handler must take the silent supersede path: no
    //    error logged, dropdown_content not populated with error markup.
    expect(consoleErrorSpy).not.toHaveBeenCalled()
    expect(select.tomselect.dropdown_content.innerHTML).not.toContain('ts-error-message')
    expect(select.tomselect.dropdown_content.innerHTML).not.toContain('Failed to load')

    consoleErrorSpy.mockRestore()
  })

  it('non-empty query string still short-circuits when source is empty', async () => {
    // Typing in the dependent field before the parent has a value must
    // still produce an empty dropdown; the user typing does not override
    // the unsatisfied dependency.
    makeFilterInput('id_magazine', '')
    const select = makeDependentSelect('id_edition')

    injectWidgetScript({
      id: 'id_edition',
      autocompleteUrl: '/autocomplete/edition/',
      filters: [{ source: 'magazine', lookup: 'magazine_id', sourceType: 'field', levelsUp: 0 }]
    })

    const cb = vi.fn()
    select.tomselect.load('iss', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
