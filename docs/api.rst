***
API
***

Setting Parameters
==================

Many of the Nengo ensemble parameters are omitted from the
``FpgaPesEnsembleNetwork`` constructor, but all of these ensemble parameters can
easily be changed once an ensemble is created:

.. code-block:: python

   # First create the ensemble
   ens = FpgaPesEnsembleNetwork(
            'de1', n_neurons=100, dimensions=2, learning_rate=1e-3)

   # Modify ensemble parameters
   ens.ensemble.neuron_type = nengo.neurons.RectifiedLinear()
   ens.ensemble.intercepts = nengo.dists.Choice([-0.5])
   ens.ensemble.max_rates = nengo.dists.Choice([100])

Since our ``FpgaPesEnsembleNetwork`` class also encompasses the connection from
the FPGA ensemble, we can similarly change the connection parameters:

.. code-block:: python

   # Modify connection parameters
   ens.connection.synapse = None
   ens.connection.solver = nengo.solvers.LstsqL2(reg=0.01)

The ``02-mnist_vision_network`` example demonstrates this capability.

If a recurrent connection exists, we can similarly modify that connection:

.. code-block:: python

   # Modify connection parameters
   ens.feedback.synapse = 0.05
   ens.feedback.function = lambda x: x*0.5


.. seealso::
   Check out the Nengo documentation for a full list of `ensemble parameters
   <nengo.Ensemble>` and
   `connection parameters <nengo.Connection>`.


Supported Neuron Types
======================

Currently NengoFPGA supports the following neuron types:

- `nengo.RecitifiedLinear <nengo.RectifiedLinear>`
- `nengo.SpikingRectifiedLinear <nengo.SpikingRectifiedLinear>`


Objects and Functions
=====================

.. autoclass:: nengo_fpga.networks.FpgaPesEnsembleNetwork
