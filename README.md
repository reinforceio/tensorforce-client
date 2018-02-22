# tensorforce-client
A local command line client for the TensorForce RL-library by
reinforce.io


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

Enter a project name (only using alphanumeric or hyphens), for example:
"TensorForce-Client". Select this project to be your active project
from here on.
Next, you will have to enable billing by providing Google with a
(non-prepaid!) credit card or a bank account number. This is necessary
in order for Google to charge you for your future accrued
cloud computing costs.

IMAGE manage_and_create_billing_account.png

Then go to "APIs and Services" from the main menu (see image below)
and activate the following APIs (some of which may have
already be enabled by default):
- Google Kubernetes Engine API

IMAGE manage_and_create_billing_account.png


#### Get the Google Cloud SDK (all platforms)

https://cloud.google.com/sdk/docs/quickstarts

Run the .exe and follow the installation instructions. At the end of
the installation process, say 'yes' to setting up the gcloud command
line client (this will conveniently set some useful defaults and is not
necessary).

#### Install python google-cloud

```
pip install --upgrade google-cloud
```



### Example
