Internals - How does TensorForce-Client Work?
=============================================

In order to use tensorforce-client, you don't really need to know how it works internally. However, it
is always beneficial to understand what's going on under the hood in case you run into problems or errors.


The 2 base tools: gcloud and kubectl
------------------------------------

Tensorforce-client uses two basic command line tools that you need to install
on your local machine prior to running the client. These are `gcloud` and `kubectl` and
they both come with the
installation of the google SDK, which is described
`in the chapter on the installation procedure here <tensorforce_client.installation.html>`_.

Gcloud
++++++

Gcloud controls everything related to the "google compute engine" and the "google Kubernetes engine". This means,
it is responsible for:

- creating and deleting a Kubernetes (k8s) cluster
- copying (via scp) config files and python scripts to all the nodes of a cluster
- executing (via ssh) commands on each node of a cluster
- downloading (via scp) results from an experiment from certain nodes of a cluster

All the above tasks are done for you under the hood and you should never have to run a gcloud command manually.

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

All experiments are always run with the exact same docker container image inside Kubernetes. The image is hosted
on dockerhub under `ducandu/tfcli_experiment:[cpu|gpu] <https://cloud.docker.com/swarm/ducandu/repository/docker/ducandu/tfcli_experiment/general>`_.

Depending on the "run_mode" parameter of the experiment (settable through the json field: "run_mode"), Kubernetes
will be set up as follows:


run_mode='single':
++++++++++++++++++

A single Pod is created on one node (you will get a warning if you use this mode on a cluster with more than one
node) that runs our docker container (the GPU or the CPU version depending on whether your cluster has GPUs). A
single RL environment (e.g. an Atari game instance) and a single agent with one tensorflow model is created and does
all exploration in this environment.

run_mode='multi-threaded':
++++++++++++++++++++++++++

A single Pod is created on one node (you will get a warning if you use this mode on a cluster with more than one
node) that runs our docker container (the GPU or the CPU version depending on whether your cluster has GPUs).
The experiment's parameter `num_workers` determines how many parallel environment/agent-pairs are created and run
each in a separate thread. Independent of the number of environment/agent-pairs (`num_workers`), only a single central
tensorflow model is created and trained using so-called hogwild updates (`https://arxiv.org/abs/1106.5730`_).
A reinforcement learning algorithm that utilizes these findings was
`first published here <https://arxiv.org/abs/1602.01783>`_.


run_mode='distributed':
+++++++++++++++++++++++

The number of k8s Pods created is the sum of the two experiment parameters `num_workers` and `num_parameter_servers`.
Each Pod should preferably run on a separate node, but this is not a hard requirement (Kubernetes will figure out
a good solution if you have fewer nodes in your cluster).
Each of the "worker" Pods (as opposed to the "parameter-server" Pods) runs a single environment/agent-pair that owns
its own tensorflow model. However, weight-updates are sent to the parameter-server Pods using tensorflow's
built-in distributed learning architecture. Experiments with run-mode "distributed-tf" follow roughly the procedure
described in `this paper here <https://arxiv.org/abs/1507.04296_>`_.


