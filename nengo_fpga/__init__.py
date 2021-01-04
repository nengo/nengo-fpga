"""
NengoFPGA
=========

NengoFPGA provides an FPGA backend for Nengo (https://www.github.com/nengo/nengo).

The source code repository for this package is found at
https://www.github.com/nengo/nengo-fpga. Examples of models can be found
in the `examples` directory of the source code repository.
"""

import nengo

from . import id_extractor, utils
from .fpga_config import fpga_config
from .simulator import Simulator
from .version import version as __version__

__copyright__ = "2013-2021, Applied Brain Research"
__license__ = "Free for non-commercial use; see LICENSE.rst"


# Only patch if we haven't patched already
if nengo.Network.add.__module__ == "nengo.network":
    net_add = nengo.Network.add

    def add(obj):
        """
        monkey-patch Network.add so that we can give a better error message
        if someone tries to add new objects.

        TODO: it'd be nice to do this without the monkey-patching, but we'll
        probably have to modify nengo
        """
        try:
            net_add(obj)
        except AttributeError as e:
            net_type = type(nengo.Network.context[-1])
            raise nengo.exceptions.NetworkContextError(
                "Cannot add new objects to a %s" % net_type
            ) from e

    nengo.Network.add = staticmethod(add)
