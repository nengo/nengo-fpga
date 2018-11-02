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
- (optional) `Nengo GUI <https://github.com/nengo/nengo-gui>`_

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

The NengoFPGA config file, ``fpga_config``, is located in the root directory of ``nengo-fpga`` and contains example settings for your host machine as well as the FPGA board you are using. Anything in square brackets (eg. ``[host]``) is defining a new entry name and everything below that name up until the blank line defines parameters of that entry.

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

    # Example DE1 FPGA board configuration
    [de1]
    ip = 10.162.177.236
    port = 22
    user = root
    pwd =
    script = /opt/nengo-de1/nengo_de1/single_pes_net.py
    use_sudo = False
    tmp = /opt/nengo-de1/params
    udp_port = 0

    # Example PYNQ FPGA board configuration
    [pynq]
    ip = 10.162.177.99
    port = 22
    user = xilinx
    pwd = xilinx
    script = /opt/nengo-pynq/nengo_pynq/single_pes_net.py
    use_sudo = True
    tmp = /opt/nengo-pynq/params
    udp_port = 0

For whichever board you are using, make sure the lines in the appropriate sections are uncommented (remove the leading # **and** space so it appears as above). These default values should be correct unless you've modified the settings or installation of your FPGA board. These parameters are described here but modifications of these values will be described in the board-specific documentation.

- **ip**: IP address of the FPGA board.
- **port**: The port used to open ``ssh`` communications between the host and FPGA board.
- **user**: User name to login to the board.
- **pwd**: Password for **user**.
- **script**: The location of the communication script on the FPGA board.
- **use_sudo**: Whether or not to run commands with sudo when executing on the FPGA board.
- **tmp**: Temporary location used to store data as it is transferred between the host and FPGA board.
- **udp_port**: The port used for UDP communications between the host and FPGA board.

.. tip::
  If any, the most likely change would be to the IP address.


Usage
=====

.. note::
  Ensure you've configured your board **and** NengoFPGA as outlined in `Configuration`_ above.


For any questions visit the `Nengo Forum <https://forum.nengo.ai>`_.

Examples
--------

NengoFPGA ships with a few example implementations in the ``nengo-fpga/docs/examples`` folder. These examples are designed to be used with Nengo GUI, so first we will install that.

1. Install the GUI with ``pip install nengo-gui``.
#. In a terminal window, navigate to the ``nengo-fpga/docs/examples`` directory.
#. Try running an example with ``nengo <file name> -b nengo_fpga``. This should open the Nengo GUI interface in a browser and display the code on the right and a graphical representation on the left.
#. Near the top of the file you should see `` --- BOARD SELECT --- ``, select th appropriate board here. (In fact, the ``de1`` and ``pynq`` correspond to the headers in the ``fpga_config`` file).
#. Click the play button in the bottom right to start the simulation. It may take several seconds to build the model and begin running.

Basic Use
---------

.. todo::
  Explain this better, maybe show two ensembles and a learning connection being replaced with an FPGA ens?

This is an extension of `Nengo core <https://github.com/nengo/nengo>`_, networks and models are described using traditional Nengo workflow and a single ensemble will be replaced with an FPGA ensemble using the ``FpgaPesEnsembleNetwork``:

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


This is designed to work with Nengo GUI, however you can see `Scripting`_ below if you prefer not to use the GUI. To view and run your networks, simply pass ``nengo_fpga`` as the backend to Nengo GUI.

.. code-block:: bash

   nengo <my_file.py> -b nengo_fpga


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

