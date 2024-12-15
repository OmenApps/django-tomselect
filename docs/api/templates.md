# Templates

Django TomSelect uses a flexible template system that allows for customization at multiple levels. All templates are located in the `django_tomselect/templates/django_tomselect/` directory.

## Template Structure

```
django_tomselect/templates/django_tomselect/
├── tomselect.html             # Main template
└── render/                    # Individual rendering components
    ├── clear_button.html      # Clear selection button
    ├── dropdown_footer.html   # Footer with actions
    ├── dropdown_header.html   # Header with column titles
    ├── item.html             # Selected item display
    ├── loading_more.html     # Loading more results indicator
    ├── loading.html          # Initial loading indicator
    ├── no_more_results.html  # End of results message
    ├── no_results.html       # No matches found message
    ├── not_loading.html      # Non-loading state
    ├── optgroup_header.html  # Option group header
    ├── optgroup.html         # Option group container
    ├── option_create.html    # Create new item option
    ├── option.html           # Individual option display
    └── select.html           # Base select element
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

{% block tomselect_plugins %}
    {# Plugin configuration #}
{% endblock tomselect_plugins %}

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

## Rendering Components

### select.html

Base `<select>` element template. Override this to modify the fundamental HTML structure.

```django
<select name="{{ widget.name }}"
        id="{% if 'id' in widget.attrs.keys %}{{ widget.attrs.id }}{% else %}{{ widget.name }}{% endif %}"
        {% include "django/forms/widgets/attrs.html" %}
        aria-label="{% translate 'Select option' %}"
        role="combobox">
</select>
```

### option.html

Defines how individual options are rendered in the dropdown.

```django
{% block code %}
option: function(data, escape) {
    {% if widget.is_tabular %}
        {# Tabular layout with columns #}
        let columns = ''
        {% if widget.plugins.dropdown_header.show_value_field %}
            columns += `<div class="col">${data[this.settings.valueField]}</div>
                       <div class="col">${data[this.settings.labelField]}</div>`
        {% else %}
            columns += `<div class="col">${data[this.settings.labelField]}</div>`
        {% endif %}
        return `<div class="row">${columns}</div>`
    {% else %}
        return `<div>${data.{{ widget.label_field }}}</div>`;
    {% endif %}
},
{% endblock code %}
```

### item.html

Controls how selected items are displayed.

```django
{% block code %}
item: function(data, escape) {
    let item = `<div>${data.{{ widget.label_field }}}`;

    {% if widget.show_detail %}
        if (data.detail_url) {
            item += `<a href="${escape(data.detail_url)}"
                       class="details-link"
                       title="{% translate 'View Details' %}">
                        <i class="icon-info"></i>
                    </a>`;
        }
    {% endif %}

    item += '</div>';
    return item;
},
{% endblock code %}
```

### dropdown_header.html

Configures the dropdown header display.

```django
{% block code %}
html: function(data) {
    let header = '';
    {% if widget.plugins.dropdown_header.show_value_field %}
        header += `<div class="col">
            <span class="label">{{ widget.plugins.dropdown_header.value_field_label }}</span>
        </div>`;
    {% endif %}
    return `<div class="header">${header}</div>`;
},
{% endblock code %}
```

### dropdown_footer.html

Configures the dropdown footer with action buttons.

```django
{% block code %}
html: function(data) {
    let footer = '';
    {% if widget.view_create_url %}
        footer += `<a href="{{ widget.view_create_url }}"
                     class="create-link">{{ widget.plugins.dropdown_footer.create_view_label }}</a>`;
    {% endif %}
    return `<div class="footer">${footer}</div>`;
},
{% endblock code %}
```

## Status Templates

### loading.html

Shows loading state while fetching results.

```django
{% block code %}
loading: function(data, escape) {
    return '<div class="spinner" role="status" aria-live="polite"></div>';
},
{% endblock code %}
```

### no_results.html

Displays when no matches are found.

```django
{% block code %}
no_results: function(data, escape) {
    return `<div class="no-results">
        {% translate "No results found for" %} "${escape(data.input)}"
    </div>`;
},
{% endblock code %}
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

For HTMX-enabled templates, additional attributes are available:

```django
{% if widget.use_htmx %}
    hx-post="{{ widget.create_url }}"
    hx-trigger="click"
    hx-target="#{{ widget.name }}"
{% endif %}
```
