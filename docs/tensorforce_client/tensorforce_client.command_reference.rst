Command Reference
=================


Projects
--------

Projects in tensorforce-client are practically directories on your local drive that are linked to
arbitrary google cloud projects from your google account.
It's ok to link more than one local project to the same remote (cloud) project.

To make a local directory a tensorforce-client project, cd into that directory and run:

.. code:: bash

    $ tfcli init -r [gcloud remote project ID] -n [local project name]

If you don't specify a remote project ID, the client will ask you to provide one. You have to link
your local project to an already existing remote google cloud project.
The project's name (`-n` option) is non-mandatory and the tool will use the remote project's name.

You will also be asked to provide the service-account (see
`installation instructions here <tensorforce_client.installation.html>`_) that you would like to use for running
`tfcli` commands as well as the private key file to use for client-server communications.

Each local tensorforce-client project contains a convenience directory for configuration files
(`config/`), into which
the tool copies - upon project creation - all tensorforce default config files for clusters, experiments,
agents, networks, and environments. You can either add more config files to this directory,
change existing ones, or ignore this folder altogether and create and maintain your config files elsewhere.




Cluster
-------

cluster --help
++++++++++++++

Lists all sub-commands that the main *cluster* command supports.


cluster create
++++++++++++++

.. code:: bash

    $ tfcli cluster create -f [json filename] -n [give the cluster some name]

Creates a Kubernetes (k8s) cluster in the cloud.

The two most important command line flags are `-f [json file]`
and `-n [name for the cluster]`. Take a look in the `configs/clusters` directory
that is created automatically inside each new project for some example cluster setups (including GPU clusters).
For the json-file, you don't need to give a path (nor the .json extension) if the file is located
in the `configs/clusters` directory.

Instead of providing the `-f` flag, however, you could also define your cluster's parameters entirely on the
command line (thus without the need for a json file). For supported flags, run:

.. code:: bash

    $ tfcli cluster create --help

For an explanation of the (more powerful) supported json fields, take a look at the
`cluster class reference here <tensorforce_client.cluster.html>`_.


cluster list
++++++++++++

.. code:: bash

    $ tfcli cluster list

Lists all clusters currently running in the cloud.


cluster delete
++++++++++++++

Deletes (shuts down) a cluster running in the cloud. You will only have to provide the name tat you gave to the cluster
when you created it via the `-c` flag.

.. code:: bash

    $ tfcli cluster delete -c [cluster's name]


Use the `cluster list` command to get the names for all currently running clusters.

Also, if you simply would like to shut down all currently running clusters in your associated gcloud project, do:

.. code:: bash

    $ tfcli cluster delete --all



Experiments
-----------

experiment --help
+++++++++++++++++

Lists all sub-commands that the main *experiment* command supports.


experiment new
++++++++++++++

.. code:: bash

    $ tfcli experiment new -f [json filename] -n [give the experiment some name]

Creates a local(!) experiment entry in the current project. By default, this command
does not start the experiment in the cloud.

The two most important command line flags are `-f [json file]`
and `-n [name for the experiment]`. Take a look in the `configs/experiments` directory
that is created automatically inside each new project for some example experiment setups.
For the json-file, you don't need to give a path (nor the .json extension) if the file is located
in the `configs/experiments` directory.

The main parts of an RL experiment are generally the algorithm used (set via the json `agent` setting),
the environment (set via athe json `environment` setting), in which the agent acts, the neural-network
that the agent uses (set via the json `network` setting), the length of the experiment (set via the various
num_timesteps, num_episodes, etc.. settings), and the run_mode. For a detailed description of the different
run_modes, `take a look here <tensorforce_client.usage.html>`_.

For an explanation of all supported json fields, take a look at the
`Experiment class reference here <tensorforce_client.experiment.html>`_.

Instead of providing the `-f` flag on the command line, you could also define your experiment's parameters
entirely on the command line (thus without the need for a json file). For supported flags, run:

.. code:: bash

    $ tfcli experiment new --help


experiment list
+++++++++++++++

.. code:: bash

    $ tfcli experiment list

Lists all experiments that currently exist in this local project. Their run status ('running', 'paused', etc..)
is shown as well.


experiment start
++++++++++++++++

.. code:: bash

    $ tfcli experiment start -e [name of the experiment to start] -c [name of the cluster to start it on]

Starts an already existing experiment on a given cluster in the cloud. The `-c` option is optional and can
be omitted, because all experiments are created automatically with a cluster specification. Should the cluster
(the `-c` provided one or the one that's coming with the experiment)
not already be running, it will be created (started) in the cloud before the experiment is set up.

A started experiment will run until one of the stop conditions (settable through `num_episodes` and/or `num_timesteps`
in the experiment's json spec file or via the command line) is met. If the cluster the eperiment runs on belongs
to the experiment (as opposed to a separately created cluster), that cluster is shut down after experiment
completion.

    **NOTE: Tensorforce-client is still largely under development. As we are conducting reinforcement
    learning experiments with our different TensorForce-supported environments in the cloud, we will add more
    and more functionality to this client, especially focusing on representing results and making it
    easier to benchmark and compare different algorithms and neural network models.
    The following experiment-related sub-commands are not implemented yet:**


experiment pause
++++++++++++++++

Pauses an already running experiment. A paused experiment can be resumed by passing the ``


experiment stop
+++++++++++++++

Stops (aborts) an experiment
