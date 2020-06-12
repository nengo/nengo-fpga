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

0.2.3 (Unreleased)
------------------

**Added**

- Added slack notifications for failing master builds
  (`#65 <https://github.com/nengo/nengo-fpga/pull/65>`__)

**Fixed**

- Update Numpy license URL.
  (`#64 <https://github.com/nengo/nengo-fpga/pull/64>`__)
- Fixed slack notification link
  (`#66 <https://github.com/nengo/nengo-fpga/pull/66>`__)


0.2.2 (May 7, 2020)
-------------------

**Added**

- Setup Nengo Bones and remote CI.
  (`#41 <https://github.com/nengo/nengo-fpga/pull/41>`__)
- Added notebook examples featuring oscillators.
  (`#46 <https://github.com/nengo/nengo-fpga/pull/46>`__)
- Added spiking to oscillator notebook examples.
  (`#49 <https://github.com/nengo/nengo-fpga/pull/49>`__)
- Add test suite.
  (`#55 <https://github.com/nengo/nengo-fpga/pull/55>`__)
- Added More detail to remote termination signals.
  (`#61 <https://github.com/nengo/nengo-fpga/pull/61>`__)

**Changed**

- Compatibility changes for Nengo 3.0.0.
  (`#44 <https://github.com/nengo/nengo-fpga/pull/44>`__)
- Minor changes to oscillator notebooks.
  (`#47 <https://github.com/nengo/nengo-fpga/pull/47>`__)
- Minor changes to getting-started documentation.
  (`#50 <https://github.com/nengo/nengo-fpga/pull/50>`__)
- Improved socket communication for better performance.
  (`#52 <https://github.com/nengo/nengo-fpga/pull/52>`__)
- Throw an error with invalid config in ID script.
  (`#53 <https://github.com/nengo/nengo-fpga/pull/53>`__)
- Update deprecated SafeConfigParser.
  (`#57 <https://github.com/nengo/nengo-fpga/pull/57>`__)
- Remove unused seed from network builder.
  (`#58 <https://github.com/nengo/nengo-fpga/pull/58>`__)
- Make all variable names lowercase.
  (`#59 <https://github.com/nengo/nengo-fpga/pull/59>`__)
- Switch to remote doc script that tracks nengo-bones.
  (`#60 <https://github.com/nengo/nengo-fpga/pull/60>`__)
- Switch to abrgl for CI scripts.
  (`#62 <https://github.com/nengo/nengo-fpga/pull/62>`__)

**Fixed**

- Fixed code to remove all linter errors.
  (`#45 <https://github.com/nengo/nengo-fpga/pull/45>`__)
- Start using intersphinx, rename docs using '-'.
  (`#48 <https://github.com/nengo/nengo-fpga/pull/48>`__)
- Add TRAVIS_JOB_NUMBER to exported variables in remote-docs.sh.
  (`#63 <https://github.com/nengo/nengo-fpga/pull/63>`__)


0.2.1 (September 17, 2019)
--------------------------

**Added**

- Add on-chip feedback connection.
  (`#35 <https://github.com/nengo/nengo-fpga/pull/35>`__)
- Requirement for numpy<1.17.
  (`#39 <https://github.com/nengo/nengo-fpga/pull/39>`__)


0.2.0 (August 27, 2019)
-----------------------

**Added**

- Added script to read device DNA from FPGA board.
  (`#11 <https://github.com/nengo/nengo-fpga/pull/11>`__)
- Add PR template, contributors, and update license.
  (`#12 <https://github.com/nengo/nengo-fpga/pull/12>`__)
- Rework documentation.
  (`#18 <https://github.com/nengo/nengo-fpga/pull/18>`__,
  `#20 <https://github.com/nengo/nengo-fpga/pull/20>`__)
- Quickstart guide.
  (`#21 <https://github.com/nengo/nengo-fpga/pull/21>`__)
- Notebook examples and example descriptions.
  (`#23 <https://github.com/nengo/nengo-fpga/pull/23>`__)
- Add firewall tip to docs.
  (`#24 <https://github.com/nengo/nengo-fpga/pull/24>`__)
- Add license to docs.
  (`#25 <https://github.com/nengo/nengo-fpga/pull/25>`__)
- Add purchase link to docs.
  (`#29 <https://github.com/nengo/nengo-fpga/pull/29>`__)
- Add example setting encoders/decoders.
  (`#30 <https://github.com/nengo/nengo-fpga/pull/30>`__)
- Add model size bounds to docs.
  (`#31 <https://github.com/nengo/nengo-fpga/pull/31>`__)

**Changed**

- Rename "DNA" to "ID" everywhere.
  (`#20 <https://github.com/nengo/nengo-fpga/pull/20>`__)
- Docs audit for consistency.
  (`#22 <https://github.com/nengo/nengo-fpga/pull/22>`__)
- Receiving a UDP packet with a negative timestep will now cause the Nengo
  simulation to terminate with an exception.
  (`#26 <https://github.com/nengo/nengo-fpga/pull/26>`__)
- Now throwing an exception on unsupported neuron type.
  (`#26 <https://github.com/nengo/nengo-fpga/pull/26>`__)
- Rework usage page in docs.
  (`#27 <https://github.com/nengo/nengo-fpga/pull/27>`__)
- Update the docs theme.
  (`#32 <https://github.com/nengo/nengo-fpga/pull/32>`__)

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
