"""
FPGA network containing:

- One ensemble
- PES learning
- Feedback connection
"""

import logging
import os
import socket
import subprocess
import sys
import threading
import time
from functools import partial

import nengo
import numpy as np
from nengo.builder.operator import Copy, Reset, SimPyFunc
from nengo.builder.signal import Signal
from nengo_fpga.fpga_config import fpga_config
from nengo_fpga.utils.fileio import write_array

logger = logging.getLogger(__name__)


class FpgaPesEnsembleNetwork(nengo.Network):
    """
    An ensemble to be run on the FPGA.

    Parameters
    ----------
    fpga_name : str
        The name of the fpga defined in the config file.
    n_neurons : int
        The number of neurons.
    dimensions : int
        The number of representational dimensions.
    learning_rate : float
        A scalar indicating the rate at which weights will be adjusted.
    function : callable or (n_eval_points, size_mid) array_like, \
               optional (Default: None)
        Function to compute across the connection. Note that ``pre`` must be
        an ensemble to apply a function across the connection.
        If an array is passed, the function is implicitly defined by the
        points in the array and the provided ``eval_points``, which have a
        one-to-one correspondence.
    transform : (size_out, size_mid) array_like, optional \
                (Default: ``np.array(1.0)``)
        Linear transform mapping the pre output to the post input.
        This transform is in terms of the sliced size; if either pre
        or post is a slice, the transform must be shaped according to
        the sliced dimensionality. Additionally, the function is applied
        before the transform, so if a function is computed across the
        connection, the transform must be of shape ``(size_out, size_mid)``.
    eval_points : (n_eval_points, size_in) array_like or int, optional \
                  (Default: None)
        Points at which to evaluate ``function`` when computing decoders,
        spanning the interval (-pre.radius, pre.radius) in each dimension.
        If None, will use the eval_points associated with ``pre``.
    socket_args : dictionary, optional (Default: Empty dictionary)
        Parameters to pass on to the ``socket`` object that is used to handle UDP
        communication between the host PC and the FPGA board. Acceptable parameters
        are:
        ``connect_timeout``: Determines the maximum timeout to wait for a connection
        from the FPGA board. Default: 300s
        ``recv_timeout``: Determines the maximum timeout for each packet received
        from the FPGA board. Default: 0.1s
    feedback : float or (D_out, D_in) array_like, optional
        Defines the transform for a recurrent connection. If ``None``, no
        recurrent connection will be built. The default synapse used for the
        recurrent connection is ``nengo.Lowpass(0.1)``, this can be changed
        using the ``feedback`` attribute of this class.
    label : str, optional (Default: None)
        A descriptive label for the connection.
    seed : int, optional (Default: None)
        The seed used for random number generation.
    add_to_container : bool, optional (Default: None)
        Determines if this network will be added to the current container. If
        ``None``, this network will be added to the network at the top of the
        ``Network.context`` stack unless the stack is empty.

    Attributes
    ----------
    input : `nengo.Node`
        A node that serves as the input interface between external Nengo
        objects and the FPGA board.
    output : `nengo.Node`
        A node that serves as the output interface between the FPGA board and
        external Nengo objects.
    error : `nengo.Node`
        A node that provides the error signal to be used by the learning rule
        on the FPGA board.
    ensemble : `nengo.Ensemble`
        An ensemble object whose parameters are used to configure the
        ensemble implementation on the FPGA board.
    connection : `nengo.Connection`
        The connection object used to configure the learning connection
        implementation on the FPGA board.
    feedback : `nengo.Connection`
        The connection object used to configure the recurrent connection
        implementation on the FPGA board.
    """

    def __init__(
        self,
        fpga_name,
        n_neurons,
        dimensions,
        learning_rate,
        function=nengo.Default,
        transform=nengo.Default,
        eval_points=nengo.Default,
        socket_args=None,
        feedback=None,
        label=None,
        seed=None,
        add_to_container=None,
    ):
        # Flags for determining whether or not the FPGA board is being used
        self.config_found = fpga_config.has_section(fpga_name)
        self.fpga_found = True  # TODO: Ping board to determine?
        self.using_fpga_sim = False

        # Save ssh details
        self.fpga_name = fpga_name
        self.arg_data_file = ""

        # Process dimensions, function, transform arguments
        self.input_dimensions = dimensions

        self.get_output_dim(function, dimensions)

        # Process feedback connection
        if nengo.utils.numpy.is_array_like(feedback):
            self.rec_transform = feedback
        elif feedback is not None:
            raise nengo.exceptions.ValidationError(
                "Must be scalar or array-like", "feedback", self
            )

        # Neuron type string map
        self.neuron_str_map = {
            nengo.neurons.RectifiedLinear: "RectifiedLinear",
            nengo.neurons.SpikingRectifiedLinear: "SpikingRectifiedLinear",
        }
        self.default_neuron_type = nengo.neurons.RectifiedLinear()

        # Store the various parameters needed to initialize the remote network
        self.seed = seed
        self.learning_rate = learning_rate

        # Call the superconstructor
        super().__init__(label, seed, add_to_container)

        # Socket attributes
        self.udp_socket = None
        self.send_buffer = None
        self.recv_buffer = None

        if socket_args is None:
            socket_args = {}
        self.connect_timeout = socket_args.get("connect_timeout", 30)
        self.recv_timeout = socket_args.get("recv_timeout", 0.1)

        # Check if the desired FPGA name is defined in the configuration file
        if self.config_found:
            # Handle the udp port selection: Use the config specified port.
            # If none is provided (i.e., the specified port number is 0),
            # choose a random udp port number between 20000 and 65535.
            self.udp_port = int(fpga_config.get(fpga_name, "udp_port"))
            if self.udp_port == 0:
                self.udp_port = int(np.random.uniform(low=20000, high=65530))

            self.send_addr = (fpga_config.get(fpga_name, "ip"), self.udp_port)
        else:
            # FPGA name not found, throw a warning.
            logger.warning("Specified FPGA configuration '%s' not found.", fpga_name)
            print(f"WARNING: Specified FPGA configuration '{fpga_name}' not found.")

        # Make nengo model. Here, a dummy ensemble is created. It will be
        # replaced with a udp_socket in the builder function (see below).
        with self:
            self.input = nengo.Node(size_in=self.input_dimensions, label="input")
            self.error = nengo.Node(size_in=self.output_dimensions, label="error")
            self.output = nengo.Node(size_in=self.output_dimensions, label="output")

            self.ensemble = nengo.Ensemble(
                n_neurons,
                self.input_dimensions,
                neuron_type=nengo.neurons.RectifiedLinear(),
                eval_points=eval_points,
                label="Dummy Ensemble",
            )
            nengo.Connection(self.input, self.ensemble, synapse=None)

            self.connection = nengo.Connection(
                self.ensemble,
                self.output,
                function=function,
                transform=transform,
                eval_points=eval_points,
                learning_rule_type=nengo.PES(learning_rate),
                synapse=None,
            )

            nengo.Connection(self.error, self.connection.learning_rule, synapse=None)

            if feedback is not None:
                self.feedback = nengo.Connection(
                    self.ensemble,
                    self.ensemble,
                    synapse=nengo.Lowpass(0.1),
                    transform=self.rec_transform,
                )
            else:
                self.feedback = None

        # Make the object lists immutable so that no extra objects can be added
        # to this network.
        for k, v in self.objects.items():
            self.objects[k] = tuple(v)

    def get_output_dim(self, function, dimensions):
        """Simplify init function by moving output shape calculation here."""
        if function is nengo.Default:
            self.output_dimensions = dimensions
        elif callable(function):
            self.output_dimensions = len(function(np.zeros(dimensions)))
        elif nengo.utils.numpy.is_array_like(function):
            self.output_dimensions = function.shape[1]
        else:
            raise nengo.exceptions.ValidationError(
                "Must be callable or array-like", "function", self
            )

    @property
    def local_data_filepath(self):
        """
        Full path to ensemble parameter value data file on the local system.

        Ensemble parameter values are generated by the builder.
        """
        return os.path.join(
            fpga_config.get(self.fpga_name, "remote_tmp"), self.arg_data_file
        )

    def terminate_client(self):
        """
        Send termination packet to FPGA board.

        Termination packet is a packet where t is less than 0.
        """
        self.udp_socket.sendto(
            (
                np.ones(self.input_dimensions + self.output_dimensions + 1) * -1
            ).tobytes(),
            self.send_addr,
        )

    def close(self):
        """Shutdown connections to FPGA if applicable."""

        # Function does nothing if FPGA configuration not found in config file
        if not self.config_found:
            return

        # Close the UDP socket if it is open
        if self.udp_socket is not None:
            # Send termination signal to the board
            self.terminate_client()

            # Close the udp socket and set it to None
            logger.info(
                "<%s> UDP Connection closed", fpga_config.get(self.fpga_name, "ip")
            )
            self.udp_socket.close()
            self.udp_socket = None

        # Reset the udp communication buffers
        self.send_buffer = np.zeros(self.input_dimensions + self.output_dimensions + 1)
        self.recv_buffer = np.zeros(self.output_dimensions + 1)

    def cleanup(self):
        """Remove FPGA data file if applicable."""

        # Function does nothing if FPGA configuration not found in config file
        if not self.config_found:
            return

        # Clean up any existing argument data files
        if os.path.isfile(self.local_data_filepath):
            os.remove(self.local_data_filepath)

    def connect(self):  # noqa: C901
        """Connect to FPGA via SSH if applicable."""

        # Function does nothing if FPGA configuration not found in config file
        if not self.config_found:
            return

        logger.info("<%s> Starting FPGA process", fpga_config.get(self.fpga_name, "ip"))
        subprocess.Popen(
            [
                "python",
                fpga_config.get(self.fpga_name, "remote_script"),
                f"--host_ip={fpga_config.get('host', 'ip')}",
                f"--remote_ip={fpga_config.get(self.fpga_name, 'ip')}",
                f"--udp_port={self.udp_port}",
                f"--arg_data_file={fpga_config.get(self.fpga_name, 'remote_tmp')}"
                + f"/{self.arg_data_file}",
            ]
        )

        logger.info("<%s> Open UDP connection", fpga_config.get(self.fpga_name, "ip"))
        # Create a UDP socket to communicate with the board
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind((fpga_config.get("host", "ip"), self.udp_port + 1))

        # # Set the socket timeout to the connection timeout and wait for the
        # # board to connect to the PC.
        # # Note that this is the "correct" way to wait for an incoming connection
        # # request. However, because the error detection mechanism in the SSH
        # # thread is done by closing the UDP socket, a polling approach is used
        # # (see below).
        # # TODO: Re-examine this during the SSH refactoring.
        # self.udp_socket.settimeout(self.connect_timeout)
        # while True:
        #     try:
        #         self.udp_socket.recv_into(self.recv_buffer.data)
        #         # Connection packet has a t of 0
        #         if self.recv_buffer[0] <= 0.0:
        #             break
        #     except socket.timeout:
        #         self.close()
        #     raise RuntimeError("Did not receive connection from board within "
        #                        + "specified timeout (%fs)." % self.connect_timeout)
        # if self.recv_buffer[0] < 0.0:
        #     self.close()
        #     raise RuntimeError("Simulation terminated by FPGA board.")

        # Connection with the board established. Set the socket timeout to
        # recv_timeout.
        self.udp_socket.settimeout(self.recv_timeout)

        # Wait for the connection packet from the board. Note that the
        # implementation above (setting the socket timeout to ``connect_timeout``)
        # is the "proper" implementation. Below is a workaround to allow the SSH
        # connection thread to terminate the connection process (by closing the
        # udp socket, so an exception is thrown).
        max_attempts = int(self.connect_timeout / self.recv_timeout)
        for conn_attempts in range(max_attempts):
            try:
                self.udp_socket.recv_into(self.recv_buffer)
                if self.recv_buffer[0] <= 0.0:
                    # Received a connection packet (t == 0) from the board, or received
                    # a "terminate client" packet (t < 0) from the board, so break out
                    # of the connection waiting loop
                    break
            except socket.timeout:
                pass
            except AttributeError:
                sys.exit(1)
        if conn_attempts >= (max_attempts - 1):
            # Number of connection attempts exceeds maximum number of attempts.
            # I.e., no connection has been received within the timeout limit.
            self.close()
            raise RuntimeError(
                f"Did not receive connection from board within "
                f"specified timeout ({self.connect_timeout}s)."
            )

        if self.recv_buffer[0] < 0.0:
            # Received a "terminate client" packet from the board, terminate the
            # Nengo simulation.
            reason = ""
            if self.recv_buffer[0] <= -20:
                reason = "Unable to load FPGA driver! "
            elif self.recv_buffer[0] <= -10:
                reason = "Unable to acquire FPGA resource lock! "
            self.close()
            raise RuntimeError(reason + "Simulation terminated by FPGA board.")

    def reset(self):
        """Reconnect to FPGA if applicable."""

        # Function does nothing if FPGA configuration not found in config file
        if not self.config_found:
            return

        # Close and reopen ssh connections
        self.close()
        self.connect()


def validate_net(network):
    """
    Helper function to simplify builder function.

    Validates network params:
        - Neuron type
        - Learning connection
        - Feedback connection

    returns [neuron_type (str),
             learning_rate (float),
            ]
    """

    # Check neuron type
    if type(network.ensemble.neuron_type) not in network.neuron_str_map:
        raise nengo.exceptions.BuildError(
            f"Neuron type '{type(network.ensemble.neuron_type)}' is not supported."
        )

    # Check learning
    if network.connection.learning_rule_type is None:
        l_rate = 0
    elif isinstance(network.connection.learning_rule_type, nengo.PES):
        l_rate = network.connection.learning_rule_type.learning_rate
    else:
        raise nengo.exceptions.BuildError(
            f"Learning rule '{type(network.connection.learning_rule_type)}' is not "
            f"supported."
        )

    # Check Feedback (params not set here)
    if network.feedback is not None:
        # Validation
        if network.feedback.learning_rule_type is not None:
            raise nengo.exceptions.BuildError(
                "The FPGA feedback connection does not support learning."
            )

        if not isinstance(network.feedback.synapse, nengo.Lowpass):
            raise nengo.exceptions.BuildError(
                "The FPGA feedback connection only supports the "
                "`nengo.Lowpass` synapse."
            )

    return [network.neuron_str_map[type(network.ensemble.neuron_type)], l_rate]


def extract_and_save_params(model, network):
    """Generate the ensemble and connection parameters and save them to file."""

    # Generate the network used to get the ensemble and output connection parameters
    param_model = nengo.builder.Model(dt=model.dt)
    nengo.builder.network.build_network(param_model, network)

    # Collect the simulation argument values
    sim_args = {}
    sim_args["dt"] = model.dt

    # Collect the ensemble argument values
    ens_args = {}
    ens_args["input_dimensions"] = network.input_dimensions
    ens_args["output_dimensions"] = network.output_dimensions
    ens_args["n_neurons"] = network.ensemble.n_neurons
    ens_args["bias"] = param_model.params[network.ensemble].bias
    ens_args["scaled_encoders"] = param_model.params[network.ensemble].scaled_encoders

    # Collect the connection argument values
    conn_args = {}
    conn_args["weights"] = param_model.params[network.connection].weights

    # Validate neuron_type, learning_rule, and feedback connection
    ens_args["neuron_type"], conn_args["learning_rate"] = validate_net(network)

    # Collect the feedback connection argument values
    recur_args = {}
    recur_args["weights"] = 0  # Necessary as flag even if not used

    if network.feedback is not None:
        # Grab relevant attributes
        recur_args["weights"] = param_model.params[network.feedback].weights
        recur_args["tau"] = network.feedback.synapse.tau

    # Save the NPZ data file
    npz_filename = "fpen_args_" + str(id(network)) + ".npz"
    network.arg_data_file = npz_filename

    # Monkey patch NumPy's write_array function to override pickle protocol from 3 to 2
    numpy_writearray = np.lib.format.write_array
    np.lib.format.write_array = write_array

    np.savez_compressed(
        network.local_data_filepath,
        sim_args=sim_args,
        ens_args=ens_args,
        conn_args=conn_args,
        recur_args=recur_args,
    )

    # Undo monkey patch
    np.lib.format.write_array = numpy_writearray


def udp_comm_func(t, x, net, dt):
    """UDP communication function for nengo SimPyFunc."""

    # Assemble the information to send to the board
    net.send_buffer[0] = t
    net.send_buffer[1:] = x

    # Send information to the board
    net.udp_socket.sendto(net.send_buffer.tobytes(), net.send_addr)

    # Receive information from the board
    try:
        while net.recv_buffer[0] < (t - dt / 2.0):
            net.udp_socket.recv_into(net.recv_buffer.data)
            if net.recv_buffer[0] < 0:
                # Received a "terminate client" packet from the board, terminate the
                # Nengo simulation.
                net.close()
                raise RuntimeError("Simulation terminated by FPGA board.")
    except socket.timeout:
        logger.info("Socket timeout for t=%0.5fs", t)

    # Return the received information
    return net.recv_buffer[1:]


@nengo.builder.Builder.register(FpgaPesEnsembleNetwork)
def build_FpgaPesEnsembleNetwork(model, network):
    """
    Builder to integrate FPGA network into Nengo.

    Add build steps like nengo?
    """

    # Check if nengo_fpga.Simulator is being used to build this network
    if not network.using_fpga_sim:
        warn_str = "FpgaPesEnsembleNetwork not being built with nengo_fpga simulator."
        logger.warning(warn_str)
        print("WARNING: " + warn_str)

    # Check if all of the requirements to use the FPGA board are met
    if not (network.using_fpga_sim and network.config_found and network.fpga_found):
        # FPGA requirements not met...
        # Build the dummy network instead of using FPGA-specific stuff
        warn_str = "Building network with dummy (non-FPGA) ensemble."
        logger.warning(warn_str)
        print("WARNING: " + warn_str)
        nengo.builder.network.build_network(model, network)
        return

    # Generate the ensemble and connection parameters and save them to file
    extract_and_save_params(model, network)

    # Build the nengo network using the network's udp_socket function
    # Set up input/output signals
    input_sig = Signal(np.zeros(network.input_dimensions), name="input")
    model.sig[network.input]["in"] = input_sig
    model.sig[network.input]["out"] = input_sig
    model.add_op(Reset(input_sig))
    input_sig = model.build(nengo.synapses.Lowpass(0), input_sig)

    error_sig = Signal(np.zeros(network.output_dimensions), name="error")
    model.sig[network.error]["in"] = error_sig
    model.sig[network.error]["out"] = error_sig
    model.add_op(Reset(error_sig))
    error_sig = model.build(nengo.synapses.Lowpass(0), error_sig)

    output_sig = Signal(np.zeros(network.output_dimensions), name="output")
    model.sig[network.output]["out"] = output_sig
    if network.connection.synapse is not None:  # pragma: no cover
        model.build(network.connection.synapse, output_sig)

    # Set up udp_socket combined input signals
    udp_socket_input_sig = Signal(
        np.zeros(network.input_dimensions + network.output_dimensions),
        name="udp_socket_input",
    )
    model.add_op(
        Copy(
            input_sig,
            udp_socket_input_sig,
            dst_slice=slice(0, network.input_dimensions),
        )
    )
    model.add_op(
        Copy(
            error_sig,
            udp_socket_input_sig,
            dst_slice=slice(network.input_dimensions, None),
        )
    )

    # Build udp socket function with Nengo SimPyFunc
    model.add_op(
        SimPyFunc(
            output=output_sig,
            fn=partial(udp_comm_func, net=network, dt=model.dt),
            t=model.time,
            x=udp_socket_input_sig,
        )
    )
