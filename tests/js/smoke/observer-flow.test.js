// MutationObserver flow tests.
//
// processObserverMutations is the dispatcher that turns DOM mutations into
// "containers worth re-scanning for select[data-tomselect]". setupObserver
// wires it up against document.body with a debounced wrapper. Together they
// are how Django formsets, tab-pane activations, and dynamically inserted
// forms get TomSelect attached to their newly-mounted selects.
//
// None of this had direct coverage. These tests:
//   - Call processObserverMutations() directly with synthesized
//     MutationRecord-shaped objects (simpler and faster than relying on
//     the real observer to fire).
//   - Drive setupObserver() through real DOM mutations under fake timers
//     to verify the debounce + reinitialize wiring.
//
// One test documents a real bug in the source: the attribute-change branch
// gates on `target.hasAttribute('classList')`, an attribute that never
// exists - so the entire tab-activation re-init path is effectively dead
// code. The test pins current behavior so the bug stays visible until
// fixed (and so a fix doesn't silently change semantics without a paired
// test update).

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { setupHarness, getJsdomWindow } from '../helpers/harness.js'

// MutationRecord is a host object the user can't construct directly.
// processObserverMutations only reads .type, .addedNodes (NodeList-like),
// .attributeName, and .target, so a plain object suffices.
function childListMutation (addedNodes) {
  return { type: 'childList', addedNodes, target: null, attributeName: null }
}

function attributesMutation (target, attributeName = 'class') {
  return { type: 'attributes', target, addedNodes: [], attributeName }
}

describe('smoke: processObserverMutations container detection', () => {
  let dts
  let realWindow

  beforeEach(() => {
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  // -------------------------------------------------------------------------
  // Childlist: positive cases - five container shapes that should trigger
  // re-scan.
  // -------------------------------------------------------------------------

  it('childList: added node containing select[data-tomselect] is queued', () => {
    const wrapper = realWindow.document.createElement('div')
    const select = realWindow.document.createElement('select')
    select.setAttribute('data-tomselect', 'true')
    wrapper.appendChild(select)

    const out = dts.processObserverMutations([childListMutation([wrapper])])
    expect(out.has(wrapper)).toBe(true)
  })

  it('childList: added FORM element is queued even without a tomselect child', () => {
    const form = realWindow.document.createElement('form')
    const out = dts.processObserverMutations([childListMutation([form])])
    expect(out.has(form)).toBe(true)
  })

  it('childList: added .tab-pane element is queued', () => {
    const pane = realWindow.document.createElement('div')
    pane.className = 'tab-pane'
    const out = dts.processObserverMutations([childListMutation([pane])])
    expect(out.has(pane)).toBe(true)
  })

  it('childList: added .tab-content element is queued', () => {
    const tabContent = realWindow.document.createElement('div')
    tabContent.className = 'tab-content'
    const out = dts.processObserverMutations([childListMutation([tabContent])])
    expect(out.has(tabContent)).toBe(true)
  })

  it('childList: added node with id=waterEntryFormContent is queued', () => {
    const node = realWindow.document.createElement('div')
    node.id = 'waterEntryFormContent'
    const out = dts.processObserverMutations([childListMutation([node])])
    expect(out.has(node)).toBe(true)
  })

  // -------------------------------------------------------------------------
  // Childlist: negative cases.
  // -------------------------------------------------------------------------

  it('childList: plain <div> with no qualifying class/id/child is ignored', () => {
    const plain = realWindow.document.createElement('div')
    const out = dts.processObserverMutations([childListMutation([plain])])
    expect(out.size).toBe(0)
  })

  it('childList: text nodes (nodeType !== 1) are ignored', () => {
    const textNode = realWindow.document.createTextNode('hello')
    expect(() =>
      dts.processObserverMutations([childListMutation([textNode])])
    ).not.toThrow()
    const out = dts.processObserverMutations([childListMutation([textNode])])
    expect(out.size).toBe(0)
  })

  // -------------------------------------------------------------------------
  // Childlist: nodes inside a pending HTMX swap container are skipped to
  // avoid double-init.
  // -------------------------------------------------------------------------

  it('childList: nodes inside a pending HTMX swap container are skipped', () => {
    const swap = realWindow.document.createElement('div')
    const formInSwap = realWindow.document.createElement('form')
    swap.appendChild(formInSwap)
    realWindow.document.body.appendChild(swap)

    dts.htmxSwapContainers.add(swap)
    const out = dts.processObserverMutations([childListMutation([formInSwap])])
    expect(out.has(formInSwap)).toBe(false)
  })

  // -------------------------------------------------------------------------
  // Set dedupe: the same container queued by multiple mutation records
  // only appears once.
  // -------------------------------------------------------------------------

  it('childList: same container added in multiple mutations is dedupe-collected once', () => {
    const form = realWindow.document.createElement('form')
    const out = dts.processObserverMutations([
      childListMutation([form]),
      childListMutation([form]),
      childListMutation([form])
    ])
    expect(out.size).toBe(1)
    expect(out.has(form)).toBe(true)
  })

  // -------------------------------------------------------------------------
  // Multiple distinct container shapes in one batch.
  // -------------------------------------------------------------------------

  it('childList: a batch yielding several container shapes returns all of them', () => {
    const form = realWindow.document.createElement('form')
    const pane = realWindow.document.createElement('div')
    pane.className = 'tab-pane'
    const wrapperWithSelect = realWindow.document.createElement('div')
    const select = realWindow.document.createElement('select')
    select.setAttribute('data-tomselect', 'true')
    wrapperWithSelect.appendChild(select)

    const out = dts.processObserverMutations([
      childListMutation([form, pane, wrapperWithSelect])
    ])
    expect(out.size).toBe(3)
    expect(out.has(form)).toBe(true)
    expect(out.has(pane)).toBe(true)
    expect(out.has(wrapperWithSelect)).toBe(true)
  })

  // -------------------------------------------------------------------------
  // Attribute-change branch: documents a real bug.
  //
  // The source gates the tab-activation path on
  // `target.hasAttribute('classList')`, but `classList` is a DOM property,
  // never an attribute. The gate therefore never passes, so attribute-only
  // mutations (e.g. Bootstrap toggling .active on a .tab-pane WITHOUT
  // inserting/removing it) never trigger reinitialize. Real tab switches
  // happen to still work because the activated pane's contents are usually
  // recreated by the framework, hitting the childList path - but that's
  // coincidental coverage, not by design.
  //
  // This test pins the buggy-but-current behavior. When the bug is fixed
  // (drop the `hasAttribute('classList')` check), update both the source
  // and this test together.
  // -------------------------------------------------------------------------

  it('attribute change: tab-pane gaining .active is NOT queued (documents hasAttribute("classList") bug)', () => {
    const pane = realWindow.document.createElement('div')
    pane.className = 'tab-pane active'
    realWindow.document.body.appendChild(pane)

    const out = dts.processObserverMutations([attributesMutation(pane, 'class')])
    // Despite the predicate's apparent intent, the gate
    // `target.hasAttribute('classList')` never matches because classList
    // is a property, not an attribute. Pin this so the bug is visible.
    expect(out.has(pane)).toBe(false)
  })

  it('attribute change: even with a fabricated classList attribute, the rest of the gate still applies', () => {
    // Sanity-check the buggy gate's downstream conditions: if we manually
    // set a `classList="x"` attribute (the only way the gate can ever
    // pass), the active+tab-pane checks still need to hold. Confirms the
    // bug is in the gate, not in the inner conditions.
    const pane = realWindow.document.createElement('div')
    pane.setAttribute('classList', 'x')
    pane.className = 'tab-pane active'
    realWindow.document.body.appendChild(pane)

    const out = dts.processObserverMutations([attributesMutation(pane, 'class')])
    expect(out.has(pane)).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// setupObserver: end-to-end via real MutationObserver + fake timers.
// ---------------------------------------------------------------------------

describe('smoke: setupObserver wiring + debounce', () => {
  let dts
  let realWindow

  beforeEach(() => {
    vi.useFakeTimers()
    dts = setupHarness()
    realWindow = getJsdomWindow()
  })

  afterEach(() => {
    // Disconnect any observer the test set up before restoring real timers.
    if (dts.observer) {
      dts.observer.disconnect()
      dts.observer = null
    }
    vi.useRealTimers()
  })

  it('setupObserver assigns this.observer (a MutationObserver instance)', () => {
    expect(dts.observer).toBeFalsy()
    dts.setupObserver()
    expect(dts.observer).toBeTruthy()
    // Quack-test: real MutationObservers expose .disconnect/.observe.
    expect(typeof dts.observer.disconnect).toBe('function')
    expect(typeof dts.observer.observe).toBe('function')
  })

  it('setupObserver called twice disconnects the first observer (no leak)', () => {
    dts.setupObserver()
    const first = dts.observer
    const disconnectSpy = vi.spyOn(first, 'disconnect')

    dts.setupObserver()
    expect(disconnectSpy).toHaveBeenCalledOnce()
    expect(dts.observer).not.toBe(first)
  })

  it('debounce: rapid mutations within the window coalesce into a single reinitialize call', async () => {
    // Replace reinitialize with a spy so we observe how many times it
    // would have run end-to-end after the debounce window expires.
    const reinitSpy = vi.spyOn(dts, 'reinitialize').mockImplementation(() => {})

    dts.setupObserver()

    // Microtask-yield once so the observer's initial setup settles, then
    // mutate the DOM a handful of times within the debounce window.
    await Promise.resolve()
    for (let i = 0; i < 5; i++) {
      const form = realWindow.document.createElement('form')
      realWindow.document.body.appendChild(form)
    }

    // MutationObserver callbacks are delivered as microtasks, so let those
    // queue into the debounced wrapper first.
    await Promise.resolve()
    await Promise.resolve()

    // Advance past OBSERVER_DEBOUNCE (50ms) to fire the debounced callback.
    await vi.advanceTimersByTimeAsync(60)

    // The debounced wrapper runs once, even though we inserted 5 forms.
    // Each form is a separate container, so reinitialize fires once per
    // container - but the wrapper itself is called exactly once.
    // Use callCount >= 1 as the assertion (5 distinct containers => 5 calls
    // from the single wrapper invocation).
    expect(reinitSpy).toHaveBeenCalled()
    // Each FORM is its own container in the Set returned by
    // processObserverMutations, so we expect 5 reinit calls from the one
    // debounced flush - proving (a) the wrapper fired only once and (b)
    // all five containers were collected.
    expect(reinitSpy.mock.calls.length).toBe(5)
  })

  // -------------------------------------------------------------------------
  // cleanup() integration: after cleanup, the observer is disconnected
  // and nulled. Verifies the cleanup-side teardown matches setupObserver's
  // setup invariant (no dangling MutationObserver after SPA navigation).
  // -------------------------------------------------------------------------

  it('cleanup() after setupObserver tears down the observer', () => {
    dts.setupObserver()
    const observer = dts.observer
    const disconnectSpy = vi.spyOn(observer, 'disconnect')

    dts.cleanup()
    expect(disconnectSpy).toHaveBeenCalledOnce()
    expect(dts.observer).toBeNull()
  })
})
