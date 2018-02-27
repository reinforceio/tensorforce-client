# tensorforce-client
A local command line client to run reinforcement learning (RL)
experiments in the google cloud using the TensorForce library by
reinforce.io and Kubernetes.
Neither local GPUs, tensorflow-/tensorforce-, nor Kubernetes
installations are required!

- Create arbitrary and custom clusters (including GPU machines) to
be able to run parallelized machine learning tasks.
- Setup your RL experiments using simple json config files.
Tensorforce-client already comes with many pre-defined configs that
can be used out of the box.
- Start your own reinforcement learning experiments on the generated
clusters via simple command lines in your favourite local shell.
- Watch the progress of your experiments by following basic stats
(e.g. average reward per episode) or via occasional tensorboard
downloads.
- Pause, stop, resume, download your experiments from your
local command line.
- Link clusters to your experiments to shut them down automatically
once the experiment is done running.

[comment]: <> (Put timers on your clusters in case you forget to shut them down Shut down all clusters when done!)


### Requirements

##### (Installation will be described in detail further below).

- A google cloud platform account (any google account will do) with
billing enabled and a bunch of so-called "google cloud APIs" activated:
- The Google Cloud SDK.
- Local installation of Python3.5 or higher.
- The tensorforce-client python module (pip-installable).


### Installation

In the following, we will be walking through the above requirements
and how to satisfy or install each one of them.

#### Get a Google Account (or use your existing one)

Then go to http://console.cloud.google.com and create a new project.

IMAGE create_project.png
IMAGE create_project_2.png

Enter a project name (only using alphanumeric or hyphens), for example:
"TensorForce-Client". Select this project to be your active project
from here on.
Next, you will have to enable billing by providing Google with a
(non-prepaid) credit card or a bank account number. This is necessary
in order for Google to charge you for your future accrued
cloud computing costs.

IMAGE manage_and_create_billing_account.png

Then go to "APIs and Services" from the main menu (see image below) ...

IMAGE apis_and_services.png

... and activate the following APIs (some of which may have
already be enabled by default):
- Google Compute Engine API
- Google Kubernetes Engine API
- Google Cloud Storage
- Google Container Registry API
- Cloud Container Builder API

IMAGE enable_kubernetes_api.png


#### Get the Google Cloud SDK (all platforms)

https://cloud.google.com/sdk/docs/quickstarts

Run the .exe and follow the installation instructions.

Make sure you enable beta commands during installation as sometimes
the tensorforce-client will rely on those.

IMAGE enable_beta_sdk_commands.png

At the end of the installation process, depending on the installer
version, say 'yes' to setting up the
command line client (`gcloud`) or make sure that `gcloud init`
runs. This will conveniently point you to your google account
and (newly created) google cloud project and set some useful defaults
(default compute region and zone).

There is a shell that comes with the installation. However, in order
to run the tensorforce-client from within any shell (anaconda, git,
or vanilla PowerShell), simply make sure that the gcloud
installation path + `/bin` is part of the %PATH env variable.

To make sure everything is setup correctly, run a test gcloud
command via:

```
$ gcloud version
```


#### Install Python3.5 or higher

.. if you haven't already done so a long time ago ;-)


#### Get the TensorForce Client

The tensorforce-client is a python module that can be installed in
one of two ways:

##### 1) The easy way: pip Installation

Installing tensorforce-client through pip:

```
$ pip install tensorforce-client
```

Note: tensorforce-client neither needs the tensorforce library itself
nor any of its core dependencies (e.g. tensorflow or tensorflow-gpu).
So this should be an easy ride.


##### 2) The hard way: git clone + setup.py

You can also get the latest development version of tensorforce-client
by cloning/pulling it directly from our github repo and then
running setup.py:

```
$ git clone github.com/reinforceio/tensorforce-client
$ cd tensorforce-client
$ python setup.py
```


#### Set an alias

Tensorforce-Client is a python module that should be run using
`python -m tensorforce_client [some command(s)]`.
You can set an alias (e.g. `tfcli`) in your current session
for this as follows:
- Windows: `doskey tfcli=python -m tensorforce_client $*`
- Linux: `alias tfcli='python -m tensorforce_client'`



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



