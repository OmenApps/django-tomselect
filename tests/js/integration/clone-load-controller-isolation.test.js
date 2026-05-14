// Verifies that when findSimilarConfig clones a config for a new formset row,
// the cloned instance's load() does not abort the source widget's in-flight
// fetch via a shared currentLoadController.
//
// Pre-fix bug: currentLoadController was IIFE-scoped in tomselect.html, so the
// cloned config's load() (a reference to the source widget's load function)
// would read the source's slot and call .abort() on the source's controller.
// The aborted source fetch was caught as AbortError and silently delivered an
// empty result set to the source row.
//
// Post-fix: currentLoadController lives on the TomSelect instance as
// self._currentLoadController. Each instance has its own slot.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  injectWidgetScript,
  IntegrationTomSelectStub
} from '../helpers/harness.js'

describe('integration: cloned-instance load does not abort source fetch', () => {
  let dts
  let realWindow
  let originalFetch
  let fetchCalls

  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
    originalFetch = realWindow.fetch

    // Abort-aware deferred fetch mock. Each call returns a controllable promise
    // that respects opts.signal: aborting the signal rejects with AbortError.
    // This is required to expose the controller-sharing bug; a vanilla mock
    // that resolves immediately would pass pre-fix because the abort would
    // be a no-op against an already-resolved promise.
    fetchCalls = []
    realWindow.fetch = vi.fn((url, opts) => {
      const call = { url, opts, resolved: false, aborted: false }
      const promise = new Promise((resolve, reject) => {
        call.resolveJson = (payload) => {
          if (call.aborted) return
          call.resolved = true
          resolve({ ok: true, json: () => Promise.resolve(payload) })
        }
        call.rejectAbort = () => {
          if (call.resolved) return
          call.aborted = true
          const err = new Error('aborted')
          err.name = 'AbortError'
          reject(err)
        }
      })
      if (opts && opts.signal) {
        opts.signal.addEventListener('abort', () => call.rejectAbort())
      }
      fetchCalls.push(call)
      return promise
    })

    if (typeof realWindow.AbortController !== 'function') {
      throw new Error('JSDOM environment does not expose AbortController')
    }
  })

  afterEach(() => {
    realWindow.fetch = originalFetch
  })

  function setupSourceRow () {
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

  it('does not abort the source row fetch when the cloned row starts its own', async () => {
    const select0 = setupSourceRow()
    const select1 = setupClonedRow()

    // Build IntegrationTomSelectStub for both instances. The IIFE stored the
    // source config in dts.configs at id_formset-0-recipients; pull from
    // there rather than dts.instances (the default TomSelectStub the IIFE's
    // initialize() created does not bind load/shouldLoad).
    const sourceConfig = dts.configs.get('id_formset-0-recipients')
    expect(sourceConfig).toBeTruthy()
    const instance0 = new IntegrationTomSelectStub(select0, sourceConfig)

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    expect(cloned).toBeTruthy()
    const instance1 = new IntegrationTomSelectStub(select1, cloned)

    const cb0 = vi.fn()
    const cb1 = vi.fn()

    // Kick off instance0's fetch, then instance1's. Pre-fix, the second call
    // would abort the first call's controller through the shared IIFE var.
    instance0.load('a', cb0)
    instance1.load('b', cb1)

    expect(fetchCalls.length).toBe(2)

    // Each instance now holds its OWN AbortController. This is the invariant
    // that the per-instance migration enforces.
    expect(instance0._currentLoadController).toBeDefined()
    expect(instance1._currentLoadController).toBeDefined()
    expect(instance0._currentLoadController).not.toBe(instance1._currentLoadController)

    // The first fetch must not have been aborted by the second.
    expect(fetchCalls[0].aborted).toBe(false)

    // Resolve fetch #0 with real results; instance0 should get a non-empty payload.
    fetchCalls[0].resolveJson({
      results: [{ id: 1, name: 'a' }],
      has_more: false,
      page: 1,
      total_pages: 1
    })
    fetchCalls[1].resolveJson({
      results: [{ id: 2, name: 'b' }],
      has_more: false,
      page: 1,
      total_pages: 1
    })

    await vi.waitFor(() => {
      expect(cb0).toHaveBeenCalled()
      expect(cb1).toHaveBeenCalled()
    }, { timeout: 2000 })

    const cb0Args = cb0.mock.calls[0][0]
    const cb1Args = cb1.mock.calls[0][0]

    // Post-fix: cb0 received the real payload from fetch #0, not the
    // superseded-empty-array fallback the catch handler would have emitted
    // pre-fix when the cloned load aborted the source's controller.
    expect(Array.isArray(cb0Args)).toBe(true)
    expect(cb0Args.length).toBe(1)
    expect(cb0Args[0].id).toBe(1)

    expect(Array.isArray(cb1Args)).toBe(true)
    expect(cb1Args.length).toBe(1)
    expect(cb1Args[0].id).toBe(2)
  })

  it('still aborts the same-instance previous fetch on rapid retyping', async () => {
    // Counter-test: the per-instance migration must preserve the original
    // intent for the SAME instance: if the user types fast, the first
    // request should be aborted by the second on the same row.
    const select0 = setupSourceRow()
    const sourceConfig = dts.configs.get('id_formset-0-recipients')
    const instance0 = new IntegrationTomSelectStub(select0, sourceConfig)

    const cbA = vi.fn()
    const cbB = vi.fn()
    instance0.load('a', cbA)
    const firstController = instance0._currentLoadController
    instance0.load('ab', cbB)

    expect(fetchCalls.length).toBe(2)
    // Second load on the same instance replaced the slot with a new controller.
    expect(instance0._currentLoadController).not.toBe(firstController)
    // First fetch must have been aborted via the slot-replacement path.
    expect(fetchCalls[0].aborted).toBe(true)

    fetchCalls[1].resolveJson({
      results: [{ id: 2, name: 'ab' }],
      has_more: false,
      page: 1,
      total_pages: 1
    })

    await vi.waitFor(() => expect(cbB).toHaveBeenCalled(), { timeout: 2000 })

    // The superseded fetch's catch branch fires callback([]) silently.
    const cbAArgs = cbA.mock.calls.length > 0 ? cbA.mock.calls[0][0] : null
    if (cbAArgs !== null) {
      expect(cbAArgs).toEqual([])
    }
    const cbBArgs = cbB.mock.calls[0][0]
    expect(Array.isArray(cbBArgs)).toBe(true)
    expect(cbBArgs.length).toBe(1)
  })
})
