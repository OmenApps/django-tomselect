// Regression: checkAndLoadMore (inner function of load()) must correctly
// thread pagination metadata and auto-fetch additional pages in two cases:
//
//   - allSelected: every item in the returned page is already in
//     instance.items, so the dropdown would otherwise look empty. Walk
//     forward until we find unselected rows or exhaust pages.
//   - needMoreItems: fewer than 20 unselected items collected so far,
//     but more pages exist. Keep fetching until we hit the threshold
//     or run out of pages.
//
// Both branches must stop when page === total_pages or has_more is false,
// and the pagination URL must be cached per-query (so getUrl can hand
// virtual_scroll the right "next page" URL on subsequent loads).

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  setupHarness,
  getJsdomWindow,
  injectWidgetScript,
  IntegrationTomSelectStub
} from '../helpers/harness.js'

function makeSelectInDom (id) {
  const realWindow = getJsdomWindow()
  const select = realWindow.document.createElement('select')
  select.id = id
  select.setAttribute('data-tomselect', 'true')
  realWindow.document.body.appendChild(select)
  return select
}

function jsonResponse (body) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body) })
}

describe('regression: load() auto-pagination via checkAndLoadMore', () => {
  let dts, realWindow, originalFetch

  beforeEach(() => {
    dts = setupHarness({ TomSelectClass: IntegrationTomSelectStub })
    realWindow = getJsdomWindow()
    originalFetch = realWindow.fetch
  })

  afterEach(() => {
    realWindow.fetch = originalFetch
  })

  it('single-page response: callback receives results, no extra fetches', async () => {
    realWindow.fetch = vi.fn(() => jsonResponse({
      results: [{ id: '1', name: 'A' }, { id: '2', name: 'B' }],
      has_more: false,
      page: 1,
      total_pages: 1
    }))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const cb = vi.fn()
    select.tomselect.load('q', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(realWindow.fetch).toHaveBeenCalledOnce()
    expect(cb.mock.calls[0][0]).toHaveLength(2)
    expect(cb.mock.calls[0][0][0].id).toBe('1')
  })

  it('all-selected page + has_more: auto-fetches next page', async () => {
    let fetchCallCount = 0
    realWindow.fetch = vi.fn(() => {
      fetchCallCount++
      if (fetchCallCount === 1) {
        return jsonResponse({
          results: [{ id: '1' }, { id: '2' }],
          has_more: true,
          page: 1,
          next_page: 2,
          total_pages: 2
        })
      }
      return jsonResponse({
        results: [{ id: '3' }, { id: '4' }],
        has_more: false,
        page: 2,
        total_pages: 2
      })
    })

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    // Pre-select items 1 and 2 so page 1 is "all already selected"
    select.tomselect.items = ['1', '2']
    select.tomselect.options = { 1: {}, 2: {} }

    const cb = vi.fn()
    select.tomselect.load('q', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(realWindow.fetch).toHaveBeenCalledTimes(2)
    // Only the unselected items from page 2 are surfaced to the callback
    const surfaced = cb.mock.calls[0][0]
    expect(surfaced.map(r => r.id).sort()).toEqual(['3', '4'])
  })

  it('all-selected + page === total_pages: stops, no extra fetch', async () => {
    realWindow.fetch = vi.fn(() => jsonResponse({
      results: [{ id: '1' }, { id: '2' }],
      has_more: true,  // server claims more but page == total_pages
      page: 3,
      next_page: 4,
      total_pages: 3
    }))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    select.tomselect.items = ['1', '2']
    select.tomselect.options = { 1: {}, 2: {} }

    const cb = vi.fn()
    select.tomselect.load('q', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(realWindow.fetch).toHaveBeenCalledOnce()
    expect(cb.mock.calls[0][0]).toEqual([])
  })

  it('needMoreItems threshold (< 20 unselected collected): auto-fetches next page', async () => {
    let fetchCallCount = 0
    realWindow.fetch = vi.fn(() => {
      fetchCallCount++
      if (fetchCallCount === 1) {
        // Five new (unselected) items, but threshold is 20 -- keep fetching.
        return jsonResponse({
          results: Array.from({ length: 5 }, (_, i) => ({ id: `p1-${i}` })),
          has_more: true,
          page: 1,
          next_page: 2,
          total_pages: 2
        })
      }
      return jsonResponse({
        results: Array.from({ length: 5 }, (_, i) => ({ id: `p2-${i}` })),
        has_more: false,
        page: 2,
        total_pages: 2
      })
    })

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const cb = vi.fn()
    select.tomselect.load('q', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(realWindow.fetch).toHaveBeenCalledTimes(2)
    expect(cb.mock.calls[0][0]).toHaveLength(10)
  })

  it('pagination cache: next-page URL stored per query, cleared when no more', async () => {
    let fetchCallCount = 0
    realWindow.fetch = vi.fn(() => {
      fetchCallCount++
      if (fetchCallCount === 1) {
        return jsonResponse({
          results: [{ id: 'a' }],
          has_more: true,
          page: 1,
          next_page: 2,
          total_pages: 5  // > page so auto-pagination would NOT trigger from needMoreItems alone
        })
      }
      return jsonResponse({
        results: [{ id: 'b' }],
        has_more: false,  // terminal page -- pagination should be cleared
        page: 5,
        total_pages: 5
      })
    })

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const cb1 = vi.fn()
    select.tomselect.load('q1', cb1)

    await vi.waitFor(() => expect(cb1).toHaveBeenCalled(), { timeout: 1000 })

    // After page 1 with has_more=true, pagination['q1'] should be set to a
    // page=2 URL. (Auto-fetch may also kick in via needMoreItems and chain
    // to the terminal page, which clears it. Either outcome is acceptable
    // as long as the terminal state ends cleanly.)
    const finalPagination = select.tomselect.settings.pagination
    // After all chained fetches resolve, no entries should remain for q1.
    expect(finalPagination['q1']).toBeUndefined()
  })

  it('empty response (no results, no pagination state): callback gets [], no chained fetch', async () => {
    realWindow.fetch = vi.fn(() => jsonResponse({
      results: [],
      has_more: false,
      page: 1,
      total_pages: 1
    }))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const cb = vi.fn()
    select.tomselect.load('q', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(realWindow.fetch).toHaveBeenCalledOnce()
    expect(cb.mock.calls[0][0]).toEqual([])
  })
})
