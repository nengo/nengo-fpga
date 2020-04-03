"""Tests for the full nengo-fpga stack including all supported devices"""

import pytest
import numpy as np

import nengo
from nengo.solvers import NoSolver

import nengo_fpga
from nengo_fpga.networks import FpgaPesEnsembleNetwork


# Mark all as fullstack, and add device parameter
pytestmark = [pytest.mark.fullstack, pytest.mark.parametrize("device", ["pynq", "de1"])]

# Tell Nengo to use 32b, like the FPGA
nengo.rc.set("precision", "bits", "32")


def test_ff_learn(params, device):
    """Feedforward test with decoders initialized to 0 and learning"""

    l_rate = 0.001
    stim_val = 0.25
    tol = 0.001
    if isinstance(params["neuron"], nengo.SpikingRectifiedLinear):
        tol *= 2
    p_syn = 0.05

    with nengo.Network() as net:
        stim = nengo.Node([stim_val] * params["dims_in"])  # Input node

        # Nengo reference
        ens = nengo.Ensemble(
            params["n_neurons"],
            params["dims_in"],
            neuron_type=params["neuron"],
            bias=params["bias"],
            encoders=params["encoders"],
            gain=params["gain"],
        )
        output = nengo.Node(size_in=params["dims_out"])
        nengo_err = nengo.Node(size_in=params["dims_out"])

        nengo.Connection(stim, ens)
        conn = nengo.Connection(
            ens,
            output,
            solver=NoSolver(np.zeros((params["n_neurons"], params["dims_out"]))),
            function=params["func"],
            learning_rule_type=nengo.PES(l_rate),
        )
        nengo.Connection(stim, nengo_err, function=params["func"], transform=-1)
        nengo.Connection(output, nengo_err)
        nengo.Connection(nengo_err, conn.learning_rule)

        p_nengo = nengo.Probe(output, synapse=p_syn)

        # FPGA
        fpga = FpgaPesEnsembleNetwork(
            device,
            params["n_neurons"],
            params["dims_in"],
            l_rate,
            function=params["func"],
        )
        fpga.connection.solver = NoSolver(np.zeros(params["decoders"].shape).T)
        fpga.ensemble.neuron_type = params["neuron"]
        fpga.ensemble.encoders = params["encoders"]
        fpga.ensemble.bias = params["bias"]
        fpga.ensemble.gain = params["gain"]
        fpga_err = nengo.Node(size_in=params["dims_out"])

        nengo.Connection(stim, fpga.input)
        nengo.Connection(stim, fpga_err, function=params["func"], transform=-1)
        nengo.Connection(fpga.output, fpga_err)
        nengo.Connection(fpga_err, fpga.error)

        p_fpga = nengo.Probe(fpga.output, synapse=p_syn)

    with nengo_fpga.Simulator(net) as sim:
        sim.run(1)

    assert fpga.config_found and fpga.using_fpga_sim  # Ensure real FPGA

    idx = 2 if device == "de1" else 1  # Compensate for DE1 off-by-one
    assert np.allclose(sim.data[p_fpga][-1], sim.data[p_nengo][-idx], atol=tol)


def test_ff_no_learn(params, device):
    """Feedforward test with solved decoders and no learning"""

    tol = 0.005
    if isinstance(params["neuron"], nengo.SpikingRectifiedLinear):
        tol *= 2
    stim_val = 0.25
    p_syn = 0.05

    with nengo.Network() as net:
        stim = nengo.Node([stim_val] * params["dims_in"])  # Input node

        # Nengo reference
        ens = nengo.Ensemble(
            params["n_neurons"],
            params["dims_in"],
            neuron_type=params["neuron"],
            bias=params["bias"],
            encoders=params["encoders"],
            gain=params["gain"],
        )
        output = nengo.Node(size_in=params["dims_out"])

        nengo.Connection(stim, ens)
        nengo.Connection(
            ens, output, function=params["func"], solver=NoSolver(params["decoders"].T)
        )

        p_nengo = nengo.Probe(output, synapse=p_syn)

        # FPGA
        fpga = FpgaPesEnsembleNetwork(
            device, params["n_neurons"], params["dims_in"], 0, function=params["func"]
        )
        fpga.connection.solver = NoSolver(params["decoders"].T)
        fpga.ensemble.neuron_type = params["neuron"]
        fpga.ensemble.encoders = params["encoders"]
        fpga.ensemble.bias = params["bias"]
        fpga.ensemble.gain = params["gain"]

        nengo.Connection(stim, fpga.input)

        p_fpga = nengo.Probe(fpga.output, synapse=p_syn)

    with nengo_fpga.Simulator(net) as sim:
        sim.run(1)

    assert fpga.config_found and fpga.using_fpga_sim  # Ensure real FPGA

    idx = 2 if device == "de1" else 1  # Compensate for DE1 off-by-one
    assert np.allclose(sim.data[p_fpga][-1], sim.data[p_nengo][-idx], atol=tol)


def test_feedback(params, device):
    """Feedback test with solved decoders"""

    stim_val = 0.5
    tol = 0.005
    if isinstance(params["neuron"], nengo.SpikingRectifiedLinear):
        tol *= 2
    tau = 0.05
    p_syn = 0.05

    def stim_func(t):
        """Return value for the first 1 second of simulation"""
        val = stim_val * tau if t < 1 else 0
        return [val] * params["dims_in"]

    with nengo.Network() as net:
        stim = nengo.Node(stim_func)  # Input node

        # Nengo reference
        ens = nengo.Ensemble(
            params["n_neurons"],
            params["dims_in"],
            neuron_type=params["neuron"],
            bias=params["bias"],
            encoders=params["encoders"],
            gain=params["gain"],
        )
        output = nengo.Node(size_in=params["dims_out"])

        nengo.Connection(stim, ens)
        nengo.Connection(
            ens, output, function=params["func"], solver=NoSolver(params["decoders"].T)
        )
        nengo.Connection(
            ens,
            ens,
            solver=NoSolver(
                np.concatenate(
                    (params["decoders"], np.zeros(params["decoders"].shape))
                ).T
            ),
            synapse=tau,
        )

        p_nengo = nengo.Probe(output, synapse=p_syn)

        # FPGA
        fpga = FpgaPesEnsembleNetwork(
            device,
            params["n_neurons"],
            params["dims_in"],
            0,
            function=params["func"],
            feedback=1,
        )
        fpga.connection.solver = NoSolver(params["decoders"].T)
        fpga.ensemble.neuron_type = params["neuron"]
        fpga.ensemble.encoders = params["encoders"]
        fpga.ensemble.bias = params["bias"]
        fpga.ensemble.gain = params["gain"]
        fpga.feedback.synapse = tau
        fpga.feedback.solver = NoSolver(
            np.concatenate((params["decoders"], np.zeros(params["decoders"].shape))).T
        )

        nengo.Connection(stim, fpga.input)

        p_fpga = nengo.Probe(fpga.output, synapse=p_syn)

    with nengo_fpga.Simulator(net) as sim:
        sim.run(1)

    assert fpga.config_found and fpga.using_fpga_sim  # Ensure real FPGA

    idx = 2 if device == "de1" else 1  # Compensate for DE1 off-by-one
    assert np.allclose(sim.data[p_fpga][-1], sim.data[p_nengo][-idx], atol=tol)
