# -*- coding: utf-8 -*-
#
# This file is execfile()d with the current directory set
# to its containing dir.

import os

import nengo_fpga


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
    'sphinx.ext.mathjax',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'numpydoc',
    "nbsphinx",
    "nengo_sphinx_theme",
]

default_role = 'py:obj'
numfig = True

# -- sphinx.ext.autodoc
autoclass_content = 'both'  # class and __init__ docstrings are concatenated
autodoc_default_options = {'members': None}
autodoc_member_order = 'bysource'  # default is alphabetical

# -- sphinx.ext.intersphinx
intersphinx_mapping = {
    'nengo': ('https://www.nengo.ai/nengo/', None),
    'numpy': ('https://docs.scipy.org/doc/numpy', None),
}

# -- sphinx.ext.todo
todo_include_todos = False

# -- numpydoc config
numpydoc_show_class_members = False

# -- nbsphinx
nbsphinx_allow_errors = False
nbsphinx_timeout = 300
nbsphinx_execute = 'always'
nbsphinx_timeout = -1

# -- sphinx
nitpicky = True
exclude_patterns = ['_build', '**/.ipynb_checkpoints']
source_suffix = '.rst'
source_encoding = 'utf-8'
master_doc = 'index'
linkcheck_timeout = 30
linkcheck_ignore = [r"http://localhost:\d+"]
linkcheck_anchors = True

# Need to include https Mathjax path for sphinx < v1.3
mathjax_path = ("https://cdn.mathjax.org/mathjax/latest/MathJax.js"
                "?config=TeX-AMS-MML_HTMLorMML")

project = u'NengoFPGA'
authors = u'Applied Brain Research'
copyright = "2013-2019 Applied Brain Research"
version = '.'.join(nengo_fpga.__version__.split('.')[:2])  # Short X.Y version
release = nengo_fpga.__version__  # Full version, with tags
pygments_style = "sphinx"

# -- Options for HTML output --------------------------------------------------

html_theme = 'nengo_sphinx_theme'
html_title = "NengoFPGA {0} docs".format(release)
html_static_path = ['_static']
html_favicon = os.path.join('_static', 'favicon.ico')
html_use_smartypants = True
htmlhelp_basename = 'NengoFPGA'
html_last_updated_fmt = ''  # Suppress 'Last updated on:' timestamp
html_show_sphinx = False
html_theme_options = {
    "sidebar_toc_depth": 4,
    "sidebar_logo_width": 200,
    "nengo_logo": "nengo-fpga-full-light.svg",
}

# -- Options for LaTeX output -------------------------------------------------

latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '11pt',
}

latex_documents = [
    # (source start file, target, title, author, documentclass [howto/manual])
    ('index', 'nengo.tex', html_title, authors, 'manual'),
]

# -- Options for manual page output -------------------------------------------

man_pages = [
    # (source start file, name, description, authors, manual section).
    ('index', 'nengo', html_title, [authors], 1)
]

# -- Options for Texinfo output -----------------------------------------------

texinfo_documents = [
    # (source start file, target, title, author, dir menu entry,
    #  description, category)
    ('index', 'nengo', html_title, authors, 'Nengo',
     'Large-scale neural simulation in Python', 'Miscellaneous'),
]
