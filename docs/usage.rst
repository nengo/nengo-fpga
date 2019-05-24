*****
Usage
*****

Basic Use
=========

NengoFPGA is an extension of `Nengo core <https://www.nengo.ai/nengo/>`_. Networks
and models are described using traditional Nengo workflow and a single ensemble
with PES learning will be replaced with an FPGA ensemble using the
``FpgaPesEnsembleNetwork``. For example, consider the following network snippet:

.. code-block:: python

   import nengo
   from nengo_fpga.networks import FpgaPesEnsembleNetwork

   with nengo.Network() as model:

      ...

      # Two ensembles of neurons
      pre = nengo.Ensemble(50, 2)
      post = nengo.Ensemble(50, 2)

      # Connect pre to post
      conn = nengo.Connection(pre, post)

      # Create an ensemble for the error signal
      # Error = actual - target = post - pre
      error = nengo.Ensemble(50, dimensions=2)
      nengo.Connection(post, error)
      nengo.Connection(pre, error, transform=-1)

      # Add the learning rule to the connection
      conn.learning_rule_type = nengo.PES(learning_rate=1e-4)

      # Connect the error into the learning rule
      nengo.Connection(error, conn.learning_rule)

      ...

NengoFPGA will replace the learning rule and the ``post`` ensemble to create a
network that looks like this:

.. code-block:: python

   import nengo
   from nengo_fpga.networks import FpgaPesEnsembleNetwork

   with nengo.Network() as model:

      ...

      # Two ensembles of neurons, one standard Nengo, one on the FPGA
      pre = nengo.Ensemble(50, 2)
      post_fpga = FpgaPesEnsembleNetwork('de1', n_neurons=50,
                                         dimensions=2,
                                         learning_rate=1e-4,
                                         label='ensemble')

      # Connect pre to post
      conn = nengo.Connection(pre, post_fpga.input)  # Note the added '.input'

      # Create an ensemble for the error signal
      # Error = actual - target = post - pre
      error = nengo.Ensemble(50, dimensions=2)
      nengo.Connection(post_fpga.output, error)  # Note the added '.output'
      nengo.Connection(pre, error, transform=-1)

      # Connect the error into the learning rule
      nengo.Connection(error, post_fpga.error)  # Note connected to the FPGA

      ...


This is designed to work with Nengo GUI, however you can see `Scripting`_ below
if you prefer not to use the GUI. To view and run your networks, simply pass
``nengo_fpga`` as the backend to Nengo GUI:

.. code-block:: bash

   nengo <my_file.py> -b nengo_fpga

..
   Ensure you've configured your board **and** NengoFPGA as outlined in
   `Configuration`_ above.

For any questions please visit the `Nengo Forum <https://forum.nengo.ai>`_.

.. _scripting:

Scripting
=========

If you are not using Nengo GUI, you can use the ``nengo_fpga`` simulator in
Nengo's scripting environment as well:

.. code-block:: python

   import nengo
   import nengo_fpga

   with nengo.Network() as model:

      ...

   with nengo_fpga.Simulator(model) as sim:
      sim.run(1)

