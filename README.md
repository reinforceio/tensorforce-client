# tensorforce-client
A local command line client to run reinforcement learning
experiments in the cloud using the TensorForce library by
reinforce.io.
- Create arbitrary and custom clusters (including GPU machines) to
be able to run parallelized machine learning tasks.
- Start your reinforcement learning experiments on these clusters
via simple local command lines.
- Watch the progress of your experiments by following simple stats
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


### Usage and Examples

Checkout the tensorforce-client documentation in order to
learn how to run your own reinforcement learning
experiments in the cloud.

#### Creating a new project and starting an experiment

```python
`# python synopsis

print("hello")
```
