import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setupHarness, makeSelect, getJsdomWindow } from '../helpers/harness.js'

describe('smoke: cleanup (SPA navigation teardown)', () => {
  let dts
  let realWindow
  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  it('destroys every stored instance and clears both Maps', () => {
    const select1 = makeSelect({ id: 'id_a' })
    const select2 = makeSelect({ id: 'id_b' })
    const i1 = dts.initialize(select1, {})
    const i2 = dts.initialize(select2, {})
    expect(dts.instances.size).toBe(2)
    expect(dts.configs.size).toBe(2)

    dts.cleanup()

    expect(i1.destroyed).toBe(true)
    expect(i2.destroyed).toBe(true)
    expect(dts.instances.size).toBe(0)
    expect(dts.configs.size).toBe(0)
  })

  it('flips initialized back to false so a later setupHandlers() can re-run', () => {
    dts.initialized = true
    dts.cleanup()
    expect(dts.initialized).toBe(false)
  })

  it('disconnects the MutationObserver and nulls the reference when one is set', () => {
    const disconnect = vi.fn()
    dts.observer = { disconnect }
    dts.cleanup()
    expect(disconnect).toHaveBeenCalledOnce()
    expect(dts.observer).toBeNull()
  })

  it('is a safe no-op when no instances and no observer exist', () => {
    expect(() => dts.cleanup()).not.toThrow()
    expect(dts.instances.size).toBe(0)
    expect(dts.configs.size).toBe(0)
    expect(dts.observer).toBeNull()
  })

  it('continues clearing state even if one instance.destroy() throws', () => {
    const cleanDestroy = vi.fn()
    dts.instances.set('throws', { destroy: () => { throw new Error('boom') } })
    dts.instances.set('clean', { destroy: cleanDestroy })

    expect(() => dts.cleanup()).not.toThrow()
    expect(cleanDestroy).toHaveBeenCalledOnce()
    expect(dts.instances.size).toBe(0)
    expect(dts.configs.size).toBe(0)
  })

  it('skips instances whose destroy is not a function', () => {
    dts.instances.set('bad', { destroy: 'not-a-function' })
    expect(() => dts.cleanup()).not.toThrow()
    expect(dts.instances.size).toBe(0)
  })

  it('deletes wasReset_* globals for each tracked config via config.resetVarName', () => {
    realWindow['wasReset_id_a'] = false
    realWindow['wasReset_id_b'] = false
    dts.instances.set('id_a', { destroy: vi.fn() })
    dts.instances.set('id_b', { destroy: vi.fn() })
    dts.configs.set('id_a', { resetVarName: 'wasReset_id_a' })
    dts.configs.set('id_b', { resetVarName: 'wasReset_id_b' })

    dts.cleanup()

    expect(Object.hasOwn(realWindow, 'wasReset_id_a')).toBe(false)
    expect(Object.hasOwn(realWindow, 'wasReset_id_b')).toBe(false)
  })

  it('falls back to ID-derived name when resetVarName is absent (hyphen -> underscore)', () => {
    realWindow['wasReset_id_formset_0_field'] = false
    dts.instances.set('id_formset-0-field', { destroy: vi.fn() })
    dts.configs.set('id_formset-0-field', {})

    dts.cleanup()

    expect(Object.hasOwn(realWindow, 'wasReset_id_formset_0_field')).toBe(false)
  })

  it('handles IDs with dots, underscores, and numeric-looking strings without affecting unrelated globals', () => {
    // Id with underscores already present: id_formset-0-user_email_123
    //   replace(/-/g, '_') -> id_formset_0_user_email_123
    realWindow['wasReset_id_formset_0_user_email_123'] = false
    // Id with dots: id.form.0.field
    //   replace(/-/g, '_') only rewrites hyphens, so dots survive verbatim.
    realWindow['wasReset_id.form.0.field'] = false
    // Numeric-looking id: '123'
    realWindow['wasReset_123'] = false
    // Unrelated global that must survive cleanup
    realWindow.appGlobal = 'preserve-me'

    dts.instances.set('id_formset-0-user_email_123', { destroy: vi.fn() })
    dts.configs.set('id_formset-0-user_email_123', {})
    dts.instances.set('id.form.0.field', { destroy: vi.fn() })
    dts.configs.set('id.form.0.field', {})
    dts.instances.set('123', { destroy: vi.fn() })
    dts.configs.set('123', {})

    dts.cleanup()

    expect(Object.hasOwn(realWindow, 'wasReset_id_formset_0_user_email_123')).toBe(false)
    expect(Object.hasOwn(realWindow, 'wasReset_id.form.0.field')).toBe(false)
    expect(Object.hasOwn(realWindow, 'wasReset_123')).toBe(false)
    expect(realWindow.appGlobal).toBe('preserve-me')
  })

  it('guard rejects non-wasReset_* names stored in config.resetVarName (data-integrity safety)', () => {
    realWindow.someAppFlag = true
    realWindow['wasReset_id_x'] = false
    dts.configs.set('id_x', { resetVarName: 'someAppFlag' })
    dts.instances.set('id_x', { destroy: vi.fn() })

    dts.cleanup()

    expect(realWindow.someAppFlag).toBe(true)
    expect(Object.hasOwn(realWindow, 'wasReset_id_x')).toBe(false)
  })

  it('cleans up instance-only entries (instances Map has key, configs does not)', () => {
    realWindow['wasReset_id_orphan'] = false
    dts.instances.set('id_orphan', {
      destroy: vi.fn(),
      settings: { resetVarName: 'wasReset_id_orphan' }
    })

    dts.cleanup()

    expect(Object.hasOwn(realWindow, 'wasReset_id_orphan')).toBe(false)
  })
})
