***
API
***

Setting Parameters
==================

Many of the Nengo ensemble parameters are omitted from the ``FpgaPesEnsembleNetwork``
constructor, but all of these ensemble parameters can easily be changed once an
ensemble is created:

.. code-block:: python

   # First create the ensemble
   ens = FpgaPesEnsembleNetwork(
            'de1', n_neurons=100, dimensions=2, learning_rate=1e-3)

   # Modify ensemble parameters
   ens.ensemble.neuron_type = nengo.neurons.RectifiedLinear()
   ens.ensemble.intercepts = nengo.dists.Choice([-0.5])
   ens.ensemble.max_rates = nengo.dists.Choice([100])

Since our ``FpgaPesEnsembleNetwork`` class also encompasses the connection to
the FPGA ensemble, we can similarly change the connection parameters:

.. code-block:: python

   # Modify connection parameters
   ens.connection.synapse = None
   ens.connection.solver = nengo.solvers.LstsqL2(reg=0.01)

The ``02-mnist_vision_network`` example demonstrates this capability.

.. seealso::
   Check out the Nengo documentation for a full list of `ensemble parameters
   <https://www.nengo.ai/nengo/frontend_api.html#nengo.Ensemble>`_ and
   `connection parameter <https://www.nengo.ai/nengo/frontend_api.html#nengo.Connection>`_.


Supported Neuron Types
======================

Currently NengoFPGA supports the following neuron types:

   - `nengo.RecitifiedLinear <https://www.nengo.ai/nengo/frontend_api.html#nengo.RectifiedLinear>`_
   - `nengo.SpikingRectifiedLinear <https://www.nengo.ai/nengo/frontend_api.html#nengo.SpikingRectifiedLinear>`_


Objects and Functions
=====================

.. todo::
   - Finish docstring for FpgaPesEnsembleNetwork
   - Do we want to add anything else here for autodocs?


.. autoclass:: nengo_fpga.networks.FpgaPesEnsembleNetwork
