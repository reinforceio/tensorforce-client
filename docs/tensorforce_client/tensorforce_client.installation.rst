Installation
============

In the following, we will be walking through the above requirements
and how to satisfy or install each one of them.

Your Google Account
-------------------

Create a new google account or use your existing one.
Then go to http://console.cloud.google.com and create a new cloud project:

.. figure:: https://raw.githubusercontent.com/reinforceio/tensorforce-client/master/docs/images/create_project.png
    :alt: Create a new Project

    Create a new Project

![Create a new Project](https://raw.githubusercontent.com/reinforceio/tensorforce-client/master/docs/images/create_project_2.png "Create a new project")

Enter a project name (only using alphanumeric or hyphens), for example:
"TensorForce-Client". Select this project to be your active project
from here on.
Next, you will have to enable billing by providing Google with a
(non-prepaid) credit card or a bank account number. This is necessary
in order for Google to charge you for your future accrued
cloud computing costs.

![Manage your billing account](https://raw.githubusercontent.com/reinforceio/tensorforce-client/master/docs/images/manage_and_create_billing_account.png "Manage your Billing Account")

Then go to "APIs and Services" from the main menu (see image below) ...

![APIs and Services](https://raw.githubusercontent.com/reinforceio/tensorforce-client/master/docs/images/apis_and_services.png "APIs and Services")

... and activate the following APIs (some of which may have
already be enabled by default):
- Google Compute Engine API
- Google Kubernetes Engine API
- Google Cloud Storage
- Google Container Registry API
- Cloud Container Builder API

![Enable the Kubernetes Engine API](https://raw.githubusercontent.com/reinforceio/tensorforce-client/master/docs/images/enable_kubernetes_api.png "Enable the Kubernetes Engine API")


Get the Google Cloud SDK (all platforms)
----------------------------------------

https://cloud.google.com/sdk/docs/quickstarts

Run the .exe and follow the installation instructions.

Make sure you enable beta commands during installation as sometimes
the tensorforce-client will rely on those.

![Enable beta SDK commands](https://raw.githubusercontent.com/reinforceio/tensorforce-client/master/docs/images/enable_beta_sdk_commands.png "Enable beta SDK Commands")

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

.. code:: bash
    $ gcloud version


Install Python3.5 or higher
---------------------------

... if you haven't already done so a long time ago ;-)


Get the TensorForce Client
--------------------------

The tensorforce-client is a python module that can be installed in
one of two ways:

1) The easy way: pip Installation
+++++++++++++++++++++++++++++++++

Installing tensorforce-client through pip:

.. code:: bash
    $ pip install tensorforce-client

Note: tensorforce-client neither needs the tensorforce library itself
nor any of its core dependencies (e.g. tensorflow or tensorflow-gpu).
So this should be an easy ride.


2) The hard way: git clone + setup.py
+++++++++++++++++++++++++++++++++++++

You can also get the latest development version of tensorforce-client
by cloning/pulling it directly from our github repo and then
running setup.py:

.. code:: bash

    $ git clone github.com/reinforceio/tensorforce-client
    $ cd tensorforce-client
    $ python setup.py


Set an alias
------------

Tensorforce-Client is a python module that should be run using
`python -m tensorforce_client [some command(s)]`.
You can set an alias (e.g. `tfcli`) in your current session
for this as follows:
- Windows: `doskey tfcli=python -m tensorforce_client $*`
- Linux: `alias tfcli='python -m tensorforce_client'`

