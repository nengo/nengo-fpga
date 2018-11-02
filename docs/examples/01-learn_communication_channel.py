import numpy as np

import nengo
from nengo_fpga.networks import FpgaPesEnsembleNetwork

# This script demonstrates how to build a basic learned communication channel
# using an adaptive neural ensemble implemented on the FPGA. The adaptive
# neural ensemble is built remotely (on the FPGA) via a command sent over SSH
# (as part of the FpgaPesEnsembleNetwork). This automated step removes the
# need of the user to manually SSH into the FPGA board to start the nengo
# script. Communication between the nengo model on the host (PC) and the remote
# (FPGA board) is handled via udp sockets (automatically configured as part of
# the FpgaPesEnsembleNetwork build process)

# To run this script in nengo_gui:
# > nengo -b nengo_board 01-learn_communication_channel.py

# Set the nengo logging level to 'info' to display all of the information
# coming back over the ssh connection.
nengo.utils.logging.log('info')


def input_func(t):
    return np.sin(t * 10)

# ---------------- BOARD SELECT ----------------------- #
# Uncomment whichever board you are using
board = 'de1'
# board = 'pynq'
# ---------------- BOARD SELECT ----------------------- #

with nengo.Network() as model:
    # Reference signal
    input_node = nengo.Node(input_func, label='input signal')

    # Adaptive neural ensemble (run on the FPGA) -- contains the pre and post
    # ensembles.
    pes_ens = FpgaPesEnsembleNetwork(
        board, n_neurons=100, dimensions=1, learning_rate=5e-5,
        function=lambda x: [0], label='pes ensemble')
    nengo.Connection(input_node, pes_ens.input)

    # Error signal computation
    error = nengo.Ensemble(50, 1)

    # Compute the error (error = actual - target = post - pre)
    # In this case we are learning the square of the input
    nengo.Connection(input_node, error, function=lambda x: x**2, transform=-1)
    nengo.Connection(pes_ens.output, error)

    # Project the error to the adaptive neural ensemble
    nengo.Connection(error, pes_ens.error)
