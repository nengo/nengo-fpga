# pylint: disable=W0611
"""Setup pytest environment to include fixtures."""
import pytest

from nengo_fpga.tests.fixtures import (
    config_contents,
    dummy_com,
    dummy_extractor,
    dummy_net,
    dummy_sim,
    gen_configs,
    params,
)


def pytest_addoption(parser):
    """Add fullstack runtime arg."""
    parser.addoption(
        "--fullstack",
        action="store_true",
        default=False,
        help="Also run the fullstack tests",
    )


def pytest_collection_modifyitems(config, items):
    """Do not run the fullstack tests by default."""
    if not config.getvalue("fullstack"):
        skip_fullstack = pytest.mark.skip("Fullstack tests skipped by default")
        for item in items:
            if item.get_closest_marker("fullstack"):
                item.add_marker(skip_fullstack)
