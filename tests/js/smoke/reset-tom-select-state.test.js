// resetTomSelectState unit tests.
//
// resetTomSelectState is the function the dependent-field machinery calls
// when an upstream field changes - it clears the dependent select's cached
// selection, options, cache, pagination, and scroll state, then triggers
// a fresh load with an empty query. It also flips the wasReset_* global
// flag that the autocomplete view reads to opt into the "reset" code path
// server-side.
//
// Prior coverage was indirect (clone-load-* tests). This file pins each
// observable side effect directly so a regression in any single step is
// caught at unit granularity.
//
// Stub strategy: a minimal InstanceStub object that records method calls
// in order and exposes the same shape (settings, dropdown_content, wrapper,
// load, ...) that the real TomSelect has. We do NOT use vi.spyOn on the
// dts.resetTomSelectState because we are testing IT - we want it to run.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setupHarness, getJsdomWindow } from '../helpers/harness.js'

function makeInstanceStub ({ withDropdown = true, withWrapper = true, settings = {} } = {}) {
  const calls = []
  const record = name => (...args) => { calls.push({ name, args }) }
  const realWindow = getJsdomWindow()
  return {
    calls,
    settings: { pagination: { 'a': '/next?a' }, ...settings },
    dropdown_content: withDropdown
      ? Object.assign(realWindow.document.createElement('div'), { scrollTop: 99 })
      : null,
    wrapper: withWrapper ? realWindow.document.createElement('div') : null,
    clear: record('clear'),
    clearOptions: record('clearOptions'),
    clearCache: record('clearCache'),
    clearPagination: record('clearPagination'),
    load: record('load')
  }
}

describe('smoke: resetTomSelectState side effects', () => {
  let dts
  let realWindow

  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  // -------------------------------------------------------------------------
  // Defensive: a null/undefined instance is a silent no-op.
  // -------------------------------------------------------------------------

  it('returns silently when instance is null', () => {
    expect(() => dts.resetTomSelectState(null, {})).not.toThrow()
  })

  it('returns silently when instance is undefined', () => {
    expect(() => dts.resetTomSelectState(undefined, {})).not.toThrow()
  })

  // -------------------------------------------------------------------------
  // The clear/clearOptions/clearCache/clearPagination quartet.
  // -------------------------------------------------------------------------

  it('calls clear(), clearOptions(), clearCache(), clearPagination() exactly once each', () => {
    const inst = makeInstanceStub()
    dts.resetTomSelectState(inst, {})

    const counts = inst.calls.reduce((acc, c) => {
      acc[c.name] = (acc[c.name] || 0) + 1
      return acc
    }, {})
    expect(counts.clear).toBe(1)
    expect(counts.clearOptions).toBe(1)
    expect(counts.clearCache).toBe(1)
    expect(counts.clearPagination).toBe(1)
  })

  it('calls clear() before clearOptions() before clearCache()', () => {
    const inst = makeInstanceStub()
    dts.resetTomSelectState(inst, {})

    const order = inst.calls.map(c => c.name)
    expect(order.indexOf('clear')).toBeLessThan(order.indexOf('clearOptions'))
    expect(order.indexOf('clearOptions')).toBeLessThan(order.indexOf('clearCache'))
  })

  // -------------------------------------------------------------------------
  // settings.pagination is wiped to {} (separate from clearPagination, which
  // is the TomSelect virtual-scroll plugin's own state).
  // -------------------------------------------------------------------------

  it('resets settings.pagination to an empty object', () => {
    const inst = makeInstanceStub({ settings: { pagination: { 'foo': '/next?foo' } } })
    expect(Object.keys(inst.settings.pagination).length).toBeGreaterThan(0)

    dts.resetTomSelectState(inst, {})
    expect(inst.settings.pagination).toEqual({})
  })

  // -------------------------------------------------------------------------
  // Scroll reset: dropdown_content.scrollTop = 0 when present; no throw when
  // missing.
  // -------------------------------------------------------------------------

  it('resets dropdown_content.scrollTop to 0 when dropdown_content exists', () => {
    const inst = makeInstanceStub({ withDropdown: true })
    inst.dropdown_content.scrollTop = 1234
    dts.resetTomSelectState(inst, {})
    expect(inst.dropdown_content.scrollTop).toBe(0)
  })

  it('does not throw when dropdown_content is missing', () => {
    const inst = makeInstanceStub({ withDropdown: false })
    expect(() => dts.resetTomSelectState(inst, {})).not.toThrow()
  })

  // -------------------------------------------------------------------------
  // URL function reset: config.originalFirstUrl wins, then instance.settings
  // fallback, then silent skip if neither.
  // -------------------------------------------------------------------------

  it('sets settings.firstUrl and settings.setNextUrl from config.originalFirstUrl', () => {
    const inst = makeInstanceStub()
    const fn = () => '/first/'
    dts.resetTomSelectState(inst, { originalFirstUrl: fn })
    expect(inst.settings.firstUrl).toBe(fn)
    expect(inst.settings.setNextUrl).toBe(fn)
  })

  it('falls back to instance.settings.originalFirstUrl when config.originalFirstUrl is absent', () => {
    const fallbackFn = () => '/fallback/'
    const inst = makeInstanceStub({ settings: { originalFirstUrl: fallbackFn, pagination: {} } })
    dts.resetTomSelectState(inst, {})
    expect(inst.settings.firstUrl).toBe(fallbackFn)
    expect(inst.settings.setNextUrl).toBe(fallbackFn)
  })

  it('prefers config.originalFirstUrl over instance.settings.originalFirstUrl', () => {
    const configFn = () => '/from-config/'
    const settingsFn = () => '/from-settings/'
    const inst = makeInstanceStub({ settings: { originalFirstUrl: settingsFn, pagination: {} } })
    dts.resetTomSelectState(inst, { originalFirstUrl: configFn })
    expect(inst.settings.firstUrl).toBe(configFn)
  })

  it('leaves settings.firstUrl untouched when neither URL source is set', () => {
    const inst = makeInstanceStub({ settings: { firstUrl: 'pre-existing', pagination: {} } })
    dts.resetTomSelectState(inst, {})
    expect(inst.settings.firstUrl).toBe('pre-existing')
  })

  // -------------------------------------------------------------------------
  // Wrapper "preloaded" class - matters because onFocus -> preload() would
  // otherwise fire another load() after we already loaded fresh data, and
  // virtual_scroll would then fetch page 2 stale-URL and clobber page 1.
  // -------------------------------------------------------------------------

  it('adds the "preloaded" class to instance.wrapper', () => {
    const inst = makeInstanceStub({ withWrapper: true })
    expect(inst.wrapper.classList.contains('preloaded')).toBe(false)
    dts.resetTomSelectState(inst, {})
    expect(inst.wrapper.classList.contains('preloaded')).toBe(true)
  })

  it('does not throw when instance.wrapper is missing', () => {
    const inst = makeInstanceStub({ withWrapper: false })
    expect(() => dts.resetTomSelectState(inst, {})).not.toThrow()
  })

  // -------------------------------------------------------------------------
  // _scrollResetPending flag - consumed by onDropdownOpen in tomselect.html.
  // -------------------------------------------------------------------------

  it('sets instance._scrollResetPending = true', () => {
    const inst = makeInstanceStub()
    expect(inst._scrollResetPending).toBeUndefined()
    dts.resetTomSelectState(inst, {})
    expect(inst._scrollResetPending).toBe(true)
  })

  // -------------------------------------------------------------------------
  // load('') is called with a callback - the empty query reloads fresh data.
  // -------------------------------------------------------------------------

  it('calls instance.load("", callback) to reload with the empty query', () => {
    const inst = makeInstanceStub()
    dts.resetTomSelectState(inst, {})
    const loadCalls = inst.calls.filter(c => c.name === 'load')
    expect(loadCalls.length).toBe(1)
    expect(loadCalls[0].args[0]).toBe('')
    expect(typeof loadCalls[0].args[1]).toBe('function')
  })

  // -------------------------------------------------------------------------
  // wasReset_* global flag: only flipped when (a) resetVar is named and
  // (b) the global already exists (typeof !== 'undefined'). This gate
  // prevents resetTomSelectState from accidentally creating arbitrary
  // globals on a stale config.
  // -------------------------------------------------------------------------

  it('flips window[resetVar] to true when config.resetVarName is set and the global pre-exists', () => {
    realWindow.wasReset_id_test = false
    const inst = makeInstanceStub()
    dts.resetTomSelectState(inst, { resetVarName: 'wasReset_id_test' })
    expect(realWindow.wasReset_id_test).toBe(true)
    delete realWindow.wasReset_id_test
  })

  it('falls back to instance.settings.resetVarName when config.resetVarName is absent', () => {
    realWindow.wasReset_id_fallback = false
    const inst = makeInstanceStub({ settings: { resetVarName: 'wasReset_id_fallback', pagination: {} } })
    dts.resetTomSelectState(inst, {})
    expect(realWindow.wasReset_id_fallback).toBe(true)
    delete realWindow.wasReset_id_fallback
  })

  it('does NOT create a new global when window[resetVar] does not pre-exist (typeof guard)', () => {
    expect(realWindow.wasReset_never_existed).toBeUndefined()
    const inst = makeInstanceStub()
    dts.resetTomSelectState(inst, { resetVarName: 'wasReset_never_existed' })
    // The typeof-undefined gate must keep the global from springing into
    // existence. This protects cleanup() and findSimilarConfig from
    // accumulating ghost globals from misconfigured rows.
    expect(Object.hasOwn(realWindow, 'wasReset_never_existed')).toBe(false)
  })

  it('does nothing with the reset flag when no resetVarName is provided', () => {
    const before = Object.keys(realWindow).filter(k => k.startsWith('wasReset_'))
    const inst = makeInstanceStub()
    dts.resetTomSelectState(inst, {})
    const after = Object.keys(realWindow).filter(k => k.startsWith('wasReset_'))
    expect(after).toEqual(before)
  })

  // -------------------------------------------------------------------------
  // End-to-end ordering invariant: the wasReset_* flag is set AFTER load()
  // is called. Otherwise the autocomplete view would see was_reset=true on
  // the very first request triggered BY the reset, which is the wrong
  // signal (the autocomplete should treat the first post-reset request as
  // ordinary, not as a reset that just happened).
  //
  // We assert this with a side-effect probe: load() captures the current
  // value of the wasReset_* global at call time.
  // -------------------------------------------------------------------------

  it('flips the wasReset_* flag AFTER calling instance.load("")', () => {
    realWindow.wasReset_order_check = false
    let observedAtLoadTime = null
    const inst = makeInstanceStub()
    inst.load = vi.fn(() => { observedAtLoadTime = realWindow.wasReset_order_check })

    dts.resetTomSelectState(inst, { resetVarName: 'wasReset_order_check' })
    expect(observedAtLoadTime).toBe(false)
    expect(realWindow.wasReset_order_check).toBe(true)
    delete realWindow.wasReset_order_check
  })
})
