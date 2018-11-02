import numpy as np

import nengo
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
# > nengo -b nengo_board 00-communication_channel.py

# Set the nengo logging level to 'info' to display all of the information
# coming back over the ssh connection.
nengo.utils.logging.log('info')


def input_func(t):
    return [np.sin(t * 10), np.cos(t * 10)]

# ---------------- BOARD SELECT ----------------------- #
# Uncomment whichever board you are using
board = 'de1'
# board = 'pynq'
# ---------------- BOARD SELECT ----------------------- #

with nengo.Network() as model:
    # Reference signal
    input_node = nengo.Node(input_func, label='input signal')

    # FPGA neural ensemble
    pes_ens = FpgaPesEnsembleNetwork(
        board, n_neurons=50, dimensions=2, learning_rate=0, label='ensemble')

    nengo.Connection(input_node, pes_ens.input)
