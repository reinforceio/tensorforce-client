[![Docs](https://readthedocs.org/projects/tensorforce-client/badge)](http://tensorforce-client.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/reinforceio/tensorforce-client/blob/master/LICENSE)

# tensorforce-client
A local command line client to run reinforcement learning (RL)
experiments in the google cloud using the TensorForce library by
reinforce.io and Kubernetes.
Neither local GPUs, tensorflow-/tensorforce-, nor Kubernetes
installations are required!


- Create fully customized clusters (including GPU machines) to
be able to run parallelized machine learning tasks.
- Setup your RL experiments using simple json config files.
Tensorforce-client already comes with many pre-defined configs that
can be used out of the box.
- Start your own reinforcement learning experiments on the generated
clusters via simple command lines in your favourite local shell.
- Watch the progress of your experiments by following basic stats
(e.g. average reward per episode) or via occasional tensorboard
downloads.
- Pause, stop, resume, download your experiments all from your
local command line.
- Link clusters to your experiments to shut them down automatically
once the experiment is done running.
- Optional: Use tensorboard (for that, you do need local TensorFlow, though) to
view and debug your RL models and experiments in the browser.


### Requirements

([For Detailled Installation Instructions: See our Docs](http://tensorforce-client.readthedocs.io/en/latest/))

- A google cloud platform account (any google account will do) with
billing enabled and certain "google cloud APIs" activated.
- The Google Cloud SDK.
- Local installation of Python3.5 or higher.
- The tensorforce-client python module (pip-installable).



### Usage and Examples

Checkout the tensorforce-client documentation in order to
learn how to run your own reinforcement learning
experiments in the cloud. To get quick help on the command line
for certain commands and subcommands, simply use the `--help` flag
like so:

```
$ python -m tensorforce_client --help
```

Or, more specifically:

```
$ python -m tensorforce_client cluster --help
```

Or:

```
$ python -m tensorforce_client experiment new --help
```


#### Creating a new project

First, create a tensorforce project on your local machine:

```
# Create, then cd into a directory of your choice in which you would
# like to start a new project.

$ python -m tensorforce_client init -r [some remote gcloud project ID e.g. TensorForce-Client]

# This will link your already existing cloud project with the current working dir on your local machine.
# Your project is now initialized.
# - Sample configs are automatically copied into the project's `config` dir.
# - An empty folder `experiments` is created into which new experiments will be placed.
```


#### Creating a cluster in the cloud

Then, start a small cluster in the cloud by using one of the already
provided json cluster config files:

```
$ python -m tensorforce_client cluster create -f small_cluster.json -n my-new-cluster
```

This will bring up a new Kubernetes cluster in the cloud, which may take
a few minutes. When the script terminates, you are all set to start your
first experiment:

#### Creating and starting an experiment



