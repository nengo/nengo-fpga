"""Tests for the FPGA network classes"""
import os
import socket

import nengo
import numpy as np
import pytest
from nengo.solvers import NoSolver

from nengo_fpga import fpga_config
from nengo_fpga.networks import FpgaPesEnsembleNetwork
from nengo_fpga.networks.fpga_pes_ensemble_network import (
    extract_and_save_params,
    udp_comm_func,
    validate_net,
)


def test_init(config_contents, gen_configs, mocker):
    """Test the FPGA network's init function"""

    # Create a dummy config for testing
    fname = os.path.join(os.getcwd(), "test-config")
    fpga_name = list(config_contents.keys())[1]

    gen_configs.create_config(fname, contents=config_contents)
    fpga_config.reload_config(fname)

    # Keep track of calls
    out_dim_spy = mocker.spy(FpgaPesEnsembleNetwork, "get_output_dim")
    nengo_net_spy = mocker.spy(nengo.Network, "__init__")

    # Arbitrary params
    dims_in = 2
    dims_out = 4
    n_neurons = 10
    l_rate = 0.001
    transform = 2
    eval_points = np.ones((2, 2)) * 0.5
    socket_args = {"connect_timeout": 10, "recv_timeout": 1}
    label = "name"
    seed = 5

    def test_func(x):
        """Dummy function to test output dim"""
        return [0] * dims_out

    dummy_net = FpgaPesEnsembleNetwork(
        fpga_name,
        n_neurons,
        dims_in,
        l_rate,
        transform=transform,
        eval_points=eval_points,
        socket_args=socket_args,
        function=test_func,
        label=label,
        seed=seed,
    )

    assert dummy_net.input_dimensions == dims_in
    out_dim_spy.assert_called_once_with(dummy_net, test_func, dims_in)
    assert dummy_net.seed == seed
    assert dummy_net.learning_rate == l_rate
    nengo_net_spy.assert_called_once_with(dummy_net, label, seed, None)
    assert dummy_net.connect_timeout == socket_args["connect_timeout"]
    assert dummy_net.recv_timeout == socket_args["recv_timeout"]
    assert dummy_net.udp_port > 0
    assert dummy_net.send_addr[0] == config_contents[fpga_name]["ip"]

    assert dummy_net.input.size_in == dims_in
    assert dummy_net.error.size_in == dims_out
    assert dummy_net.output.size_in == dims_out

    assert dummy_net.ensemble.n_neurons == n_neurons
    assert dummy_net.ensemble.dimensions == dims_in
    assert np.all(dummy_net.ensemble.eval_points == eval_points)

    assert dummy_net.connection.pre == dummy_net.ensemble
    assert dummy_net.connection.post == dummy_net.output
    assert dummy_net.connection.function == test_func
    assert np.all(dummy_net.connection.transform.init == transform)
    assert np.all(dummy_net.connection.eval_points == eval_points)

    assert dummy_net.feedback is None

    # Test invalid feedback
    with pytest.raises(nengo.exceptions.ValidationError):
        _ = FpgaPesEnsembleNetwork(
            fpga_name, n_neurons, dims_in, l_rate, feedback="invalid"
        )

    # Test feedback not None
    rec_transform = np.eye(dims_in)
    dummy_net = FpgaPesEnsembleNetwork(
        fpga_name, n_neurons, dims_in, l_rate, feedback=rec_transform
    )

    assert dummy_net.feedback.pre == dummy_net.ensemble
    assert dummy_net.feedback.post == dummy_net.ensemble
    assert dummy_net.feedback.synapse.tau == 0.1
    assert np.all(dummy_net.feedback.transform.init == rec_transform)

    # Test config not found
    dummy_net = FpgaPesEnsembleNetwork("not found", n_neurons, dims_in, l_rate)

    assert dummy_net.config_found is False

    # Check we skip conditional code
    assert not hasattr(dummy_net, "udp_port")
    assert not hasattr(dummy_net, "send_addr")

    # Check a couple token things to ensure we still built the network
    assert hasattr(dummy_net, "input")
    assert hasattr(dummy_net, "ensemble")
    assert hasattr(dummy_net, "connection")


def test_init_default(config_contents, gen_configs, mocker):
    """Test the FPGA network's init function"""

    # Create a dummy config for testing
    fname = os.path.join(os.getcwd(), "test-config")
    fpga_name = list(config_contents.keys())[1]

    gen_configs.create_config(fname, contents=config_contents)
    fpga_config.reload_config(fname)

    # Keep track of calls
    out_dim_spy = mocker.spy(FpgaPesEnsembleNetwork, "get_output_dim")
    nengo_net_spy = mocker.spy(nengo.Network, "__init__")

    # Arbitrary params
    dims_in = 2
    n_neurons = 10
    l_rate = 0.001

    dummy_net = FpgaPesEnsembleNetwork(
        fpga_name,
        n_neurons,
        dims_in,
        l_rate,
    )

    assert dummy_net.input_dimensions == dims_in
    out_dim_spy.assert_called_once_with(dummy_net, nengo.Default, dims_in)
    assert dummy_net.seed is None
    assert dummy_net.learning_rate == l_rate
    nengo_net_spy.assert_called_once_with(dummy_net, None, None, None)
    assert dummy_net.connect_timeout == 30
    assert dummy_net.recv_timeout == 0.1
    assert dummy_net.udp_port > 0
    assert dummy_net.send_addr[0] == config_contents[fpga_name]["ip"]

    assert dummy_net.input.size_in == dims_in
    assert dummy_net.error.size_in == dims_in
    assert dummy_net.output.size_in == dims_in

    assert dummy_net.ensemble.n_neurons == n_neurons
    assert dummy_net.ensemble.dimensions == dims_in
    assert np.all(dummy_net.ensemble.eval_points == nengo.Ensemble.eval_points.default)

    assert dummy_net.connection.pre == dummy_net.ensemble
    assert dummy_net.connection.post == dummy_net.output
    assert dummy_net.connection.function is None
    assert type(dummy_net.connection.transform) == nengo.transforms.NoTransform
    assert np.all(
        dummy_net.connection.eval_points == nengo.Connection.eval_points.default
    )

    assert dummy_net.feedback is None


def test_output_dim(dummy_net, mocker):
    """Test we correctly interpret output dimensionality"""

    # Test default output function
    default_dim = 1
    dummy_net.get_output_dim(nengo.Default, default_dim)
    assert dummy_net.output_dimensions == default_dim

    # Test callable function
    callable_dim = 2
    dummy_net.get_output_dim(lambda x: np.zeros(callable_dim), default_dim)
    assert dummy_net.output_dimensions == callable_dim

    # Test transform array
    array_dim = 3
    dummy_net.get_output_dim(np.zeros((default_dim, array_dim)), default_dim)
    assert dummy_net.output_dimensions == array_dim

    # Test invalid
    with pytest.raises(nengo.exceptions.ValidationError):
        dummy_net.get_output_dim("invalid", default_dim)


def test_data_filepath(dummy_net, mocker):
    """Test local_data_filepath property"""

    # Arbitrary file path
    path = "path"
    fname = "file.txt"

    dummy_net.arg_data_path = path
    dummy_net.arg_data_file = fname

    assert dummy_net.local_data_filepath == os.path.join(path, fname)


def test_terminate_client(dummy_net, dummy_com, config_contents, mocker):
    """Test the FPGA network's terminate_client function"""

    # The udp socket isn't defined in init, so make a dummy one here
    dummy_net.udp_socket = dummy_com()
    send_mock = mocker.patch.object(dummy_net.udp_socket, "sendto")

    dummy_net.terminate_client()

    address = (config_contents["test-fpga"]["ip"], dummy_net.udp_port)

    # Check -1 signal and address
    assert np.all(np.frombuffer(send_mock.call_args_list[0][0][0]) == -1)
    assert send_mock.call_args_list[0][0][1] == address


def test_close(dummy_net, dummy_com, mocker):
    """Test the FPGA network's close function"""

    # Mock out cleanup functions
    terminate_mock = mocker.patch.object(dummy_net, "terminate_client")
    ssh_close_mock = mocker.patch.object(dummy_net.ssh_client, "close")

    # Test no config condition returns immediately
    dummy_net.config_found = False
    dummy_net.close()

    terminate_mock.assert_not_called()
    ssh_close_mock.assert_not_called()
    assert dummy_net.send_buffer is None
    assert dummy_net.recv_buffer is None

    # Test no UDP socket
    dummy_net.config_found = True
    dummy_net.close()

    terminate_mock.assert_not_called()
    ssh_close_mock.assert_called_once()
    assert np.all(dummy_net.send_buffer == 0)
    assert np.all(dummy_net.recv_buffer == 0)

    # Reset for full test
    ssh_close_mock.reset_mock()
    dummy_net.send_buffer = None
    dummy_net.recv_buffer = None

    # Test full
    dummy_net.udp_socket = dummy_com()
    udp_close_mock = mocker.patch.object(dummy_net.udp_socket, "close")

    dummy_net.close()

    terminate_mock.assert_called_once()
    udp_close_mock.assert_called_once()
    ssh_close_mock.assert_called_once()
    assert dummy_net.udp_socket is None
    assert np.all(dummy_net.send_buffer == 0)
    assert np.all(dummy_net.recv_buffer == 0)


def test_cleanup(dummy_net, mocker):
    """Test the FPGA network's cleanup function"""

    # Don't actually touch files
    isfile_mock = mocker.patch("os.path.isfile", return_value=True)
    remove_mock = mocker.patch("os.remove")

    # Test no config returns immediately
    dummy_net.config_found = False
    dummy_net.cleanup()

    isfile_mock.assert_not_called()
    remove_mock.assert_not_called()

    # Test full
    dummy_net.config_found = True
    dummy_net.cleanup()

    isfile_mock.assert_called_once()
    remove_mock.assert_called_once()


@pytest.mark.parametrize(
    "ssh_method", [None, ("ssh_pwd", "passwd"), ("ssh_key", "key-path")]
)
def test_connect_ssh_client(
    ssh_method, dummy_net, config_contents, gen_configs, mocker
):
    """Test the FPGA networks connect_ssh_client function

    Almost identical to test in "test_id"
    """

    # Create a dummy config for testing
    fname = os.path.join(os.getcwd(), "test-config")
    fpga_name = list(config_contents.keys())[1]

    # Add ssh_connection method to dummy config dict
    if ssh_method is not None:
        config_contents[fpga_name][ssh_method[0]] = ssh_method[1]

    gen_configs.create_config(fname, contents=config_contents)
    fpga_config.reload_config(fname)

    # Don't actually connect the ssh client
    connect_mock = mocker.patch.object(dummy_net.ssh_client, "connect")

    # Grab params
    ssh_user = config_contents[fpga_name]["ssh_user"]
    remote_ip = config_contents[fpga_name]["ip"]
    ssh_port = config_contents[fpga_name]["ssh_port"]
    dummy_net.connect_ssh_client(ssh_user, remote_ip)

    # Create the expected call based on the config
    if ssh_method is None:
        connect_mock.assert_called_once_with(
            remote_ip, port=ssh_port, username=ssh_user
        )
    elif ssh_method[0] == "ssh_pwd":
        connect_mock.assert_called_once_with(
            remote_ip, port=ssh_port, username=ssh_user, password=ssh_method[1]
        )
    elif ssh_method[0] == "ssh_key":
        connect_mock.assert_called_once_with(
            remote_ip, port=ssh_port, username=ssh_user, key_filename=ssh_method[1]
        )


def test_connect_thread_func(dummy_net, dummy_com, config_contents, mocker):
    """Test the FPGA network's connect_thread_func

    Similar to the test in "test_id"
    """

    # Don't use ssh connections
    ssh_client_mock = mocker.patch.object(dummy_net, "connect_ssh_client")

    dummy_sftp = dummy_com()
    mocker.patch.object(dummy_net.ssh_client, "open_sftp", return_value=dummy_sftp)
    ssh_put_mock = mocker.patch.object(dummy_sftp, "put")
    ssh_close_mock = mocker.patch.object(dummy_sftp, "close")

    dummy_channel = dummy_com()
    mocker.patch.object(
        dummy_net.ssh_client, "invoke_shell", return_value=dummy_channel
    )
    chan_send_mock = mocker.patch.object(dummy_channel, "send")
    chan_recv_mock = mocker.patch.object(dummy_channel, "recv")
    chan_close_mock = mocker.patch.object(dummy_channel, "close")

    # Mock some other class functions
    process_mock = mocker.patch.object(dummy_net, "process_ssh_output")
    check_str_mock = mocker.patch.object(dummy_net, "check_ssh_str")
    net_close_mock = mocker.patch.object(dummy_net, "close")

    # Test no config condition returns immediately
    dummy_net.config_found = False
    dummy_net.connect_thread_func()

    ssh_client_mock.assert_not_called()

    # Test working case
    dummy_net.config_found = True
    mocker.patch("os.path.exists", return_value=True)  # No real data file

    # First pass we get input, then recv nothing to break on second pass
    recv_list = ["something", ""]
    chan_recv_mock.side_effect = recv_list
    check_str_mock.return_value = (0, [])
    dummy_net.ssh_info_str = "something\n"

    dummy_net.connect_thread_func()

    ssh_client_mock.assert_called_once_with(
        config_contents["test-fpga"]["ssh_user"], config_contents["test-fpga"]["ip"]
    )
    ssh_put_mock.assert_called_once_with(
        dummy_net.local_data_filepath,
        f"{config_contents['test-fpga']['remote_tmp']}/{dummy_net.arg_data_file}",
    )
    ssh_close_mock.assert_called_once()
    chan_send_mock.assert_has_calls(
        [mocker.call("sudo su\n"), mocker.call(dummy_net.ssh_string)]
    )
    assert chan_recv_mock.call_count == len(recv_list)
    chan_close_mock.assert_called_once()
    process_mock.assert_called_once()
    check_str_mock.assert_called_once()
    net_close_mock.assert_not_called()

    # Test recv fatal error
    check_str_mock.return_value = (2, [])
    recv_list = ["something", "another thing"]
    chan_recv_mock.side_effect = recv_list
    dummy_net.ssh_info_str = "something\n"

    with pytest.raises(RuntimeError):
        dummy_net.connect_thread_func()

    net_close_mock.assert_called_once()


def test_connect(dummy_net, mocker):
    """Test the FPGA network's connect function"""

    # Test no config condition returns immediately
    dummy_net.config_found = False
    dummy_net.connect()

    assert dummy_net.udp_socket is None

    # Setup for full test
    dummy_net.config_found = True
    close_mock = mocker.patch.object(dummy_net, "close")

    # Don't actually create and start a thread
    thread_mock = mocker.patch("threading.Thread")

    # Don't use sockets
    mocker.patch("socket.socket.bind")

    # Test Attribute error
    recv_mock = mocker.patch("socket.socket.recv_into", side_effect=AttributeError())
    with pytest.raises(SystemExit):
        dummy_net.connect()

    recv_mock.assert_called_once()
    thread_mock.assert_called_once_with(target=dummy_net.connect_thread_func, args=())
    mocker.resetall()

    # Test socket timeout
    recv_mock.side_effect = socket.timeout()
    with pytest.raises(RuntimeError):
        dummy_net.connect()

    close_mock.assert_called_once()
    assert recv_mock.call_count == int(
        dummy_net.connect_timeout / dummy_net.recv_timeout
    )
    thread_mock.assert_called_once_with(target=dummy_net.connect_thread_func, args=())
    mocker.resetall()

    # Test receive -1 kill signal
    dummy_net.recv_buffer = np.zeros(1)  # Init buffer

    def recv_func_kill(data):
        """Dummy recv_into function to update recv buffer"""
        data[0] = -1  # Return -1 kill signal

    recv_mock.side_effect = recv_func_kill
    with pytest.raises(RuntimeError) as e:
        dummy_net.connect()

    assert str(e.value).startswith("Simulation terminated")  # No specific reason
    close_mock.assert_called_once()
    recv_mock.assert_called_once()
    thread_mock.assert_called_once_with(target=dummy_net.connect_thread_func, args=())
    # start_mock.assert_called_once()
    mocker.resetall()

    # Test receive -11 unavailable resource lock signal
    def recv_func_lock(data):
        """Dummy recv_into function to update recv buffer"""
        data[0] = -11  # Return -1 kill signal

    recv_mock.side_effect = recv_func_lock
    with pytest.raises(RuntimeError) as e:
        dummy_net.connect()

    assert str(e.value).startswith("Unable to acquire FPGA resource lock!")
    close_mock.assert_called_once()
    recv_mock.assert_called_once()
    thread_mock.assert_called_once_with(target=dummy_net.connect_thread_func, args=())
    # start_mock.assert_called_once()
    mocker.resetall()

    # Test receive -21 driver failure signal
    def recv_func_driver(data):
        """Dummy recv_into function to update recv buffer"""
        data[0] = -21  # Return -1 kill signal

    recv_mock.side_effect = recv_func_driver
    with pytest.raises(RuntimeError) as e:
        dummy_net.connect()

    assert str(e.value).startswith("Unable to load FPGA driver!")
    close_mock.assert_called_once()
    recv_mock.assert_called_once()
    thread_mock.assert_called_once_with(target=dummy_net.connect_thread_func, args=())
    # start_mock.assert_called_once()
    mocker.resetall()

    # Test normal working condition
    def recv_func_normal(data):
        """Dummy recv_into function to update recv buffer"""
        data[0] = 0  # Return valid data

    recv_mock.side_effect = recv_func_normal

    dummy_net.connect()

    close_mock.assert_not_called()


def test_process_ssh_output(dummy_net):
    """Test the IDExtractor's process_ssh_output

    Almost identical to test in "test_id"
    """

    # Create a test string using carraige returns that should be replaced
    strs = ["First", "Second", "Third", "Fourth", "Fifth"]
    input_str = "{}\r\n{}\r\r{}\r{}\n{}".format(*strs)

    dummy_net.process_ssh_output(input_str.encode("latin1"))

    # New lines should all be '\n', so we should get our strs list back
    assert dummy_net.ssh_info_str.split("\n") == strs


def test_check_ssh_str(dummy_net):
    """Test remote string processing

    Almost identical to test in "test_id"
    """

    # Init
    error_strs = []
    got_error = 0

    # Test no error condition
    got_error, error_strs = dummy_net.check_ssh_str(
        "No Problem", error_strs, got_error, "1.2.3.4"
    )
    assert got_error == 0
    assert error_strs == []

    # Test killed condition
    kill_str = "Killed starts the string"
    got_error, error_strs = dummy_net.check_ssh_str(
        kill_str, error_strs, got_error, "1.2.3.4"
    )
    assert got_error == 2
    assert error_strs[0] == kill_str

    # Reset
    error_strs = []
    got_error = 0

    # Test traceback condition
    done_token = "done"
    trace_str = ["Traceback", " First line", " Second line", done_token]
    for s in trace_str:
        got_error, error_strs = dummy_net.check_ssh_str(
            s, error_strs, got_error, "1.2.3.4"
        )
        # Expect error 1 until we finish
        expected_err = 2 if s == done_token else 1
        assert got_error == expected_err
        assert error_strs[-1] == s


def test_reset(dummy_net, mocker):
    """Test the FPGA network's reset function"""

    # Mock out some class functions
    close_mock = mocker.patch.object(dummy_net, "close")
    connect_mock = mocker.patch.object(dummy_net, "connect")

    # Test no config stops immediately
    dummy_net.config_found = False
    dummy_net.reset()

    close_mock.assert_not_called()
    connect_mock.assert_not_called()

    # Test full
    dummy_net.config_found = True
    dummy_net.reset()

    close_mock.assert_called_once()
    connect_mock.assert_called_once()


def test_ssh_string(dummy_net, config_contents):
    """Test we have the correct arguments in the string command

    Almost identical to test in "test_id"
    """

    # Set arg data file name
    arg_fname = "file.npz"
    dummy_net.arg_data_file = arg_fname

    # Split up the ssh command string
    args = dummy_net.ssh_string.split(" ")

    # Check args
    assert args[0] == "python"
    assert args[1] == config_contents["test-fpga"]["remote_script"]
    assert args[2].split("=")[0] == "--host_ip"
    assert args[2].split("=")[1] == f"'{config_contents['host']['ip']}'"
    assert args[3].split("=")[0] == "--remote_ip"
    assert args[3].split("=")[1] == f"'{config_contents['test-fpga']['ip']}'"
    assert args[4].split("=")[0] == "--udp_port"
    assert args[4].split("=")[1] == f"{dummy_net.udp_port}"
    assert args[5].split("=")[0] == "--arg_data_file"
    assert (
        args[5].split("=")[1]
        == f"'{config_contents['test-fpga']['remote_tmp']}/{arg_fname}'\n"
    )

    # Test default case
    dummy_net.config_found = False
    assert dummy_net.ssh_string == ""


def test_validate_net(dummy_net):
    """Test validation of FPGA networks"""

    # Test unsupported (must be valid nengo neuron or we get ValidationErrors)
    dummy_net.ensemble.neuron_type = nengo.LIF()

    with pytest.raises(nengo.exceptions.BuildError):
        _, _ = validate_net(dummy_net)

    # Test no learning rule
    neuron_type = nengo.RectifiedLinear()
    neuron_str = "RectifiedLinear"
    dummy_net.ensemble.neuron_type = neuron_type  # Set a valid neuron
    dummy_net.connection.learning_rule_type = None

    neuron, rate = validate_net(dummy_net)

    assert neuron == neuron_str
    assert rate == 0

    # Test set learning rule
    l_rate = 0.005
    dummy_net.connection.learning_rule_type = nengo.PES(l_rate)

    neuron, rate = validate_net(dummy_net)

    assert neuron == neuron_str
    assert rate == l_rate

    # Test invalid learning rule
    class DummyRule(nengo.learning_rules.LearningRuleType):
        """Dummy learning rule

        Can't use BCM or Oja since they use neuron connections
        Can't use Voja since it needs a post ensemble and we have a node
        """

        modifies = "decoders"

    dummy_net.connection.learning_rule_type = DummyRule()

    with pytest.raises(nengo.exceptions.BuildError):
        _, _ = validate_net(dummy_net)

    # Test valid feedback
    dummy_net.connection.learning_rule_type = nengo.PES(l_rate)  # Set valid
    # Add valid feedback connection
    dummy_net.feedback = nengo.Connection(
        dummy_net.ensemble,
        dummy_net.ensemble,
        synapse=nengo.Lowpass(0.1),
        add_to_container=False,
    )

    neuron, rate = validate_net(dummy_net)

    assert neuron == neuron_str
    assert rate == l_rate

    # Test with invalid feedback learning
    dummy_net.feedback.learning_rule_type = nengo.PES()

    with pytest.raises(nengo.exceptions.BuildError):
        _, _ = validate_net(dummy_net)

    # Test with invalid feedback synapse
    dummy_net.feedback.learning_rule_type = None  # Set valid
    dummy_net.feedback.synapse = nengo.Alpha(0.1)

    with pytest.raises(nengo.exceptions.BuildError):
        _, _ = validate_net(dummy_net)


def test_save_params(config_contents, gen_configs, mocker):
    """Test saving params to file"""

    # Create a dummy model object (we only need dt)
    class DummyModel:
        """Dummy model object to provide dt"""

        def __init__(self, dt):
            self.dt = dt

    dt = 0.001
    model = DummyModel(dt)

    # Create a dummy network

    # Create a dummy config for testing
    # (can't use fixture since some ensemble params are readonly)
    fname = os.path.join(os.getcwd(), "test-config")
    fpga_name = list(config_contents.keys())[1]

    gen_configs.create_config(fname, contents=config_contents)
    fpga_config.reload_config(fname)

    # Arbitrary params
    dims_in = 2
    dims_out = 2  # Dims are equal to simplify feedback connection
    n_neurons = 10
    bias_val = 1
    bias = np.ones(n_neurons) * bias_val
    enc_val = 2
    encoders = np.ones((n_neurons, dims_in)) * enc_val
    dec_val = 3
    decoders = np.ones((dims_out, n_neurons)) * dec_val
    rec_val = 4
    rec_decoders = np.ones((dims_in, n_neurons)) * rec_val
    neuron = "RectifiedLinear"
    l_rate = 0.005
    tau = 0.05

    # Setup dummy FPGA net with params
    dummy_net = FpgaPesEnsembleNetwork(
        fpga_name, n_neurons, dims_in, l_rate, feedback=1
    )

    dummy_net.output_dimensions = dims_out

    dummy_net.ensemble.bias = bias
    dummy_net.ensemble.encoders = encoders
    dummy_net.ensemble.normalize_encoders = False
    dummy_net.ensemble.gain = np.ones(n_neurons)

    dummy_net.connection.solver = NoSolver(decoders.T)
    mocker.patch(
        "nengo_fpga.networks.fpga_pes_ensemble_network.validate_net",
        return_value=(neuron, l_rate),
    )

    dummy_net.feedback.synapse = tau
    dummy_net.feedback.solver = NoSolver(rec_decoders.T)

    extract_and_save_params(model, dummy_net)

    # Check we write file
    assert os.path.isfile(dummy_net.local_data_filepath)

    # Check contents
    arg_data = np.load(
        dummy_net.local_data_filepath, encoding="latin1", allow_pickle=True
    )
    sim = arg_data["sim_args"].item()
    ens = arg_data["ens_args"].item()
    conn = arg_data["conn_args"].item()
    recur = arg_data["recur_args"].item()

    # Use try/except so we still cleanup on failure
    try:
        assert sim["dt"] == dt

        assert ens["input_dimensions"] == dims_in
        assert ens["output_dimensions"] == dims_out
        assert ens["n_neurons"] == n_neurons
        assert np.all(ens["bias"] == bias_val)
        assert np.all(ens["scaled_encoders"] == enc_val)
        assert ens["neuron_type"] == neuron

        assert np.all(conn["weights"] == dec_val)

        assert np.all(recur["weights"] == rec_val)
        assert recur["tau"] == tau
    except AssertionError:
        os.remove(dummy_net.local_data_filepath)
        raise

    os.remove(dummy_net.local_data_filepath)


def test_udp_comm_func(dummy_net, dummy_com, mocker):
    """Test SimPyFunc udp implementation"""

    # Don't use sockets
    dummy_net.udp_socket = dummy_com()
    send_mock = mocker.patch.object(dummy_net.udp_socket, "sendto")
    recv_mock = mocker.patch.object(dummy_net.udp_socket, "recv_into")

    close_mock = mocker.patch.object(dummy_net, "close")

    # Init buffers
    dummy_net.send_buffer = np.zeros(2)
    dummy_net.recv_buffer = np.zeros(2)

    # Arbitrary values
    dt = 0.001
    t = 1
    x = 2

    # Test socket_timeout case
    recv_mock.side_effect = socket.timeout()
    val = udp_comm_func(t, x, dummy_net, dt)

    close_mock.assert_not_called()

    # Test case receiving kill signal -1
    def recv_kill(data):
        """Dummy function to update recv_into data"""
        np.frombuffer(data)[0] = -1  # Send terminate signal

    recv_mock.side_effect = recv_kill

    with pytest.raises(RuntimeError):
        val = udp_comm_func(t, x, dummy_net, dt)

    close_mock.assert_called_once()

    # Test normal case with a delay step inside the while loop
    dummy_net.recv_buffer = np.zeros(2)
    dummy_net.send_buffer = np.zeros(2)
    recv_mock.reset_mock()

    def recv_func(data):
        """Dummy function to update recv_into data"""

        # Increment time, we want two steps in the loop hence t / 2
        np.frombuffer(data)[0] += t / 2.0
        np.frombuffer(data)[1] = x

    recv_mock.side_effect = recv_func

    val = udp_comm_func(t, x, dummy_net, dt)

    assert np.all(dummy_net.send_buffer == (t, x))
    send_mock.assert_called_with(dummy_net.send_buffer.tobytes(), dummy_net.send_addr)
    assert recv_mock.call_count == 2
    assert val == x


def test_builder(dummy_net, mocker):
    """Build a few networks to hit all the builder code"""

    # Don't generate params file
    mocker.patch(
        "nengo_fpga.networks.fpga_pes_ensemble_network.extract_and_save_params"
    )
    nengo_build_spy = mocker.spy(nengo.builder.network, "build_network")

    # Not using_fpga_sim
    model = nengo.builder.Model()
    model.build(dummy_net)
    nengo_build_spy.assert_called_once()
    nengo_build_spy.reset_mock()

    # No config found
    dummy_net.using_fpga_sim = True
    dummy_net.config_found = False
    model = nengo.builder.Model()
    model.build(dummy_net)
    nengo_build_spy.assert_called_once()
    nengo_build_spy.reset_mock()

    # No fpga_found
    dummy_net.config_found = True
    dummy_net.fpga_found = False
    model = nengo.builder.Model()
    model.build(dummy_net)
    nengo_build_spy.assert_called_once()
    nengo_build_spy.reset_mock()

    # Use FPGA builder
    dummy_net.fpga_found = True
    model = nengo.builder.Model()
    model.build(dummy_net)
    nengo_build_spy.assert_not_called()
