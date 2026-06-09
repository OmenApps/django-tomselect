# Usage Guide

`django_tomselect` provides form fields and widgets to integrate [Tom Select](https://tom-select.js.org/) into your Django projects, enabling dynamic and customizable `<select>` elements with advanced features like autocomplete, tagging, and search.

Most of the code samples throughout this guide are based on the example app provided with the package. You can find the complete example app in the `example_project/example/` directory of the repository.

This guide is split into the following sections:

- **[Installation](usage/installation.md)** - install the package and wire up the middleware, context processor, and static assets.
- **[Quick Start](usage/quickstart.md)** - a complete end-to-end example, from form to view to URLs to template.
- **[Core Components](usage/core_components.md)** - the autocompletes, form fields, and widgets that make up the package.
- **[Configuration](usage/configuration.md)** - the `TomSelectConfig` object, plugins, and global vs. field-level settings.
- **[Working with Models](usage/working_with_models.md)** - autocomplete views, queryset filtering, related fields, and search.
- **[Working with Forms](usage/working_with_forms.md)** - integrating fields into forms and ModelForms, initial values, and validation.
- **[Advanced Features](usage/advanced_features.md)** - dependent/chained fields, exclusions, pagination, and custom search.
- **[Customization](usage/customization.md)** - styling, custom templates, plugin configuration, and dropdown layouts.
- **[Security Considerations](usage/security.md)** - permissions, authorization hooks, caching, and CSP nonce support.

```{toctree}
:hidden:
:maxdepth: 2

usage/installation
usage/quickstart
usage/core_components
usage/configuration
usage/working_with_models
usage/working_with_forms
usage/advanced_features
usage/customization
usage/security
```
