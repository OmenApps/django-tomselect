// Regression: when autocomplete returns rows that are ALREADY selected on
// the widget, load()/checkAndLoadMore must call updateOption(value, item)
// to merge the full record into the in-memory option.
//
// Selected items are initially seeded into instance.options from a minimal
// {value, label} dict (see tomselect.html onInitialize). The autocomplete
// response returns the full record with extra_columns, virtual_fields, urls,
// etc. Without the updateOption merge, selected pills render with degraded
// data after the user focuses the dropdown -- a silent UX regression.

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

describe('regression: load() updates already-selected options with full record', () => {
  let dts, realWindow, originalFetch

  beforeEach(() => {
    dts = setupHarness({ TomSelectClass: IntegrationTomSelectStub })
    realWindow = getJsdomWindow()
    originalFetch = realWindow.fetch
  })

  afterEach(() => {
    realWindow.fetch = originalFetch
  })

  it('selected item returned by fetch triggers updateOption with full record', async () => {
    // The fetch response contains the selected id=42 plus extra columns.
    realWindow.fetch = vi.fn(() => jsonResponse({
      results: [
        { id: '42', name: 'Full Name', publisher: 'Acme', issue_count: 12 },
        { id: '43', name: 'Another' }
      ],
      has_more: false,
      page: 1,
      total_pages: 1
    }))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const instance = select.tomselect
    // Simulate the onInitialize state: item 42 selected with a thin record.
    instance.items = ['42']
    instance.options = { 42: { id: '42', name: 'Old Name' } }

    const updateSpy = vi.spyOn(instance, 'updateOption')

    instance.load('q', vi.fn())
    await vi.waitFor(() => expect(updateSpy).toHaveBeenCalled(), { timeout: 1000 })

    expect(updateSpy).toHaveBeenCalledTimes(1)
    expect(updateSpy).toHaveBeenCalledWith('42', {
      id: '42',
      name: 'Full Name',
      publisher: 'Acme',
      issue_count: 12
    })
  })

  it('does NOT call updateOption when the returned id is not in items', async () => {
    realWindow.fetch = vi.fn(() => jsonResponse({
      results: [{ id: '99', name: 'Unselected' }],
      has_more: false,
      page: 1,
      total_pages: 1
    }))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const instance = select.tomselect
    instance.items = ['42']
    instance.options = { 42: { id: '42' } }

    const updateSpy = vi.spyOn(instance, 'updateOption')

    const cb = vi.fn()
    instance.load('q', cb)
    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })

    expect(updateSpy).not.toHaveBeenCalled()
  })

  it('updates option even when ids are numeric in the response but strings in items', async () => {
    // String(item[valueField]) coercion contract: the guard is
    // `self.items.includes(String(item[valueField]))`, so a numeric id in
    // the JSON must still match a string-id in items.
    realWindow.fetch = vi.fn(() => jsonResponse({
      results: [{ id: 42, name: 'Full' }],
      has_more: false,
      page: 1,
      total_pages: 1
    }))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const instance = select.tomselect
    instance.items = ['42']
    instance.options = { 42: { id: '42' } }

    const updateSpy = vi.spyOn(instance, 'updateOption')

    instance.load('q', vi.fn())
    await vi.waitFor(() => expect(updateSpy).toHaveBeenCalled(), { timeout: 1000 })

    expect(updateSpy).toHaveBeenCalledWith('42', { id: 42, name: 'Full' })
  })

  it('selected item is still filtered out of the callback results (no double-render)', async () => {
    // updateOption refreshes the existing option's data; the result list
    // surfaced to the callback should NOT also include the selected item
    // as a "new" result (otherwise the dropdown shows duplicates).
    realWindow.fetch = vi.fn(() => jsonResponse({
      results: [
        { id: '42', name: 'Already selected' },
        { id: '43', name: 'New option' }
      ],
      has_more: false,
      page: 1,
      total_pages: 1
    }))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const instance = select.tomselect
    instance.items = ['42']
    instance.options = { 42: { id: '42' } }

    const cb = vi.fn()
    instance.load('q', cb)
    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })

    const surfaced = cb.mock.calls[0][0]
    expect(surfaced.map(r => r.id)).toEqual(['43'])
  })
})
