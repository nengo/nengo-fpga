*****
Usage
*****

Converting from Standard Nengo
==============================

NengoFPGA is an extension of :std:doc:`Nengo core <nengo:index>`.
Networks and models are described using the traditional Nengo workflow and a
single ensemble, including PES learning, can be replaced with an FPGA ensemble
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

       # "Pre" ensemble of neurons, and connection from the input
       pre = nengo.Ensemble(50, 2)
       nengo.Connection(input_node, pre)

       # "Post" ensemble of neurons, and connection from "Pre"
       post = nengo.Ensemble(50, 2)
       conn = nengo.Connection(pre, post)

       # Create an ensemble for the error signal
       # Error = actual - target = "post" - input
       error = nengo.Ensemble(50, 2)
       nengo.Connection(post, error)
       nengo.Connection(input_node, error, transform=-1)

       # Add the learning rule on the pre-post connection
       conn.learning_rule_type = nengo.PES(learning_rate=1e-4)

       # Connect the error into the learning rule
       nengo.Connection(error, conn.learning_rule)

The Nengo code above creates two neural ensembles, ``pre`` and ``post``, and
forms a PES-learning connection between these two ensembles. The weights of
this connection are modulated by an error signal computed by a third neural
ensemble (``error``).

NengoFPGA can be used to replace the ``pre`` ensemble with an ensemble that
will run on the FPGA. Converting the Nengo model above into a NengoFPGA model
proceeds in three steps:

1. Replacing the desired neural ensemble with and FPGA ensemble.
#. Making the appropriate connections to and from the FPGA ensemble.
#. If desired (i.e., if learning is required), making the connections to and
   from an error-computing neural ensemble.

Constructing the FPGA Ensemble
------------------------------

To use the FPGA ensemble, first import the ``FpgaPesEnsembleNetwork`` class:

.. code-block:: python

   from nengo_fpga.networks import FpgaPesEnsembleNetwork

In the code above, the ``pre`` ensemble is to be replaced by the FPGA
ensemble. The standard Nengo code for the ``pre`` ensemble was:

.. code-block:: python

   # "Pre" ensemble of neurons, and connection from the input
   pre = nengo.Ensemble(50, 2)

and this is replaced with the ``FpgaPesEnsembleNetwork`` class. Since learning
is desired in the above model, the learning rule definition on the pre-post
connection (``conn.learning_rule_type = nengo.PES(learning_rate=1e-4)``) has
been removed and rolled into the ``FpgaPesEnsembleNetwork`` constructor.

.. code-block:: python

   # "Pre" ensemble & learning rule
   ens_fpga = FpgaPesEnsembleNetwork('de1', n_neurons=50,
                                     dimensions=2,
                                     learning_rate=1e-4)

Notice that the ``ens_fpga`` ensemble maintains the same arguments as the
original ``pre`` ensemble and the learning rule which it encompasses --
50 neurons, 2 dimensions, and a learning rate of 1e-4. The ``ens_fpga`` has
an additional argument, in this case ``'de1'``, which specifies the desired
FPGA device
(see :ref:`NengoFPGA Software Configuration <nengofpga-config>`
for more details).

Connecting the FPGA Ensemble
----------------------------

With the FPGA ensemble created, the connections to and from the original
``pre`` ensemble will have to be updated. The original connections are defined
as:

.. code-block:: python

   # Connection from input to "pre" ensemble
   nengo.Connection(input_node, pre)

   # Connection from "pre" to "post" ensemble
   conn = nengo.Connection(pre, post)

and are replaced with the slightly modified FPGA versions:

.. code-block:: python

   # Connection from input to "pre" (FPGA) ensemble
   nengo.Connection(input_node, ens_fpga.input)  # Note the added '.input'

   # Connection from "pre" (FPGA) to "post" ensemble
   nengo.Connection(ens_fpga.output, post)  # Note the added '.output'

The NengoFPGA connections are very similar to the original Nengo connections
with the exception that they use the interfaces of the
``FpgaPesEnsembleNetwork`` object.
The ``ens_fpga.input`` and ``ens_fpga.output`` replace the input and output
of the original ``pre`` ensemble.

Connecting the Error Ensemble
-----------------------------

In the original Nengo model, a neural ensemble was used to compute the error
signal that drives the PES learning rule. Using NengoFPGA, this neural
ensemble is still needed, and the only change required is to modify the
connections from this error ensemble to the FPGA ensemble. The original Nengo
model defined the error ensemble and associated connections as:

.. code-block:: python

   # Create an ensemble for the error signal
   # Error = actual - target = "post" - input
   error = nengo.Ensemble(50, 2)
   nengo.Connection(post, error)
   nengo.Connection(input_node, error, transform=-1)

   # Add the learning rule on the pre-post connection
   conn.learning_rule_type = nengo.PES(learning_rate=1e-4)

   # Connect the error into the learning rule
   nengo.Connection(error, conn.learning_rule)

The NengoFPGA equivalent code would be:

.. code-block:: python

   # Create an ensemble for the error signal
   # Error = actual - target = "post" - input
   error = nengo.Ensemble(50, 2)  # Remains unchanged
   nengo.Connection(post, error)  # Remains unchanged
   nengo.Connection(input_node, error, transform=-1)  # Remains unchanged

   # Connect the error into the learning rule
   nengo.Connection(error, ens_fpga.error)  # Note the added '.error'

Note that -- as mentioned previously -- in the NengoFPGA equivalent code, the
``learning_rule_type`` definition of the pre-post connection has been removed
as this is declared in the ``FpgaPesEnsembleNetwork`` object.


Final NengoFPGA Model
---------------------

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

       # "Pre" ensemble of neurons, and connection from the input
       ens_fpga = FpgaPesEnsembleNetwork('de1', n_neurons=50,
                                         dimensions=2,
                                         learning_rate=1e-4)
       nengo.Connection(input_node, ens_fpga.input)  # Note the added '.input'

       # "Post" ensemble of neurons, and connection from "Pre"
       post = nengo.Ensemble(50, 2)
       conn = nengo.Connection(ens_fpga.output, post)  # Note the added '.output'

       # Create an ensemble for the error signal
       # Error = actual - target = "post" - input
       error = nengo.Ensemble(50, 2)
       nengo.Connection(post, error)
       nengo.Connection(input_node, error, transform=-1)

       # Connect the error into the learning rule
       nengo.Connection(error, ens_fpga.error)  # Note the added '.error'


Basic Use
=========

NengoFPGA is designed to work with NengoGUI, however you can see also run
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
NengoGUI:

.. code-block:: bash

   nengo <my_file.py> -b nengo_fpga

This should open the GUI in a browser and display the network from
``my_file.py``. You can begin execution by clicking the play button in the
bottom left corner. this may take a few moments to establish a connection and
initialize the FPGA device.

.. _scripting:

Scripting
=========

If you are not using NengoGUI, you can use the ``nengo_fpga.Simulator`` in
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


Maximum Model Size
==================

When running Nengo models on other hardware there is no set limit to model or
network size. The system will continue to allocate resources (like memory) until
it runs out which leads to different limits depending on the capabilities of
your hardware. On the other hand, the NengoFPGA design is fixed and therefore we
must provision resources up front. As a result, we have specific upper bounds
which are chosen such that the resource allocation balances performance and
flexibility for the given architecture. We store all  neuron parameters on-chip
giving us bounds based on specific memory requirements:

- The maximum number of neurons, *N*, used to allocate memory for things like
  neuron activity and bias.
- The maximum number of representational dimensions (input or output), *D*,
  used to allocate memory for things like the input and output vector.
- The maximum product of neurons and dimensions, *NxD*, used to allocate
  memory for things like encoder and decoder matrices.

These maximum model size values are summarized in the hardware-specific
documentation:

- :ref:`DE1-SoC feasible model size
  <nengo-de1:/appendix.rst#maximum-model-size>`
- :ref:`PYNQ-Z1 / Z2 feasible model size
  <nengo-pynq:/appendix.rst#maximum-model-size>`
