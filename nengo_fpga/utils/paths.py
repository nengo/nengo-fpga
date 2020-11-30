"""Provides standard paths to configs and resources"""

import os
import sys

import nengo

if sys.platform.startswith("win"):
    config_dir = os.path.expanduser(os.path.join("~", ".nengo"))
else:
    config_dir = os.path.expanduser(os.path.join("~", ".config", "nengo"))

install_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
nengo_dir = os.path.abspath(os.path.join(os.path.dirname(nengo.__file__), os.pardir))
examples_dir = os.path.join(install_dir, "examples")

fpga_config = {
    "nengo": os.path.join(nengo_dir, "nengo-data", "fpga_config"),
    "system": os.path.join(install_dir, "fpga_config"),
    "user": os.path.join(config_dir, "fpga_config"),
    "project": os.path.abspath(os.path.join(os.curdir, "fpga_config")),
}
