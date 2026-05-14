// Regression test for ISSUE_findsimilarconfig_element_closure_leak.md
//
// When findSimilarConfig clones a config for a new formset row, the cloned
// config's callbacks must target the cloned row's DOM - NOT the source
// widget's. Before the fix, four callbacks closed over the source IIFE:
//   - onDropdownOpen / onDropdownClose flipped aria-expanded on the source
//     <select> via the IIFE-captured `element` constant.
//   - onItemAdd / onItemRemove wrote sr-status text to the source row's
//     <span> via the template-rendered '{{widget.name}}_sr_status' literal.
//
// The fix routes these through `this.input` (the per-instance underlying
// element exposed by real Tom Select 2.x). The cloned select's `name`
// attribute reflects the cloned row's formset prefix, so deriving the
// sr-status id from `this.input.name` is correct for both clean and
// cloned configs.

import { describe, it, expect, beforeEach } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  injectWidgetScript,
  IntegrationTomSelectStub
} from '../helpers/harness.js'

describe('regression: cloned-config callbacks target this.input, not the source widget closure', () => {
  let dts
  let realWindow

  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  function setupSourceWidget () {
    const select0 = realWindow.document.createElement('select')
    select0.id = 'id_formset-0-recipients'
    select0.name = 'formset-0-recipients'
    select0.setAttribute('data-tomselect', 'true')
    realWindow.document.body.appendChild(select0)

    const status0 = realWindow.document.createElement('span')
    status0.id = 'formset-0-recipients_sr_status'
    realWindow.document.body.appendChild(status0)

    injectWidgetScript({
      id: 'id_formset-0-recipients',
      name: 'formset-0-recipients',
      autocompleteUrl: '/autocomplete/recipients/'
    })

    return { select0, status0 }
  }

  function setupClonedRow () {
    const select1 = realWindow.document.createElement('select')
    select1.id = 'id_formset-1-recipients'
    select1.name = 'formset-1-recipients'
    select1.setAttribute('data-tomselect', 'true')
    realWindow.document.body.appendChild(select1)

    const status1 = realWindow.document.createElement('span')
    status1.id = 'formset-1-recipients_sr_status'
    realWindow.document.body.appendChild(status1)

    return { select1, status1 }
  }

  it('onDropdownOpen sets aria-expanded on the cloned select, not the source', () => {
    const { select0 } = setupSourceWidget()
    const { select1 } = setupClonedRow()

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    expect(cloned).toBeTruthy()

    const instance = new IntegrationTomSelectStub(select1, cloned)

    cloned.onDropdownOpen.call(instance)

    expect(select1.getAttribute('aria-expanded')).toBe('true')
    // Source select must be untouched.
    expect(select0.getAttribute('aria-expanded')).toBeNull()
  })

  it('onDropdownClose sets aria-expanded=false on the cloned select, not the source', () => {
    const { select0 } = setupSourceWidget()
    const { select1 } = setupClonedRow()

    // Seed both with 'true' so the test cleanly distinguishes which one the
    // callback toggles to 'false'.
    select0.setAttribute('aria-expanded', 'true')
    select1.setAttribute('aria-expanded', 'true')

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    const instance = new IntegrationTomSelectStub(select1, cloned)

    cloned.onDropdownClose.call(instance)

    expect(select1.getAttribute('aria-expanded')).toBe('false')
    // Source select still 'true'.
    expect(select0.getAttribute('aria-expanded')).toBe('true')
  })

  it('onItemAdd writes sr-status text to the cloned span, not the source span', () => {
    const { status0 } = setupSourceWidget()
    const { select1, status1 } = setupClonedRow()

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    const instance = new IntegrationTomSelectStub(select1, cloned)

    cloned.onItemAdd.call(instance, '42', { textContent: '  Bob  ' })

    expect(status1.textContent).toBe('Bob selected')
    expect(status0.textContent).toBe('')
  })

  it('onItemRemove writes sr-status text to the cloned span, not the source span', () => {
    const { status0 } = setupSourceWidget()
    const { select1, status1 } = setupClonedRow()

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    const instance = new IntegrationTomSelectStub(select1, cloned)

    cloned.onItemRemove.call(instance, '42')

    expect(status1.textContent).toBe('Item removed')
    expect(status0.textContent).toBe('')
  })
})
