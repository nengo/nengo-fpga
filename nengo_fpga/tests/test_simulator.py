"""Tests for NengoFPGA Simulator"""
import nengo
import pytest

from nengo_fpga.networks import FpgaPesEnsembleNetwork
from nengo_fpga.simulator import Simulator


def test_init(mocker):
    """Test simulator network with standard nengo network"""

    # Don't actually create a simulator
    super_mock = mocker.patch("nengo.simulator.Simulator.__init__")

    # Test a non-FPGA network first
    nengo_net = nengo.Network()
    dt = 1  # Check kwargs are passed through
    sim = Simulator(nengo_net, dt=dt)

    assert sim.fpga_networks_list == []
    super_mock.assert_called_once_with(nengo_net, dt=dt)
    super_mock.reset_mock()

    # Add an FPGA network
    with nengo_net as net:
        net.fpga_net = FpgaPesEnsembleNetwork("test", 1, 1, 0.001)

    sim2 = Simulator(nengo_net)

    assert nengo_net.fpga_net.using_fpga_sim
    assert sim2.fpga_networks_list == [net.fpga_net]
    super_mock.assert_called_once_with(nengo_net)


@pytest.mark.parametrize("probe", ["ensemble", "neurons", "connection"])
def test_probe_list(mocker, probe):
    """Test probe checks in init"""

    # Don't actually create a simulator
    super_mock = mocker.patch("nengo.simulator.Simulator.__init__")

    # Create a dummy net with a given illegal probe
    with nengo.Network() as net:
        fpga_net = FpgaPesEnsembleNetwork("test", 1, 1, 0.001)

        probe_map = {
            "ensemble": fpga_net.ensemble,
            "neurons": fpga_net.ensemble.neurons,
            "connection": fpga_net.connection,
        }
        nengo.Probe(probe_map[probe])

    with pytest.raises(nengo.exceptions.BuildError):
        Simulator(net)

    assert super_mock.call_count == 0


def test_nengo_sim():
    """Test using the nengo simulator with an fpga network"""

    # Create a dummy net
    with nengo.Network() as net:
        net.fpga_net = FpgaPesEnsembleNetwork("test", 1, 1, 0.001)

    nengo.Simulator(net)

    assert not net.fpga_net.using_fpga_sim


def test_close(dummy_sim, mocker):
    """Test the Simulator's close function"""

    # Grab test objects from fixture
    net = dummy_sim[0]
    sim = dummy_sim[1]

    # Mock out local and super calls
    close_mock = mocker.patch.object(net, "close")
    super_close_mock = mocker.patch("nengo.simulator.Simulator.close")

    sim.close()

    assert close_mock.call_count == 2
    super_close_mock.assert_called_once()


def test_reset(dummy_sim, mocker):
    """Test the Simulator's reset function"""

    # Grab test objects from fixture
    net = dummy_sim[0]
    sim = dummy_sim[1]

    # Mock out local and super calls
    reset_mock = mocker.patch.object(net, "reset")
    super_reset_mock = mocker.patch("nengo.simulator.Simulator.reset")

    seed = 5
    sim.reset(seed)  # Call with args

    assert reset_mock.call_count == 2
    super_reset_mock.assert_called_once_with(seed)


def test_terminate(dummy_sim, mocker):
    """Test the Simulator's terminate function"""

    # Grab test objects from fixture
    net = dummy_sim[0]
    sim = dummy_sim[1]

    # Mock out calls
    cleanup_mock = mocker.patch.object(net, "cleanup")
    close_mock = mocker.patch.object(sim, "close")

    sim.terminate()

    assert cleanup_mock.call_count == 2
    close_mock.assert_called_once()
