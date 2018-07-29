# Reinforcement Learning

# Here we have a simple agent in a simple world.  It has three actions
# (go forward, turn left, and turn right), and its only sense are three
# range finders (radar).

# Initially, its basal ganglia action selection system is set up to have
# fixed utilities for the three actions (moving forward has a utility of 0.8,
# which is larger than turning left or right (0.7 and 0.6), so it should always
# go forward.

# The reward system is set up to give a positive value when moving forward, and
# a negative value if the agent crashes into a wall.  In theory, this should
# cause it to learn to avoid obstacles.  In particular, it will start to turn
# before it hits the obstacle, and so the reward should be negative much less
# often.

# The error signal in this case is very simple: the difference between the
# computed utility and the instantaneous reward.  This error signal should
# only be applied to whatever action is currently being chosen (although it
# isn't quite perfect at doing this).  Note that this means it cannot learn
# to do actions that will lead to *future* rewards.

import time
import numpy as np

# requires CCMSuite https://github.com/tcstewar/ccmsuite/
import ccm.lib.grid
import ccm.lib.continuous
import ccm.ui.nengo

import nengo
from nengo_fpga.networks import FpgaPesEnsembleNetwork
# Note: Requires the "keyboard_state" branch of nengo_gui


# Set the nengo logging level to 'info' to display all of the information
# coming back over the ssh connection.
nengo.utils.logging.log('info')


# ----------- WORLD CONFIGURATION ---------------------------------------------
class Cell(ccm.lib.grid.Cell):
    def color(self):
        return 'black' if self.wall else None

    def load(self, char):
        if char == '#':
            self.wall = True
        else:
            self.wall = False


class WorldConfig(object):
    curr_ind = -1
    world_maps = ["""
#########
#       #
#       #
#   ##  #
#   ##  #
#       #
#########""", """
#########
#       #
#       #
#   ##  #
#   ##  #
#   ##  #
#########""", """
#########
#       #
#  ###  #
#       #
#  ###  #
#       #
#########""", """
#########
#       #
#   #####
#       #
#####   #
#       #
#########"""]
    init_pos = [(1, 3, 2), (1, 3, 2), (1, 1, 1), (1, 1, 1)]

    world = None
    body = None

    def get_init_pos(self):
        return self.init_pos[self.curr_ind]

    def get_map(self):
        return self.world_maps[self.curr_ind]

    def set_ind(self, new_ind):
        if new_ind >= 0 and new_ind < len(self.world_maps):
            self.curr_ind = new_ind
            lines = self.get_map().splitlines()

            if (len(lines[0])) == 0:
                del lines[0]
            lines = [x.rstrip() for x in lines]
            for j in range(len(lines)):
                for i in range(len(lines[0])):
                    self.world.get_cell(i, j).load(lines[j][i])

    def reset_pos(self):
            self.body.x = self.get_init_pos()[0]
            self.body.y = self.get_init_pos()[1]
            self.body.dir = self.get_init_pos()[2]
            self.body.cell = self.world.get_cell(self.body.x, self.body.y)

world_cfg = WorldConfig()
world = ccm.lib.cellular.World(Cell, map=world_cfg.get_map(),
                               directions=4)
body = ccm.lib.continuous.Body()
world_cfg.world = world
world_cfg.body = body
world_cfg.set_ind(0)
world_cfg.world.add(body, x=world_cfg.get_init_pos()[0],
                    y=world_cfg.get_init_pos()[1],
                    dir=world_cfg.get_init_pos()[2])

# ----------- LEARNING & MODEL PARAMETERS -------------------------------------
learn_rate = 1e-4
learn_synapse = 0.030
learn_timeout = 60.0
radar_dim = 5
turn_bias = 0.25
action_threshold = 0.1
init_transform = [0.8, 0.6, 0.7]

# ----------- MODEL SEED CONFIGURATION ----------------------------------------
seed = int(time.time())
print("USING SEED: {0}".format(seed))

# ----------- MODEL PROPER ----------------------------------------------------
print("Press 'q' to enable permanent exploration.")
print("Press 'e' to turn off exploration and reset body position.")
print("Press 'w' to reset body position.")
print("Press 1-{0} to change maps.".format(len(world_cfg.world_maps)))

model = nengo.Network(seed=seed)
with model:
    # Create the environment
    env = ccm.ui.nengo.GridNode(world_cfg.world, dt=0.005)

    # Handle the movement of the agent, and generate the movement
    # "goodness" grade
    def move(t, x, world_cfg=world_cfg):
        speed, rotation = x
        dt = 0.001
        max_speed = 10.0  # 10.0
        max_rotate = 10.0  # 10.0
        world_cfg.body.turn(rotation * dt * max_rotate)
        success = world_cfg.body.go_forward(speed * dt * max_speed)
        if not success:
            world_cfg.body.color = 'red'
            return 0
        else:
            world_cfg.body.color = 'blue'
            return (turn_bias + speed)

    movement = nengo.Ensemble(n_neurons=100, dimensions=2, radius=1.4)
    movement_node = nengo.Node(move, size_in=2, label='reward')
    nengo.Connection(movement, movement_node)

    # Generate the context (radar distance to walls front, left, right)
    def detect(t):
        angles = (np.linspace(-0.5, 0.5, radar_dim) +
                  body.dir) % world.directions
        return [body.detect(d, max_distance=4)[0] for d in angles]
    stim_radar = nengo.Node(detect)

    # Create the action selection networks
    bg = nengo.networks.actionselection.BasalGanglia(3)
    thal = nengo.networks.actionselection.Thalamus(3)
    nengo.Connection(bg.output, thal.input)

    # Convert the selection actions to movement transforms
    nengo.Connection(thal.output[0], movement, transform=[[1], [0]])
    nengo.Connection(thal.output[1], movement, transform=[[0], [1]])
    nengo.Connection(thal.output[2], movement, transform=[[0], [-1]])

    # Generate the training (error) signal
    def error_func(t, x):
        actions = np.array(x[:3])
        utils = np.array(x[3:6])
        r = x[6]
        activate = x[7]

        max_action = max(actions)
        actions[actions < action_threshold] = 0
        actions[actions != max_action] = 0
        actions[actions == max_action] = 1

        return (
            activate * (
                np.multiply(actions,
                            (utils - r) * (1 - r) ** 5) +
                np.multiply((1 - actions),
                            (utils - 1) * (1 - r) ** 5)))

    errors = nengo.Node(error_func, size_in=8, size_out=3)
    nengo.Connection(thal.output, errors[:3])
    nengo.Connection(bg.input, errors[3:6])
    nengo.Connection(movement_node, errors[6])

    # the learning is done on the board
    adapt_ens = FpgaPesEnsembleNetwork(
        'de1', n_neurons=100 * radar_dim, dimensions=radar_dim,
        learning_rate=learn_rate, function=lambda x: init_transform,
        seed=1524081122, label='pes ensemble')
    adapt_ens.ensemble.radius = 4

    nengo.Connection(stim_radar, adapt_ens.input, synapse=learn_synapse)
    nengo.Connection(errors, adapt_ens.error)
    nengo.Connection(adapt_ens.output, bg.input)

    # Node to control and display current learning status
    def learn_activate_func(t, world_cfg=world_cfg, _is_learning=[1]):
        # _is_learning values:
        # < 0: no learning
        # 1: learning, will stop at learn_timeout
        # 2: continuoues learning

        init_body_pos = False
        if 'q' in __page__.keys_pressed:
            _is_learning[0] = 2
            init_body_pos = True
        elif 'e' in __page__.keys_pressed:
            _is_learning[0] = -1
            init_body_pos = True
        elif 'w' in __page__.keys_pressed:
            init_body_pos = True
        if len(__page__.keys_pressed) > 0:
            for k in __page__.keys_pressed:
                if k.isdigit():
                    new_map_ind = int(k) - 1
                    if new_map_ind != world_cfg.curr_ind:
                        world_cfg.set_ind(new_map_ind)
                        init_body_pos = True

        learn_on = (((t <= learn_timeout) or (_is_learning[0] == 2)) and
                    _is_learning[0] > 0)
        learn_activate_func._nengo_html_ = '''
        <svg width="100%" height="100%" viewbox="0 0 200 50">
            <text x="50%" y="50%" fill="{0}" text-anchor="middle"
             alignment-baseline="middle" font-size="50">{1}</text>
        </svg>
        '''.format("red" if learn_on else "grey",
                   "Explore: ON" if learn_on else "Explore: Off")

        if not learn_on and _is_learning[0] == 1:
            init_body_pos = True
            _is_learning[0] = -1

        if init_body_pos:
            world_cfg.reset_pos()

        return int(learn_on)

    learn_on = nengo.Node(learn_activate_func)
    nengo.Connection(learn_on, errors[7])
