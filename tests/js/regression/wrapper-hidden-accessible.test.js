import { describe, it, expect, beforeEach } from 'vitest'
import { setupHarness, makeSelect, loadTemplateScript, getJsdomWindow } from '../helpers/harness.js'

// Harness-utility tests intentionally do NOT call setupHarness() - they must
// fail FIRST and with a precise diagnostic if their prerequisites are wrong,
// rather than being masked by setupHarness() throwing.
describe('harness utility prerequisites', () => {
  it('JSDOM executes injected <script> elements (runScripts probe)', () => {
    // Vitest 4 keeps the test-facing `window` separate from JSDOM's internal
    // window. Side effects of injected scripts land on JSDOM's window
    // (window.jsdom.window), not on the test-facing global. So the probe
    // reads back via the JSDOM window directly.
    const realWindow = getJsdomWindow()
    delete realWindow.__dts_probe
    const probe = document.createElement('script')
    probe.textContent = 'window.__dts_probe = 42'
    document.head.appendChild(probe)
    expect(realWindow.__dts_probe).toBe(42)
  })

  it('loadTemplateScript picks the real djangoTomSelect block, not the comment example', () => {
    const js = loadTemplateScript()
    expect(js).toContain('window.djangoTomSelect')
    expect(js).toContain('prepareElement')
    expect(js).not.toContain('Custom global setup code here')
    expect(js).not.toContain('{%')
    expect(js).not.toContain('{{')
  })
})

describe('harness sanity', () => {
  let dts
  beforeEach(() => {
    dts = setupHarness()
  })

  it('loads djangoTomSelect and exposes the expected API', () => {
    expect(dts).toBeTruthy()
    expect(typeof dts.initialize).toBe('function')
    expect(typeof dts.destroy).toBe('function')
    expect(typeof dts.prepareElement).toBe('function')
    expect(typeof dts.fixAccessibilityClasses).toBe('function')
  })

  it('first initialize() produces a wrapper without ts-hidden-accessible and a select with it', () => {
    const select = makeSelect({ className: 'w-100 my-widget-class' })
    const instance = dts.initialize(select, {})
    expect(instance).toBeTruthy()
    const wrapper = document.querySelector('.ts-wrapper')
    expect(wrapper).toBeTruthy()
    expect(wrapper.classList.contains('ts-hidden-accessible')).toBe(false)
    expect(select.classList.contains('ts-hidden-accessible')).toBe(true)
    expect(select.classList.contains('tomselected')).toBe(true)
  })

  it('happy-path re-init (destroy succeeds) keeps the wrapper clean - passes either way; documents baseline', () => {
    // When destroy() succeeds, classes are already off the <select> before
    // snapshot, so the bug does NOT manifest here. This test belongs in
    // sanity, not regression - it proves the harness models the happy path
    // correctly, not that the fix works.
    const select = makeSelect({ className: 'w-100' })
    dts.initialize(select, {})
    dts.initialize(select, {})

    const wrappers = document.querySelectorAll('.ts-wrapper')
    expect(wrappers.length).toBe(1)
    expect(wrappers[0].classList.contains('ts-hidden-accessible')).toBe(false)
  })
})

describe('regression: ts-hidden-accessible must not transfer to the wrapper', () => {
  let dts
  beforeEach(() => {
    dts = setupHarness()
  })

  it('case A: prepareElement() strips ts-hidden-accessible alongside tomselected', () => {
    const select = makeSelect({ className: 'tomselected ts-hidden-accessible foo' })
    dts.prepareElement(select)
    expect(select.classList.contains('tomselected')).toBe(false)
    expect(select.classList.contains('ts-hidden-accessible')).toBe(false)
    expect(select.classList.contains('foo')).toBe(true)
  })

  it('case A2: prepareElement() does not affect hyphen-overlapping class names', () => {
    // Regression guard for the cleaner classList.remove() fix vs. the issue's
    // proposed \b-regex form. With the regex form, a class like
    // `my-tomselected-state` would be partially stripped. With classList.remove
    // it survives intact.
    const select = makeSelect({ className: 'tomselected my-tomselected-state ts-hidden-accessible something-ts-hidden-accessible-x' })
    dts.prepareElement(select)
    expect(select.classList.contains('my-tomselected-state')).toBe(true)
    expect(select.classList.contains('something-ts-hidden-accessible-x')).toBe(true)
    expect(select.classList.contains('tomselected')).toBe(false)
    expect(select.classList.contains('ts-hidden-accessible')).toBe(false)
  })

  it('case B: initialize() with lingering class + no live instance does not leak the class onto the new wrapper', () => {
    // Reproduces the bug from the issue: prior destroy() silently failed
    // (or never ran), so the <select> still carries ts-hidden-accessible
    // and no live instance is registered. The next initialize() must NOT
    // copy the lingering class onto the new wrapper.
    const select = makeSelect({ className: 'w-100 tomselected ts-hidden-accessible' })
    dts.instances.delete(select.id)
    delete select.tomselect
    expect(select.classList.contains('ts-hidden-accessible')).toBe(true)

    const instance = dts.initialize(select, {})

    expect(instance).toBeTruthy()
    expect(instance.wrapper.classList.contains('ts-hidden-accessible')).toBe(false)
    expect(instance.wrapper.classList.contains('ts-wrapper')).toBe(true)
    expect(instance.wrapper.classList.contains('w-100')).toBe(true)
  })
})
