***************
Getting Started
***************

Installation
============

Maybe package for pip

Requirements
------------

- Nengo
- supported board
   - or you can use a dummy interface (is this working?)

Developer Install
-----------------

If you want to modify NengoFPGA, or get the very latest updates,
you will need to perform a developer installation:

.. code-block:: bash

  git clone https://github.com/nengo/nengo-fpga.git
  pip install -e ./nengo-fpga

Configuration
=============

nengo-fpga is the frontend that connects to one of many backend FPGA devices.
You will need to have a supported board with access to ABR designs.
Each FPGA board will have it's own setup and configuration procedure and then we will tie that to the configuration of the ``nengo-fpga`` frontend.


FPGA Board
----------

Follow docs for your particular FPGA device. Point to repos? not sure the plan here

.. todo::
   Pointing to hardware: How are we granting access to the hardware backend repos?


fpga_config
-----------

- square brackets are settings/section names
- explain some stuff a bit here
- maybe put some stuff in an 'advanced' section?


.. todo::
   Host side config: May be different depending on if we are using a network or directly connected to the board?

- Get ``[host]`` ip with ``ifconfig``/``ipconfig`` (all platforms)
- update ip address
- uncomment (remove hash **and** space) for lns 4,5
- get IP from device either DE1 or PYNQ from board setup (external docs)
- update ip, change ports if required
- uncomment (remove hash **and** space) device settings



Usage
=====

- import nengo_fpga
- make an ensemble

.. code-block:: python

   fpga_ens = FpgaPesEnsembleNetwork(
        'de1', n_neurons=50, dimensions=2, learning_rate=0, label='ensemble')

Check out examples


Scripting
---------

Use the ``nengo_fpga`` simulator

.. code-block:: python

   ...

   with nengo_fpga.simulator(model)


GUI
---

Simply tell the GUI to use the ``nengo_fpga`` backend simulator:

.. code-block:: bash

   nengo <my_file.py> -b nengo_fpga
