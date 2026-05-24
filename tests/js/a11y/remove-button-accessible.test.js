// Accessibility tests for the keyboard-operable remove_button plugin
// (client/plugins/remove_button_accessible/plugin.js).
//
// Tom Select plugins run with `this === tomSelectInstance` and register a
// hook; the render override is installed when the `setupTemplates` hook fires,
// not when the plugin function is called. The fake instance below mirrors that
// contract: call the plugin, fire the hook, then exercise render.item.

import { describe, it, expect } from 'vitest'

import accessibleRemoveButton from '../../../client/plugins/remove_button_accessible/plugin.js'

function makeInstance (settings = {}) {
  const hooks = {}
  const self = {
    isLocked: false,
    settings: Object.assign({
      labelField: 'name',
      valueField: 'id',
      render: {
        item: (data) => {
          const node = document.createElement('div')
          node.className = 'item'
          node.textContent = data[self.settings.labelField] != null
            ? String(data[self.settings.labelField])
            : String(data[self.settings.valueField])
          return node
        }
      }
    }, settings),
    hook (when, name, fn) { hooks[name] = fn },
    shouldDelete () { return true },
    removeItem () { self._removed = true },
    refreshOptions () {},
    inputState () {}
  }
  return { self, hooks }
}

describe('accessible remove_button plugin', () => {
  it('renders a focusable <button> with an item-specific aria-label', () => {
    const { self, hooks } = makeInstance()
    accessibleRemoveButton.call(self, { label: '×', title: 'Remove', className: 'remove' })
    expect(typeof hooks.setupTemplates).toBe('function')
    hooks.setupTemplates()

    const item = self.settings.render.item({ name: 'North Lateral 4A' }, (s) => s)
    const btn = item.querySelector('button')
    expect(btn).toBeTruthy()
    expect(btn.getAttribute('type')).toBe('button')
    expect(btn.classList.contains('remove')).toBe(true)
    // Must be tab-reachable: no negative tabindex (unlike the bundled <a>).
    expect(btn.hasAttribute('tabindex')).toBe(false)
    expect(btn.getAttribute('aria-label')).toBe('Remove North Lateral 4A')
  })

  it('removes the item when the button is activated', () => {
    const { self, hooks } = makeInstance()
    accessibleRemoveButton.call(self, {})
    hooks.setupTemplates()

    const item = self.settings.render.item({ name: 'Gate 12' }, (s) => s)
    const btn = item.querySelector('button')
    btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }))
    expect(self._removed).toBe(true)
  })

  it('falls back to the value field when the label field is absent', () => {
    const { self, hooks } = makeInstance()
    accessibleRemoveButton.call(self, {})
    hooks.setupTemplates()

    const item = self.settings.render.item({ id: 42 }, (s) => s)
    const btn = item.querySelector('button')
    expect(btn.getAttribute('aria-label')).toBe('Remove 42')
  })

  it('does not override rendering when append is disabled', () => {
    const { self, hooks } = makeInstance()
    accessibleRemoveButton.call(self, { append: false })
    expect(hooks.setupTemplates).toBeUndefined()
  })
})
