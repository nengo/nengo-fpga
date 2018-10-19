***************
Getting Started
***************

Installation
============

Download the NengoFPGA source code from github using git::

    git clone https://github.com/nengo/nengo-fpga.git

or navigate to the `repository <https://github.com/nengo/nengo-fpga>`_ and download the files manually. Once downloaded, navigate to the ``nengo-fpga`` folder in a terminal window and install with::

    python setup.py install

.. NengoFPGA can be easily installed with pip:

.. .. code-block:: bash

..   pip install nengo-fpga

Requirements
------------

- Nengo
- A :doc:`supported FPGA board <supported_hw>`

Developer Install
-----------------

If you want to modify NengoFPGA, or get the very latest updates,
you will need to perform a developer installation, simply replace ``install`` with ``develop`` when running setup::

    python setup.py develop

.. .. code-block:: bash

..   git clone https://github.com/nengo/nengo-fpga.git
..   pip install -e ./nengo-fpga

Configuration
=============

NengoFPGA is the frontend that connects to one of many backend FPGA devices.
You will need to have a :doc:`supported FPGA board <supported_hw>` with access to ABR designs. Each FPGA board will have it's own setup and configuration procedure outlined in it's own documentation, however, this NengoFPGA frontend has its own configuration file as well.


FPGA Board Setup
----------------

Follow docs for your particular FPGA device:

- `Terasic DE1-SoC <https://www.nengo.ai/nengo-de1>`_ (Intel Cyclone V)
- `Digilent PYNQ <https://www.nengo.ai/nengo-pynq>`_ (Xilinx Zynq)


NengoFPGA Frontend Config
-------------------------

The ``fpga_config`` file contains example settings for your host machine as well as the FPGA board you are using. Anything in square brackets (eg. ``[host]``) is defining a new entry name and everything below that name up until the blank line defines parameters of that entry.

Host
^^^^

First we will look at the host configuration; this is information about your computer and must be called ``[host]``:

.. code-block:: none

   [host]
   ip = 10.162.177.10

Make sure these lines are uncommented (remove the leading # **and** space so it appears as above). This is just an example value for ``ip``, you will need to replace this with your computer's actual IP address, see :ref:`ip-addr` for instructions on finding your IP address.

.. note::
  Your computer IP address will need to be in the same range as the board IP address, follow your board specific instructions to get the board IP and setup your computer IP before proceeding.

FPGA Board
^^^^^^^^^^

.. do we want any of this in the board-specific repos?

The entries that define the FPGA board parameters have more values than the host entry, however the name (eg. ``[pynq]``) can be anything, though we recommend using a descriptive name such as ``[pynq]`` or ``[de1]``.

.. code-block:: none

   [pynq]
   ip = 10.162.177.99
   port = 22
   user = xilinx
   pwd = xilinx
   script = /opt/nengo-pynq/nengo_pynq/single_pes_net.py
   use_sudo = True
   tmp = /opt/nengo-pynq/params
   udp_port = 0

Make sure these lines are uncommented (remove the leading # **and** space so it appears as above).  Most of these default values should be correct unless you've modified the settings or installation of your FPGA board. These parameters are described here but modifications of these values will be described in the board-specific documentation.

- **ip**: IP address of the FPGA board.
- **port**: The port used to open ``ssh`` communications between the host and FPGA board.
- **user**: User name to login to the board.
- **pwd**: Password for **user**.
- **script**: The location of the communication script on the FPGA board.
- **use_sudo**: Whether or not to run commands with sudo when executing on the FPGA board.
- **tmp**: Temporary location used to store data as it is transferred between the host and FPGA board.
- **udp_port**: The port used for UDP communications between the host and FPGA board.


Usage
=====

This is an extension of :ref: `Nengo core <nengo>`, Networks and models are described using traditional Nengo workflow and a single ensemble will be replaced with an FPGA ensemble using the ``FpgaPesEnsembleNetwork``:

.. code-block:: python

   import nengo
   from nengo_fpga.networks import FpgaPesEnsembleNetwork

   with nengo.Network() as model:

      ...

      fpga_ens = FpgaPesEnsembleNetwork('de1', n_neurons=50,
                                        dimensions=2,
                                        learning_rate=0,
                                        label='ensemble')

      ...


And to view and run your networks, simply pass ``nengo_fpga`` as the backend to Nengo GUI:

.. code-block:: bash

   nengo <my_file.py> -b nengo_fpga

Take a look at the examples that ship with the NengoFPGA package. For any questions visit the `Nengo Forum <https://forum.nengo.ai>`_.


Scripting
---------

If you are not using Nengo GUI you can use the ``nengo_fpga`` simulator in the scripting environment as well:

.. code-block:: python

   import nengo
   import nengo_fpga

   with nengo.Network() as model:

      ...

   with nengo_fpga.simulator(model) as sim:
      sim.run(1)

