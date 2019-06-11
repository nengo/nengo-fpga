*****
Usage
*****

Converting from Standard Nengo
==============================

NengoFPGA is an extension of `Nengo core <https://www.nengo.ai/nengo/>`_.
Networks and models are described using the traditional Nengo workflow and a
single ensemble, including PES learning, will be replaced with an FPGA ensemble
using the ``FpgaPesEnsembleNetwork`` class. For example, consider the following
example of a learned communication channel built with standard Nengo:

.. code-block:: python

   import nengo
   import numpy as np


   def input_func(t):
       return [np.sin(t * 2*np.pi), np.cos(t * 2*np.pi)]

   with nengo.Network() as model:

      # Input stimulus
      input_node = nengo.Node(input_func)

      # Two ensembles of neurons
      pre = nengo.Ensemble(50, 2)
      post = nengo.Ensemble(50, 2)

      # Connect input, pre, and post
      nengo.Connection(input_node, pre)
      conn = nengo.Connection(pre, post)

      # Create an ensemble for the error signal
      # Error = actual - target = post - pre
      error = nengo.Ensemble(50, 2)
      nengo.Connection(post, error)
      nengo.Connection(pre, error, transform=-1)

      # Add the learning rule on the pre-post connection
      conn.learning_rule_type = nengo.PES(learning_rate=1e-4)

      # Connect the error into the learning rule
      nengo.Connection(error, conn.learning_rule)


NengoFPGA will replace the learning rule and the ``post`` ensemble and run
them on the FPGA. First we need to import the ``FpgaPesEnsembleNetwork``:

.. code-block:: python

   from nengo_fpga.networks import FpgaPesEnsembleNetwork

Now we can use this class to replace pieces of our Nengo network and offload
them to the FPGA. From the standard Nengo model we replace the following pieces

.. code-block:: python

   # Post-synaptic ensemble
   post = nengo.Ensemble(50, 2)

   # Learning rule on the pre-post connection
   conn.learning_rule_type = nengo.PES(learning_rate=1e-4)

with the NengoFPGA counterparts

.. code-block:: python

   # Post-synaptic ensemble & learning rule
   post_fpga = FpgaPesEnsembleNetwork('de1', n_neurons=50,
                                      dimensions=2,
                                      learning_rate=1e-4)


Notice that the ``post_fpga`` ensemble maintains the same arguments as the
original ``post`` ensemble and the learning rule which it encompasses --
50 neurons, 2 dimensions, and a learning rate of 1e-4. The ``post_fpga`` has
an additional argument, in this case ``'de1'``, which specifies the desired
FPGA device
(see :ref:`NengoFPGA Software Configuration <nengofpga-config>`
for more details).

Now that we've replaced the post-synaptic ensemble and the learning rule with
the new ``post_fpga`` ensemble, we will need to update the connections as well.
The original connections

.. code-block:: python

   # Connection from pre- to post-synaptic ensembles
   conn = nengo.Connection(pre, post)

   # Connection from post-synaptic ensemble to error
   nengo.Connection(post, error)

   # Connection from error into the learning rule
   nengo.Connection(error, conn.learning_rule)

are replaced with the slightly modified FPGA versions

.. code-block:: python

   # Connection from pre- to post-synaptic ensembles
   nengo.Connection(pre, post_fpga.input)  # Note the added '.input'

   # Connection from post-synaptic ensemble to error
   nengo.Connection(post_fpga.output, error)  # Note the added '.output'

   # Connection from error into the learning rule
   nengo.Connection(error, post_fpga.error)  # Note connected to the FPGA

These NengoFPGA connections are very similar to the original Nengo connections
except now we are using the interfaces of the ``FpgaPesEnsembleNetwork`` object.
The ``poast_fpga.input`` and ``post_fpga.output`` replace the input and output
of the original ``post`` ensemble and the ``post_fpga.error`` interface replaces
the connection into the learning rule, which is now encompassed in the
``post_fpga`` object.

Altogether the NengoFPGA version of the learned communication channel would
look something like this:

.. code-block:: python

   import nengo
   import numpy as np

   from nengo_fpga.networks import FpgaPesEnsembleNetwork

   def input_func(t):
       return [np.sin(t * 2*np.pi), np.cos(t * 2*np.pi)]

   with nengo.Network() as model:

      # Input stimulus
      input_node = nengo.Node(input_func)

      # Two ensembles of neurons, one standard Nengo, one on the FPGA
      pre = nengo.Ensemble(50, 2)
      post_fpga = FpgaPesEnsembleNetwork('de1', n_neurons=50,
                                         dimensions=2,
                                         learning_rate=1e-4)

      # Connect input, pre, and post
      nengo.Connection(input_node, pre)
      nengo.Connection(pre, post_fpga.input)  # Note the added '.input'

      # Create an ensemble for the error signal
      # Error = actual - target = post - pre
      error = nengo.Ensemble(50, dimensions=2)
      nengo.Connection(post_fpga.output, error)  # Note the added '.output'
      nengo.Connection(pre, error, transform=-1)

      # Connect the error into the learning rule
      nengo.Connection(error, post_fpga.error)  # Note connected to the FPGA



Basic Use
=========

NengoFPGA is designed to work with Nengo GUI, however you can see also run
as a script if you prefer not to use the GUI. In either case, if the FPGA device
is not correctly configured, or the NengoFPGA backend is not selected, the
``FpgaPesEnsembleNetwork`` will be converted to run as standard Nengo objects
and a warning will be printed.

For any questions please visit the `Nengo Forum <https://forum.nengo.ai>`_.

.. note::
   Ensure you've configured your board **and** NengoFPGA as outlined in the
   :ref:`Getting Started Guide <quick-guide>`.


Using the GUI
-------------

To view and run your networks, simply pass ``nengo_fpga`` as the backend to
Nengo GUI:

.. code-block:: bash

   nengo <my_file.py> -b nengo_fpga

This should open the GUI in a browser and display the network from
``my_file.py``. You can begin execution by clicking the play button in the bottom left corner. this may take a few moments to establish a connection and
initialize the FPGA device.

.. _scripting:

Scripting
=========

If you are not using Nengo GUI, you can use the ``nengo_fpga.Simulator`` in
Nengo's scripting environment as well. Consider the following example of
running a standard Nengo network:

.. code-block:: python

   import nengo

   with nengo.Network() as model:

      # Your network description...

   with nengo.Simulator(model) as sim:
      sim.run(1)

Simply replace the ``Simulator`` with the one from NengoFPGA:

.. code-block:: python

   import nengo
   import nengo_fpga

   with nengo.Network() as model:

      # Your network description...
      # Including an FpgaPesEnsembleNetwork

   with nengo_fpga.Simulator(model) as sim:
      sim.run(1)
