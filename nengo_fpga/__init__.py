from . import utils
from .simulator import Simulator
from .fpga_config import fpga_config
from . import id_extractor

# monkey-patch Network.add so that we can give a better error message
# if someone tries to add new objects.
# TODO: it'd be nice to do this without the monkey-patching, but we'll
# probably have to modify nengo
import nengo

from .version import version as __version__
__copyright__ = "2013-2017, Applied Brain Research"
__license__ = "Free for non-commercial use; see LICENSE.rst"

# Only patch if we haven't patched already
if nengo.Network.add.__module__ == "nengo.network":
    net_add = nengo.Network.add

    def add(obj):
        try:
            net_add(obj)
        except AttributeError:
            net_type = type(nengo.Network.context[-1])
            raise nengo.exceptions.NetworkContextError(
                "Cannot add new objects to a %s" % net_type)

    nengo.Network.add = staticmethod(add)
