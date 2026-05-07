// django-tomselect - token widget client plugin.
//
// Exposed via window.djangoTomSelectToken.init(rootEl). The Django template
// (templates/django_tomselect/tomselect_token.html) emits an inline init
// script per widget; that pattern matches the existing tomselect.html.
//
// All DOM construction uses createElement + textContent (no innerHTML) so
// rendered chip/dropdown content is XSS-safe by construction.

/* eslint-disable no-multi-spaces */

import { parseQuery, PARSE_ERRORS } from './parser.js'

const HYDRATION_CACHE_KEY = '__djangoTomSelectTokenHydrationCache'

// ---------------------------------------------------------------------------
// Networking
// ---------------------------------------------------------------------------

async function fetchOperators (compositeUrl) {
  const url = new URL(compositeUrl, window.location.origin)
  url.searchParams.set('mode', 'operators')
  const resp = await window.fetch(url.toString(), { credentials: 'same-origin' })
  if (!resp.ok) throw new Error('operators fetch failed: ' + resp.status)
  return resp.json()
}

async function fetchValueResults (compositeUrl, opKey, query, page, signal) {
  const url = new URL(compositeUrl, window.location.origin)
  url.searchParams.set('mode', 'value')
  url.searchParams.set('op', opKey)
  url.searchParams.set('q', query || '')
  if (page) url.searchParams.set('p', String(page))
  const opts = { credentials: 'same-origin' }
  if (signal) opts.signal = signal
  const resp = await window.fetch(url.toString(), opts)
  if (!resp.ok) throw new Error('value fetch failed: ' + resp.status)
  return resp.json()
}

async function fetchResolveBatch (compositeUrl, pairs) {
  const url = new URL(compositeUrl, window.location.origin)
  url.searchParams.set('mode', 'resolve')
  for (const [op, id] of pairs) {
    url.searchParams.append('op', op)
    url.searchParams.append('id', id)
  }
  const resp = await window.fetch(url.toString(), { credentials: 'same-origin' })
  if (!resp.ok) throw new Error('resolve fetch failed: ' + resp.status)
  return resp.json()
}

// ---------------------------------------------------------------------------
// DOM construction helpers (createElement + textContent - no innerHTML).
// ---------------------------------------------------------------------------

function el (tag, attrs, children) {
  const node = document.createElement(tag)
  if (attrs) {
    for (const k of Object.keys(attrs)) {
      const v = attrs[k]
      if (v == null) continue
      if (k === 'class') node.className = v
      else if (k === 'text') node.textContent = v
      else if (k.startsWith('data-') || k === 'aria-label' || k === 'type' || k === 'hidden') {
        node.setAttribute(k, v === true ? '' : String(v))
      } else node.setAttribute(k, String(v))
    }
  }
  if (children) {
    for (const c of children) {
      if (c == null) continue
      if (typeof c === 'string') node.appendChild(document.createTextNode(c))
      else node.appendChild(c)
    }
  }
  return node
}

function buildTokenChip (token, label) {
  const valueText = token.values.join(',')
  const isMissing = label === null
  const labelMarkup = isMissing
    ? el('span', { class: 'tw-tok-label', text: '(missing)' })
    : (label != null ? el('span', { class: 'tw-tok-label', text: label }) : null)
  return el(
    'span',
    {
      class: 'tw-tok' + (isMissing ? ' tw-tok-missing' : ''),
      'data-op': token.key,
      'data-value': valueText
    },
    [
      el('span', { class: 'tw-tok-k', text: token.key + ':' }),
      el('span', { class: 'tw-tok-v' }, [
        el('span', { class: 'tw-tok-id', text: valueText }),
        labelMarkup ? document.createTextNode(' ') : null,
        labelMarkup
      ]),
      el('button', { type: 'button', class: 'tw-tok-x', 'aria-label': 'Remove', text: '×' })
    ]
  )
}

function buildFreeTextChip (text) {
  return el('span', { class: 'tw-tok tw-tok-freetext', 'data-freetext': text }, [
    el('span', { class: 'tw-tok-k', text: '"' }),
    el('span', { class: 'tw-tok-v' }, [el('span', { class: 'tw-tok-label', text })]),
    el('button', { type: 'button', class: 'tw-tok-x', 'aria-label': 'Remove', text: '×' })
  ])
}

function buildErrorChip (text) {
  return el('span', { class: 'tw-tok tw-tok-error' }, [
    el('span', { class: 'tw-tok-k', text: '!' }),
    el('span', { class: 'tw-tok-v' }, [el('span', { class: 'tw-tok-label', text })]),
    el('button', { type: 'button', class: 'tw-tok-x', 'aria-label': 'Remove', text: '×' })
  ])
}

function buildOperatorMenu (operators, draft) {
  const filtered = operators.filter(o =>
    !draft || o.key.toLowerCase().startsWith(draft.toLowerCase())
  )
  const wrapper = document.createDocumentFragment()
  if (filtered.length === 0) {
    wrapper.appendChild(el('div', { class: 'tw-dropdown-heading', text: 'No operators match.' }))
    return wrapper
  }
  const section = el('div', { class: 'tw-dropdown-section' }, [
    el('div', { class: 'tw-dropdown-heading', text: 'Operators' })
  ])
  filtered.forEach((op, i) => {
    const opt = el('div', {
      class: 'tw-opt' + (i === 0 ? ' active' : ''),
      'data-action': 'select-operator',
      'data-key': op.key
    }, [
      el('span', { class: 'tw-opt-k', text: op.key + ':' }),
      el('span', { class: 'tw-opt-text', text: op.label || op.key }),
      op.multi ? el('span', { class: 'tw-opt-hint', text: 'multi' }) : null
    ])
    section.appendChild(opt)
  })
  wrapper.appendChild(section)
  wrapper.appendChild(buildFooter())
  return wrapper
}

function buildValueDropdown (opKey, results, opMeta) {
  const wrapper = document.createDocumentFragment()
  if (!results || results.length === 0) {
    wrapper.appendChild(el('div', { class: 'tw-dropdown-heading', text: 'No matches.' }))
    wrapper.appendChild(buildFooter('close'))
    return wrapper
  }
  const section = el('div', { class: 'tw-dropdown-section' }, [
    el('div', { class: 'tw-dropdown-heading', text: opMeta.label || opKey })
  ])
  results.forEach((row, i) => {
    const id = row[opMeta.value_field]
    const label = row[opMeta.label_field]
    section.appendChild(el('div', {
      class: 'tw-opt' + (i === 0 ? ' active' : ''),
      'data-action': 'select-value',
      'data-id': id,
      'data-label': label
    }, [
      el('span', { class: 'tw-opt-id', text: String(id) }),
      el('span', { class: 'tw-opt-text', text: String(label) })
    ]))
  })
  wrapper.appendChild(section)
  wrapper.appendChild(buildFooter())
  return wrapper
}

function buildFooter (variant) {
  const footer = el('div', { class: 'tw-dropdown-footer' })
  if (variant === 'close') {
    footer.appendChild(el('kbd', { text: 'esc' }))
    footer.appendChild(document.createTextNode(' close'))
    return footer
  }
  const items = [
    [el('kbd', { text: '↑↓' }), document.createTextNode(' navigate')],
    [el('kbd', { text: '↵' }), document.createTextNode(' insert')],
    [el('kbd', { text: 'tab' }), document.createTextNode(' complete')]
  ]
  items.forEach((parts, i) => {
    if (i > 0) footer.appendChild(document.createTextNode(' · '))
    parts.forEach(p => footer.appendChild(p))
  })
  return footer
}

// ---------------------------------------------------------------------------
// Widget controller
// ---------------------------------------------------------------------------

function init (root) {
  if (!root || root.dataset.djangoTomselectTokenInitialized === '1') return
  root.dataset.djangoTomselectTokenInitialized = '1'

  const targetName = root.dataset.targetName
  const compositeUrl = root.dataset.composite || root.dataset.compositeUrl
  if (!compositeUrl) {
    console.warn('[django-tomselect-token] no composite URL on', root)
    return
  }

  let config = {}
  try {
    config = JSON.parse(root.dataset.config || '{}')
  } catch (e) {
    console.warn('[django-tomselect-token] invalid config JSON on', root)
  }

  // CSS.escape() - guards against form-field names with CSS-meaningful chars
  // (e.g. dotted formset names) that would break a naive attribute selector.
  const hiddenInput = document.querySelector(
    'input[data-django-tomselect-token-input][name="' + (window.CSS && window.CSS.escape ? window.CSS.escape(targetName) : targetName) + '"]'
  )
  if (!hiddenInput) {
    console.warn('[django-tomselect-token] hidden input not found for', targetName)
    return
  }

  // State
  let operatorList = []
  let operatorMap = {}
  const hydration = (window[HYDRATION_CACHE_KEY] = window[HYDRATION_CACHE_KEY] || new Map())
  let mode = 'operator-menu'
  let activeOpKey = null
  // AbortController for the in-flight value-mode fetch. Each new keystroke
  // aborts the prior request so a slow response can't overwrite a faster
  // newer one (race condition).
  let valueFetchController = null

  // DOM construction
  while (root.firstChild) root.removeChild(root.firstChild)
  const chipsEl = el('div', { class: 'tw-chips' })
  chipsEl.style.display = 'contents'
  root.appendChild(chipsEl)

  const draftEl = el('input', { class: 'tw-input', type: 'text' })
  draftEl.placeholder = (hiddenInput.placeholder || '')
  root.appendChild(draftEl)

  const dropdownEl = el('div', { class: 'tw-dropdown', hidden: true })
  root.appendChild(dropdownEl)

  const errorEl = el('div', { class: 'tw-error-msg' })
  errorEl.style.display = 'none'
  root.parentNode.insertBefore(errorEl, root.nextSibling)

  function operatorRegistryForParser () {
    const out = {}
    for (const op of operatorList) out[op.key] = { multi: !!op.multi }
    return out
  }

  function serializedValue () { return hiddenInput.value || '' }

  function setSerialized (s) {
    hiddenInput.value = s
    hiddenInput.dispatchEvent(new Event('change', { bubbles: true }))
  }

  function clearChildren (node) {
    while (node.firstChild) node.removeChild(node.firstChild)
  }

  function renderChips () {
    const parsed = parseQuery(serializedValue(), operatorRegistryForParser(), {
      max_raw_length: config.max_query_length || 4096,
      max_tokens: config.max_tokens || 32
    })

    clearChildren(chipsEl)
    let hasError = false

    for (const err of parsed.errors) {
      hasError = true
      chipsEl.appendChild(buildErrorChip(err.message))
    }

    for (const t of parsed.tokens) {
      const valueText = t.values.join(',')
      const cacheKey = t.key + ':' + valueText
      const cached = hydration.has(cacheKey) ? hydration.get(cacheKey) : undefined
      chipsEl.appendChild(buildTokenChip(t, cached))
      if (cached === undefined && t.values.length === 1) {
        scheduleResolve([[t.key, t.values[0]]])
      }
    }

    for (const ft of parsed.free_text) {
      chipsEl.appendChild(buildFreeTextChip(ft))
    }

    if (hasError) root.classList.add('error')
    else root.classList.remove('error')
  }

  let resolveQueue = []
  let resolveScheduled = false
  function scheduleResolve (pairs) {
    for (const p of pairs) resolveQueue.push(p)
    if (resolveScheduled) return
    resolveScheduled = true
    Promise.resolve().then(async () => {
      resolveScheduled = false
      const pending = resolveQueue.slice()
      resolveQueue = []
      try {
        const data = await fetchResolveBatch(compositeUrl, pending)
        for (const r of data.results || []) {
          const cacheKey = r.op + ':' + (r.value != null ? r.value : r.id)
          hydration.set(cacheKey, r.missing ? null : r.label)
        }
        renderChips()
      } catch (e) {
        console.warn('[django-tomselect-token] resolve failed:', e)
      }
    })
  }

  function showOperatorMenu (draft) {
    mode = 'operator-menu'
    clearChildren(dropdownEl)
    dropdownEl.appendChild(buildOperatorMenu(operatorList, draft))
    dropdownEl.hidden = false
  }

  async function showValueDropdown (opKey, draft) {
    mode = 'value-mode'
    activeOpKey = opKey
    clearChildren(dropdownEl)
    dropdownEl.appendChild(el('div', { class: 'tw-dropdown-heading', text: 'Loading…' }))
    dropdownEl.hidden = false

    // Abort any prior in-flight fetch. The new keystroke supersedes it; we
    // never want a slow stale response to overwrite a fresh one.
    if (valueFetchController) valueFetchController.abort()
    const controller = (typeof AbortController !== 'undefined') ? new AbortController() : null
    valueFetchController = controller

    try {
      const data = await fetchValueResults(
        compositeUrl, opKey, draft, 1, controller ? controller.signal : null
      )
      // If we've been superseded between fetch and resolve, drop the response.
      if (controller && controller.signal.aborted) return
      // Mode might have changed (user pressed Esc / committed); only render
      // if we are still in value-mode for the same operator.
      if (mode !== 'value-mode' || activeOpKey !== opKey) return
      const opMeta = operatorMap[opKey]
      clearChildren(dropdownEl)
      dropdownEl.appendChild(buildValueDropdown(opKey, data.results || [], opMeta))
    } catch (e) {
      // AbortError fires when we superseded; silent drop.
      if (e && e.name === 'AbortError') return
      // Don't render the error if mode/op changed under us.
      if (mode !== 'value-mode' || activeOpKey !== opKey) return
      clearChildren(dropdownEl)
      dropdownEl.appendChild(el('div', { class: 'tw-dropdown-heading', text: 'Error loading results.' }))
    }
  }

  function closeDropdown () {
    mode = 'closed'
    dropdownEl.hidden = true
  }

  function commitOperatorAndEnterValueMode (opKey) {
    draftEl.value = ''
    showValueDropdown(opKey, '')
  }

  function commitValueSelection (opKey, id, label) {
    const cacheKey = opKey + ':' + id
    if (label != null) hydration.set(cacheKey, label)
    const existing = serializedValue()
    const newPart = opKey + ':' + id
    const next = existing ? existing + ' ' + newPart : newPart
    setSerialized(next)
    draftEl.value = ''
    closeDropdown()
    activeOpKey = null
    renderChips()
  }

  function commitFreeText (text) {
    if (!text) return
    if (config.allow_free_text === false) return
    const existing = serializedValue()
    const part = /\s/.test(text) ? '"' + text.replace(/"/g, '\\"') + '"' : text
    setSerialized(existing ? existing + ' ' + part : part)
    draftEl.value = ''
    closeDropdown()
    renderChips()
  }

  function removeChipByIndex (index) {
    const parsed = parseQuery(serializedValue(), operatorRegistryForParser(), {
      max_raw_length: config.max_query_length || 4096,
      max_tokens: config.max_tokens || 32
    })
    const flat = []
    for (const t of parsed.tokens) flat.push({ kind: 'token', token: t })
    for (const ft of parsed.free_text) flat.push({ kind: 'freetext', text: ft })
    flat.splice(index, 1)
    const parts = flat.map(item => {
      if (item.kind === 'token') {
        return item.token.key + ':' + item.token.values.join(',')
      }
      return /\s/.test(item.text) ? '"' + item.text.replace(/"/g, '\\"') + '"' : item.text
    })
    setSerialized(parts.join(' '))
    renderChips()
  }

  draftEl.addEventListener('input', () => {
    const draft = draftEl.value
    if (mode === 'value-mode' && activeOpKey) {
      showValueDropdown(activeOpKey, draft)
      return
    }
    const colonIdx = draft.indexOf(':')
    if (colonIdx >= 0) {
      const candidate = draft.slice(0, colonIdx)
      if (operatorMap[candidate]) {
        const remainder = draft.slice(colonIdx + 1)
        commitOperatorAndEnterValueMode(candidate)
        if (remainder) {
          draftEl.value = remainder
          showValueDropdown(candidate, remainder)
        }
        return
      }
    }
    showOperatorMenu(draft)
  })

  draftEl.addEventListener('focus', () => {
    root.classList.add('focused')
    if (mode === 'closed') showOperatorMenu(draftEl.value)
  })

  draftEl.addEventListener('blur', () => {
    setTimeout(() => { root.classList.remove('focused') }, 150)
  })

  draftEl.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
      ev.preventDefault()
      closeDropdown()
    } else if (ev.key === 'Enter' || ev.key === 'Tab') {
      const active = dropdownEl.querySelector('.tw-opt.active')
      if (active) {
        ev.preventDefault()
        active.click()
      } else if (ev.key === 'Enter' && draftEl.value) {
        ev.preventDefault()
        commitFreeText(draftEl.value)
      }
    } else if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
      const opts = Array.from(dropdownEl.querySelectorAll('.tw-opt'))
      if (opts.length === 0) return
      ev.preventDefault()
      const cur = opts.findIndex(elt => elt.classList.contains('active'))
      let next = ev.key === 'ArrowDown' ? cur + 1 : cur - 1
      if (next < 0) next = opts.length - 1
      if (next >= opts.length) next = 0
      opts.forEach(elt => elt.classList.remove('active'))
      opts[next].classList.add('active')
    } else if (ev.key === 'Backspace' && draftEl.value === '') {
      const chips = chipsEl.querySelectorAll('.tw-tok')
      if (chips.length > 0) {
        ev.preventDefault()
        removeChipByIndex(chips.length - 1)
      }
    } else if (ev.key === ' ' && draftEl.value) {
      const text = draftEl.value
      if (config.allow_free_text !== false && !text.includes(':')) {
        ev.preventDefault()
        commitFreeText(text)
      }
    }
  })

  dropdownEl.addEventListener('mousedown', (ev) => {
    const opt = ev.target.closest('.tw-opt')
    if (!opt) return
    ev.preventDefault()
    const action = opt.dataset.action
    if (action === 'select-operator') {
      commitOperatorAndEnterValueMode(opt.dataset.key)
    } else if (action === 'select-value' && activeOpKey) {
      commitValueSelection(activeOpKey, opt.dataset.id, opt.dataset.label)
    }
  })

  chipsEl.addEventListener('click', (ev) => {
    const x = ev.target.closest('.tw-tok-x')
    if (!x) return
    const chips = Array.from(chipsEl.querySelectorAll('.tw-tok'))
    const idx = chips.indexOf(x.closest('.tw-tok'))
    if (idx >= 0) removeChipByIndex(idx)
  })

  root.addEventListener('click', (ev) => {
    if (ev.target === root || ev.target === chipsEl) {
      draftEl.focus()
    }
  })

  fetchOperators(compositeUrl).then(data => {
    operatorList = data.operators || []
    operatorMap = {}
    for (const op of operatorList) operatorMap[op.key] = op
    renderChips()
  }).catch(e => {
    console.warn('[django-tomselect-token] could not load operators:', e)
    errorEl.textContent = 'Could not load filter options. Free-text search still works.'
    errorEl.style.display = 'block'
  })
}

// ---------------------------------------------------------------------------
// Public global
// ---------------------------------------------------------------------------

if (typeof window !== 'undefined') {
  window.djangoTomSelectToken = window.djangoTomSelectToken || {}
  window.djangoTomSelectToken.init = init
  window.djangoTomSelectToken.parseQuery = parseQuery
  window.djangoTomSelectToken.PARSE_ERRORS = PARSE_ERRORS
}

export { init, parseQuery, PARSE_ERRORS }
