Usage - How to Run RL-Experiments in the Cloud?
===============================================

In this chapter, we will walk through an example experiment that runs the Atari 2600 game Space Invaders in
an A3C fashion on a 2-node GPU cluster. We will use only 1 parameter server and 4 workers (agents that explore the
space invaders environment). We will run a simple DQN algorithm for 1,000,000 timesteps (in total across all agents)
using a replay buffer that fits 10,000 experience tuples (state, action, reward, next-state). The exploration
strategy will be an epsilon decay starting from 1.0 at timestep 0 and linearly decreasing epsilon until it reaches
0.1 at timestep 1,000,000.


Creating the Cluster
--------------------

The `tfcli cluster create` command starts a cluster in the cloud. For our example
Use the

.. code:: bash

    $ tfcli cluster create

command to start a cluster in the cloud.

For our example, we will use this command as follows:



The following options are supported:
