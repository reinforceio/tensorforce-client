TensorForce-Client - Running Parallelized Reinforcement Learning Experiments in the Cloud
=========================================================================================

.. generate all docs using: `sphinx-build -b html . _build` inside the `docs` directory

TensorForce-Client is an easy to use command line interface to the open source
reinforcement learning (RL) library `"TensorForce" <https://github.com/reinforceio/tensorforce>`_.
This client helps you to setup
and run your own RL experiments in the cloud (only google cloud supported so far),
utilizing GPUs, multi-parallel execution algorithms, and TensorForce's support for
a large variety of environments ranging from simple grid-worlds to Atari games and
Unreal Engine 4 games.
Tensorforce-client submits RL-jobs using Kubernetes and docker containers in a fully automated fashion.
To read more about the internal workings of the client, check out `this chapter here
<tensorforce_client/tensorforce_client.internals.html>`_.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tensorforce_client/tensorforce_client.installation
   tensorforce_client/tensorforce_client.usage
   tensorforce_client/tensorforce_client.internals
   tensorforce_client/tensorforce_client.command_reference
   tensorforce_client/tensorforce_client.class_reference


More information
----------------

You can find more information at our `TensorForce-Client GitHub repository <https://github.com/reinforceio/TensorForce-Client>`__.

For the core TensorForce library, visit: `<https://github.com/reinforceio/TensorForce>`__.

We also have a seperate repository available for benchmarking our algorithm implementations
[here](https://github.com/reinforceio/tensorforce-benchmark).
