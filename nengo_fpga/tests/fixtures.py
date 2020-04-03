# pylint: disable=redefined-outer-name
"""Test fixtures used in the test suite"""
import os
import pytest
import numpy as np

import nengo
import nengo_fpga
from nengo_fpga.id_extractor import IDExtractor
from nengo_fpga import fpga_config
from nengo_fpga.simulator import Simulator
from nengo_fpga.networks import FpgaPesEnsembleNetwork


@pytest.fixture  # noqa: C901
def gen_configs(request):
    """Helper fixture to generate and cleanup some dummy configs"""

    class MyConfigs:
        """To keep track of configs we generate"""

        def __init__(self):
            self.default_contents = {"config": {"a": "1", "b": "2", "c": "3"}}

            self.rm_dirs = []  # Keep track of dirs we create
            self.configs = []  # Keep track of configs we create

        def create_config(self, fname, contents=None):
            """Create a dummy config

            `fname` - str
                The full filepath and file name used for the config
            `sections` = list of str
                List of sections to create in the config file
            `contents` = list of dict
                Contents to use for each section
            """
            if contents is None:
                contents = self.default_contents

            d_name = os.path.dirname(fname)
            # Create directory if needed
            if not os.path.isdir(d_name):
                os.makedirs(d_name)
                self.rm_dirs.append(d_name)

            # If a config exists here, create a backup
            if os.path.isfile(fname):
                os.rename(fname, fname + ".bak")

            # Write config file
            with open(fname, "w") as f:
                self.configs.append(fname)
                for sec, content in contents.items():
                    f.write("[{}]\n".format(sec))
                    for k, v in content.items():
                        f.write("{} = {}\n".format(k, v))
                    f.write("\n")

        def cleanup(self):
            """Cleanup the configs we made"""

            # Cleanup files
            for f in self.configs:
                if os.path.isfile(f):  # Removed in some tests before this
                    os.remove(f)  # Delete dummy configs
                if os.path.isfile(f + ".bak"):
                    os.rename(f + ".bak", f)  # Restore original config if any

            # Cleanup directories (currently only does leaf dir, no parents)
            for d in self.rm_dirs:
                os.rmdir(d)

    dummy_configs = MyConfigs()

    def teardown(configs=dummy_configs):
        """Run cleanup code on test exit"""
        configs.cleanup()
        nengo_fpga.fpga_config.reload_config()  # Reload previous config

    # Add cleanup to teardown
    request.addfinalizer(teardown)

    return dummy_configs


@pytest.fixture
def config_contents():
    """Config contents used to test the ID Extractor class"""

    # We omit ssh_key and ssh_pwd as they will be tested separately
    contents = {
        "host": {"ip": "1.2.3.4"},
        "test-fpga": {
            "udp_port": "0",
            "ssh_port": "1",
            "ip": "5.6.7.8",
            "ssh_user": "McTester",
            "id_script": "id_script.py",
            "remote_script": "pes_script.py",
            "remote_tmp": "/test/dir",
        },
    }

    return contents


@pytest.fixture
def dummy_extractor(config_contents, gen_configs, mocker):  # noqa: W0521
    """Setup an ID extractor

        `config_contents` was kept separate so we can update the config file
    """

    # Create a dummy config for testing
    fname = os.path.join(os.getcwd(), "test-config")
    fpga_name = list(config_contents.keys())[1]

    gen_configs.create_config(fname, contents=config_contents)
    fpga_config.reload_config(fname)

    # Don't actually connect the socket in init
    mocker.patch("socket.socket.bind")
    mocker.patch("socket.socket.listen")

    return IDExtractor(fpga_name)


@pytest.fixture
def dummy_net(config_contents, gen_configs):  # noqa: W0521
    """Setup an FPGA network

        `config_contents` was kept separate so we can update the config file
    """

    # Create a dummy config for testing
    fname = os.path.join(os.getcwd(), "test-config")
    fpga_name = list(config_contents.keys())[1]

    gen_configs.create_config(fname, contents=config_contents)
    fpga_config.reload_config(fname)

    return FpgaPesEnsembleNetwork(fpga_name, 1, 1, 0.001)


@pytest.fixture
def dummy_sim(mocker):
    """Setup dummy network and simulator"""

    class DummyNet:
        """Dummy network class with token functions"""

        def close(self):
            """Dummy close function"""

        def reset(self):
            """Dummy reset function"""

        def cleanup(self):
            """Dummy cleanup function"""

    my_net = DummyNet()

    # Don't actually spin up a simulator
    mocker.patch.object(Simulator, "__init__", return_value=None)

    sim = Simulator(my_net)  # Using `my_net` as a dummy arg. init is mocked
    sim.fpga_networks_list = [my_net, my_net]

    # Simulator cleanup was complaining these weren't defined
    sim.closed = False
    sim.model = None

    return my_net, sim


@pytest.fixture
def dummy_com():
    """Dummy class to mock out ssh channel and socket

       Some socket functions are readonly and require a mock class
    """

    class DummyCom:
        """Dummy ssh channel"""

        def send(self, *args):
            """Dummy send functions"""

        def put(self, *args):
            """Dummy send functions"""

        def recv(self, *args):
            """Dummy recv function"""

        def close(self):
            """Dummy close function"""

        def accept(self):
            """Dummy accept function"""

        def sendto(self, *args):
            """Dummy sendto function"""

        def recv_into(self, *args):
            """Dummy recv_into function"""

    return DummyCom


@pytest.fixture(params=[nengo.RectifiedLinear(), nengo.SpikingRectifiedLinear()])
def params(request):  # pragma: no cover
    """Create a dummy network and extract params for fullstack tests

        Fixture itself is parametrized for neuron type
    """

    # Tell Nengo to use 32b, like the FPGA
    nengo.rc.set("precision", "bits", "32")

    # Arbitrary params (keep `my_func` in mind if changing dims)
    neuron = request.param
    n_neurons = 200
    dims_out = 2
    dims_in = 2 * dims_out
    seed = 10

    def my_func(x):
        """Define function that maps input dims to output dims"""

        half = int(len(x) / 2)
        # Add dims 1 + 3, 2+ 4
        return np.add(x[:half], x[half:])

    with nengo.Network(seed=seed) as param_net:
        stim = nengo.Node([0.25] * dims_in)
        a = nengo.Ensemble(n_neurons, dims_in, neuron_type=neuron)
        b = nengo.Node(size_in=dims_out)
        nengo.Connection(stim, a, synapse=None)
        conn = nengo.Connection(
            a, b, function=lambda x: x[:dims_out] + x[dims_out:], synapse=None
        )

    with nengo.Simulator(param_net) as param_sim:
        bias = param_sim.data[a].bias
        decoders = param_sim.data[conn].weights
        encoders = param_sim.data[a].encoders
        gain = param_sim.data[a].gain

    # Return params to be used in fullstack tets
    params = {
        "bias": bias,
        "decoders": decoders,
        "encoders": encoders,
        "gain": gain,
        "func": my_func,
        "n_neurons": n_neurons,
        "dims_in": dims_in,
        "dims_out": dims_out,
        "neuron": neuron,
    }

    return params
