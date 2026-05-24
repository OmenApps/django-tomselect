// django-tomselect - accessible "remove_button" plugin.
//
// Drop-in replacement for Tom Select's bundled `remove_button` plugin. The
// bundled one renders `<a href="javascript:void(0)" tabindex="-1">`, which is
// excluded from the tab order - keyboard users cannot remove a selected item
// (only Backspace on the last one). This renders a real, tab-reachable
// `<button type="button">` (Enter/Space activate it natively) with an
// item-specific `aria-label` so screen-reader users know what each button
// removes.
//
// Registered under the same `remove_button` name in client/django-tomselect.js,
// so every existing `plugin_remove_button=` config inherits the accessible
// markup with no per-form change.
//
// Based on Tom Select's bundled remove_button plugin (Apache-2.0).

/* eslint-disable camelcase */

// Normalize the original render output (Tom Select item renderers may return
// an HTML string or a DOM node) into a DOM element. Mirrors Tom Select's
// internal getDom for the cases this plugin encounters.
function getDom (query) {
  if (query && query.jquery) return query[0]
  if (query instanceof window.HTMLElement) return query
  if (typeof query === 'string' && query.indexOf('<') > -1) {
    const tpl = document.createElement('template')
    tpl.innerHTML = query.trim()
    return tpl.content.firstChild
  }
  return document.querySelector(query)
}

// Decode a decorative label (default '&times;') to its plain-text glyph
// without injecting live HTML. The button's accessible name is the aria-label,
// so the visible content only needs to be the rendered character - extracting
// textContent via DOMParser keeps this XSS-safe.
function decodeLabel (raw) {
  return new window.DOMParser().parseFromString(String(raw), 'text/html').documentElement.textContent || ''
}

function preventDefault (evt, stop) {
  if (evt) {
    evt.preventDefault()
    if (stop) evt.stopPropagation()
  }
}

export default function (userOptions) {
  const options = Object.assign({
    label: '&times;',
    title: 'Remove',
    className: 'remove',
    append: true
  }, userOptions)

  const self = this

  // Match the bundled plugin's opt-out: nothing to append, nothing to wrap.
  if (!options.append) return

  self.hook('after', 'setupTemplates', () => {
    const orig_render_item = self.settings.render.item

    self.settings.render.item = (data, escape) => {
      const item = getDom(orig_render_item.call(self, data, escape))

      // Name the button after the item it removes. Prefer the configured
      // label field; fall back to the value field when no label is present.
      const labelField = self.settings.labelField
      const valueField = self.settings.valueField
      let itemLabel = (data && labelField != null && data[labelField] != null)
        ? data[labelField]
        : (data && valueField != null ? data[valueField] : '')
      itemLabel = (itemLabel == null) ? '' : String(itemLabel)

      const close_button = document.createElement('button')
      close_button.type = 'button'
      close_button.className = options.className
      if (options.title) close_button.title = options.title
      close_button.setAttribute('aria-label', ('Remove ' + itemLabel).trim())
      close_button.textContent = decodeLabel(options.label)
      item.appendChild(close_button)

      // Keep mousedown from stealing focus / blurring the control, matching
      // the bundled plugin's behavior.
      close_button.addEventListener('mousedown', (evt) => {
        preventDefault(evt, true)
      })

      close_button.addEventListener('click', (evt) => {
        if (self.isLocked) return
        // Stop propagation so single-mode doesn't reopen the dropdown.
        preventDefault(evt, true)
        if (self.isLocked) return
        if (!self.shouldDelete([item], evt)) return
        self.removeItem(item)
        self.refreshOptions(false)
        self.inputState()
        // removeItem() destroys the focused button without moving focus, so a
        // keyboard user would be dropped onto <body>. Return focus to the
        // control input (Tom Select's text entry) instead.
        if (self.control_input && typeof self.control_input.focus === 'function') {
          self.control_input.focus()
        }
      })

      return item
    }
  })
}
