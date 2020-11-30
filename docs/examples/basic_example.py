import argparse
import logging

import nengo
import numpy as np

from nengo_fpga import Simulator
from nengo_fpga.networks import FpgaPesEnsembleNetwork

# This script demonstrates how to build a basic communication channel
# using an adaptive neural ensemble implemented on the FPGA. The adaptive
# neural ensemble is built remotely (on the FPGA) via a command sent over SSH
# (as part of the FpgaPesEnsembleNetwork). This automated step removes the
# need of the user to manually SSH into the FPGA board to start the nengo
# script. Communication between the nengo model on the host (PC) and the remote
# (FPGA board) is handled via udp sockets (automatically configured as part of
# the FpgaPesEnsembleNetwork build process)

# To run this script in nengo_gui:
# > python S-00-communication_channel.py <board>
# where <board> is the name of the device as it appears in `fpga_config`.
# For example:
# > python S-00-communication_channel.py pynq

# Set the nengo logging level to 'info' to display all of the information
# coming back over the ssh connection.
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

parser = argparse.ArgumentParser(
    description="A simple communication channel example showing how to"
    " script with NengoFPGA."
)
parser.add_argument(
    "board", type=str, help="The name of the FPGA device as it appears in fpga_config."
)
parser.add_argument(
    "--time",
    "-t",
    type=float,
    default=2,
    help="The time in seconds over which to run the simulator.",
)

args = parser.parse_args()


def input_func(t):
    return [np.sin(t * 10)]


with nengo.Network() as model:
    # Reference signal
    input_node = nengo.Node(input_func, label="input signal")

    # FPGA neural ensemble
    pes_ens = FpgaPesEnsembleNetwork(
        args.board, n_neurons=100, dimensions=1, learning_rate=0, label="ensemble"
    )

    nengo.Connection(input_node, pes_ens.input)

    # Reference value passthrough node
    ref_node = nengo.Node(size_in=1)
    nengo.Connection(input_node, ref_node)

    # Output probes
    p_fpga = nengo.Probe(pes_ens.output, synapse=0.005)
    p_ref = nengo.Probe(ref_node, synapse=0.005)

with Simulator(model) as sim:
    sim.run(args.time)

# Compute RMSE between reference node and output of FPGA neural ensemble
rmse = np.sqrt(np.mean(sim.data[p_fpga] - sim.data[p_ref]) ** 2)
print("\nComputed RMSE: %0.05f" % rmse)
