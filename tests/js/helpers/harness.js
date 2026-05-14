import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const TEMPLATE_PATH = resolve(
  __dirname,
  '../../../src/django_tomselect/templates/django_tomselect/tomselect_setup.html'
)

// Vitest 4's JSDOM environment copies dom.window properties onto Node's
// global, but the test-facing `window` is NOT the same object as JSDOM's
// internal window. Scripts injected via document.head.appendChild execute
// in JSDOM's window context, so `window.foo = ...` inside an injected
// script lands on JSDOM's window - accessible only via window.jsdom.window
// (which Vitest exposes by stashing the JSDOM instance there).
export function getJsdomWindow () {
  if (!window.jsdom || !window.jsdom.window) {
    throw new Error('window.jsdom.window is not available - is the Vitest JSDOM environment active?')
  }
  return window.jsdom.window
}

export function loadTemplateScript () {
  const html = readFileSync(TEMPLATE_PATH, 'utf-8')

  const decommented = html.replace(/\{%\s*comment\s*%\}[\s\S]*?\{%\s*endcomment\s*%\}/g, '')

  const scriptMatches = [...decommented.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)]
  let candidate = null
  for (const sm of scriptMatches) {
    if (sm[1].includes('window.djangoTomSelect')) {
      candidate = sm[1]
    }
  }
  if (!candidate) {
    throw new Error('Could not locate the djangoTomSelect <script> block in ' + TEMPLATE_PATH)
  }
  let js = candidate

  js = js.replace(/\{%\s*if not widget\.use_htmx\s*%\}[\s\S]*?\{%\s*endif\s*%\}/g, '')
  js = js.replace(/\{%[\s\S]*?%\}/g, '')
  js = js.replace(/\{\{[\s\S]*?\}\}/g, '')

  if (!js.includes('prepareElement')) {
    throw new Error('Extracted script does not contain prepareElement; extraction is wrong')
  }
  if (js.includes('Custom global setup code here')) {
    throw new Error('Extracted script came from the {% comment %} example, not the real block')
  }
  if (js.includes('{%') || js.includes('{{')) {
    throw new Error('Extracted script still contains Django template tags')
  }

  return js
}

// Stub mirrors real Tom Select setup() at node_modules/tom-select/src/tom-select.ts:167/173/410/432:
// snapshot input.getAttribute('class'), create wrapper with those classes, insert wrapper as
// sibling AFTER the input, then add tomselected + ts-hidden-accessible to the input.
export class TomSelectStub {
  constructor (element, config) {
    const snapshottedClasses = element.getAttribute('class') || ''
    this.element = element
    this.config = config
    this.destroyed = false

    const wrapper = element.ownerDocument.createElement('div')
    wrapper.className = ('ts-wrapper ' + snapshottedClasses).trim()
    element.insertAdjacentElement('afterend', wrapper)

    element.classList.add('tomselected')
    element.classList.add('ts-hidden-accessible')

    element.tomselect = this
    this.wrapper = wrapper
  }

  destroy () {
    this.destroyed = true
    this.element.classList.remove('tomselected')
    this.element.classList.remove('ts-hidden-accessible')
    if (this.wrapper && this.wrapper.parentNode) {
      this.wrapper.remove()
    }
    delete this.element.tomselect
  }
}

export function setupHarness (options = {}) {
  const { TomSelectClass = TomSelectStub } = options
  const realWindow = getJsdomWindow()

  delete realWindow.djangoTomSelect
  document.body.replaceChildren()
  document.querySelectorAll('script[data-harness="dts"]').forEach(s => s.remove())

  realWindow.TomSelect = TomSelectClass

  const js = loadTemplateScript()
  const script = document.createElement('script')
  script.dataset.harness = 'dts'
  script.textContent = js
  document.head.appendChild(script)

  if (!realWindow.djangoTomSelect) {
    throw new Error('Harness failed to populate window.djangoTomSelect. Check that vitest.config.js sets runScripts: "dangerously".')
  }
  return realWindow.djangoTomSelect
}

export function makeSelect ({ id = 'id_test', className = '' } = {}) {
  const select = document.createElement('select')
  select.id = id
  if (className) select.className = className
  select.setAttribute('data-tomselect', 'true')
  document.body.appendChild(select)
  return select
}
