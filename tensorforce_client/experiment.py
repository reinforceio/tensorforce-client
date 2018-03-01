# Copyright 2018 reinforce.io. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import json
import os.path
import re
from warnings import warn
import tensorforce_client.utils as util
from tensorforce_client.cluster import Cluster, get_cluster_from_string


class Experiment(object):
    def __init__(self, **kwargs):
        """
        Keyword Args:
            file (str): The Experiment's json spec file (can contain all other args).
            name (str): The name of the Experiment. This is also the name of the folder where it is stored.
            environment (str): The filename of the json env-spec file to use (see TensorForce documentation).
            agent (str): The filename of the json agent-spec file to use (see TensorForce documentation).
            network (str):  The filename of the json network-spec file to use (see TensorForce documentation).
            cluster (str): The filename of the json cluster-spec file to use (see class `Cluster`).
            episodes (int): The total number of episodes to run (all parallel agents).
            total_timesteps (int): The max. total number of timesteps to run (all parallel agents).
            max_timesteps_per_episode (int): The max. number of timesteps to run in each episode.
            deterministic (bool): Whether to not(!) use stochastic exploration on top of plain action outputs.
            repeat_actions (int): The number of actions to repeat for each action selection (by calling agent.act()).
            debug_logging (bool): Whether to switch on debug logging (default: False).
            run_mode (str): Which runner mode to use. Valid values are only 'single', 'multi-threaded' and
                'distributed'.
            num_workers (int): The number of worker processes to use (see `distributed` and `multi-threaded`
                run_modes).
            num_parameter_servers (int): The number of parameter servers to use (see distributed tensorflow).
            saver_frequency (str): The frequency with which to save the model. This is a combination of an int
                and a unit (e.g. "600s"), where unit can be "s" (seconds), "e" (episodes), or "t" (timesteps).
            summary_frequency (str): The frequency with which to save a tensorboard summary.
                This is a combination of an int and a unit (e.g. "600s"), where unit can be "s" (seconds)
                or "t" (timesteps). The episode unit (e) is not allowed here.
        """
        # see whether we have a json (yaml?) file for the experiment
        # TODO: yaml support
        self.file = kwargs.get("file")
        if self.file:
            from_json = util.read_json_spec(self.file, "experiments")
        # get all attributes from kwargs
        else:
            from_json = {}
        # From here on, give kwargs priority over spec (from file), so that single settings in the json file can be
        # overwritten by command line.

        # sanity check name
        self.name = kwargs.get("name") or from_json.get("name", "")
        if not re.match(r'^\w+$', self.name):
            raise util.TFCliError("ERROR: Name of experiment needs to be all alphanumeric characters")
        self.name_hyphenated = re.sub(r'_', '-', self.name)

        self.path = "experiments/{}/".format(self.name)
        self.k8s_config = "{}experiment.yaml".format(self.path)

        # read in sub-spec files (to JSON)
        self.environment = kwargs.get("environment") or from_json.get("environment")
        if isinstance(self.environment, str):
            self.environment = util.read_json_spec(self.environment, "environments")
        if self.environment.get("remote") and not self.environment.get("image"):
            raise util.TFCliError("WARNING: Defining a remote environment without a docker image in experiment spec! "
                                  "Use field `image` to define a docker image for the remote env.")

        self.network = kwargs.get("network") or from_json.get("network")
        if isinstance(self.network, str):
            self.network = util.read_json_spec(self.network, "networks")

        self.agent = kwargs.get("agent") or from_json.get("agent")
        if isinstance(self.agent, str):
            self.agent = util.read_json_spec(self.agent, "agents")

        self.cluster = kwargs.get("cluster") or from_json.get("cluster")
        if isinstance(self.cluster, str):
            cluster = get_cluster_from_string(self.cluster)
            self.cluster = cluster.get_spec()
        elif not isinstance(self.cluster, dict):
            raise util.TFCliError("ERROR: Cluster (-c option) has to be given as json filename.")

        self.episodes = kwargs.get("episodes") or from_json.get("episodes", 10000)
        self.total_timesteps = kwargs.get("total_timesteps") or from_json.get("total_timesteps", 1000000)
        self.max_timesteps_per_episode = kwargs.get("max_timesteps_per_episode") or \
                                         from_json.get("max_timesteps_per_episode", 1000)
        self.deterministic = kwargs.get("deterministic")
        if self.deterministic is None:
            self.deterministic = from_json.get("deterministic", False)
        self.repeat_actions = kwargs.get("repeat_actions") or from_json.get("repeat_actions", 1)

        self.num_workers = kwargs.get("num_workers") or from_json.get("num_workers", 3)
        self.num_parameter_servers = kwargs.get("num_parameter_servers") or from_json.get("num_parameter_servers", 1)

        # update our json file pointer and write us into the experiment's dir
        self.file = "{}experiment.json".format(self.path)
        self.debug_logging = kwargs.get("debug_logging") or from_json.get("debug_logging", False)

        # the experiment's run type
        self.run_mode = kwargs.get("run_mode") or from_json.get("run_mode", "distributed")
        assert self.run_mode in ["distributed", "multi-threaded", "single"],\
            "ERROR: run-type needs to be one of distributed|multi-threaded|single!"
        if self.run_mode == "distributed" and self.num_parameter_servers <= 0:
            raise util.TFCliError("ERROR: Cannot create experiment of run-mode=distributed and zero parameter servers!")

        self.saver_frequency = kwargs.get("saver_frequency")\
            or from_json.get("saver_frequency", "600s" if self.run_mode == "distributed" else "100e")
        self.summary_frequency = kwargs.get("summary_frequency")\
            or from_json.get("summary_frequency", "120s" if self.run_mode == "distributed" else "10e")

        # whether this experiment runs on a dedicated cluster
        self.has_dedicated_cluster = kwargs.get("has_dedicated_cluster") or from_json.get("has_dedicated_cluster", True)

        # status (running, paused, stopped, etc..)
        self.status = kwargs.get("status") or from_json.get("status", None)

        # json file specific to a certain experiment 'run' (e.g. cluster may differ from experiment's base config)
        self.running_json_file = "experiment_running.json"

    def generate_locally(self):
        """
        Writes the local json spec file for this Experiment object into the Experiment's dir.
        This file contains all settings (including agent, network, cluster, run-mode, etc..).
        """

        # check whether this experiment already exists (as a folder inside project's folder)
        # create a new dir for this experiment
        if not os.path.exists(self.path+"results/"):
            print("+ Creating experiment's directory {}.".format(self.path))
            os.makedirs(self.path+"results/")
        # write experiment data into experiment file (for future fast constructs of experiment parameters)
        print("+ Writing Experiment's settings to local disk.")
        self.write_json_file(self.path + "experiment.json")

    def setup_cluster(self, cluster, project_id, start=False):
        """
        Given a cluster name (or None) and a remote project-ID,
        sets up the cluster settings for this Experiment locally.
        Also starts the cluster if start is set to True.

        Args:
            cluster (str): The name of the cluster. If None, will get cluster-spec from the Experiment, or create a
                default Cluster object.
            project_id (str): The remote gcloud project ID.
            start (bool): Whether to already create (start) the cluster in the cloud.

        Returns: The Cluster object.

        """

        clusters = util.get_cluster_specs()

        # cluster is given (separate from experiment's own cluster)
        if cluster:
            cluster = get_cluster_from_string(cluster, running_clusters=clusters)
            self.has_dedicated_cluster = False
        # use experiment's own cluster
        elif self.cluster:
            cluster = Cluster(running_clusters=clusters, **self.cluster)
            self.has_dedicated_cluster = True
        # use a default cluster
        else:
            cluster = Cluster(name=self.name_hyphenated)
            self.has_dedicated_cluster = True

        # start cluster if not up yet
        if start and not cluster.started:
            cluster.create()
        # cluster up but not in good state
        elif clusters[cluster.name_hyphenated]["status"] != "RUNNING":
            raise util.TFCliError("ERROR: Given cluster {} is not in status RUNNING (but in status {})!".
                                  format(cluster.name_hyphenated, clusters[cluster.name_hyphenated]["status"]))

        # check cluster vs experiment setup and warn or abort if something doesn't match
        if self.run_mode != "distributed" and cluster.num_nodes > 1:
            warn("WARNING: Running non-distributed experiment on cluster with more than 1 node. Make sure you are "
                 "not wasting costly resources!")
        num_gpus = cluster.num_nodes * cluster.gpus_per_node
        if self.run_mode == "distributed" and self.num_workers + self.num_parameter_servers > num_gpus:
            warn("WARNING: Running distributed experiment with {} processes total on cluster with only {} GPUs! "
                 "This could lead to K8s scheduling problems.".
                 format(self.num_workers + self.num_parameter_servers, num_gpus))

        print("+ Setting up credentials to connect to cluster {}.".format(cluster.name_hyphenated))
        util.syscall("gcloud container clusters get-credentials {} --zone {} --project {}".
                     format(cluster.name_hyphenated, cluster.location, project_id))

        print("+ Setting kubectl to point to cluster {}.".format(cluster.name_hyphenated))
        util.syscall("kubectl config set-cluster {} --server={}".
                     format(cluster.name_hyphenated, clusters[cluster.name_hyphenated]["master_ip"]))

        self.cluster = cluster.get_spec()
        return cluster

    def start(self, project_id, resume=False, cluster=None):
        """
        Starts the Experiment in the cloud (using kubectl).
        The respective cluster is started (if it's not already running).

        Args:
            project_id (str): The remote gcloud project-ID.
            resume (bool): Whether we are resuming an already started (and paused) experiment.
            cluster (str): The name of the cluster to use (will be started if not already running). None for
                using the Experiment's own cluster or - if not given either - a default cluster.
        """

        # Update our cluster spec
        cluster = self.setup_cluster(cluster, project_id, start=False if resume else True)
        # Rewrite our json file.
        self.status = "running"
        self.write_json_file(file=self.path+self.running_json_file)

        # Render the k8s yaml config file for the experiment.
        print("+ Generating experiment's k8s config file.")
        #gpus_per_container = 0
        if self.run_mode == "distributed":
            gpus_per_container = int(cluster.num_gpus /
                                     (self.num_workers + self.num_parameter_servers))
        else:
            gpus_per_container = cluster.gpus_per_node
        util.write_kubernetes_yaml_file(self, self.k8s_config, gpus_per_container)
        print("+ Deleting old Kubernetes Workloads.")
        _ = util.syscall("kubectl delete -f {}".format(self.k8s_config), return_outputs="as_str")

        # TODO: wipe out previous experiments' results

        # Copy all required files to all nodes' disks.
        print("+ Copying all necessary config files to all nodes ...")

        # - create /experiment directory on primary disk
        # - change permissions on the experiment's folder
        # - copy experiment-running config file into /experiment directory
        cluster.ssh_parallel("sudo mount --make-shared /mnt/stateful_partition/",  # make partition shared
                             "sudo mkdir /mnt/stateful_partition/experiment/ ; "  # create experiment dir
                             "sudo chmod -R 0777 /mnt/stateful_partition/experiment/",  # make writable
                             # copy experiment's json file into new dir
                             [self.path+self.running_json_file, "_NODE_:/mnt/stateful_partition/experiment/."],
                             silent=False)

        # Create kubernetes services (which will start the experiment).
        print("+ Creating new Kubernetes Services and ReplicaSets.")
        util.syscall("kubectl create -f {}".format(self.k8s_config))

    def pause(self, project_id):
        """
        Pauses the already running Experiment.

        Args:
            project_id (str): The remote gcloud project-ID.
        """
        _ = self.setup_cluster(cluster=None, project_id=project_id)
        # delete the kubernetes workloads
        print("+ Deleting Kubernetes Workloads.")
        util.syscall("kubectl delete -f {}".format(self.k8s_config))

        self.status = "paused"
        self.write_json_file(file=self.path+self.running_json_file)

        print("+ Experiment is paused. Resume with `experiment start --resume -e {}`.".format(self.name_hyphenated))

    def stop(self, no_download=False):
        """
        Stops an already running Experiment by deleting the Kubernetes workload. If no_download is set to False
        (default), will download all results before stopping. If the cluster that the experiment runs on
        is dedicated to this experiment, will also delete the cluster.

        Args:
            no_download (bool): Whether to not(!) download the experiment's results so far (default: False).
        """

        # download data before stopping
        if not no_download:
            self.download()
        if self.status == "stopped":
            warn("WARNING: Experiment seems to be stopped already. Trying anyway. ...")
        # figure out whether cluster was created along with experiment
        # if yes: shut down cluster
        if self.has_dedicated_cluster:
            cluster = get_cluster_from_string(self.cluster.get("name"))
            print("+ Shutting down experiment's cluster {}.".format(cluster.name_hyphenated))
            cluster.delete()
        # if not: simply stop k8s jobs
        else:
            print("+ Deleting Kubernetes Workloads.")
            _ = util.syscall("kubectl delete -f {}".format(self.k8s_config), return_outputs=True)

        self.status = "stopped"
        self.write_json_file(file=self.path+self.running_json_file)

    def download(self):
        """
        Downloads the experiment's results (model checkpoints and tensorboard summary files) so far.
        """
        cluster = get_cluster_from_string(self.cluster.get("name"))
        cluster.ssh_parallel(["_NODE_:/mnt/stateful_partition/experiment/{}*".
                             format("results/" if self.run_mode != "distributed" else ""),
                              self.path+"results/."])

    def write_json_file(self, file=None):
        """
        Writes all the Experiment's settings to disk as a json file.

        Args:
            file (str): The filename to use. If None, will use the Experiment's filename.
        """
        with open(self.file if not file else file, "w") as f:
            json.dump(self.__dict__, f, indent=4)


def get_experiment_from_string(experiment, running=False):
    """
    Returns an Experiment object given a string of either a json file or a name of an already existing eperiment.

    Args:
        experiment (str): The string to look for (either local json file or local experiment's name)
        running (bool): Whether this experiment is already running.

    Returns:
        The found Experiment object.
    """
    file = "experiments/{}/{}.json". \
        format(experiment, "experiment" if not running else "experiment_running")
    if not os.path.exists(file):
        if running:
            raise util.TFCliError("ERROR: Experiment {} does not seem to be running right now! You have to create, then"
                                  "start it with 'experiment new/start'.".format(experiment))
        else:
            raise util.TFCliError("ERROR: Experiment {} not found! You have to create it first with 'experiment new'.".
                                  format(experiment))
    # get the experiment object from its json file
    with open(file) as f:
        spec = json.load(f)
        exp_obj = Experiment(**spec)

    return exp_obj


def get_local_experiments(as_objects=False):
    """
    Args:
        as_objects (bool): Whether to return a list of strings (names) or actual Experiment objects.

    Returns: A list of all Experiment names/objects that already exist in this project.
    """

    content = os.listdir("experiments/")
    experiments = [get_experiment_from_string(c) if as_objects else c
                   for c in content if os.path.isdir("experiments/"+c)]
    return experiments

