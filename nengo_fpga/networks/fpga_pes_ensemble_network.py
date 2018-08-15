import os
import re
import time
import logging
import threading
import numpy as np
import paramiko

import nengo
from nengo.builder.signal import Signal
from nengo.builder.operator import Reset, Copy, SimPyFunc
# Temporarily import from local sockets module
# TODO: Remove when sockets merged into nengo_extras
try:
    from nengo_extras import sockets
except ImportError:
    from nengo_fpga import sockets

from nengo_fpga.fpga_config import fpga_config


logger = logging.getLogger(__name__)


class FpgaPesEnsembleNetwork(nengo.Network):
    """ An ensemble to be run on the FPGA

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
    socket_args : TODO
        TODO
    label : str, optional (Default: None)
        A descriptive label for the connection.
    seed : int, optional (Default: None)
        The seed used for random number generation.
    add_to_container : TODO
        TODO

    Attributes
    ----------
    Just point to nengo? or list everything here?

    """
    def __init__(self, fpga_name, n_neurons, dimensions, learning_rate,
                 function=nengo.Default, transform=nengo.Default,
                 eval_points=nengo.Default, socket_args={},
                 label=None, seed=None, add_to_container=None):

        # Flags for determining whether or not the FPGA board is being used
        self.config_found = fpga_config.has_section(fpga_name)
        self.fpga_found = True  # TODO: Ping board to determine?
        self.using_fpga_sim = False

        # Make SSHClient object
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_info_str = ''
        self.ssh_lock = False

        # Save ssh details
        self.fpga_name = fpga_name
        self.arg_data_path = os.curdir
        self.arg_data_file = ''

        # Process dimensions, function, transform arguments
        self.input_dimensions = dimensions

        if function is nengo.Default:
            self.output_dimensions = dimensions
        elif callable(function):
            self.output_dimensions = len(function(np.zeros(dimensions)))
        elif nengo.utils.compat.is_array_like(function):
            self.output_dimensions = function.shape[1]
        else:
            raise nengo.exceptions.ValidationError(
                "must be callable or array-like", "function", self)

        # Neuron type string map
        self.neuron_str_map = {
            nengo.neurons.RectifiedLinear: 'RectifiedLinear',
            nengo.neurons.SpikingRectifiedLinear: 'SpikingRectifiedLinear'
        }
        self.default_neuron_type = nengo.neurons.RectifiedLinear()

        # Store the various parameters needed to initialize the remote network
        self.seed = seed
        self.learning_rate = learning_rate

        # Call the superconstructor
        super(FpgaPesEnsembleNetwork, self).__init__(label, seed,
                                                     add_to_container)

        # Check if the desired FPGA name is defined in the configuration file
        if self.config_found:
            # Handle the udp port selection: Use the config specified port.
            # If none is provided (i.e., the specified port number is 0),
            # choose a random udp port number between 20000 and 65535.
            self.udp_port = int(fpga_config.get(fpga_name, 'udp_port'))
            if self.udp_port == 0:
                self.udp_port = int(np.random.uniform(low=20000, high=65535))

            # Set default udp socket arguments
            socket_kwargs = dict(socket_args)
            socket_kwargs.setdefault('recv_timeout', 0.1)

            # Make the UDP socket nengo process.
            self.udp_socket = sockets.UDPSendReceiveSocket(
                listen_addr=(fpga_config.get('host', 'ip'), self.udp_port),
                remote_addr=(fpga_config.get(fpga_name, 'ip'), self.udp_port),
                **socket_kwargs)
        else:
            # FPGA name not found, throw a warning.
            logger.warn("Specified FPGA configuration '" + fpga_name + "' " +
                        'not found.')
            print("WARNING: Specified FPGA configuration '" + fpga_name +
                  "' not found.")
            self.udp_socket = None

        # Make nengo model. Here, a dummy ensemble is created. It will be
        # replaced with a udp_socket in the builder function (see below).
        with self:
            self.input = nengo.Node(size_in=self.input_dimensions,
                                    label='input')
            self.error = nengo.Node(size_in=self.output_dimensions,
                                    label='error')
            self.output = nengo.Node(size_in=self.output_dimensions,
                                     label='output')

            self.ensemble = nengo.Ensemble(
                n_neurons, self.input_dimensions,
                neuron_type=nengo.neurons.RectifiedLinear(),
                eval_points=eval_points, label='Dummy Ensemble')
            nengo.Connection(self.input, self.ensemble, synapse=None)

            self.connection = nengo.Connection(
                self.ensemble, self.output, function=function,
                transform=transform, eval_points=eval_points,
                learning_rule_type=nengo.PES(learning_rate))
            nengo.Connection(self.error, self.connection.learning_rule,
                             synapse=None)

        # Make the object lists immutable so that no extra objects can be added
        # to this network.
        for k, v in self.objects.items():
            self.objects[k] = tuple(v)

    @property
    def local_data_filepath(self):
        # Full path to ensemble parameter value data file on the local system.
        # Ensemble parameter values are generated by the builder.
        return os.path.join(self.arg_data_path, self.arg_data_file)

    def close(self):
        logger.info("<%s> SSH connection closed" %
                    fpga_config.get(self.fpga_name, 'ip'))
        self.ssh_client.close()

    def cleanup(self):
        # Clean up any existing argument data files
        if os.path.exists(self.local_data_filepath):
            os.remove(self.local_data_filepath)

    def connect_thread_func(self):
        remote_ip = fpga_config.get(self.fpga_name, 'ip')

        # Connect to remote location over ssh
        self.ssh_client.connect(
            fpga_config.get(self.fpga_name, 'ip'),
            port=fpga_config.get(self.fpga_name, 'port'),
            username=fpga_config.get(self.fpga_name, 'user'),
            password=fpga_config.get(self.fpga_name, 'pwd'))

        # Send argument file over
        remote_data_filepath = \
            '%s/%s' % (fpga_config.get(self.fpga_name, 'tmp'),
                       self.arg_data_file)

        if os.path.exists(self.local_data_filepath):
            logger.info("<%s> Sending argument data (%s) to fpga board" %
                        (fpga_config.get(self.fpga_name, 'ip'),
                         self.arg_data_file))

            # Send the argument data over to the fpga board
            # Create sftp connection
            sftp_client = self.ssh_client.open_sftp()
            sftp_client.put(self.local_data_filepath, remote_data_filepath)

            # Close sftp connection and release ssh connection lock
            sftp_client.close()

            # Delete argument file (no longer needed)
            os.remove(self.local_data_filepath)

        # Invoke a shell in the ssh client
        ssh_channel = self.ssh_client.invoke_shell()

        # If board configuration specifies using sudo to run scripts
        if fpga_config.getboolean(self.fpga_name, 'use_sudo') and \
           fpga_config.get(self.fpga_name, 'user') != 'root':
            logger.info('<%s> Script to be run with sudo. Sudoing.' %
                        remote_ip)
            ssh_channel.send('sudo su\n')

            # Wait for '[sudo]' prompt for password
            data = ssh_channel.recv(256)
            self.process_ssh_output(data)
            while not re.search(".*\[sudo\].*", self.ssh_info_str):
                time.sleep(1)
                data = ssh_channel.recv(256)
                self.process_ssh_output(data)

            # Prompt received. Provide password
            logger.info('<%s> Password requested for sudo. Sending password.' %
                        remote_ip)
            ssh_channel.send('%s\n' % fpga_config.get(self.fpga_name, 'pwd'))

        # Send required ssh string
        logger.info("<%s> Sending cmd to fpga board: \n%s" %
                    (fpga_config.get(self.fpga_name, 'ip'),
                     self.ssh_string))
        ssh_channel.send(self.ssh_string)

        # Variable for remote error handling
        got_error = 0
        error_strs = []

        # Get and process the information being returned over the ssh
        # connection
        while True:
            data = ssh_channel.recv(256)
            if not data:
                # If no data is received, the client has been closed, so close
                # the channel, and break out of the while loop
                ssh_channel.close()
                break

            self.process_ssh_output(data)
            info_str_list = self.ssh_info_str.split('\n')
            for info_str in info_str_list[:-1]:
                if info_str.startswith('Killed'):
                    logger.error('<%s> ENCOUNTERED ERROR!' % remote_ip)
                    got_error = 2

                if info_str.startswith('Traceback'):
                    logger.error('<%s> ENCOUNTERED ERROR!' % remote_ip)
                    got_error = 1
                elif got_error > 0 and info_str[0] != ' ':
                    # Error string is no longer tabbed, so the actual error
                    # is bring printed. Collect and terminate (see below)
                    got_error = 2

                if got_error > 0:
                    # Once an error is encountered, keep collecting error
                    # messages until the termination condition (above)
                    error_strs.append(info_str)
                else:
                    logger.info('<%s> %s', remote_ip, info_str)
            self.ssh_info_str = info_str_list[-1]

            # The traceback usually contains 3 lines, so collect the first
            # three lines then display it.
            if got_error == 2:
                ssh_channel.close()
                raise RuntimeError(
                    'Received the following error on the remote side <%s>:\n%s'
                    % (remote_ip, '\n'.join(error_strs)))

    def connect(self):
        logger.info("<%s> Open SSH connection" %
                    fpga_config.get(self.fpga_name, 'ip'))
        # Start a new thread to open the ssh connection. Use a thread to
        # handle the opening of the connection because it can lag for certain
        # devices, and we dont want it to impact the rest of the build process.
        connect_thread = threading.Thread(target=self.connect_thread_func,
                                          args=())
        connect_thread.start()

    def process_ssh_output(self, data):
        # Clean up the data stream coming back over ssh
        str_data = data.decode('latin1').replace('\r\n', '\r')
        str_data = str_data.replace('\r\r', '\r')
        str_data = str_data.replace('\r', '\n')

        # Process and dump the returned ssh data to logger. Data (strings)
        # returned over SSH are terminated by a newline, so, keep track of
        # the data and write the data to logger only when a newline is
        # received.
        self.ssh_info_str += str_data

    def reset(self):
        logger.info("<%s> Resetting SSH connection:" %
                    fpga_config.get(self.fpga_name, 'ip'))
        # Close and reopen ssh connections
        self.close()
        self.connect()

    @property
    def ssh_string(self):
        # Generate the string to be sent over the ssh connection to run the
        # remote side ssh script (with appropriate arguments)
        if self.config_found:
            ssh_str = \
                ('python ' + fpga_config.get(self.fpga_name, 'script') +
                 ' --host_ip="%s"' % fpga_config.get('host', 'ip') +
                 ' --remote_ip="%s"' % fpga_config.get(self.fpga_name, 'ip') +
                 ' --udp_port=%i' % self.udp_port +
                 ' --arg_data_file="%s/%s"' %
                 (fpga_config.get(self.fpga_name, 'tmp'),
                  self.arg_data_file) +
                 ' --seed=%s' % str(self.seed) +
                 '\n')
        else:
            ssh_str = ''
        return ssh_str


@nengo.builder.Builder.register(FpgaPesEnsembleNetwork)
def build_FpgaPesEnsembleNetwork(model, network):
    """ Add build steps like nengo?
    """


    # Check if nengo_fpga.Simulator is being used to build this network
    if not network.using_fpga_sim:
        warn_str = 'FpgaPesEnsembleNetwork not being built with nengo_fpga' + \
                   ' simulator.'
        logger.warn(warn_str)
        print('WARNING: ' + warn_str)

    # Check if all of the requirements to use the FPGA board are met
    if network.using_fpga_sim and network.config_found and network.fpga_found:
        # FPGA requirements met!

        if network.seed is None:
            # Inherit seed from parent network's build process
            seeded = True
            network.seed = model.seeds[network]
        else:
            seeded = False

        # Generate the network used to get the ensemble and output connection
        # parameters
        param_model = nengo.builder.Model(dt=model.dt)
        nengo.builder.network.build_network(param_model, network)

        if seeded:
            # Restore the original seed=None, so that we don't alter the
            # network state if it is used again in a different network
            network.seed = None

        # Collect the simulation argument values
        sim_args = {}
        sim_args['dt'] = model.dt

        # Collect the ensemble argument values
        ens_args = {}
        ens_args['input_dimensions'] = network.input_dimensions
        ens_args['output_dimensions'] = network.output_dimensions
        ens_args['n_neurons'] = network.ensemble.n_neurons
        ens_args['bias'] = param_model.params[network.ensemble].bias
        if type(network.ensemble.neuron_type) in network.neuron_str_map:
            ens_args['neuron_type'] = \
                network.neuron_str_map[type(network.ensemble.neuron_type)]
        else:
            warn_str = \
                'Neuron type "' + str(type(network.ensemble.neuron_type)) + \
                '" is currently not supported. Using default "' + \
                str(type(network.default_neuron_type)) + '" neuron.'
            logger.warn(warn_str)
            print('WARNING: ' + warn_str)

        ens_args['scaled_encoders'] = \
            param_model.params[network.ensemble].scaled_encoders

        # Collect the connection argument values
        conn_args = {}
        conn_args['weights'] = param_model.params[network.connection].weights

        if network.connection.learning_rule_type is None:
            conn_args['learning_rate'] = 0
        elif isinstance(network.connection.learning_rule_type, nengo.PES):
            conn_args['learning_rate'] = \
                network.connection.learning_rule_type.learning_rate
        else:
            raise nengo.exceptions.BuildError(
                'Learning rule "%s" not supported.' %
                type(network.connection.learning_rule_type))

        # Save the NPZ data file
        npz_filename = 'fpen_args_' + str(id(network)) + '.npz'
        network.arg_data_file = npz_filename
        np.savez_compressed(network.local_data_filepath, sim_args=sim_args,
                            ens_args=ens_args, conn_args=conn_args)

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
        if network.connection.synapse is not None:
            model.build(network.connection.synapse, output_sig)

        # Set up udp_socket combined input signals
        udp_socket_input_sig = \
            Signal(np.zeros(network.input_dimensions +
                            network.output_dimensions),
                   name="udp_socket_input")
        model.add_op(Copy(input_sig, udp_socket_input_sig,
                          dst_slice=slice(0, network.input_dimensions)))
        model.add_op(Copy(error_sig, udp_socket_input_sig,
                          dst_slice=slice(network.input_dimensions, None)))

        # Build udp_socket nengo process
        model.build(network.udp_socket, udp_socket_input_sig, output_sig)
    else:
        # Build the dummy network instead of using FPGA-specific stuff
        warn_str = 'Building network with dummy (non-FPGA) ensemble.'
        logger.warn(warn_str)
        print('WARNING: ' + warn_str)
        nengo.builder.network.build_network(model, network)
