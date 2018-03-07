Internals - How does TensorForce-Client Work?
=============================================

Tensorforce-client is under development and in alpha phase. As us developers will start running our own experiments
using this client, we will add  more and more functionality to the tool.
In order to use tensorforce-client, you don't really need to know how it works internally. However, it
is always beneficial to understand what's going on under the hood in case you run into problems or errors
(which you should then report via the "Issues"-tab of the github repo).


The 2 base tools: gcloud and kubectl
------------------------------------

Tensorforce-client uses two basic command line tools that you need to install
on your local machine prior to running the client. These are `gcloud` and `kubectl` and
they both come with the installation of the google SDK, which is described
`in the chapter on the installation procedure here <tensorforce_client.installation.html>`_.

Gcloud
++++++

Gcloud controls everything related to the `google compute engine <https://cloud.google.com/compute>`_ and
the `google Kubernetes engine <https://cloud.google.com/container>`_. This means, it is responsible for:

- Creating and deleting Kubernetes (k8s) clusters of various sizes and types.
- Copying (via scp) config files and python scripts to all the nodes of a cluster.
- Executing (via ssh) commands on each node of a cluster.
- Downloading (via scp) results from an experiment from certain nodes of a cluster.

All the above tasks are done for you under the hood and you should never have to run a *gcloud* command manually.


Kubectl
+++++++

Kubectl controls the workloads that go into the Kubernetes (k8s) service that's pre-installed on a cluster whenever
you create one, using the `tfcli cluster create`-command of this client.
Tensorforce-client makes sure all k8s yaml-config files are created correctly according to your experiment settings
and runs the repsective kubectl commands automatically.

Just like for `gcloud`, all kubectl-specific tasks are done for you under the hood and you should never have
to run a kubectl command manually.


So how does it work now - really?
---------------------------------

When you start an experiment, tensorflow-client first checks the cluster setting on your command line
or in the experiment's json and creates the cluster (via gcloud), if it's not already up.

Then it creates a k8s config file (yaml) out of a jinja2 template file, which will contain all the specifications
for Kubernetes `pods`, `jobs`, `services` and `volume mounts` that are necessary to place the experiment
in the Kubernetes engine running on the cluster.

All experiments are always run under Kubernetes using our docker container image. This image is hosted
on dockerhub under `ducandu/tfcli_experiment:[cpu|gpu] <https://cloud.docker.com/swarm/ducandu/repository/docker/ducandu/tfcli_experiment/general>`_.

Depending on the "run_mode" parameter of the experiment (settable through the experiment-json field:
"run_mode"), the Kubernetes workloads will be set up as follows:


run_mode='single':
++++++++++++++++++

A single Kubernetes Pod is created on one node (you will get a warning if you use this mode on a cluster
with more than one
node) that runs our docker container (the GPU or the CPU version depending on whether your cluster has GPUs). Also
within this container, a
single RL environment (e.g. an Atari game instance) and a single agent with one tensorflow model is created and does
all exploration in this environment.

run_mode='multi-threaded':
++++++++++++++++++++++++++

A single Pod is created on one node (you will get a warning if you use this mode on a cluster with more than one
node) that runs our docker container (the GPU or the CPU version depending on whether your cluster has GPUs).
The experiment's parameter `num_workers` determines how many parallel environment/agent-pairs are created inside
that container and are being run each in a separate thread.
Independent of the number of environment/agent-pairs (`num_workers`), only a single central
tensorflow model is created and trained using so-called hogwild updates
(`see this paper here <https://arxiv.org/abs/1106.5730>`_).
The reinforcement learning algorithm that utilizes this technique was
`first published here <https://arxiv.org/abs/1602.01783>`_.


run_mode='distributed':
+++++++++++++++++++++++

The distributed uses many tensorflow models, where some serve merely as storages for the parameters
(parameter-servers) and others are actively being trained (workers) and then send their
gradients upstream to these parameter-servers.
Each parameter server and each worker get their own Pod and all communication between them happens over the network.
The number of k8s Pods created is hence the sum of the two experiment parameters `num_workers` and
`num_parameter_servers`.
Each Pod should preferably run on a separate node, but this is not a hard requirement (Kubernetes will figure out
a good solution if you have fewer nodes in your cluster).
Each of the "worker" Pods actively runs a single environment/agent-pair that owns
its own tensorflow model and actively explores the environment. Parameter-servers also get an agent (including a model)
but do not perform any exploration in an environment. Paraeter servers are only there for receiving gradient updates
from workers and then redistributing these updates back to all other workers.
This procedure utilizes tensorflow's built-in distributed learning architecture.
Experiments with run-mode "distributed" follow the procedure
described first in `this paper here <https://arxiv.org/abs/1507.04296_>`_.

