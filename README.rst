.. image:: https://www.nengo.ai/design/_images/nengo-fpga-full-light.svg
  :target: https://www.nengo.ai/nengo-fpga
  :alt: NengoFPGA
  :width: 400px

************************
Connecting Nengo to FPGA
************************

NengoFPGA is an extension for `Nengo <https://www.nengo.ai/nengo/>`_ that
connects to FPGA. The current implementation supports a single ensemble of
neurons with the PES learning rule.

You will need a
`supported FPGA device <https://www.nengo.ai/nengo-fpga/supported_hw.html>`_,
then simply replace a standard ensemble with the augmented FPGA ensemble:

.. code-block:: python

   import nengo
   from nengo_fpga.networks import FpgaPesEnsembleNetwork

   # This standard Nengo ensemble...
   ens = nengo.Ensemble(50, 1)

   # ...is replaced with an FPGA ensemble
   fpga_ens = FpgaPesEnsembleNetwork(
        'de1', n_neurons=50, dimensions=1, learning_rate=0)

Check out the rest of the `documentation <https://www.nengo.ai/nengo-fpga/>`_
for more information.
