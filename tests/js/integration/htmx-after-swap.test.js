// HTMX afterSwap integration tests.
//
// Exercises the htmx:afterSwap pipeline that drives most HTMX-on-Django
// integrations: when HTMX replaces a chunk of DOM that contains a
// select[data-tomselect], djangoTomSelect must (a) detect the swap,
// (b) mark the container as in-flight in htmxSwapContainers so the
// MutationObserver does not race ahead with a duplicate init, and
// (c) call reinitialize() to attach TomSelect instances to the swapped
// selects. None of this surface had coverage before this file.
//
// The reinitialize path is deferred by REINIT_DELAY=100ms, so these
// tests use vi.useFakeTimers() to advance past it deterministically
// rather than waitFor()-ing on the real clock.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  makeSelect
} from '../helpers/harness.js'

describe('integration: htmx:afterSwap pipeline', () => {
  let dts
  let realWindow

  beforeEach(() => {
    vi.useFakeTimers()
    dts = setupHarness()
    realWindow = getJsdomWindow()
    // The harness strips the {% if not widget.use_htmx %}...{% endif %}
    // bootstrap block so handlers are not wired automatically. Wire them
    // here so document.addEventListener('htmx:afterSwap', ...) is in place.
    dts.setupHandlers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // -------------------------------------------------------------------------
  // setupHtmxHandlers registers the listener and dispatches reinitialize
  // -------------------------------------------------------------------------

  it('htmx:afterSwap on a connected container with a tomselect-flagged select triggers initialize', () => {
    const container = realWindow.document.createElement('div')
    container.id = 'swap-target-1'
    realWindow.document.body.appendChild(container)

    const select = realWindow.document.createElement('select')
    select.id = 'id_swapped'
    select.setAttribute('data-tomselect', 'true')
    container.appendChild(select)

    // Pre-stash a config keyed by the select's id so reinitialize() finds
    // a real config rather than falling through to findSimilarConfig.
    dts.configs.set('id_swapped', { url: '/autocomplete/' })

    realWindow.document.dispatchEvent(
      new realWindow.CustomEvent('htmx:afterSwap', { detail: { target: container } })
    )

    // setupHtmxHandlers immediately calls reinitialize, which itself defers
    // the actual init via setTimeout(REINIT_DELAY=100). Advance past it.
    vi.advanceTimersByTime(101)

    expect(select.tomselect).toBeDefined()
    expect(dts.instances.has('id_swapped')).toBe(true)
  })

  it('marks the swapped container in htmxSwapContainers before reinitialize runs', () => {
    const container = realWindow.document.createElement('div')
    container.id = 'swap-target-2'
    realWindow.document.body.appendChild(container)

    realWindow.document.dispatchEvent(
      new realWindow.CustomEvent('htmx:afterSwap', { detail: { target: container } })
    )

    // Pre-advance: the WeakSet entry is added synchronously inside the
    // event handler, before the deferred reinitialize body runs.
    expect(dts.htmxSwapContainers.has(container)).toBe(true)
  })

  it('removes the container from htmxSwapContainers after reinitialize finishes', () => {
    const container = realWindow.document.createElement('div')
    container.id = 'swap-target-3'
    realWindow.document.body.appendChild(container)

    realWindow.document.dispatchEvent(
      new realWindow.CustomEvent('htmx:afterSwap', { detail: { target: container } })
    )
    expect(dts.htmxSwapContainers.has(container)).toBe(true)

    vi.advanceTimersByTime(101)

    // The finally{} clause inside reinitialize() removes the entry so the
    // observer is free to operate on this subtree again.
    expect(dts.htmxSwapContainers.has(container)).toBe(false)
  })

  it('reinitialize skips selects that already have a live tomselect instance', () => {
    const container = realWindow.document.createElement('div')
    realWindow.document.body.appendChild(container)

    const select = realWindow.document.createElement('select')
    select.id = 'id_already_live'
    select.setAttribute('data-tomselect', 'true')
    container.appendChild(select)

    // First init: synchronous via dts.initialize.
    dts.configs.set('id_already_live', { url: '/autocomplete/' })
    const liveInstance = dts.initialize(select, dts.configs.get('id_already_live'))
    expect(select.tomselect).toBe(liveInstance)

    realWindow.document.dispatchEvent(
      new realWindow.CustomEvent('htmx:afterSwap', { detail: { target: container } })
    )
    vi.advanceTimersByTime(101)

    // The same TomSelect instance must still be attached - no re-init.
    expect(select.tomselect).toBe(liveInstance)
  })

  // -------------------------------------------------------------------------
  // Detached-target fallback (outerHTML swap leaves event.detail.target
  // pointing at the OLD removed node).
  // -------------------------------------------------------------------------

  it('detached target falls back to document.getElementById(container.id) when a replacement exists', () => {
    // Simulate an outerHTML swap: build a "removed" detached node with the
    // same id as a node that lives in the document.
    const replacement = realWindow.document.createElement('div')
    replacement.id = 'outerhtml-target'
    realWindow.document.body.appendChild(replacement)

    const replacementSelect = realWindow.document.createElement('select')
    replacementSelect.id = 'id_post_swap'
    replacementSelect.setAttribute('data-tomselect', 'true')
    replacement.appendChild(replacementSelect)
    dts.configs.set('id_post_swap', { url: '/autocomplete/' })

    const detached = realWindow.document.createElement('div')
    detached.id = 'outerhtml-target'
    // Critical: not attached to the document. detached.isConnected === false.
    expect(detached.isConnected).toBe(false)

    realWindow.document.dispatchEvent(
      new realWindow.CustomEvent('htmx:afterSwap', { detail: { target: detached } })
    )

    // The WeakSet should hold the REPLACEMENT, not the detached node.
    expect(dts.htmxSwapContainers.has(replacement)).toBe(true)
    expect(dts.htmxSwapContainers.has(detached)).toBe(false)

    vi.advanceTimersByTime(101)
    expect(replacementSelect.tomselect).toBeDefined()
  })

  it('detached target with no id stays as the detached node (no body fallback)', () => {
    // The source's fallback chain is:
    //   if (!container.isConnected) {
    //     if (container.id) { container = document.getElementById(container.id); }
    //     if (!container)   { container = document.body; }
    //   }
    // The `!container` branch only fires when getElementById returned null,
    // which requires container.id to have been truthy. A detached node with
    // no id therefore stays as itself - the body fallback is NOT reached.
    // This test pins that actual behavior so a future refactor does not
    // silently change it (and surfaces it as a documented edge case worth
    // reviewing - a detached container yields a reinitialize() that walks
    // an orphan subtree).
    const detached = realWindow.document.createElement('div')
    expect(detached.isConnected).toBe(false)
    expect(detached.id).toBe('')

    expect(() => {
      realWindow.document.dispatchEvent(
        new realWindow.CustomEvent('htmx:afterSwap', { detail: { target: detached } })
      )
    }).not.toThrow()

    expect(dts.htmxSwapContainers.has(detached)).toBe(true)
    expect(dts.htmxSwapContainers.has(realWindow.document.body)).toBe(false)
  })

  it('detached target whose id no longer matches anything falls back to document.body', () => {
    const detached = realWindow.document.createElement('div')
    detached.id = 'never-existed-id'
    expect(realWindow.document.getElementById('never-existed-id')).toBeNull()

    realWindow.document.dispatchEvent(
      new realWindow.CustomEvent('htmx:afterSwap', { detail: { target: detached } })
    )

    expect(dts.htmxSwapContainers.has(realWindow.document.body)).toBe(true)
  })

  // -------------------------------------------------------------------------
  // Defensive: malformed events must not throw.
  // -------------------------------------------------------------------------

  it('htmx:afterSwap without event.detail is a silent no-op', () => {
    expect(() => {
      realWindow.document.dispatchEvent(new realWindow.Event('htmx:afterSwap'))
    }).not.toThrow()
  })

  it('htmx:afterSwap with event.detail but no .target is a silent no-op', () => {
    expect(() => {
      realWindow.document.dispatchEvent(
        new realWindow.CustomEvent('htmx:afterSwap', { detail: {} })
      )
    }).not.toThrow()
  })

  // -------------------------------------------------------------------------
  // isInsidePendingHtmxSwap walks the parent chain.
  // -------------------------------------------------------------------------

  it('isInsidePendingHtmxSwap returns true for the swap container itself', () => {
    const container = makeSelect({ id: 'irrelevant_select' }).parentElement
    dts.htmxSwapContainers.add(container)
    expect(dts.isInsidePendingHtmxSwap(container)).toBe(true)
  })

  it('isInsidePendingHtmxSwap returns true for any descendant of a swap container', () => {
    const container = realWindow.document.createElement('div')
    const child = realWindow.document.createElement('span')
    const grandchild = realWindow.document.createElement('em')
    container.appendChild(child)
    child.appendChild(grandchild)
    realWindow.document.body.appendChild(container)

    dts.htmxSwapContainers.add(container)
    expect(dts.isInsidePendingHtmxSwap(grandchild)).toBe(true)
  })

  it('isInsidePendingHtmxSwap returns false for nodes outside any swap container', () => {
    const a = realWindow.document.createElement('div')
    const b = realWindow.document.createElement('div')
    realWindow.document.body.appendChild(a)
    realWindow.document.body.appendChild(b)

    dts.htmxSwapContainers.add(a)
    expect(dts.isInsidePendingHtmxSwap(b)).toBe(false)
  })

  it('isInsidePendingHtmxSwap returns false when no swap is pending', () => {
    const node = realWindow.document.createElement('div')
    realWindow.document.body.appendChild(node)
    expect(dts.isInsidePendingHtmxSwap(node)).toBe(false)
  })
})
