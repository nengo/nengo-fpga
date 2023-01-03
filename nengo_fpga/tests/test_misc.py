"""Tests for some misc incidental functions."""
from importlib import reload

import nengo
import pytest

from nengo_fpga.utils import paths


def test_monkey_patch(dummy_net):
    """Check monkey patch from __init__ fails with wrong type."""

    with pytest.raises(nengo.exceptions.NetworkContextError):
        with dummy_net:
            _ = nengo.Node()


def test_windows_path(mocker):
    """We test on Linux, so pretend we are on Windows."""

    mocker.patch("sys.platform", "windows")
    reload(paths)

    assert paths.config_dir.endswith(".nengo")
