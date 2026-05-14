// Verifies that the previousQuery state used by shouldLoad() is per-instance,
// not shared across cloned configs.
//
// Pre-fix bug: previousQuery was IIFE-scoped in tomselect.html, so typing in
// the source row would set the shared previousQuery; the cloned row's first
// shouldLoad('') would see that non-empty value, classify the call as a
// non-empty->empty transition, and fire resetTomSelectState on the cloned
// row even though the user never typed in it.
//
// Post-fix: previousQuery lives on the TomSelect instance as
// this._previousQuery. Each instance has its own slot. Also,
// resetTomSelectState now clears _previousQuery so the same instance does
// not immediately re-fire the reset path.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  injectWidgetScript,
  IntegrationTomSelectStub
} from '../helpers/harness.js'

describe('integration: cloned-instance shouldLoad does not bleed previousQuery', () => {
  let dts
  let realWindow
  let originalFetch

  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
    originalFetch = realWindow.fetch

    // resetTomSelectState calls tomSelect.load(''), which calls fetch(...).
    // A minimal resolving mock keeps the reset path quiet so tests aren't
    // noisy with unrelated async failures.
    realWindow.fetch = vi.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ results: [], has_more: false, page: 1, total_pages: 1 })
    }))
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

  function buildPair () {
    const select0 = setupSourceRow()
    const select1 = setupClonedRow()
    const sourceConfig = dts.configs.get('id_formset-0-recipients')
    const clonedConfig = dts.findSimilarConfig('id_formset-1-recipients')
    expect(sourceConfig).toBeTruthy()
    expect(clonedConfig).toBeTruthy()
    return {
      instance0: new IntegrationTomSelectStub(select0, sourceConfig),
      instance1: new IntegrationTomSelectStub(select1, clonedConfig)
    }
  }

  it('typing in the source row does not trigger reset on the cloned row\'s first empty query', () => {
    const { instance0, instance1 } = buildPair()

    const clearOptionsSpy = vi.spyOn(instance1, 'clearOptions')
    const clearCacheSpy = vi.spyOn(instance1, 'clearCache')

    // Source row receives input.
    instance0.shouldLoad('abc')
    expect(instance0._previousQuery).toBe('abc')

    // Cloned row's first call: empty query. Pre-fix, the shared previousQuery
    // would be 'abc' and the reset path would fire on instance1.
    instance1.shouldLoad('')

    expect(clearOptionsSpy).not.toHaveBeenCalled()
    expect(clearCacheSpy).not.toHaveBeenCalled()

    // Source instance state is untouched by the cloned call.
    expect(instance0._previousQuery).toBe('abc')
    // Cloned instance recorded its own (empty) query.
    expect(instance1._previousQuery).toBe('')
  })

  it('same-instance non-empty -> empty transition still fires the reset path', () => {
    const { instance1 } = buildPair()
    const clearOptionsSpy = vi.spyOn(instance1, 'clearOptions')
    const clearCacheSpy = vi.spyOn(instance1, 'clearCache')

    instance1.shouldLoad('xyz')
    expect(instance1._previousQuery).toBe('xyz')

    instance1.shouldLoad('')

    // The per-instance migration must preserve the original intent for the
    // same instance: a non-empty->empty transition fires the reset helper.
    expect(clearOptionsSpy).toHaveBeenCalled()
    expect(clearCacheSpy).toHaveBeenCalled()
  })

  it('resetTomSelectState clears _previousQuery so subsequent empty queries do not re-fire', () => {
    const { instance1 } = buildPair()
    const clearOptionsSpy = vi.spyOn(instance1, 'clearOptions')

    // Drive the reset path via shouldLoad (resetTomSelectState is IIFE-scoped
    // and not directly callable from the test).
    instance1.shouldLoad('xyz')
    instance1.shouldLoad('')

    // The reset path ran, AND it cleared _previousQuery.
    expect(clearOptionsSpy).toHaveBeenCalledTimes(1)
    expect(instance1._previousQuery).toBe('')

    // A second consecutive shouldLoad('') must NOT fire the reset path again,
    // because _previousQuery is now ''.
    instance1.shouldLoad('')
    expect(clearOptionsSpy).toHaveBeenCalledTimes(1)
  })
})
