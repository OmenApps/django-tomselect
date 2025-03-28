# HTMX Tabs Demo

## Example Overview

This example demonstrates how to use Bootstrap 5 tabs with **[HTMX](https://htmx.org/)** to load tab content dynamically without full page reloads. Each tab makes an HTMX request when selected.

### Key features highlighted:
- Bootstrap 5 tabs integration
- Automatic loading of initial tab content

---

## Key Code Segments

### Main Template with Tabs Structure

The main template sets up the Bootstrap 5 tabs and configures HTMX requests for each tab.

:::{admonition} HTMX Tabs Template
:class: dropdown

```html
<div class="card card-action mb-4">
    <div class="card-body p-0">
        <div class="nav-align-top">
            <ul class="nav nav-tabs nav-fill tabs-line border-bottom-0" role="tablist">
                <li class="nav-item">
                    <a class="nav-link active"
                       data-bs-toggle="tab"
                       aria-selected="true"
                       data-hx-get="{% url 'demo-htmx-form-fragment' %}?tab=1"
                       data-hx-trigger="click"
                       data-hx-target="#tabContent"
                       role="tab">Tab 1</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link"
                       data-bs-toggle="tab"
                       aria-selected="false"
                       data-hx-get="{% url 'demo-htmx-form-fragment' %}?tab=2"
                       data-hx-trigger="click"
                       data-hx-target="#tabContent"
                       role="tab">Tab 2</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link"
                       data-bs-toggle="tab"
                       aria-selected="false"
                       data-hx-get="{% url 'demo-htmx-form-fragment' %}?tab=3"
                       data-hx-trigger="click"
                       data-hx-target="#tabContent"
                       role="tab">Tab 3</a>
                </li>
            </ul>
            <div class="tab-content border-0 px-4 pt-5 mt-2 mx-1" id="tabContent">
                <div class="tab-pane fade show active"
                     role="tabpanel"
                     data-hx-get="{% url 'demo-htmx-form-fragment' %}?tab=1"
                     data-hx-trigger="load"></div>
            </div>
        </div>
    </div>
</div>
```
:::

- **Purpose**: Creates a tabbed interface where each tab triggers an HTMX request to load content dynamically.
- **Key HTMX Attributes**:
  - `data-hx-get`: The URL to fetch content from when the tab is clicked
  - `data-hx-trigger`: When to trigger the request (on click or load)
  - `data-hx-target`: Where to place the loaded content

---

### Tab Content Fragment Template

The fragment template defines the content that will be loaded into each tab.

:::{admonition} Tab Content Fragment Template
:class: dropdown

```html
{% load static %}

{{ form.media }}

<div class="card">
    <div class="card-header">
        <h2>Loading content via htmx Demo</h2>
    </div>
    <div class="card-body">
        <div class="pb-5">This page demonstrates loading the form using htmx.</div>
        <form>
            {% csrf_token %}
            {{ form.as_div }}
        </form>
    </div>
</div>
```
:::

---

### View Functions

The view functions handle both the main page and the tab content fragments.

:::{admonition} HTMX Tabs Views
:class: dropdown

```python
def htmx_tabs_view(request: HttpRequest) -> HttpResponse:
    """View for the htmx tabs demo page."""
    template = "example/basic_demos/htmx_tabs.html"
    context = {}

    return TemplateResponse(request, template, context)


def htmx_form_fragment_view(request: HttpRequest) -> HttpResponse:
    """View for the htmx form fragment page."""
    template = "example/basic_demos/htmx_fragment.html"
    context = {}

    form = Bootstrap5StylingHTMXForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            messages.success(request, "Form submitted successfully!")
        else:
            messages.error(request, "Please correct the errors in the form before proceeding.")

        return HttpResponseRedirect("/")

    # Get the tab parameter to customize content if needed
    tab = request.GET.get('tab', '1')
    context["form"] = form
    context["tab_id"] = tab
    context["tab_title"] = f"Tab {tab} Content"

    return TemplateResponse(request, template, context)
```
:::

---

## Design and Implementation Notes

### Implementation Details
- Each tab link contains the necessary HTMX attributes to trigger content loading
- The initially active tab loads its content via the `data-hx-trigger="load"` attribute
- Bootstrap's tab styling and behavior are preserved while enhancing with dynamic content loading
