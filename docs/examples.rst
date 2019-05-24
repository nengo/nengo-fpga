.. _examples:

********
Examples
********

NengoFPGA has a few examples to show you what's possible and get you started.
There are some simple examples that are built with Jupyter
notebooks that illustrate the code with interspersed text information.
These notebook examples use the :ref:`scripting <scripting>` mode of
NengoFPGA without needing Nengo GUI.

There are also some more complex examples that are not built in notebooks
and instead use Nengo GUI. These examples are more complex and some have
opportunities for you to interact with the system via the GUI.


Notebook Examples
=================

These example notebooks are statically rendered here for your perusal.
If you wish to experiment with these examples yourself, you can do so by
running the notebook from your own computer.
See :ref:`Using Jupyter Notebooks <jupyter>` for help.


.. toctree::
   :maxdepth: 1

   examples/notebooks/00-communication_channel
   examples/notebooks/01-learn_communication_channel


GUI Examples
============

.. |gui_dir| replace:: ``nengo_fpga/docs/examples/gui``

These examples are designed to be used with Nengo GUI, so first we will
install that.

.. rst-class:: compact

1. Install the GUI:

   .. code-block:: bash

      pip install nengo-gui

#. In a terminal, navigate to the |gui_dir| directory.
#. Try running an example:

   .. code-block:: bash

      nengo <file name> -b nengo_fpga

   where ``-b nengo_fpga`` tells the GUI to use ``nengo_fpga`` instead
   of standard Nengo for the backend.

   This should open the Nengo GUI interface in a browser and display the
   code on the right and a graphical representation on the left.

#. Near the top of the file you should see **# --- BOARD SELECT ---**, select
   the appropriate board here. (The names **de1** and **pynq** correspond to the
   headers in the ``fpga_config`` file).
#. Click the play button in the bottom right to start the simulation. It may
   take several seconds to build the model and begin running.


MNIST Digit Classifier
----------------------

From the |gui_dir| directory, run with:

.. code-block:: none

   nengo 02-mnist_vision_network.py -b nengo_fpga

This is an example of a vision network that classifies the handwritten
digits from the MNIST dataset.

This example has some additional requirements,
be sure you have the required packages installed:

1. Nengo Extras: ``pip install nengo_extras``
#. Python image library: ``pip install pillow``

Once the GUI is brought up and the simulation is running you should see a few
things:

- The digit being presented to the network is shown on the left.
- The ``output_spa`` graphic in the middle is a visualization
  of the plot on the right. These are showing the confidence of the
  classifier for each category. The larger text (and larger plotted value)
  corresponding to higher confidence in that category.


Adaptive Pendulum Control
-------------------------

From the |gui_dir| directory, run with:

.. code-block:: none

   nengo 03-adaptive_pendulum.py -b nengo_fpga

In this example we use a Proportional-Integral-Derivative
(PID) controller to control a variable mass pendulum.
The adaptive neural ensemble is used to supply the
integral term and compensates for changing steady state
error as the gravity acting on the pendulum varies.

Once the GUI is brought up and the simulation is running you should see a few
things:

.. rst-class:: compact

- The pendulum visualization:

  - The the blue line represents the target, or desired
    position of the pendulum.
  - The black line is the model being controlled by our adaptive
    PID controller.

- There are two sliders:

  - **Target Pendulum Angle** is the target input (the blue line).
    This slider is automatically controlled by the input node, but you are
    able to manually move it if desired.
  - **Extra Mass** controls the variable mass of the controlled pendulum
    (the black line).

Try moving the **Extra Mass** slider up or down in the GUI and
observe how the added or reduced mass affects
the position of the pendulum, especially as it
approaches horizontal where the torque due to
gravity is at it's peak.

Reinforcement Learning
----------------------

From the |gui_dir| directory, run with:

.. code-block:: none

   nengo 04-RL_demo.py -b nengo_fpga

Here we have a simple agent in a simple world.  It has three actions
(go forward, turn left, and turn right), and its only sense are three
range finders (radar).

Initially, its basal ganglia action selection system is set up to have
fixed utilities for the three actions (moving forward has a utility of 0.8,
which is larger than turning left or right (0.7 and 0.6), so it should always
go forward.

The reward system is set up to give a positive value when moving forward, and
a negative value if the agent crashes into a wall.  In theory, this should
cause it to learn to avoid obstacles.  In particular, it will start to turn
before it hits the obstacle, and so the reward should be negative much less
often.

The error signal in this case is very simple: the difference between the
computed utility and the instantaneous reward.  This error signal should
only be applied to whatever action is currently being chosen (although it
isn't quite perfect at doing this).  Note that this means it cannot learn
to do actions that will lead to *future* rewards.

This example has some additional requirements,
be sure you have the required packages installed:

.. rst-class:: compact

1. CCMSuite

   i. Download or clone this repository from
      `github <https://github.com/tcstewar/ccmsuite/>`_.
   #. Then from the ``ccmsuite`` directory:

      .. code-block:: bash

         pip install -e .

#. (optional) ``keyboard-state`` branch of Nengo GUI. This will allow you to
   control the GUI simulation using key presses.

.. should we include instructions on installing a dev version of the GUI
   and how to switch branches? or just leave it for people who know what
   they are doing and hopefully it gets merged soon.

Once the GUI is brought up and the simulation is running you should see a
small environment with an agent (triangle) moving about. If you have the
``keyboard-state`` branch of Nengo GUI you should see instructions printed
in the console pane on the bottom right. If you do not see instructions for key
presses then this feature is currently not available with your installed
version of Nengo GUI.
