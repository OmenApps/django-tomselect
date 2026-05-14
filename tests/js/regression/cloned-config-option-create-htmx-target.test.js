// Regression test for ISSUE_findsimilarconfig_option_create_htmx_target.md
//
// The option_create render callback in render/option_create.html previously
// baked widget.name into hx-target at template render time:
//
//   hx-target="#id_{{ widget.name|escapejs }}"
//
// Because cloneConfig copies the render callbacks by reference, the cloned
// formset row's "Create new option" button posted an HTMX swap targeted at
// the SOURCE row's <select> rather than the cloned row's. The fix resolves
// hx-target at call time via `#${this.input.id}` - which is per-instance
// because Tom Select invokes render callbacks with this === instance and
// this.input is the underlying <select>.

import { describe, it, expect, beforeEach } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  injectWidgetScript,
  IntegrationTomSelectStub
} from '../helpers/harness.js'

describe('regression: cloned render.option_create targets the cloned row, not the source', () => {
  let dts
  let realWindow

  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  function appendSelect (id, name) {
    const select = realWindow.document.createElement('select')
    select.id = id
    select.name = name
    select.setAttribute('data-tomselect', 'true')
    realWindow.document.body.appendChild(select)

    const status = realWindow.document.createElement('span')
    status.id = `${name}_sr_status`
    realWindow.document.body.appendChild(status)

    return select
  }

  it('hx-target resolves to the cloned select\'s id when called on the cloned instance', () => {
    appendSelect('id_formset-0-recipients', 'formset-0-recipients')
    injectWidgetScript({
      id: 'id_formset-0-recipients',
      name: 'formset-0-recipients',
      autocompleteUrl: '/autocomplete/recipients/',
      create: true,
      optionCreate: { createWithHtmx: true, viewCreateUrl: '/recipients/create/' }
    })

    const select1 = appendSelect('id_formset-1-recipients', 'formset-1-recipients')

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')
    expect(cloned).toBeTruthy()
    expect(cloned.render).toBeDefined()
    expect(typeof cloned.render.option_create).toBe('function')

    const instance = new IntegrationTomSelectStub(select1, cloned)

    const html = cloned.render.option_create.call(
      instance,
      { input: 'new entry' },
      (s) => s
    )

    expect(html).toContain('hx-target="#id_formset-1-recipients"')
    expect(html).not.toContain('#id_formset-0-recipients')
    // Sanity: the swap target is the per-row endpoint shared by all clones.
    expect(html).toContain('hx-post="/recipients/create/"')
  })

  it('hx-target tracks each clone independently across multiple cloned rows', () => {
    appendSelect('id_formset-0-recipients', 'formset-0-recipients')
    injectWidgetScript({
      id: 'id_formset-0-recipients',
      name: 'formset-0-recipients',
      autocompleteUrl: '/autocomplete/recipients/',
      create: true,
      optionCreate: { createWithHtmx: true, viewCreateUrl: '/recipients/create/' }
    })

    const select1 = appendSelect('id_formset-1-recipients', 'formset-1-recipients')
    const select2 = appendSelect('id_formset-2-recipients', 'formset-2-recipients')

    const cloned1 = dts.findSimilarConfig('id_formset-1-recipients')
    const cloned2 = dts.findSimilarConfig('id_formset-2-recipients')

    const instance1 = new IntegrationTomSelectStub(select1, cloned1)
    const instance2 = new IntegrationTomSelectStub(select2, cloned2)

    const html1 = cloned1.render.option_create.call(instance1, { input: 'foo' }, (s) => s)
    const html2 = cloned2.render.option_create.call(instance2, { input: 'bar' }, (s) => s)

    expect(html1).toContain('hx-target="#id_formset-1-recipients"')
    expect(html2).toContain('hx-target="#id_formset-2-recipients"')
    expect(html1).not.toContain('#id_formset-2-recipients')
    expect(html2).not.toContain('#id_formset-1-recipients')
  })
})
