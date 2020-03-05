# -*- coding: utf-8 -*-
#
# Automatically generated by nengo-bones, do not edit this file directly

import os

import nengo_fpga

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "nbsphinx",
    "nengo_sphinx_theme",
    "nengo_sphinx_theme.ext.redirects",
    "numpydoc",
]

# -- sphinx.ext.autodoc
autoclass_content = "both"  # class and __init__ docstrings are concatenated
autodoc_default_options = {"members": None}
autodoc_member_order = "bysource"  # default is alphabetical

# -- sphinx.ext.doctest
doctest_global_setup = """
import nengo_fpga
"""

# -- sphinx.ext.intersphinx
intersphinx_mapping = {
    "nengo": ("https://www.nengo.ai/nengo/", None),
    "numpy": ("https://docs.scipy.org/doc/numpy", None),
    "python": ("https://docs.python.org/3", None),
    "nengo-de1": ("https://www.nengo.ai/nengo-de1/", None),
    "nengo-pynq": ("https://www.nengo.ai/nengo-pynq/", None),
}

# -- sphinx.ext.todo
todo_include_todos = True

# -- numpydoc config
numpydoc_show_class_members = False

# -- nbsphinx
nbsphinx_timeout = -1

# -- sphinx
nitpicky = True
exclude_patterns = [
    "_build",
    "**/.ipynb_checkpoints",
]
linkcheck_timeout = 30
source_suffix = ".rst"
source_encoding = "utf-8"
master_doc = "index"
linkcheck_ignore = [r"http://localhost:\d+"]
linkcheck_anchors = True
default_role = "py:obj"
pygments_style = "sphinx"

project = "NengoFPGA"
authors = "Applied Brain Research"
copyright = "2018-2020 Applied Brain Research"
version = ".".join(nengo_fpga.__version__.split(".")[:2])  # Short X.Y version
release = nengo_fpga.__version__  # Full version, with tags

# -- HTML output
templates_path = ["_templates"]
html_static_path = ["_static"]
html_theme = "nengo_sphinx_theme"
html_title = "NengoFPGA {0} docs".format(release)
htmlhelp_basename = "NengoFPGA"
html_last_updated_fmt = ""  # Default output format (suppressed)
html_show_sphinx = False
html_favicon = os.path.join("_static", "favicon.ico")
html_theme_options = {
    "nengo_logo": "nengo-fpga-full-light.svg",
    "nengo_logo_color": "#541a8b",
}
html_redirects = [
    ("getting_started.html", "getting-started.html"),
    (
        "examples/notebooks/00-communication_channel.html",
        "examples/notebooks/00-communication-channel.html",
    ),
    (
        "examples/notebooks/01-learn_communication_channel.html",
        "examples/notebooks/01-learn-communication-channel.html",
    ),
    (
        "examples/notebooks/02-set_neuron_params.html",
        "examples/notebooks/02-set-neuron-params.html",
    ),
    (
        "examples/notebooks/05-controlled_oscillator.html",
        "examples/notebooks/05-controlled-oscillator.html",
    ),
    (
        "examples/notebooks/06-chaotic_attractor.html",
        "examples/notebooks/06-chaotic-attractor.html",
    ),
]
