# Templates

Django TomSelect uses a flexible template system that allows for customization at multiple levels. All templates are located in the `django_tomselect/templates/django_tomselect/` directory.

## Template Structure

```
django_tomselect/templates/django_tomselect/
├── helpers/                  # Helper templates
│   └── decode_if_needed.html # HTML entity decoding helper
├── render/                   # Individual rendering components
│   ├── clear_button.html     # Clear selection button
│   ├── dropdown_footer.html  # Footer with actions
│   ├── dropdown_header.html  # Header with column titles
│   ├── item.html             # Selected item display
│   ├── loading_more.html     # Loading more results indicator
│   ├── loading.html          # Initial loading indicator
│   ├── no_more_results.html  # End of results message
│   ├── no_results.html       # No matches found message
│   ├── not_loading.html      # Non-loading state
│   ├── optgroup_header.html  # Option group header
│   ├── optgroup.html         # Option group container
│   ├── option_create.html    # Create new item option
│   ├── option.html           # Individual option display
│   └── select.html           # Base select element
├── tomselect_setup.html      # Global setup and initialization
└── tomselect.html            # Main template
```

## Main Template

### tomselect.html

The main template that orchestrates the Tom Select initialization and rendering.

```django
{% block select_element %}
    {% include "django_tomselect/render/select.html" with widget=widget %}
{% endblock select_element %}

{% block tomselect_init %}
    {# Tom Select initialization code #}
{% endblock tomselect_init %}

{% block tomselect_url_setup %}
    {# URL construction logic #}
{% endblock tomselect_url_setup %}

{% block tomselect_config %}
    {# TomSelect configuration object #}
{% endblock tomselect_config %}

{% block tomselect_plugins %}
    {# Plugin configuration #}
{% endblock tomselect_plugins %}

{% block tomselect_render %}
    {# Render functions for different components #}
{% endblock tomselect_render %}

{% block tomselect_extra_js %}
    {# Additional JavaScript #}
{% endblock tomselect_extra_js %}
```

#### Customization Example

```django
{# templates/myapp/custom_tomselect.html #}
{% extends "django_tomselect/tomselect.html" %}

{% block tomselect_init %}
    {{ block.super }}
    {# Add custom initialization code #}
    document.addEventListener("tomselect:initialized", function(e) {
        console.log("TomSelect initialized:", e.detail);
    });
{% endblock %}
```

## Global Setup Template

### tomselect_setup.html

This template is used to set up the global TomSelect configuration and initialization logic once per page, including an observer for dynamic content.

```django
{% extends "django_tomselect/tomselect.html" %}

{% load i18n %}
{% load django_tomselect %}

<script>
    {% block tomselect_global_setup %}
        // Global namespace for django-tomselect
        if (!window.djangoTomSelect) {
            window.djangoTomSelect = {
                configs: new Map(),
                instances: new Map(),
                initialized: false,
                // ... other configuration

                // Setup MutationObserver for dynamic content
                setupObserver: function() {
                    // ... observer setup code
                },

                // Setup HTMX event handlers
                setupHtmxHandlers: function() {
                    // ... htmx event handlers
                }
            };
        }
    {% endblock tomselect_global_setup %}
</script>
```

## Helper Templates

### decode_if_needed.html

A utility helper that safely decodes HTML entities only when needed.

```django
{% comment %}
Helper function to safely decode HTML entities only if they exist.
{% endcomment %}
function decodeIfNeeded(str) {
    if (!str || typeof str !== 'string') return '';

    // Check if string contains HTML entities
    if (/&[a-z]+;|&#[0-9]+;/i.test(str)) {
        const textarea = document.createElement('textarea');
        textarea.innerHTML = str;
        return textarea.value;
    }

    // No HTML entities, return as is
    return str;
}
```

## Rendering Components

### select.html

Base `<select>` element template. Override this to modify the fundamental HTML structure.

```django
<select name="{{ widget.name }}"
        id="{% if 'id' in widget.attrs.keys and widget.attrs.id %}{{ widget.attrs.id }}{% else %}{{ widget.name }}{% endif %}"
        {% include "django/forms/widgets/attrs.html" with widget=widget %}
        aria-label="{% translate 'Select option' %}"
        aria-expanded="false"
        role="combobox">
</select>
```

### option.html

Defines how individual options are rendered in the dropdown.

```django
{% comment %}
Renders each option (search result) in the dropdown.
If is_tabular is true, renders a row of columns.
If not, checks for custom rendering templates.
{% endcomment %}
{% load i18n %}

option: function(data, escape) {
    {% include "django_tomselect/helpers/decode_if_needed.html" %}

    {% if 'data_template_option' in widget.attrs.keys and widget.attrs.data_template_option %}
        var template = {{ widget.attrs.data_template_option|safe }};
        var result = template.replace(/\$\{data\.(\w+)\}/g, function(match, fieldName) {
            var value = data[fieldName];
            if (value === undefined || value === null) return '';
            return escape(String(value));
        });
        // Also support ${escape(data.fieldName)} pattern for explicit escaping
        result = result.replace(/\$\{escape\(data\.(\w+)\)\}/g, function(match, fieldName) {
            var value = data[fieldName];
            if (value === undefined || value === null) return '';
            return escape(String(value));
        });
        return result;
    {% elif widget.is_tabular %}
        // For tabular display, show in rows and columns
        let columns = '';

        {% if widget.plugins.dropdown_header.show_value_field %}
            columns += `<div class="col" role="gridcell">${escape(data[this.settings.valueField])}</div>
            <div class="col" role="gridcell">${escape(data[this.settings.labelField])}</div>`;
        {% else %}
            columns += `<div class="col" role="gridcell">${escape(data[this.settings.labelField])}</div>`;
        {% endif %}

        {% for item in widget.plugins.dropdown_header.extra_values %}
            columns += `<div class="col" role="gridcell">${escape(data['{{ item|escapejs }}'] || '')}</div>`;
        {% endfor %}

        return `<div class="row" role="row">${columns}</div>`;
    {% else %}
        const safeValue = escape(decodeIfNeeded(data['{{ widget.label_field|escapejs }}']));

        return `<div role="option">${safeValue}</div>`;
    {% endif %}
},
```

### item.html

Controls how selected items are displayed.

```django
{% comment %}
Renders each selected item in the TomSelect input.
{% endcomment %}
{% load i18n %}

item: function(data, escape) {
    {% include "django_tomselect/helpers/decode_if_needed.html" %}

    {% if 'data_template_item' in widget.attrs.keys and widget.attrs.data_template_item %}
        var template = {{ widget.attrs.data_template_item|safe }};
        var result = template.replace(/\$\{data\.(\w+)\}/g, function(match, fieldName) {
            var value = data[fieldName];
            if (value === undefined || value === null) return '';
            return escape(String(value));
        });
        // Also support ${escape(data.fieldName)} pattern for explicit escaping
        result = result.replace(/\$\{escape\(data\.(\w+)\)\}/g, function(match, fieldName) {
            var value = data[fieldName];
            if (value === undefined || value === null) return '';
            return escape(String(value));
        });
        return result;
    {% else %}
        let item = '';
        const safeValue = escape(decodeIfNeeded(data['{{ widget.label_field|escapejs }}']));

        item += `<div role="option">${safeValue}`;

        {% if "show_detail" in widget and widget.show_detail %}
            if (data.detail_url) {
                item += `
                <a href="${escape(data.detail_url)}"
                   class="update"
                   title="{% translate 'Detail' %}"
                   tabindex="-1"
                   aria-label="{% translate 'View Detail' %}"
                   onclick="event.stopPropagation(); return true;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-info" role="img" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="8"></line></svg>
                </a>`;
            }
        {% endif %}

        {% if "show_delete" in widget and widget.show_delete %}
            if (data.delete_url) {
                item += `
                <a href="${escape(data.delete_url)}"
                   class="update"
                   title="{% translate 'Delete' %}"
                   tabindex="-1"
                   aria-label="{% translate 'Delete item' %}"
                   onclick="event.stopPropagation(); return true;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-danger" role="img" aria-hidden="true"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                </a>`;
            }
        {% endif %}

        {% if "show_update" in widget and widget.show_update %}
            if (data.update_url) {
                item += `
                <a href="${escape(data.update_url)}"
                   class="update"
                   title="{% translate 'Update' %}"
                   target="_blank"
                   tabindex="-1"
                   aria-label="{% translate 'Update item' %}"
                   onclick="event.stopPropagation(); return true;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-success" role="img" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                </a>`;
            }
        {% endif %}

        item += '</div>';
        return item;
    {% endif %}
},
```

### dropdown_header.html

Configures the dropdown header display.

```django
{% comment %}
Renders the Dropdown Header plugin's HTML.
{% endcomment %}
{% load i18n %}

html: function (data) {
    let header = '';

    {% if widget.plugins.dropdown_header.show_value_field %}
        header += `
        <div class="col">
            <span class="{{ widget.plugins.dropdown_header.label_class }}" role="columnheader">{{ widget.plugins.dropdown_header.value_field_label|escapejs }}</span>
        </div>
        <div class="col">
            <span class="{{ widget.plugins.dropdown_header.label_class }}" role="columnheader">{{ widget.plugins.dropdown_header.label_field_label|escapejs }}</span>
        </div>
        `;
    {% else %}
        header += `
        <div class="col">
            <span class="{{ widget.plugins.dropdown_header.label_class }}" role="columnheader">{{ widget.plugins.dropdown_header.label_field_label|escapejs }}</span>
        </div>
        `;
    {% endif %}

    {% for header_text in widget.plugins.dropdown_header.extra_headers %}
        header += `
        <div class="col">
            <span class="{{ widget.plugins.dropdown_header.label_class }}" role="columnheader">{{ header_text|escapejs }}</span>
        </div>
        `;
    {% endfor %}

    return `<div class="{{ widget.plugins.dropdown_header.header_class }}" title="{{ widget.plugins.dropdown_header.title|escapejs }}" role="row">
                <div class="{{ widget.plugins.dropdown_header.title_row_class }}">${header}</div>
            </div>`;
},
```

### dropdown_footer.html

Configures the dropdown footer with action buttons.

```django
{% comment %}
Renders the Dropdown Footer plugin's HTML.
{% endcomment %}
{% load i18n %}

{% block code %}
html: function (data) {
    let footer = ''
    footer += `
    <div title="{{ widget.plugins.dropdown_footer.title|escapejs }}" class="{{ widget.plugins.dropdown_footer.footer_class }}">
        {% if "view_create_url" in widget and widget.view_create_url %}
            <a href="{{ widget.view_create_url|escapejs }}" title='{% translate "Go to Create View for these items" %}' class="{{ widget.plugins.dropdown_footer.create_view_class }}" target="_blank" rel="noopener noreferrer">{{ widget.plugins.dropdown_footer.create_view_label|escapejs }}</a>
        {% endif %}

        {% if "view_list_url" in widget and widget.view_list_url %}
            <a href="{{ widget.view_list_url|escapejs }}" title='{% translate "Go to List View for these items" %}' class="{{ widget.plugins.dropdown_footer.list_view_class }}" target="_blank" rel="noopener noreferrer">{{ widget.plugins.dropdown_footer.list_view_label|escapejs }}</a>
        {% endif %}
    </div>
    `
    return footer
},
{% endblock code %}
```

## Status Templates

### loading.html

Shows loading state while fetching results.

```django
{% comment %}
Renders the loading spinner/message while initial results load.
{% endcomment %}
{% load i18n %}

loading: function(data, escape){
    return '<div class="spinner" role="status" aria-label="{% translate 'Loading' %}" aria-live="polite"></div>';
},
```

### loading_more.html

Shows the loading indicator when fetching more results.

```django
{% comment %}
Renders the "Loading more results..." message.
{% endcomment %}
{% load i18n %}

loading_more: function(data, escape) {
    return `<div class="loading-more-results py-2 d-flex align-items-center" role="status" aria-live="polite">
        <div class="spinner" aria-hidden="true"></div>
        {% translate "Loading more results..." %}
    </div>`;
},
```

### no_results.html

Displays when no matches are found.

```django
{% comment %}
Renders the message when no search results are found.
{% endcomment %}
{% load i18n %}

no_results: function(data, escape){
    return `<div class="no-results" role="status" aria-live="polite">
        {% translate "No results found for" %} "${escape(data.input)}"
    </div>`;
},
```

### no_more_results.html

Displays when the end of results is reached.

```django
{% comment %}
Renders the message when no more results are available.
{% endcomment %}
{% load i18n %}
no_more_results: function(data, escape) {
    return `<div class="no-more-results" role="status" aria-live="polite">{% translate "No more results" %}</div>`;
},
```

### option_create.html

Template for the "create new option" element. This template renders the UI that appears when a user types a value that doesn't match any existing options (when `create=True` in the config).

When `create_with_htmx=True` and a `create_url` is configured on the autocomplete view, clicking the create option will POST to that URL via HTMX. Otherwise, it renders the standard Tom Select create option.

```django
{% comment %}
Renders the "Create new option" element if enabled.

When create_with_htmx is True and a view_create_url is configured on the autocomplete view,
the create option will POST to that URL via HTMX. Otherwise, it renders the standard
Tom Select create option that triggers the native create flow.
{% endcomment %}
{% load i18n %}
option_create: function(data, escape) {
    {% if 'create_with_htmx' in widget.keys and widget.create_with_htmx and 'view_create_url' in widget.keys and widget.view_create_url %}
        return `<div class="create"
                    hx-post="{{ widget.view_create_url|escapejs }}"
                    hx-swap="outerHTML"
                    hx-trigger="click"
                    hx-target="#id_{{ widget.name|escapejs }}"
                    role="option"
                    aria-label="{% translate 'Create new item' %}">${escape(data.input)}</div>`;
    {% else %}
        return `<div class="create" role="option">
            {% translate "Add" %} <strong>${escape(data.input)}</strong>&hellip;
        </div>`;
    {% endif %}
},
```

```{note}
The HTMX version requires `create_url` to be defined on your autocomplete view. If `create_with_htmx=True` but no `create_url` is configured, the template falls back to the standard (non-HTMX) create option.
```

## Custom Rendering Examples

### Custom Option Display

```django
{# templates/myapp/custom_option.html #}
{% block code %}
option: function(data, escape) {
    return `
        <div class="custom-option">
            <img src="${escape(data.thumbnail_url)}" alt="">
            <div class="details">
                <div class="title">${escape(data.title)}</div>
                <div class="subtitle">${escape(data.subtitle)}</div>
            </div>
        </div>
    `;
},
{% endblock code %}
```

### Custom Item Display

```django
{# templates/myapp/custom_item.html #}
{% block code %}
item: function(data, escape) {
    return `
        <div class="custom-item">
            <span class="badge">${escape(data.category)}</span>
            <span class="label">${escape(data.label)}</span>
            {% if widget.show_update %}
                <a href="${escape(data.update_url)}" class="edit-btn">
                    <i class="icon-edit"></i>
                </a>
            {% endif %}
        </div>
    `;
},
{% endblock code %}
```

## Template Context

The following context variables are available in all templates:

- `widget`: The widget instance with all its attributes and configuration
  - `name`: Field name
  - `value`: Current value
  - `attrs`: HTML attributes
  - `config`: TomSelect configuration
  - `is_multiple`: Boolean indicating multiple selection
  - `selected_options`: List of currently selected options
  - `plugins`: Configuration for all enabled plugins
  - `show_detail`: Whether to show detail links
  - `show_update`: Whether to show update links
  - `show_delete`: Whether to show delete links

## Overriding Templates

To override any template:

1. Create a matching template path in your project:
```
your_project/
└── templates/
    └── django_tomselect/
        └── render/
            └── template_to_override.html
```

2. Add your template directory to settings:
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        # ...
    },
]
```

## HTMX Integration

For HTMX-enabled templates, additional attributes and functionality are available:

```django
{% if widget.use_htmx %}
    {# In option_create.html for creating new items #}
    hx-post="{{ widget.create_url }}"
    hx-swap="outerHTML"
    hx-trigger="click"
    hx-target="#id_{{ widget.name|escapejs }}"
{% endif %}
```
