// setupFieldHandlers wiring tests.
//
// setupFieldHandlers is called by initialize() and is the bridge that makes
// dependent / exclude fields work: when the upstream field changes, the
// downstream (dependent) TomSelect must clear its cached selection and
// re-load from the server with the new filter applied. Before this file
// there was no direct coverage of:
//   - The four code paths (filterFields, legacy dependentField,
//     excludeFields, legacy excludeField).
//   - filterFields taking precedence over dependentField when both are set.
//   - The "field instance not yet in the map" silent skip (a common case
//     in formset clone scenarios).
//   - The early bailout when no dependent/exclude config is present.
//
// These tests stub the field instance with a minimal .on()/fireChange()
// recorder so we can drive the 'change' callback synchronously and assert
// that resetTomSelectState was invoked on the dependent instance.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setupHarness, getJsdomWindow } from '../helpers/harness.js'

// Minimal stub: exposes the .on()/destroy() surface that setupFieldHandlers
// and cleanup() use, plus fireChange() so tests can synthesize a user
// changing the upstream field.
class FieldStub {
  constructor () {
    this.listeners = {}
  }
  on (event, cb) {
    if (!this.listeners[event]) this.listeners[event] = []
    this.listeners[event].push(cb)
  }
  fireChange (value) {
    (this.listeners.change || []).forEach(cb => cb(value))
  }
  destroy () {}
}

describe('integration: setupFieldHandlers wiring', () => {
  let dts
  let realWindow

  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  // -------------------------------------------------------------------------
  // Early bailout - the four-flag short-circuit.
  // -------------------------------------------------------------------------

  it('is a no-op when none of dependentField/excludeField/filterFields/excludeFields is configured', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})
    const field = new FieldStub()
    dts.instances.set('id_some_field', field)

    // No dependent config at all - setupFieldHandlers should not subscribe.
    const dependentInstance = { dummy: true }
    dts.setupFieldHandlers(dependentInstance, {})

    field.fireChange('whatever')
    expect(resetSpy).not.toHaveBeenCalled()
  })

  // -------------------------------------------------------------------------
  // Legacy single-field paths.
  // -------------------------------------------------------------------------

  it('legacy dependentField: change on the upstream field triggers resetTomSelectState on the dependent instance', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    const upstreamField = new FieldStub()
    dts.instances.set('id_magazine', upstreamField)

    const dependent = { stub: 'dependent' }
    const config = { dependentField: 'id_magazine' }

    dts.setupFieldHandlers(dependent, config)
    upstreamField.fireChange(42)

    expect(resetSpy).toHaveBeenCalledOnce()
    expect(resetSpy).toHaveBeenCalledWith(dependent, config)
  })

  it('legacy excludeField: change on the upstream field triggers resetTomSelectState', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    const upstreamField = new FieldStub()
    dts.instances.set('id_exclude_source', upstreamField)

    const dependent = { stub: 'dependent' }
    const config = { excludeField: 'id_exclude_source' }

    dts.setupFieldHandlers(dependent, config)
    upstreamField.fireChange(7)

    expect(resetSpy).toHaveBeenCalledOnce()
    expect(resetSpy).toHaveBeenCalledWith(dependent, config)
  })

  // -------------------------------------------------------------------------
  // Plural filterFields / excludeFields paths.
  // -------------------------------------------------------------------------

  it('filterFields: every listed field gets a change handler and any one of them triggers reset', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    const f1 = new FieldStub()
    const f2 = new FieldStub()
    const f3 = new FieldStub()
    dts.instances.set('id_filter_a', f1)
    dts.instances.set('id_filter_b', f2)
    dts.instances.set('id_filter_c', f3)

    const dependent = { stub: 'dependent' }
    const config = { filterFields: ['id_filter_a', 'id_filter_b', 'id_filter_c'] }
    dts.setupFieldHandlers(dependent, config)

    f1.fireChange('a')
    f3.fireChange('c')
    f2.fireChange('b')

    expect(resetSpy).toHaveBeenCalledTimes(3)
    resetSpy.mock.calls.forEach(args => {
      expect(args[0]).toBe(dependent)
      expect(args[1]).toBe(config)
    })
  })

  it('excludeFields: every listed field gets a change handler', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    const e1 = new FieldStub()
    const e2 = new FieldStub()
    dts.instances.set('id_exclude_a', e1)
    dts.instances.set('id_exclude_b', e2)

    const dependent = { stub: 'dependent' }
    const config = { excludeFields: ['id_exclude_a', 'id_exclude_b'] }
    dts.setupFieldHandlers(dependent, config)

    e1.fireChange('a')
    e2.fireChange('b')

    expect(resetSpy).toHaveBeenCalledTimes(2)
  })

  // -------------------------------------------------------------------------
  // Plural-vs-legacy precedence: when BOTH filterFields and dependentField
  // are set, the plural form wins (the else-if structure in the source).
  // This matters for code that migrates from legacy to plural and forgets
  // to drop the old key - a duplicate subscription would double-fire.
  // -------------------------------------------------------------------------

  it('filterFields takes precedence over dependentField (no double subscription)', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    const pluralField = new FieldStub()
    const legacyField = new FieldStub()
    dts.instances.set('id_plural', pluralField)
    dts.instances.set('id_legacy', legacyField)

    const dependent = { stub: 'dependent' }
    const config = {
      filterFields: ['id_plural'],
      dependentField: 'id_legacy' // should be ignored when filterFields present
    }
    dts.setupFieldHandlers(dependent, config)

    legacyField.fireChange('legacy')
    expect(resetSpy).not.toHaveBeenCalled()

    pluralField.fireChange('plural')
    expect(resetSpy).toHaveBeenCalledOnce()
  })

  it('excludeFields takes precedence over excludeField', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    const pluralExclude = new FieldStub()
    const legacyExclude = new FieldStub()
    dts.instances.set('id_excl_plural', pluralExclude)
    dts.instances.set('id_excl_legacy', legacyExclude)

    const dependent = { stub: 'dependent' }
    const config = {
      excludeFields: ['id_excl_plural'],
      excludeField: 'id_excl_legacy'
    }
    dts.setupFieldHandlers(dependent, config)

    legacyExclude.fireChange('legacy')
    expect(resetSpy).not.toHaveBeenCalled()

    pluralExclude.fireChange('plural')
    expect(resetSpy).toHaveBeenCalledOnce()
  })

  // -------------------------------------------------------------------------
  // Silent skip when the upstream field isn't yet a registered TomSelect.
  // This happens in formset-clone races (the clone fires findSimilarConfig
  // before its upstream sibling has been initialized) and also when the
  // upstream "field" is a plain <input> rather than a TomSelect.
  // -------------------------------------------------------------------------

  it('silently skips fields whose ID is not in dts.instances (no throw)', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    // Only one of three upstreams is a registered TomSelect.
    const present = new FieldStub()
    dts.instances.set('id_present', present)

    const dependent = { stub: 'dependent' }
    const config = {
      filterFields: ['id_missing_1', 'id_present', 'id_missing_2']
    }

    expect(() => dts.setupFieldHandlers(dependent, config)).not.toThrow()

    // The only firing channel is the registered one.
    present.fireChange('go')
    expect(resetSpy).toHaveBeenCalledOnce()
  })

  // -------------------------------------------------------------------------
  // End-to-end via initialize(): the integration that real users hit.
  // initialize() auto-invokes setupFieldHandlers, so a config with a
  // dependent field should wire up the listener without an explicit call.
  // -------------------------------------------------------------------------

  it('initialize() auto-wires the dependent field handler', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    const upstream = new FieldStub()
    dts.instances.set('id_upstream', upstream)

    const select = realWindow.document.createElement('select')
    select.id = 'id_downstream'
    realWindow.document.body.appendChild(select)

    const config = { filterFields: ['id_upstream'] }
    const inst = dts.initialize(select, config)
    expect(inst).toBeTruthy()

    upstream.fireChange('something')
    expect(resetSpy).toHaveBeenCalledOnce()
    expect(resetSpy).toHaveBeenCalledWith(inst, config)
  })

  // -------------------------------------------------------------------------
  // Combined filterFields + excludeFields: both subscribe.
  // -------------------------------------------------------------------------

  it('subscribes to both filterFields and excludeFields when both are set', () => {
    const resetSpy = vi.spyOn(dts, 'resetTomSelectState').mockImplementation(() => {})

    const filterField = new FieldStub()
    const excludeField = new FieldStub()
    dts.instances.set('id_filter', filterField)
    dts.instances.set('id_exclude', excludeField)

    const dependent = { stub: 'dependent' }
    const config = {
      filterFields: ['id_filter'],
      excludeFields: ['id_exclude']
    }
    dts.setupFieldHandlers(dependent, config)

    filterField.fireChange('f')
    excludeField.fireChange('e')

    expect(resetSpy).toHaveBeenCalledTimes(2)
  })
})
