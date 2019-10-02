#!/usr/bin/env python

# Automatically generated by nengo-bones, do not edit this file directly

import io
import os
import runpy

try:
    from setuptools import find_packages, setup
except ImportError:
    raise ImportError(
        "'setuptools' is required but not installed. To install it, "
        "follow the instructions at "
        "https://pip.pypa.io/en/stable/installing/#installing-with-get-pip-py"
    )


def read(*filenames, **kwargs):
    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("sep", "\n")
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


root = os.path.dirname(os.path.realpath(__file__))
version = runpy.run_path(os.path.join(root, "nengo_fpga", "version.py"))["version"]

install_req = ["nengo>=2.8.0", "numpy>=1.13.0,<1.17", "paramiko>=2.4.1"]
docs_req = [
    "sphinx>=1.8",
    "jupyter",
    "matplotlib>=1.4",
    "nbsphinx",
    "numpydoc>=0.6",
    "nengo_sphinx_theme>=0.12.0",
]
optional_req = []
tests_req = []

setup(
    name="nengo-fpga",
    version=version,
    author="Applied Brain Research",
    author_email="info@appliedbrainresearch.com",
    packages=find_packages(),
    url="https://www.nengo.ai/nengo-fpga",
    include_package_data=False,
    license="Free for non-commercial use",
    description="FPGA backend for Nengo",
    long_description=read("README.rst", "CHANGES.rst"),
    zip_safe=False,
    install_requires=install_req,
    extras_require={
        "all": docs_req + optional_req + tests_req,
        "docs": docs_req,
        "optional": optional_req,
        "tests": tests_req,
    },
    python_requires=">=3.5",
    package_data={"nengo_fpga": ["fpga_config"]},
    entry_points={"nengo.backends": ["fpga = nengo_fpga:Simulator"]},
)
