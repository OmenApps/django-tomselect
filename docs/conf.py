"""Sphinx configuration for django-tomselect documentation."""

import inspect
import os
import sys
from datetime import datetime

import django
from django.utils.html import strip_tags

sys.path.insert(0, os.path.abspath(".."))
os.environ["DJANGO_SETTINGS_MODULE"] = "example_project.settings"
django.setup()


# Project information
project = "django-tomselect"
author = "Jack Linke"
copyright = f"{datetime.now().year}, {author}"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_click",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_togglebutton",
    "sphinxcontrib.mermaid",
]

# Any paths that contain templates here, relative to this directory.
# templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "special-members": "__init__",
    "exclude-members": "__weakref__",
}
autodoc_mock_imports = [
    "django",
]  # Add any modules that might cause import errors during doc building

# Intersphinx settings
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
}

# MyST Parser settings
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]


def project_django_models(app, what, name, obj, options, lines):  # pylint: disable=W0613 disable=R0913
    """Process Django models for autodoc.

    From: https://djangosnippets.org/snippets/2533/
    """
    from django.db import models  # pylint: disable=C0415

    # Only look at objects that inherit from Django's base model class
    if inspect.isclass(obj) and issubclass(obj, models.Model):
        # Grab the field list from the meta class
        fields = obj._meta.get_fields()  # pylint: disable=W0212

        for field in fields:
            # If it's a reverse relation, skip it
            if isinstance(
                field,
                (
                    models.fields.related.ManyToOneRel,
                    models.fields.related.ManyToManyRel,
                    models.fields.related.OneToOneRel,
                ),
            ):
                continue

            # Decode and strip any html out of the field's help text
            help_text = strip_tags(field.help_text) if hasattr(field, "help_text") else None

            # Decode and capitalize the verbose name, for use if there isn't
            # any help text
            verbose_name = field.verbose_name if hasattr(field, "verbose_name") else ""

            if help_text:
                # Add the model field to the end of the docstring as a param
                # using the help text as the description
                lines.append(f":param {field.attname}: {help_text}")
            else:
                # Add the model field to the end of the docstring as a param
                # using the verbose name as the description
                lines.append(f":param {field.attname}: {verbose_name}")

            # Add the field's type to the docstring
            lines.append(f":type {field.attname}: {field.__class__.__name__}")

    # Return the extended docstring
    return lines


def setup(app):
    """Register the Django model processor with Sphinx."""
    app.connect("autodoc-process-docstring", project_django_models)
