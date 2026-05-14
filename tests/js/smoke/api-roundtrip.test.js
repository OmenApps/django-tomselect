import { describe, it, expect, beforeEach } from 'vitest'
import { setupHarness, makeSelect } from '../helpers/harness.js'

describe('smoke: initialize / destroy round-trip', () => {
  let dts
  beforeEach(() => {
    dts = setupHarness()
  })

  it('destroy() removes the wrapper and the tomselected/ts-hidden-accessible classes from the select', () => {
    const select = makeSelect()
    dts.initialize(select, {})
    expect(document.querySelector('.ts-wrapper')).toBeTruthy()

    dts.destroy(select)
    expect(document.querySelector('.ts-wrapper')).toBeNull()
    expect(select.classList.contains('tomselected')).toBe(false)
    expect(select.classList.contains('ts-hidden-accessible')).toBe(false)
    expect(dts.instances.has(select.id)).toBe(false)
    expect(dts.configs.has(select.id)).toBe(false)
  })

  it('initialize() after destroy() restores a clean wrapper', () => {
    const select = makeSelect({ className: 'w-100' })
    dts.initialize(select, {})
    dts.destroy(select)
    const instance = dts.initialize(select, {})

    expect(instance).toBeTruthy()
    const wrappers = document.querySelectorAll('.ts-wrapper')
    expect(wrappers.length).toBe(1)
    expect(wrappers[0].classList.contains('ts-hidden-accessible')).toBe(false)
    expect(wrappers[0].classList.contains('w-100')).toBe(true)
  })

  it('initialize() rejects non-HTMLElement inputs gracefully', () => {
    expect(dts.initialize(null, {})).toBeNull()
    expect(dts.initialize('not-an-element', {})).toBeNull()
  })
})

describe('smoke: prepareElement preserves unrelated classes', () => {
  let dts
  beforeEach(() => {
    dts = setupHarness()
  })

  it('preserves unrelated classes on the select while stripping the two TS-added ones', () => {
    const select = makeSelect({ className: 'tomselected ts-hidden-accessible w-100 my-app-class' })
    dts.prepareElement(select)
    expect(select.classList.contains('w-100')).toBe(true)
    expect(select.classList.contains('my-app-class')).toBe(true)
    expect(select.classList.contains('tomselected')).toBe(false)
    expect(select.classList.contains('ts-hidden-accessible')).toBe(false)
  })
})

// Codex review note: an earlier draft included a "multi-wrapper cleanup"
// smoke test that nested wrappers inside each other and expected
// prepareElement() to flatten them. That test is invalid against the
// current template - element.parentNode.querySelectorAll('.ts-wrapper')
// only finds descendants of the parent, so ancestor/parent wrappers are
// never visited and the test would fail regardless of the fix. The
// wrapper-cleanup path in prepareElement is effectively dead code for
// real Tom Select DOM (wrappers are siblings of the input, not ancestors)
// and is a separate concern from this bug. Dropped per Codex review.

describe('smoke: fixAccessibilityClasses', () => {
  let dts
  beforeEach(() => {
    dts = setupHarness()
  })

  it('adds ts-hidden-accessible to selects that have a sibling .ts-wrapper but lack the class', () => {
    const container = document.createElement('div')
    document.body.appendChild(container)

    const select = document.createElement('select')
    select.id = 'id_fix'
    select.setAttribute('data-tomselect', 'true')
    container.appendChild(select)

    const wrapper = document.createElement('div')
    wrapper.className = 'ts-wrapper'
    container.appendChild(wrapper)

    expect(select.classList.contains('ts-hidden-accessible')).toBe(false)

    dts.fixAccessibilityClasses(container)

    expect(select.classList.contains('ts-hidden-accessible')).toBe(true)
  })

  it('does not add ts-hidden-accessible to .ts-wrapper itself', () => {
    const container = document.createElement('div')
    document.body.appendChild(container)

    const select = document.createElement('select')
    select.id = 'id_fix2'
    select.setAttribute('data-tomselect', 'true')
    container.appendChild(select)

    const wrapper = document.createElement('div')
    wrapper.className = 'ts-wrapper'
    container.appendChild(wrapper)

    dts.fixAccessibilityClasses(container)

    expect(wrapper.classList.contains('ts-hidden-accessible')).toBe(false)
  })
})
