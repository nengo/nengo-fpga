***************
Getting Started
***************

Things You Need
===============

- `Nengo <https://www.nengo.ai/nengo/getting_started.html>`_
- A :ref:`supported FPGA board <supported-hardware>`
- (Optional) `Nengo GUI <https://github.com/nengo/nengo-gui>`_

.. _quick-guide:

Installation Quick Reference Guide
==================================

Placeholder


.. _software-install:

NengoFPGA Software Installation
===============================

Download the NengoFPGA source code from github using git::

   git clone https://github.com/nengo/nengo-fpga.git

or navigate to the `repository <https://github.com/nengo/nengo-fpga>`_ and download the files manually. Once downloaded, navigate to the ``nengo-fpga`` folder in a terminal window and install with::

   pip install -e .

.. _board-setup:

FPGA Board Setup
================

Follow docs for your particular FPGA device:

- `Terasic DE1-SoC <https://www.nengo.ai/nengo-de1/getting_started.html>`_ (Intel Cyclone V)
- `Digilent PYNQ <https://www.nengo.ai/nengo-pynq/getting_started.html>`_ (Xilinx Zynq)

The full list of hardware that NengoFPGA supports, and the links to their
respective documentation can be found :ref:`here <supported-hardware>`.

.. _nengofpga-config:

NengoFPGA Software Configuration
================================

NengoFPGA is the frontend that connects to one of many backend FPGA devices.
You will need to have a :ref:`supported FPGA board <supported-hardware>` with access
to ABR designs. Each FPGA board will have it's own setup and configuration
procedure outlined in it's own documentation, however, the NengoFPGA frontend
has its own configuration as outlined below.

The NengoFPGA default config file, `fpga_config`, is located in the root
directory of `nengo-fpga` and contains example settings for your host machine
as well as the FPGA board you are using. You can also create a copy in the
directory in which your project files are located. Anything in square brackets
(eg. `[host]`) defines a new entry name and everything below that name up
until the name defines parameters of that entry.

Host
----

First we will look at the host configuration; this is information about your
computer and must be called `[host]`:

.. code-block:: none

   [host]
   ip = 10.162.177.10

Make sure these lines are uncommented (remove the leading # **and** space so it
appears as above). This is just an example value for `ip`, you will need to
replace this with your computer's actual IP address, see :ref:`ip-addr` for
instructions on finding your IP address.

.. note::
   Your computer IP address will need to be in the same subnet as the board IP
   address, follow your board specific instructions to get the board IP and
   setup your computer IP before proceeding.

FPGA Board
----------

.. do we want any of this in the board-specific repos?

The entries that define the FPGA board parameters have more values than the
host entry, the name (eg. `[pynq]`) can be anything, though we recommend
using a descriptive name such as `[pynq]` or `[de1]`.

.. code-block:: none

   # Example DE1 FPGA board configuration
   [de1]
   ip = 10.162.177.236
   ssh_port = 22
   ssh_user = root
   ssh_pwd =
   # Refer to the online documentation for SSH key configuration options
   remote_script = /opt/nengo-de1/nengo_de1/single_pes_net.py
   id_script = /opt/nengo-de1/nengo_de1/id_script.py
   remote_tmp = /opt/nengo-de1/params
   udp_port = 0

   # Example PYNQ FPGA board configuration
   [pynq]
   ip = 10.162.177.99
   ssh_port = 22
   ssh_user = xilinx
   ssh_pwd = xilinx
   # Refer to the online documentation for SSH key configuration options
   remote_script = /opt/nengo-pynq/nengo_pynq/single_pes_net.py
   id_script = /opt/nengo-pynq/nengo_pynq/id_script.py
   remote_tmp = /opt/nengo-pynq/params
   udp_port = 0

For whichever board you are using, make sure the lines in the appropriate
sections are uncommented (remove the leading # *and* space so it
appears as above). These default values should be correct unless you've
modified the settings or installation of your FPGA board. These parameters are
described here but modifications of these values will be described in the
board-specific documentation.

- **ip**: IP address of the FPGA board.
- **ssh_port**: The port used to open SSH communications between the host
  and FPGA board.
- **ssh_user**: SSH username to use to login to the board.
- **ssh_pwd**: Password for `ssh_user` to use to login to the board. Note
  that the `fpga_config` file supports the use of SSH keys
  (see :ref:`ssh-key`) as an alternate form of authentication.
- **remote_script**: The location of the main communication script on the FPGA
  board.
- **id_script**: The location of the script that extracts the unique device
  identifier.
- **remote_tmp**: Temporary location used to store data as it is transferred
  between the host and FPGA board.
- **udp_port**: The port used for UDP communications between the host and FPGA
  board.

.. note::
   It should be noted that the FPGA board should be configured such that
   non-root users do not require a password to perform ``sudo`` commands.
   Refer to the respective FGPA board documentation for instructions on how to
   do this.

Copy Protection
===============

Our hardware design (known as the bitstream) is locked to a specific device.
Each bitstream is compiled with your unique board identifier (called Device ID)
and therefore you will need to provide this unique ID to us before we
can compile and deliver your tailored bitstream.

Reading Device ID
------------------

To easily read your Device ID, first ensure you have setup your board to be
NengoFPGA ready. Instructions on how to do this can be found in each board's
respective documentation (see :ref:`Board Setup <board-setup>`). Additionally, ensure
you have reviewed the :ref:`NengoFPGA configuration <nengofpga-config>` section,
and appropriately modified the `fpga_config` file.

Once done, simply run the `dna_extractor.py` script located in the `nengo_fpga`
directory from within the `nengo-fpga` root folder. This will print the Device
ID as well as save it to a file for future reference. The script requires that
you provide the name of your board as it appears in the `fpga_config` file.
For example, from the root directory (`nengo-fpga`) run::

   python nengo_fpga/dna_extractor.py pynq
