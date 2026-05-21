// Regression: two independent (non-formset-clone) widgets on the same page
// must not share runtime state. Several historical bugs traced to
// IIFE-scoped variables leaking across instances:
//
//   - _currentLoadController shared via IIFE closure (fixed in
//     `Make currentLoadController and previousQuery per-instance to prevent
//     cross-row leaks`)
//   - _previousQuery shared via the same path
//   - resetVarName collisions when elementId-derived names overlap
//
// The fixes moved this state onto `self` / `self.settings`. These tests
// pin the contract so any regression that re-hoists state to the IIFE
// scope (or to a global) fails immediately.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  injectWidgetScript,
  IntegrationTomSelectStub
} from '../helpers/harness.js'

function makeSelectInDom (id) {
  const realWindow = getJsdomWindow()
  const select = realWindow.document.createElement('select')
  select.id = id
  select.setAttribute('data-tomselect', 'true')
  realWindow.document.body.appendChild(select)
  return select
}

function jsonResponse (body) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body) })
}

describe('regression: independent widgets do not share runtime state', () => {
  let dts, realWindow, originalFetch

  beforeEach(() => {
    dts = setupHarness({ TomSelectClass: IntegrationTomSelectStub })
    realWindow = getJsdomWindow()
    originalFetch = realWindow.fetch
  })

  afterEach(() => {
    realWindow.fetch = originalFetch
  })

  it('load() on widget A does not touch widget B\'s _currentLoadController', () => {
    // Both fetches hang -- we just want to inspect controller state.
    realWindow.fetch = vi.fn(() => new Promise(() => {}))

    const selectA = makeSelectInDom('id_a')
    injectWidgetScript({ id: 'id_a', autocompleteUrl: '/a/' })

    const selectB = makeSelectInDom('id_b')
    injectWidgetScript({ id: 'id_b', autocompleteUrl: '/b/' })

    selectA.tomselect.load('qa', vi.fn())
    const aController = selectA.tomselect._currentLoadController
    expect(aController).toBeTruthy()
    expect(aController.signal.aborted).toBe(false)

    selectB.tomselect.load('qb', vi.fn())
    const bController = selectB.tomselect._currentLoadController
    expect(bController).toBeTruthy()
    expect(bController).not.toBe(aController)

    // A's controller must be UNTOUCHED by B's load.
    expect(selectA.tomselect._currentLoadController).toBe(aController)
    expect(aController.signal.aborted).toBe(false)
  })

  it('reset flag (resetVarName) is per-element, not shared', () => {
    const selectA = makeSelectInDom('id_alpha')
    injectWidgetScript({ id: 'id_alpha', autocompleteUrl: '/a/' })

    const selectB = makeSelectInDom('id_beta')
    injectWidgetScript({ id: 'id_beta', autocompleteUrl: '/b/' })

    const aResetVar = selectA.tomselect.settings.resetVarName
    const bResetVar = selectB.tomselect.settings.resetVarName

    expect(aResetVar).toBeTruthy()
    expect(bResetVar).toBeTruthy()
    expect(aResetVar).not.toBe(bResetVar)

    realWindow[aResetVar] = true
    expect(realWindow[bResetVar]).not.toBe(true)
  })

  it('pagination state is per-instance', async () => {
    let aCallCount = 0
    let bCallCount = 0
    realWindow.fetch = vi.fn((url) => {
      if (url.includes('/a/')) {
        aCallCount++
        return jsonResponse({
          results: [{ id: `a-${aCallCount}` }],
          has_more: true,
          page: 1,
          next_page: 2,
          total_pages: 5  // > page so terminal auto-pagination doesn't fire
        })
      }
      bCallCount++
      return jsonResponse({
        results: [{ id: `b-${bCallCount}` }],
        has_more: true,
        page: 1,
        next_page: 2,
        total_pages: 5
      })
    })

    const selectA = makeSelectInDom('id_a')
    injectWidgetScript({ id: 'id_a', autocompleteUrl: '/a/' })

    const selectB = makeSelectInDom('id_b')
    injectWidgetScript({ id: 'id_b', autocompleteUrl: '/b/' })

    const cbA = vi.fn()
    const cbB = vi.fn()
    selectA.tomselect.load('shared', cbA)
    selectB.tomselect.load('shared', cbB)

    await vi.waitFor(() => expect(cbA).toHaveBeenCalled() && expect(cbB).toHaveBeenCalled(), { timeout: 1000 })

    // Each instance has its own pagination dict object.
    expect(selectA.tomselect.settings.pagination).not.toBe(selectB.tomselect.settings.pagination)

    // Both should have a 'shared' entry pointing at their OWN next-page URL.
    const aNext = selectA.tomselect.settings.pagination.shared
    const bNext = selectB.tomselect.settings.pagination.shared
    expect(aNext).toContain('/a/')
    expect(bNext).toContain('/b/')
  })

  it('_previousQuery (used by shouldLoad reset detection) is per-instance', () => {
    const selectA = makeSelectInDom('id_a')
    injectWidgetScript({ id: 'id_a', autocompleteUrl: '/a/' })

    const selectB = makeSelectInDom('id_b')
    injectWidgetScript({ id: 'id_b', autocompleteUrl: '/b/' })

    // shouldLoad records the query on the instance via this._previousQuery.
    selectA.tomselect.shouldLoad('alpha')
    selectB.tomselect.shouldLoad('beta')

    expect(selectA.tomselect._previousQuery).toBe('alpha')
    expect(selectB.tomselect._previousQuery).toBe('beta')
  })

  it('aborting widget A does not abort widget B (controller objects are distinct)', () => {
    realWindow.fetch = vi.fn(() => new Promise(() => {}))

    const selectA = makeSelectInDom('id_a')
    injectWidgetScript({ id: 'id_a', autocompleteUrl: '/a/' })

    const selectB = makeSelectInDom('id_b')
    injectWidgetScript({ id: 'id_b', autocompleteUrl: '/b/' })

    selectA.tomselect.load('qa', vi.fn())
    selectB.tomselect.load('qb', vi.fn())

    const bSignal = selectB.tomselect._currentLoadController.signal

    // Second load on A supersedes its own controller (only).
    selectA.tomselect.load('qa2', vi.fn())

    expect(bSignal.aborted).toBe(false)
  })
})
