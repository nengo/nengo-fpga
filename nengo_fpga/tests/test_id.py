"""Tests for the ID extraction process"""
import os
import socket

import pytest

from nengo_fpga import fpga_config, id_extractor
from nengo_fpga.id_extractor import IDExtractor


def test_script(mocker):
    """Test the ID script run as __main__"""

    # Explicitly set args to parse
    args = [
        "id_extractor.py",
        "test-name",
    ]
    mocker.patch("sys.argv", args)

    # Force id_script to run under __name__ == __main__
    mocker.patch.object(id_extractor, "__name__", "__main__")

    # We only need to check if main is called, don't actually run here
    main_mock = mocker.patch.object(id_extractor, "main")

    id_extractor.run()

    main_mock.assert_called_with(args[1])


def test_missing_arg(mocker):
    """Test the ID script run as __main__ without fpga_name arg"""

    # Explicitly set args to parse
    args = [
        "id_extractor.py",
    ]
    mocker.patch("sys.argv", args)

    # Force id_script to run under __name__ == __main__
    mocker.patch.object(id_extractor, "__name__", "__main__")

    # We only need to check if main is called, don't actually run here
    main_mock = mocker.patch.object(id_extractor, "main")

    # Should print help and exit, no call to main
    with pytest.raises(SystemExit):
        id_extractor.run()

    main_mock.assert_not_called()


def test_main(mocker):
    """Test the main function of the ID extractor script"""

    # Don't actually create the driver
    mocker.patch.object(IDExtractor, "__init__", return_value=None)

    # Keep track of calls we expect to see
    connect_mock = mocker.patch.object(IDExtractor, "connect")
    recv_id_mock = mocker.patch.object(IDExtractor, "recv_id")
    cleanup_mock = mocker.patch.object(IDExtractor, "cleanup")

    # Create a dummy ID attribute
    test_id = 12345
    mocker.patch.object(IDExtractor, "id_int", test_id, create=True)

    test_fpga_name = "test"
    id_extractor.main(test_fpga_name)

    # Check for calls we expect
    connect_mock.assert_called_once()
    recv_id_mock.assert_called_once()
    cleanup_mock.assert_called_once()

    # Check we wrote a file with the ID and cleanup
    id_file = os.path.join(os.getcwd(), "id_" + test_fpga_name + ".txt")
    assert os.path.isfile(id_file)
    os.remove(id_file)


def test_driver_no_config():
    """Test the ID extractor given an invalid fpga name"""

    with pytest.raises(SystemExit):
        IDExtractor("not-a-valid-name")


def test_driver_init(dummy_extractor):
    """Check a few token values on our dummy extractor init"""
    assert dummy_extractor.ssh_info_str == ""
    assert dummy_extractor.config_found
    assert dummy_extractor.tcp_port > 0


def test_cleanup(dummy_extractor, dummy_com, mocker):
    """Test the IDExtractor's cleanup function"""

    # Mock out close calls
    dummy_extractor.tcp_init = dummy_com()
    tcp_mock = mocker.patch.object(dummy_extractor.tcp_init, "close")
    ssh_mock = mocker.patch.object(dummy_extractor.ssh_client, "close")

    dummy_extractor.cleanup()  # Won't close tcp_recv since it's not created

    dummy_extractor.tcp_recv = dummy_com()
    recv_mock = mocker.patch.object(dummy_extractor.tcp_recv, "close")
    dummy_extractor.cleanup()  # Should close tcp_recv now

    assert tcp_mock.call_count == 2
    assert ssh_mock.call_count == 2
    assert recv_mock.call_count == 1


@pytest.mark.parametrize(
    "ssh_method", [None, ("ssh_pwd", "passwd"), ("ssh_key", "key-path")]
)
def test_connect_ssh_client(ssh_method, config_contents, gen_configs, mocker):
    """Test the IDExtractor's connect_ssh_client function

    Almost identical to test in "test_networks"
    """

    # Create a dummy config for testing
    fname = os.path.join(os.getcwd(), "test-config")
    fpga_name = list(config_contents.keys())[1]

    # Add ssh_connection method to dummy config dict
    if ssh_method is not None:
        config_contents[fpga_name][ssh_method[0]] = ssh_method[1]

    gen_configs.create_config(fname, contents=config_contents)
    fpga_config.reload_config(fname)

    # Don't actually connect the socket in init
    mocker.patch("socket.socket.bind")
    mocker.patch("socket.socket.listen")

    # Create driver
    extractor = IDExtractor(fpga_name)

    # Don't actually connect the ssh client
    connect_mock = mocker.patch.object(extractor.ssh_client, "connect")

    ssh_user = config_contents[fpga_name]["ssh_user"]
    remote_ip = config_contents[fpga_name]["ip"]
    ssh_port = config_contents[fpga_name]["ssh_port"]
    extractor.connect_ssh_client(ssh_user, remote_ip)

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


def test_connect_thread_func(dummy_extractor, dummy_com, config_contents, mocker):
    """Test the IDExtractor's connect_thread_func function

    Similar to the test in "test_id"
    """

    # Don't use ssh connections
    ssh_client_mock = mocker.patch.object(dummy_extractor, "connect_ssh_client")

    dummy_channel = dummy_com()
    mocker.patch.object(
        dummy_extractor.ssh_client, "invoke_shell", return_value=dummy_channel
    )
    chan_send_mock = mocker.patch.object(dummy_channel, "send")
    chan_recv_mock = mocker.patch.object(dummy_channel, "recv")
    chan_close_mock = mocker.patch.object(dummy_channel, "close")

    # Mock some other class functions
    process_mock = mocker.patch.object(dummy_extractor, "process_ssh_output")
    check_str_mock = mocker.patch.object(dummy_extractor, "check_ssh_str")

    # Test working case
    # First pass we get input, then recv nothing to break on second pass
    recv_list = ["something", ""]
    chan_recv_mock.side_effect = recv_list
    check_str_mock.return_value = (0, [])
    dummy_extractor.ssh_info_str = "something\n"

    dummy_extractor.connect_thread_func()

    ssh_client_mock.assert_called_once_with(
        config_contents["test-fpga"]["ssh_user"], config_contents["test-fpga"]["ip"]
    )
    chan_send_mock.assert_has_calls(
        [mocker.call("sudo su\n"), mocker.call(dummy_extractor.ssh_string)]
    )
    assert chan_recv_mock.call_count == len(recv_list)
    chan_close_mock.assert_called_once()
    chan_close_mock.reset_mock()
    process_mock.assert_called_once()
    check_str_mock.assert_called_once()

    # Test recv fatal error
    check_str_mock.return_value = (2, [])
    recv_list = ["something", "another thing"]
    chan_recv_mock.side_effect = recv_list
    dummy_extractor.ssh_info_str = "something\n"

    with pytest.raises(RuntimeError):
        dummy_extractor.connect_thread_func()

    chan_close_mock.assert_called_once()


def test_connect(dummy_extractor, mocker):
    """Test the IDExtractor's connect function"""

    # Don't actually create and start a thread
    thread_mock = mocker.patch("threading.Thread")

    dummy_extractor.connect()

    thread_mock.assert_called_once_with(
        target=dummy_extractor.connect_thread_func, args=()
    )


def test_process_ssh_output(dummy_extractor):
    """Test the IDExtractor's process_ssh_output

    Almost identical to test in "test_networks"
    """

    # Create a test string using carraige returns that should be replaced
    strs = ["First", "Second", "Third", "Fourth", "Fifth"]
    input_str = "{}\r\n{}\r\r{}\r{}\n{}".format(*strs)

    dummy_extractor.process_ssh_output(input_str.encode("latin1"))

    # New lines should all be '\n', so we should get our strs list back
    assert dummy_extractor.ssh_info_str.split("\n") == strs


def test_check_ssh_str(dummy_extractor):
    """Test remote string processing

    Almost identical to test in "test_networks"
    """

    # Init
    error_strs = []
    got_error = 0

    # Test no error condition
    got_error, error_strs = dummy_extractor.check_ssh_str(
        "No Problem", error_strs, got_error, "1.2.3.4"
    )
    assert got_error == 0
    assert error_strs == []

    # Test killed condition
    kill_str = "Killed starts the string"
    got_error, error_strs = dummy_extractor.check_ssh_str(
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
        got_error, error_strs = dummy_extractor.check_ssh_str(
            s, error_strs, got_error, "1.2.3.4"
        )
        # Expect error 1 until we finish
        expected_err = 2 if s == done_token else 1
        assert got_error == expected_err
        assert error_strs[-1] == s


def test_ssh_string(dummy_extractor, config_contents):
    """Test we have the correct arguments in the string command

    Almost identical to test in "test_networks"
    """

    # Split up the ssh command string
    args = dummy_extractor.ssh_string.split(" ")

    # Check args
    assert args[0] == "python"
    assert args[1] == config_contents["test-fpga"]["id_script"]
    assert args[2].split("=")[0] == "--host_ip"
    assert args[2].split("=")[1] == '"{}"'.format(config_contents["host"]["ip"])
    assert args[3].split("=")[0] == "--tcp_port"
    assert args[3].split("=")[1] == "{}\n".format(dummy_extractor.tcp_port)

    # Test default case
    dummy_extractor.config_found = False
    assert dummy_extractor.ssh_string == ""


def test_recv_id(dummy_extractor, dummy_com, mocker):
    """Test the IDExtractor's recv_id function"""

    # Arbitrary expected val
    expected_int = 1234

    # Setup mock sockets
    dummy_extractor.tcp_init = dummy_com()
    recv_socket = dummy_com()
    mocker.patch.object(
        recv_socket, "recv", return_value=expected_int.to_bytes(4, "big")
    )
    accept_mock = mocker.patch.object(
        dummy_extractor.tcp_init, "accept", return_value=(recv_socket, 0)
    )
    cleanup_mock = mocker.patch.object(dummy_extractor, "cleanup")

    dummy_extractor.recv_id()

    # Not checking bytes value since we explicitly return that in the mock
    assert dummy_extractor.id_int == expected_int

    # Update our mock to return an error and test the `except` case
    accept_mock.side_effect = socket.timeout()

    with pytest.raises(Exception):
        dummy_extractor.recv_id()

    # +1 calls for the initial successful call
    assert accept_mock.call_count == dummy_extractor.max_attempts + 1
    assert cleanup_mock.call_count == 1
