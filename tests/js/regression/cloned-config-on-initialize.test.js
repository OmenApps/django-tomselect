// Regression test for ISSUE_findsimilarconfig_oninitialize_selected_options.md
//
// onInitialize in tomselect.html is built at template render time and bakes
// widget.selected_options into the function body via a {% for %} loop. The
// function reference is preserved by cloneConfig (which copies function-typed
// values by reference), so a populated source row's onInitialize, when carried
// into a cloned formset row by findSimilarConfig, would call addOptions and
// setValue with the source row's option IDs - pre-selecting them in the new
// (intended-empty) row.
//
// The fix in findSimilarConfig deletes onInitialize from the cloned config so
// cloned rows start empty. The non-clone path (first row / empty_form) is
// untouched and still pre-selects initial values from its own IIFE.

import { describe, it, expect, beforeEach } from 'vitest'
import { setupHarness } from '../helpers/harness.js'

describe('regression: cloned config drops onInitialize to prevent selected_options leakage', () => {
  let dts

  beforeEach(() => {
    dts = setupHarness()
  })

  it('strips onInitialize from the cloned config', () => {
    const sourceOnInitialize = function () {
      // In the real template this body addOptions/setValue with the source
      // row's selected options. The body doesn't matter for the contract test
      // - what matters is that findSimilarConfig drops the reference.
      this.addOptions({ '42': { id: '42', name: 'Alice' } })
      this.setValue(['42'], true)
    }

    dts.configs.set('id_formset-0-recipients', {
      onInitialize: sourceOnInitialize
    })

    const cloned = dts.findSimilarConfig('id_formset-1-recipients')

    expect(cloned).toBeTruthy()
    expect(cloned.onInitialize).toBeUndefined()
  })

  it('strips onInitialize alongside the other instance-specific state (items, renderCache)', () => {
    // Co-test with the existing items/renderCache strip so a future refactor
    // of findSimilarConfig that touches the cleanup block keeps all three
    // strips together.
    dts.configs.set('id_formset-0-recipients', {
      items: ['42', '43'],
      renderCache: { foo: 'bar' },
      onInitialize: function () { /* would re-select source row's items */ }
    })

    const cloned = dts.findSimilarConfig('id_formset-2-recipients')

    expect(cloned.items).toBeUndefined()
    expect(cloned.renderCache).toBeUndefined()
    expect(cloned.onInitialize).toBeUndefined()
  })
})
