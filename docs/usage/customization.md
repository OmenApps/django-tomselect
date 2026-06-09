# Customization

`django_tomselect` is highly flexible, allowing you to adjust its visual appearance, modify how data is displayed, and fine-tune plugin settings. From selecting different CSS frameworks to defining custom template blocks, you can tailor the user experience to match the style and functionality of your application.

## Styling and Theming

One of the simplest ways to customize the look of your TomSelect widgets is by choosing a supported CSS framework and adding custom CSS classes.

### CSS Framework Selection

`django_tomselect` supports `default`, `bootstrap4`, and `bootstrap5` frameworks out-of-the-box. You can configure the framework and the use of minified assets in your project’s Django settings:

```python
# settings.py

TOMSELECT = {
    # Options: "default", "bootstrap4", "bootstrap5"
    "DEFAULT_CSS_FRAMEWORK": "bootstrap5",
    # Controls whether to use minified JS/CSS; defaults to opposite of DEBUG
    "DEFAULT_USE_MINIFIED": True,
}
```

If you choose a bootstrap-based theme, `django_tomselect` will automatically apply framework-specific classes to your dropdowns and items, creating a consistent look and feel with the rest of your UI.

### Custom CSS Classes

You can further refine the appearance by adding custom CSS classes to the widget’s HTML attributes. For example, you can add your own `form-control` classes, spacing utilities, or brand-specific color classes:

```python
from django import forms
from django_tomselect.forms import TomSelectModelChoiceField
from django_tomselect import TomSelectConfig

class CustomStyledForm(forms.Form):
    category = TomSelectModelChoiceField(
        config=TomSelectConfig(
            url="autocomplete-category",
            attrs={
                "class": "form-control custom-select mb-3",
                "placeholder": "Select a category",
            }
        )
    )
```

This approach lets you leverage both the chosen framework’s utility classes and your custom styles.

## Custom Templates

The rendering of items, dropdowns, and other UI elements is handled through templates located in `django_tomselect/templates/django_tomselect/render/`. By overriding these templates in your own project’s template directory, you can gain complete control over the output.

### Visualizing Template Structure

```{mermaid}

    flowchart TD
        subgraph Template Structure
            A[tomselect.html] -->|includes| B[render/select.html]
            A -->|contains| C[Initialization Script]

            C -->|uses| D[Plugin Templates]

            subgraph Plugin Templates
                E[clear_button.html]
                F[dropdown_header.html]
                G[dropdown_footer.html]
                H[item.html]
                I[loading.html]
                J[no_results.html]
                K[option.html]
                L[option_create.html]
            end

            subgraph Context
                M[Widget Context]
                N[Plugin Context]
                O[URL Context]
                P[Permission Context]
            end

            A -->|renders with| Context
        end

        style A fill:#f9f,stroke:#333
        style B fill:#bbf,stroke:#333
        style C fill:#fbf,stroke:#333
        style D fill:#ddf,stroke:#333
```

### Adjusting Template Blocks

`django_tomselect` uses template blocks to let you override pieces of the rendering logic. For instance, you could override `option.html` or `item.html` to change how options and selected items appear in the dropdown.

If you want to display additional data, format labels differently, or integrate icons, you can do so by editing these templates. Just ensure that your overridden templates are placed in `templates/django_tomselect/render/` so that Django’s template loading mechanism finds and uses them.

### Example: Customizing Item Display

Suppose you want to display extra metadata like the number of related articles next to an author’s name. You could override `option.html` to display a more detailed layout:

```html
{# templates/django_tomselect/render/option.html #}
option: function(data, escape) {
    return `<div role="option">
              <strong>${escape(data.name)}</strong><br>
              <small>${escape(data.article_count)} articles</small>
            </div>`;
},
```

By integrating logic directly into the template, you can dynamically show additional attributes returned by your autocomplete view’s `prepare_results()` method.

### Custom Selected Item Display

You can also tailor how selected items appear in the input field by overriding `item.html`. For example, adding an update button next to the selected item:

```html
{# templates/django_tomselect/render/item.html #}
item: function(data, escape) {
    let item = `<div>${escape(data.name)}`;
    if (data.update_url) {
        item += `<a href="${escape(data.update_url)}" class="ms-1" title="Update" target="_blank">
                    <i class="bi bi-pencil-square text-success"></i>
                 </a>`;
    }
    item += `</div>`;
    return item;
},
```

## Plugin Configuration

`django_tomselect` supports various plugins-such as clear buttons, dropdown headers/footers, remove buttons, and more-that enhance the functionality and appearance of your dropdowns. You can configure these plugins through `TomSelectConfig`:

```python
from django import forms
from django_tomselect.forms import TomSelectModelMultipleChoiceField
from django_tomselect import (
    TomSelectConfig,
    PluginDropdownHeader,
    PluginDropdownFooter,
    PluginClearButton,
    PluginRemoveButton,
)

class CustomPluginForm(forms.Form):
    authors = TomSelectModelMultipleChoiceField(
        config=TomSelectConfig(
            url="autocomplete-author",
            value_field="id",
            label_field="name",
            plugin_dropdown_header=PluginDropdownHeader(
                title="Author Selection",
                header_class="bg-primary text-white p-2"
            ),
            plugin_dropdown_footer=PluginDropdownFooter(
                title="Browse All Authors",
                footer_class="border-top mt-2 px-2"
            ),
            plugin_clear_button=PluginClearButton(
                title="Clear Selection",
                class_name="clear-button btn-sm"
            ),
            plugin_remove_button=PluginRemoveButton(
                title="Remove this author",
                class_name="remove-item"
            )
        )
    )
```

By adjusting the plugin settings, you can control label text, classes, and additional columns displayed in tabular layouts.

## Dropdown Customization

The dropdown can be rendered in a tabular format, show multiple columns, or present custom states while loading or fetching more data.

### Tabular Layout

If you have additional metadata for each option (e.g., year, pages, publication number), you can create a tabular layout by enabling `plugin_dropdown_header` with extra columns:

```python
from django_tomselect import TomSelectConfig, PluginDropdownHeader

config = TomSelectConfig(
    url="autocomplete-edition",
    value_field="id",
    label_field="name",
    plugin_dropdown_header=PluginDropdownHeader(
        label_field_label="Edition",
        extra_columns={
            "year": "Year",
            "pages": "Pages",
            "pub_num": "Publication Number",
        }
    )
)
```

In the template, `option.html` and `dropdown_header.html` work together to display data in columns, giving your users a more structured view of their choices.

### Custom Rendering Functions

By returning extra data in `prepare_results()` from your `AutocompleteModelView`, you can reference those fields in your templates. Add logic to `prepare_results()` to annotate querysets or perform computations, and then display those computed fields directly in the rendered templates.

```python
def prepare_results(self, results):
    data = []
    for author in results:
        data.append({
            "id": author["id"],
            "name": author["name"],
            "article_count": author["article_count"],
            "formatted_name": f"{author['name']} ({author['article_count']} articles)",
        })
    return data
```

Then reference `formatted_name` in your `option.html` template to display a customized label.

### Loading States

Enhance the user experience by customizing loading states. Override the `loading.html` and `loading_more.html` templates to provide spinners, animated indicators, or descriptive messages.

```html
{# templates/django_tomselect/render/loading.html #}
loading: function(data, escape) {
    return `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
},
```

This ensures users have visual feedback when the widget is fetching new data.
