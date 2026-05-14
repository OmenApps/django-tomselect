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

  it('matches nested formsets when both outer and inner indices differ', () => {
    dts.configs.set('id_orders-0-items-1-product', { url: '/nested' })
    const result = dts.findSimilarConfig('id_orders-2-items-3-product')
    expect(result).toBeTruthy()
    expect(result.url).toBe('/nested')
  })

  it('does not match when terminal field names differ (negative case)', () => {
    // Regression guard: normalising every `-\d+-` must not collapse IDs whose
    // stable (non-index) segments differ.
    dts.configs.set('id_orders-0-items-1-product', { url: '/x' })
    expect(dts.findSimilarConfig('id_orders-2-items-3-category')).toBeNull()
  })

  it('rebuilds formPrefix for nested formsets', () => {
    dts.configs.set('id_orders-0-items-1-product', {})
    const result = dts.findSimilarConfig('id_orders-2-items-3-product')
    expect(result.formPrefix).toBe('orders-2-items-3-')
  })

  it('rebuilds originalFirstUrl with the nested form prefix', () => {
    const calls = []
    const createFirstUrlFunction = (prefix, filterConfig) => {
      calls.push({ prefix, filterConfig })
      return () => `url-for-${prefix}`
    }
    dts.configs.set('id_orders-0-items-1-product', {
      createFirstUrlFunction,
      filterConfig: { foo: 'bar' }
    })
    const result = dts.findSimilarConfig('id_orders-2-items-3-product')
    expect(calls).toEqual([{ prefix: 'orders-2-items-3-', filterConfig: { foo: 'bar' } }])
    expect(result.originalFirstUrl()).toBe('url-for-orders-2-items-3-')
  })

  it('rewrites sibling filterFields positionally for nested formsets', () => {
    // Sibling fields share the select's full nesting depth; both indices get
    // substituted positionally.
    dts.configs.set('id_orders-0-items-1-product', {
      filterFields: ['id_orders-0-items-1-category', 'id_orders-0-items-1-color']
    })
    const result = dts.findSimilarConfig('id_orders-2-items-3-product')
    expect(result.filterFields).toEqual([
      'id_orders-2-items-3-category',
      'id_orders-2-items-3-color'
    ])
  })

  it('leaves surplus index positions unchanged when a filterField has more indices than the new selectId', () => {
    // Contract: applyIndices preserves the original index (does NOT fall back
    // to `0`) when a stored field has more `-\d+-` occurrences than the new
    // selectId provides. The stored SELECT structure must still match the
    // new selectId for lookup to succeed; surplus indices live only in the
    // related field.
    dts.configs.set('id_orders-0-product', {
      filterFields: ['id_orders-0-items-1-category']
    })
    const result = dts.findSimilarConfig('id_orders-3-product')
    // newIndices = ['3']; the second `-1-` in the field ID has no
    // corresponding new index, so it is preserved verbatim.
    expect(result.filterFields).toEqual(['id_orders-3-items-1-category'])
  })

  it('rebuilds firstUrl (not just originalFirstUrl) with the new prefix', () => {
    // tomselect.html exposes both `firstUrl` and `originalFirstUrl` in the
    // initial config. TomSelect's `getUrl()` reads
    // `this.settings.firstUrl(query)`, so a cloned config that updates only
    // originalFirstUrl would still issue AJAX with the stale prefix until
    // resetTomSelectState() reassigns firstUrl. Both must be rebuilt.
    const createFirstUrlFunction = (prefix) => () => `url-for-${prefix}`
    dts.configs.set('id_orders-0-items-1-product', {
      createFirstUrlFunction,
      filterConfig: {}
    })
    const result = dts.findSimilarConfig('id_orders-2-items-3-product')
    expect(result.originalFirstUrl()).toBe('url-for-orders-2-items-3-')
    expect(result.firstUrl()).toBe('url-for-orders-2-items-3-')
    expect(result.firstUrl).toBe(result.originalFirstUrl)
  })

  it('rewrites dependentField positionally for nested formsets', () => {
    dts.configs.set('id_orders-0-items-1-product', {
      dependentField: 'id_orders-0-items-1-category'
    })
    const result = dts.findSimilarConfig('id_orders-4-items-7-product')
    expect(result.dependentField).toBe('id_orders-4-items-7-category')
  })

  it('rewrites excludeFields and excludeField positionally for nested formsets', () => {
    dts.configs.set('id_orders-0-items-1-product', {
      excludeFields: ['id_orders-0-items-1-x', 'id_orders-0-items-1-w'],
      excludeField: 'id_orders-0-items-1-z'
    })
    const result = dts.findSimilarConfig('id_orders-5-items-6-product')
    expect(result.excludeFields).toEqual(['id_orders-5-items-6-x', 'id_orders-5-items-6-w'])
    expect(result.excludeField).toBe('id_orders-5-items-6-z')
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
