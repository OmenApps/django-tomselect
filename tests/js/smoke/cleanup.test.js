import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setupHarness, makeSelect } from '../helpers/harness.js'

describe('smoke: cleanup (SPA navigation teardown)', () => {
  let dts
  beforeEach(() => { dts = setupHarness() })

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
})
