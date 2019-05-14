import imp
import os

try:
    from setuptools import find_packages, setup
except ImportError:
    raise ImportError(
        "'setuptools' is required but not installed. To install it, "
        "follow the instructions at "
        "https://pip.pypa.io/en/stable/installing/#installing-with-get-pip-py")

root = os.path.dirname(os.path.realpath(__file__))
version_module = imp.load_source(
    "version", os.path.join(root, "nengo_fpga", "version.py"))

setup(
    name='nengo_fpga',
    packages=find_packages(),
    version=version_module.version,
    author='Applied Brain Research',
    description='NengoFPGA Interface',
    author_email='info@appliedbrainresearch.com',
    install_requires=["nengo>=2.8.0", "numpy>=1.13.0", "paramiko>=2.4.1"],
)
