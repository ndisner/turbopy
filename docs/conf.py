# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import sphinx_rtd_theme
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'turboPy'
# copyright = '2020, Steve Richardson'
html_show_copyright = False
author = 'Steve Richardson'

# The full version, including alpha/beta/rc tags — pulled from the package
# metadata so it stays in sync with `turbopy.__version__`.
try:
    from turbopy import __version__ as _turbopy_version
    release = _turbopy_version
except Exception:  # pragma: no cover - fallback if import fails at build time
    release = ''


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]
# Might want to add 'numpydoc', but readthedocs doesn't like it

# autodoc defaults so inherited members and __init__ show up on every class.
autodoc_default_options = {
    'members': True,
    'inherited-members': True,
    'show-inheritance': True,
    'special-members': '__init__',
}

# Generate stub pages for autosummary directives automatically.
autosummary_generate = True

master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Options for the napoleon preprocessor
napoleon_google_docstring = False
napoleon_numpy_docstring = True

# Options for intersphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"

# Paths containing custom static files (images, style sheets). Copied after
# the theme's own static files.
html_static_path = ['_static']

# Sidebar logo. This is a Sphinx-level setting (not a theme option), so it
# works regardless of theme; sphinx_rtd_theme places it above the nav.
html_logo = '_static/turbopy_cpfw.png'

# Only options actually recognized by sphinx_rtd_theme belong here — putting
# alabaster keys (github_user, github_banner, etc.) here would emit
# "unsupported theme option" warnings on every build.
html_theme_options = {
    'logo_only': True,
    'collapse_navigation': False,
    'navigation_depth': 3,
}

# Enables the sphinx_rtd_theme "Edit on GitHub" link at the top of every
# page. The keys below are the ones the theme's layout template reads;
# putting them here (rather than in html_theme_options) is the RTD-idiomatic
# pattern and does not emit "unsupported theme option" warnings.
html_context = {
    'display_github': True,
    'github_user': 'NRL-Plasma-Physics-Division',
    'github_repo': 'turbopy',
    'github_version': 'main',
    'conf_py_path': '/docs/',
}
