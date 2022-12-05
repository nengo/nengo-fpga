"""Tests for fpga_config parser."""
import os

from nengo_fpga import fpga_config
from nengo_fpga.fpga_config import _FPGA_CONFIG, fpga_config_files
from nengo_fpga.utils import paths


def test_load_hierarchy(mocker, gen_configs):
    """Ensure we load configs from the correct locations."""

    # Set project dir to differentiate from system dir (root package dir)
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    mocker.patch.dict(
        paths.fpga_config, {"project": os.path.join(tmp_dir, "fpga_config")}
    )

    # Create a list to use in the test with this tmp project dir
    my_config_files = [
        paths.fpga_config["nengo"],
        paths.fpga_config["system"],
        paths.fpga_config["user"],
        paths.fpga_config["project"],
    ]

    # Create some dummy configs
    sec = "config"
    entry = "file"
    for k, v in paths.fpga_config.items():
        gen_configs.create_config(v, contents={sec: {entry: k}})

    # Explicitly define keys in reverse hierarchical order
    keys = ["project", "user", "system", "nengo"]

    # Load configs, then remove the highest priority file and reload
    for k in keys:
        fpga_config.reload_config(my_config_files)
        assert fpga_config.item_dict(sec)[entry] == k
        os.remove(paths.fpga_config[k])


def test_reload_config(mocker):
    """Check the reload_config behaviour."""

    # Don't actually do anything with configs
    clear_mock = mocker.patch.object(_FPGA_CONFIG, "_clear")
    read_mock = mocker.patch.object(_FPGA_CONFIG, "read")

    dummy_call = "fake_files"
    dummy_config = _FPGA_CONFIG()
    dummy_config.reload_config(dummy_call)

    read_mock.assert_has_calls(
        [mocker.call(fpga_config_files), mocker.call(dummy_call)]
    )
    assert clear_mock.call_count == 2


def test_clear(gen_configs):
    """Test the clear function of the config parser."""

    # Create a dummy config and load it
    fname = os.path.join(os.getcwd(), "test_config")
    gen_configs.create_config(fname)
    fpga_config.reload_config(fname)

    # Confirm we loaded our dummy config
    assert len(fpga_config.sections()) == len(gen_configs.default_contents)

    # Clear and confirm
    fpga_config._clear()
    assert len(fpga_config.sections()) == 0


def test_read(gen_configs):
    """Test the read function of the config parser."""

    # Create a dummy config
    fname = os.path.join(os.getcwd(), "test_config")
    gen_configs.create_config(fname)

    # Grab current number of sections
    entries = len(fpga_config.sections())

    # Read config and check we added a section (default one section)
    fpga_config.read(fname)
    assert len(fpga_config.sections()) == entries + len(gen_configs.default_contents)


def test_item_dict(gen_configs):
    """Test the item dict function of the config parser."""

    # Create a dummy config and load it
    fname = os.path.join(os.getcwd(), "test_config")
    gen_configs.create_config(fname)
    fpga_config.reload_config(fname)

    section = list(gen_configs.default_contents.keys())[0]
    config_dict = fpga_config.item_dict(section)

    assert config_dict == gen_configs.default_contents[section]
