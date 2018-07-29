from setuptools import find_packages, setup

setup(
    name='nengo_fpga',
    packages=find_packages(),
    version='0.0.1',
    author='Applied Brain Research',
    description='Nengo FPGA Interface',
    author_email='xuan.choo@appliedbrainresearch.com',
    install_requires=["nengo>=2.8.0", "numpy>=1.13.0", "paramiko>=2.4.1"],
)
