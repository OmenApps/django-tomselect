import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setupHarness, getJsdomWindow } from '../helpers/harness.js'

describe('smoke: cloneConfig', () => {
  let dts
  let realWindow
  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  it('preserves primitives', () => {
    const original = { s: 'hello', n: 42, b: true, f: 1.5 }
    const cloned = dts.cloneConfig(original)
    expect(cloned).toEqual(original)
    expect(cloned).not.toBe(original)
  })

  it('preserves null without treating it as object (typeof null === "object" guard)', () => {
    const original = { x: null }
    const cloned = dts.cloneConfig(original)
    expect(cloned.x).toBeNull()
  })

  it('preserves undefined own-property values', () => {
    const original = { defined: 1, undef: undefined }
    const cloned = dts.cloneConfig(original)
    expect('undef' in cloned).toBe(true)
    expect(cloned.undef).toBeUndefined()
  })

  it('deep-clones nested objects so mutations do not leak across copies', () => {
    const original = { inner: { count: 1, deeper: { name: 'a' } } }
    const cloned = dts.cloneConfig(original)
    cloned.inner.count = 99
    cloned.inner.deeper.name = 'z'
    expect(original.inner.count).toBe(1)
    expect(original.inner.deeper.name).toBe('a')
  })

  it('clones arrays so push/splice does not leak (string elements)', () => {
    const original = { items: ['a', 'b'] }
    const cloned = dts.cloneConfig(original)
    cloned.items.push('c')
    cloned.items.splice(0, 1)
    expect(original.items).toEqual(['a', 'b'])
    expect(cloned.items).toEqual(['b', 'c'])
  })

  it('produces a new RegExp instance preserving pattern and flags', () => {
    // RegExp must be constructed in JSDOM's realm so cloneConfig's
    // `config[key] instanceof RegExp` branch matches (the check uses JSDOM's
    // RegExp constructor; in production both creator and template run in the
    // same realm so this is automatic).
    const re = new realWindow.RegExp('abc', 'gi')
    const cloned = dts.cloneConfig({ pattern: re })
    expect(cloned.pattern).not.toBe(re)
    expect(cloned.pattern.source).toBe('abc')
    expect(cloned.pattern.flags).toBe('gi')
  })

  it('preserves functions by reference (does not attempt to clone)', () => {
    const fn = () => 'hello'
    const cloned = dts.cloneConfig({ handler: fn })
    expect(cloned.handler).toBe(fn)
    expect(cloned.handler()).toBe('hello')
  })

  it('ignores inherited (non-own) properties', () => {
    const proto = { inherited: 'should-not-clone' }
    const original = Object.create(proto)
    original.own = 'should-clone'
    const cloned = dts.cloneConfig(original)
    expect(cloned.own).toBe('should-clone')
    expect('inherited' in cloned).toBe(false)
  })
})

describe('smoke: findSimilarConfig (formset config inheritance)', () => {
  let dts
  let realWindow
  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  it('returns null when no similar key exists', () => {
    expect(dts.findSimilarConfig('id_form-0-field')).toBeNull()
  })

  it('finds a similar config by normalising the form index in the key', () => {
    dts.configs.set('id_formset-0-recipients', { url: '/x', value_field: 'id' })
    const result = dts.findSimilarConfig('id_formset-2-recipients')
    expect(result).toBeTruthy()
    expect(result.url).toBe('/x')
    expect(result.value_field).toBe('id')
  })

  it('rebuilds formPrefix from the new selectId', () => {
    dts.configs.set('id_formset-0-recipients', {})
    const result = dts.findSimilarConfig('id_formset-3-recipients')
    expect(result.formPrefix).toBe('formset-3-')
  })

  it('rewrites filterFields IDs with the new form index', () => {
    dts.configs.set('id_formset-0-recipients', {
      filterFields: ['id_formset-0-parent', 'id_formset-0-other']
    })
    const result = dts.findSimilarConfig('id_formset-5-recipients')
    expect(result.filterFields).toEqual(['id_formset-5-parent', 'id_formset-5-other'])
  })

  it('rewrites dependentField with the new form index', () => {
    dts.configs.set('id_formset-0-recipients', { dependentField: 'id_formset-0-parent' })
    const result = dts.findSimilarConfig('id_formset-7-recipients')
    expect(result.dependentField).toBe('id_formset-7-parent')
  })

  it('rewrites excludeFields and excludeField with the new form index', () => {
    dts.configs.set('id_formset-0-recipients', {
      excludeFields: ['id_formset-0-x'],
      excludeField: 'id_formset-0-y'
    })
    const result = dts.findSimilarConfig('id_formset-4-recipients')
    expect(result.excludeFields).toEqual(['id_formset-4-x'])
    expect(result.excludeField).toBe('id_formset-4-y')
  })

  it('rebuilds originalFirstUrl via createFirstUrlFunction with the new prefix', () => {
    const calls = []
    const createFirstUrlFunction = (prefix, filterConfig) => {
      calls.push({ prefix, filterConfig })
      return () => `url-for-${prefix}`
    }
    dts.configs.set('id_formset-0-recipients', {
      createFirstUrlFunction,
      filterConfig: { foo: 'bar' }
    })
    const result = dts.findSimilarConfig('id_formset-2-recipients')
    expect(calls).toEqual([{ prefix: 'formset-2-', filterConfig: { foo: 'bar' } }])
    expect(typeof result.originalFirstUrl).toBe('function')
    expect(result.originalFirstUrl()).toBe('url-for-formset-2-')
  })

  it('wraps load() so calling it sets _currentResetVar on this.settings and still invokes the original', () => {
    // Scope note: this verifies the WRAPPER from findSimilarConfig. The
    // per-widget load() defined in tomselect.html reads its OWN closed-over
    // `resetVarName` and `originalFirstUrl`, not `_currentResetVar`. So a
    // green test here does not prove that cloned formset configs route
    // reset-triggered loads to the new prefix - only that this wrapper
    // sets the marker and forwards the call. Wider integration coverage
    // would require rendering tomselect.html alongside this template.
    const originalLoad = vi.fn()
    dts.configs.set('id_formset-0-recipients', { load: originalLoad })
    const result = dts.findSimilarConfig('id_formset-1-recipients')
    const fakeInstance = { settings: {} }
    const cb = vi.fn()
    result.load.call(fakeInstance, 'q', cb)
    expect(fakeInstance.settings._currentResetVar).toBe(result.resetVarName)
    expect(originalLoad).toHaveBeenCalledOnce()
    expect(originalLoad).toHaveBeenCalledWith('q', cb)
  })

  it('contract: only the FIRST -N- in the selectId is normalized (nested formsets cross inner indices do not match)', () => {
    // Documented limitation: id.replace(/-\d+-/, '-X-') replaces only the
    // first match. For nested formsets like `id_outer-0-inner-1-field`, a
    // lookup against `id_outer-2-inner-3-field` normalizes both to
    // `id_outer-X-inner-1-field` and `id_outer-X-inner-3-field`, which differ
    // on the inner index - so no match. Outer-only varying indices DO match.
    dts.configs.set('id_outer-0-inner-1-field', { url: '/nested' })
    expect(dts.findSimilarConfig('id_outer-2-inner-3-field')).toBeNull()
    const sameInner = dts.findSimilarConfig('id_outer-9-inner-1-field')
    expect(sameInner).toBeTruthy()
    expect(sameInner.url).toBe('/nested')
  })

  it('drops instance-specific state (items, renderCache) from the cloned config', () => {
    dts.configs.set('id_formset-0-recipients', {
      items: [1, 2, 3],
      renderCache: { foo: 'bar' }
    })
    const result = dts.findSimilarConfig('id_formset-2-recipients')
    expect(result.items).toBeUndefined()
    expect(result.renderCache).toBeUndefined()
  })

  it('creates a fresh reset variable on the JSDOM window for the new instance', () => {
    dts.configs.set('id_formset-0-recipients', {})
    const result = dts.findSimilarConfig('id_formset-9-recipients')
    expect(result.resetVarName).toBe('wasReset_id_formset_9_recipients')
    expect(realWindow[result.resetVarName]).toBe(false)
  })
})
