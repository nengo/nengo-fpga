Release History
===============

.. Changelog entries should follow this format:

   version (release date)
   ======================

   **section**

   - One-line description of change (link to Github issue/PR)

.. Changes should be organized in one of several sections:

   - Added
   - Changed
   - Deprecated
   - Removed
   - Fixed

0.2.0 (August 27, 2019)
-----------------------

**Added**

- Add model size bounds to docs.
  (`#31 <https://github.com/nengo/nengo-fpga/pull/31>`__)

- Add example setting encoders/decoders.
  (`#30 <https://github.com/nengo/nengo-fpga/pull/30>`__)

- Add purchase link to docs.
  (`#29 <https://github.com/nengo/nengo-fpga/pull/29>`__)

- Add license to docs.
  (`#25 <https://github.com/nengo/nengo-fpga/pull/25>`__)

- Add firewall tip to docs.
  (`#24 <https://github.com/nengo/nengo-fpga/pull/24>`__)

- Notebook examples and example descriptions.
  (`#23 <https://github.com/nengo/nengo-fpga/pull/23>`__)

- Quickstart guide.
  (`#21 <https://github.com/nengo/nengo-fpga/pull/21>`__)

- Rework documentation.
  (`#18 <https://github.com/nengo/nengo-fpga/pull/18>`__,
  `#20 <https://github.com/nengo/nengo-fpga/pull/20>`__)

- Add PR template, contributors, and update license.
  (`#12 <https://github.com/nengo/nengo-fpga/pull/12>`__)

- Added script to read device DNA from FPGA board.
  (`#11 <https://github.com/nengo/nengo-fpga/pull/11>`__)

**Changed**

- Update the docs theme.
  (`#32 <https://github.com/nengo/nengo-fpga/pull/32>`__)

- Rework usage page in docs.
  (`#27 <https://github.com/nengo/nengo-fpga/pull/27>`__)

- Docs audit for consistency.
  (`#22 <https://github.com/nengo/nengo-fpga/pull/22>`__)

- Rename "DNA" to "ID" everywhere.
  (`#20 <https://github.com/nengo/nengo-fpga/pull/20>`__)

- Receiving a UDP packet with a negative timestep will now cause the Nengo
  simulation to terminate with an exception.
  (`#26 <https://github.com/nengo/nengo-fpga/pull/26>`__)

- Now throwing an exception on unsupported neuron type.
  (`#26 <https://github.com/nengo/nengo-fpga/pull/26>`__)

**Fixed**

- Fixed behaviour of code when provided FPGA name string is not found in the
  fpga_config file.
  (`#33 <https://github.com/nengo/nengo-fpga/pull/33>`__)

- Fixed simulation hanging error when two simulations are run one after the
  other.
  (`#34 <https://github.com/nengo/nengo-fpga/pull/34>`__)


0.1.0 (December 19, 2018)
-------------------------

Initial release of NengoFPGA!
