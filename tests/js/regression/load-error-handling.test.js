// Regression: load() catch handler must distinguish three error modes:
//
//   1. Non-ok HTTP response (e.g. 500): render "Failed to load options" UI
//      and log to console.error.
//   2. Real timeout (AbortError where self._currentLoadController === controller
//      because the abort came from the 30s setTimeout, not from a newer load):
//      render "Request timed out" UI.
//   3. Superseded AbortError (a newer load() replaced the controller before the
//      old fetch's catch ran): silently call callback([]) with no error UI
//      and no console.error.
//
// This branch has churned several times historically (see commits
// `Properly handle fetch errors`, `Fix issue with options jumping to page 2`,
// plus the dependent-field empty-source fix). Pinning all three sub-cases.

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

describe('regression: load() error handling', () => {
  let dts, realWindow, originalFetch, consoleErrorSpy

  beforeEach(() => {
    dts = setupHarness({ TomSelectClass: IntegrationTomSelectStub })
    realWindow = getJsdomWindow()
    originalFetch = realWindow.fetch
    // The IIFE runs in JSDOM's window context, so console.error inside load()
    // resolves to JSDOM's console, not the test-runner global. Spy on the
    // JSDOM window's console.error instead.
    consoleErrorSpy = vi.spyOn(realWindow.console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    realWindow.fetch = originalFetch
    consoleErrorSpy.mockRestore()
  })

  it('non-ok response renders "Failed to load" UI and logs to console.error', async () => {
    realWindow.fetch = vi.fn(() => Promise.resolve({
      ok: false,
      status: 500,
      json: () => Promise.resolve({})
    }))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const cb = vi.fn()
    select.tomselect.load('query', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(select.tomselect.dropdown_content.innerHTML).toContain('ts-error-message')
    expect(select.tomselect.dropdown_content.innerHTML).toContain('Failed to load')
    expect(select.tomselect.dropdown_content.innerHTML).not.toContain('timed out')
    expect(consoleErrorSpy).toHaveBeenCalled()
  })

  it('network error (fetch rejects with non-AbortError) renders "Failed to load" UI', async () => {
    realWindow.fetch = vi.fn(() => Promise.reject(new TypeError('NetworkError: connection refused')))

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const cb = vi.fn()
    select.tomselect.load('query', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(select.tomselect.dropdown_content.innerHTML).toContain('Failed to load')
    expect(consoleErrorSpy).toHaveBeenCalled()
  })

  it('real timeout (AbortError, no supersession) renders "Request timed out" UI', async () => {
    // Real-world trigger: the 30s setTimeout fires controller.abort() but
    // self._currentLoadController still points at the same controller. The
    // catch sees AbortError + same controller => takes the timeout branch.
    // We synthesize this by rejecting fetch immediately with AbortError,
    // because no newer load() runs in between.
    realWindow.fetch = vi.fn(() => {
      const err = new Error('The user aborted a request.')
      err.name = 'AbortError'
      return Promise.reject(err)
    })

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const cb = vi.fn()
    select.tomselect.load('query', cb)

    await vi.waitFor(() => expect(cb).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb).toHaveBeenCalledWith([])
    expect(select.tomselect.dropdown_content.innerHTML).toContain('ts-error-message')
    expect(select.tomselect.dropdown_content.innerHTML).toContain('timed out')
    expect(select.tomselect.dropdown_content.innerHTML).not.toContain('Failed to load')
    expect(consoleErrorSpy).toHaveBeenCalled()
  })

  it('superseded AbortError (second load() replaces controller) is silent', async () => {
    // First fetch hangs; signal listener rejects it on abort. Second fetch
    // resolves cleanly. The first fetch's catch must take the supersede
    // branch (self._currentLoadController !== controller) -> no error UI.
    realWindow.fetch = vi.fn((url, opts) => {
      if (url.includes('q2')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ results: [], has_more: false, page: 1, total_pages: 1 })
        })
      }
      return new Promise((_resolve, reject) => {
        opts.signal.addEventListener('abort', () => {
          const err = new Error('aborted')
          err.name = 'AbortError'
          reject(err)
        })
      })
    })

    const select = makeSelectInDom('id_test')
    injectWidgetScript({ id: 'id_test', autocompleteUrl: '/x/' })

    const cb1 = vi.fn()
    const cb2 = vi.fn()
    select.tomselect.load('q1', cb1)
    select.tomselect.load('q2', cb2)

    await vi.waitFor(() => expect(cb1).toHaveBeenCalled() && expect(cb2).toHaveBeenCalled(), { timeout: 1000 })
    expect(cb1).toHaveBeenCalledWith([])
    expect(select.tomselect.dropdown_content.innerHTML).not.toContain('ts-error-message')
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })
})
