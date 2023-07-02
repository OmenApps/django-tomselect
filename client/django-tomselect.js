import TomSelect from 'tom-select/src/tom-select'

/* eslint-disable camelcase */
import clear_button from 'tom-select/src/plugins/clear_button/plugin'
import dropdown_header from 'tom-select/src/plugins/dropdown_header/plugin'
import dropdown_input from 'tom-select/src/plugins/dropdown_input/plugin'
import remove_button from 'tom-select/src/plugins/remove_button/plugin'
import virtual_scroll from 'tom-select/src/plugins/virtual_scroll/plugin'
/* eslint-enable camelcase */

TomSelect.define('clear_button', clear_button)
TomSelect.define('dropdown_header', dropdown_header)
TomSelect.define('dropdown_input', dropdown_input)
TomSelect.define('remove_button', remove_button)
TomSelect.define('virtual_scroll', virtual_scroll)

/**
 * Extract the form prefix from the name of the given element.
 */
function getFormPrefix (elem) {
  const parts = elem.getAttribute('name').split('-').slice(0, -1)
  if (parts.length) {
    return parts.join('-') + '-'
  }
  return ''
}

/**
 * Walk through the given (form) prefixes and return the first element
 * matching prefix + name.
 **/
function getElementByPrefixedName (name, prefixes) {
  const _prefixes = prefixes || []
  _prefixes.push('')
  for (let i = 0; i < _prefixes.length; i++) {
    const element = document.querySelector(`[name=${prefixes[i] + name}]`)
    if (element) {
      return element
    }
  }
}

function getSettings (elem) {
  function buildUrl (query, page) {
    // Get the fields to select with queryset.values()
    let valuesSelect = [elem.dataset.valueField, elem.dataset.labelField]
    if (elem.extraColumns) {
      valuesSelect = valuesSelect.concat(elem.extraColumns)
    }
    const params = new URLSearchParams({
      q: encodeURIComponent(query),
      p: page,
      model: encodeURIComponent(elem.dataset.model),
      sl: encodeURIComponent(elem.dataset.searchLookup),
      vs: encodeURIComponent(JSON.stringify(valuesSelect))
    })
    if (elem.filterByElem) {
      params.append('f', encodeURIComponent(`${elem.filterByLookup}=${elem.filterByElem.value}`))
    }
    return `${elem.dataset.autocompleteUrl}?${params.toString()}`
  }
  elem.extraColumns = elem.hasAttribute('is-tabular') ? JSON.parse(elem.dataset.extraColumns) : []
  elem.labelColClass = elem.extraColumns.length > 0 && elem.extraColumns.length < 4 ? 'col-5' : 'col'
  if (elem.dataset.filterBy) {
    const filterBy = JSON.parse(elem.dataset.filterBy)
    elem.filterByElem = getElementByPrefixedName(filterBy[0], [getFormPrefix(elem)])
    elem.filterByLookup = filterBy[1]
  }

  return {
    preload: 'focus',
    maxOptions: null,
    searchField: [], // disable sifter search
    // Add bootstrap 'form-control' to the search input:
    controlInput: '<input class="form-control mb-1"/>',
    // Pad the dropdown to make it appear in a neat box:
    dropdownClass: 'ts-dropdown p-2',
    maxItems: elem.hasAttribute('is-multiple') ? null : 1,

    valueField: elem.dataset.valueField,
    labelField: elem.dataset.labelField,
    showValueField: elem.dataset.showValueField ? JSON.parse(elem.dataset.showValueField) : false,
    createField: elem.dataset.createField,
    extraColumns: elem.extraColumns,
    labelColClass: elem.labelColClass,

    firstUrl: (query) => buildUrl(query, 1),
    load: function (query, callback) {
      const url = this.getUrl(query)
      fetch(url)
        .then(response => response.json())
        .then(json => {
          if (json.has_more) {
            this.setNextUrl(query, buildUrl(query, json.page + 1))
          }
          this.settings.showCreateOption = json.show_create_option
          // Workaround for an issue of the virtual scroll plugin
          // where it  scrolls to the top of the results whenever
          // a new page of results is added.
          // https://github.com/orchidjs/tom-select/issues/556
          const _scrollToOption = this.scrollToOption
          this.scrollToOption = () => {}
          callback(json.results)
          this.scrollToOption = _scrollToOption
        }).catch(() => {
          callback()
        })
    },
    plugins: getPlugins(elem),
    render: getRenderTemplates(elem)
  }
}

function getPlugins (elem) {
  const plugins = {
    dropdown_input: null,
    virtual_scroll: null
  }

  if (elem.hasAttribute('is-multiple')) {
    plugins.remove_button = { title: 'Removed' }
    plugins.clear_button = { title: 'Clear' }
  }

  if (elem.hasAttribute('is-tabular')) {
    plugins.dropdown_header = {
      html: function (settings) {
        let header = ""

        if (settings.showValueField === true) {
          header = `<div class="col-1"><span class="${settings.labelClass}">${settings.valueFieldLabel}</span></div>
                      <div class="${settings.labelColClass}"><span class="${settings.labelClass}">${settings.labelFieldLabel}</span></div>`
        } else {
          header = `<div class="${settings.labelColClass}"><span class="${settings.labelClass}">${settings.labelFieldLabel}</span></div>`
        }

        for (const h of settings.extraHeaders) {
          header += `<div class="col"><span class="${settings.labelClass}">${h}</span></div>`
        }
        return `<div class="${settings.headerClass}"><div class="${settings.titleRowClass}">${header}</div></div>`
      },
      valueFieldLabel: elem.dataset.valueFieldLabel,
      labelFieldLabel: elem.dataset.labelFieldLabel,
      labelColClass: elem.labelColClass,
      showValueField: elem.dataset.showValueField ? JSON.parse(elem.dataset.showValueField) : false,
      extraHeaders: JSON.parse(elem.dataset.extraHeaders),
      headerClass: 'container-fluid bg-primary text-bg-primary pt-1 pb-1 mb-2 dropdown-header',
      titleRowClass: 'row'
    }
  }
  return plugins
}

function getRenderTemplates (elem) {
  const templates = {
    no_results: function (data, escape) {
      return '<div class="no-results">No Results</div>'
    },
    option_create: function (data, escape) {
      return '<div class="create bg-secondary text-bg-secondary">Add value <strong>' + escape(data.input) + '</strong>&hellip;</div>'
    },
    loading_more: function (data, escape) {
      return '<div class="loading-more-results py-2 d-flex align-items-center"><div class="spinner"></div> Load more results </div>'
    },
    no_more_results: function (data, escape) {
      return '<div class="no-more-results">No more results</div>'
    }
  }
  if (elem.hasAttribute('is-tabular')) {
    templates.option = function (data, escape) {
      let columns = "";

      if (this.settings.showValueField === true) {
        columns = `<div class="col-1">${data[this.settings.valueField]}</div>
                   <div class="${this.settings.labelColClass}">${data[this.settings.labelField]}</div>`
      } else {
        columns = `<div class="${this.settings.labelColClass}">${data[this.settings.labelField]}</div>`
      }

      for (const c of this.settings.extraColumns) {
        columns += `<div class="col">${escape(data[c] || '')}</div>`
      }
      return `<div class="row">${columns}</div>`
    }
  }
  return templates
}

function attachFooter (ts, elem) {
  const listviewURL = elem.dataset.listviewUrl
  const addURL = elem.dataset.addUrl
  if (listviewURL || addURL) {
    const footer = document.createElement('div')
    footer.classList.add('d-flex', 'mt-1', 'dropdown-footer')

    if (addURL) {
      const addBtn = document.createElement('a')
      addBtn.classList.add('btn', 'btn-success', 'add-btn', 'd-none')
      addBtn.href = addURL
      addBtn.target = '_blank'
      addBtn.innerHTML = 'Add value'
      footer.appendChild(addBtn)
      ts.on('load', () => {
        if (ts.settings.showCreateOption) {
          addBtn.classList.remove('d-none')
        } else {
          addBtn.classList.add('d-none')
        }
      })
      ts.on('type', (query) => {
        if (query) {
          addBtn.innerHTML = `Add value '${query}'`
        } else {
          addBtn.innerHTML = 'Add value'
        }
      })
      ts.on('blur', () => { addBtn.innerHTML = 'Add value' })

      // If given a create field, try adding new model objects via AJAX request.
      const createField = elem.dataset.createField
      if (createField) {
        addBtn.addEventListener('click', (e) => {
          if (!ts.lastValue) {
            // No search term: just open the add page.
            return
          }
          e.preventDefault()
          const form = new FormData()
          form.append('create-field', createField)
          form.append(createField, ts.lastValue)
          form.append('model', elem.dataset.model)
          const options = {
            method: 'POST',
            headers: {
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: form
          }
          fetch(elem.dataset.autocompleteUrl, options)
            .then(response => {
              if (!response.ok) {
                throw new Error('POST request failed.')
              }
              return response.json()
            }).then(json => {
              const data = {}
              data[ts.settings.valueField] = json.pk
              data[ts.settings.labelField] = json.text
              ts.addOption(data, true)
              ts.setCaret(ts.caretPos)
              ts.addItem(json.pk)
            }).catch((error) => console.log(error))
        })
      }
    }

    if (listviewURL) {
      const listviewLink = document.createElement('a')
      listviewLink.classList.add('btn', 'btn-info', 'ms-auto', 'cl-btn')
      listviewLink.href = listviewURL
      listviewLink.target = '_blank'
      listviewLink.innerHTML = 'List View'
      footer.appendChild(listviewLink)
      ts.on('type', (query) => {
        // TODO: include value of filterBy in query
        if (query) {
          // Update the URL to the listview to include the query
          const queryString = new URLSearchParams({ q: encodeURIComponent(query) }).toString()
          listviewLink.href = `${listviewURL}?${queryString}`
        } else {
          listviewLink.href = listviewURL
        }
      })
      ts.on('blur', () => { listviewLink.href = listviewURL })
    }

    ts.dropdown.appendChild(footer)
  }
}

document.addEventListener('DOMContentLoaded', (event) => {
  document.querySelectorAll('[is-tomselect]').forEach((elem) => {
    const ts = new TomSelect(elem, getSettings(elem))
    attachFooter(ts, elem)

    // Reload the default/initial options when the input is cleared:
    ts.on('type', (query) => {
      if (!query) {
        ts.load('')
        ts.refreshOptions()
      }
    })
    if (elem.filterByElem) {
      // Force re-fetching the options when the value of the filterBy element
      // changes.
      elem.filterByElem.addEventListener('change', () => {
        // Reset the pagination (query:url) mapping of the virtual_scroll
        // plugin. This is necessary because the filter value is not part of
        // the query string, which means that the mapping might return an URL
        // that is incorrect for the current filter.
        ts.getUrl(null)
        // Clear all options, but leave the selected items.
        ts.clearOptions()
        // Remove the flag that this element has already been loaded.
        ts.wrapper.classList.remove('preloaded')
      })
    }
  })
})
