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

import re
import threading
import tensorforce_client.utils as util


class Cluster(object):
    """
    A cloud cluster object specifying things like:
    - number of nodes
    - GPUs per node and GPU type
    - memory per node
    - disk size
    - zone
    - etc..
    """
    def __init__(self, **kwargs):
        self.file = kwargs.get("file")
        if self.file:
            from_json = util.read_json_spec(self.file, "clusters")
        # get all attributes from kwargs
        else:
            from_json = {}

        self.name = kwargs.get("name") or from_json.get("name")
        if not self.name:
            raise util.TFCliError("ERROR: Cluster requires a name!")
        self.name_hyphenated = re.sub(r'_', '-', self.name)
        self.machine_type = kwargs.get("machine_type") or from_json.get("machine_type")
        # alternative to machine_type -> provide `cpus_per_node` and `memory_per_node`
        if not self.machine_type:
            cpus = kwargs.get("cpus_per_node") or from_json.get("cpus_per_node")
            mem = kwargs.get("memory_per_node") or from_json.get("memory_per_node")
            if not cpus or not mem:
                raise util.TFCliError("ERROR: no vCPUs_per_node OR no memory_per_node given for cluster {}".
                                      format(self.name))
            self.machine_type = "custom-{}-{}".format(cpus, mem * 1024)
        self.num_nodes = kwargs.get("num_nodes") or from_json.get("num_nodes", 3)
        self.num_gpus = 0
        self.gpu_type = None
        self.gpus_per_node = kwargs.get("gpus_per_node") or from_json.get("gpus_per_node", 0)
        if self.gpus_per_node > 0:
            self.gpu_type = kwargs.get("gpu_type") or from_json.get("gpu_type", "nvidia-tesla-k80")
            self.num_gpus = self.gpus_per_node * self.num_nodes
        # size of single disks (one per node)
        self.disk_size = kwargs.get("disk_size") or from_json.get("disk_size", 100)
        self.location = kwargs.get("location") or from_json.get("location")

        # add information from running clusters
        if "running_clusters" in kwargs:
            self.instances, self.primary_name = util.get_compute_instance_specs(self.name_hyphenated)
            self.started = True if self.instances else False
        # cluster is not running yet
        else:
            self.instances = None
            self.primary_name = None
            self.started = False

        self.deleted = False  # is terminated or being shut down right now?

    def create(self):
        """
        Create the Kubernetes cluster with the options given in self.
        This also sets up the local kubectl app to point to the new cluster automatically.
        """
        print("+ Creating cluster: {}. This may take a few minutes ...".format(self.name_hyphenated))
        if self.num_gpus == 0:
            out = util.syscall("gcloud container clusters create {} -m {} --disk-size {} --num-nodes {} {}".
                               format(self.name_hyphenated, self.machine_type, self.disk_size, self.num_nodes,
                                      "--zone " + self.location if self.location else ""), return_outputs="as_str")
        else:
            out = util.syscall("gcloud beta container clusters create {} --enable-cloud-logging --enable-cloud-monitoring "
                               "--accelerator type={},count={} {} -m {} --disk-size {} --enable-kubernetes-alpha "
                               "--image-type COS --num-nodes {} --cluster-version 1.9.2-gke.1 --quiet".
                               format(self.name_hyphenated, self.gpu_type, self.gpus_per_node,
                                      "--zone "+self.location if self.location else "", self.machine_type, self.disk_size,
                                      self.num_nodes), return_outputs="as_str")
        # check output of cluster generating code
        if re.search(r'error', out, re.IGNORECASE):
            raise util.TFCliError(out)
        else:
            print("+ Successfully created cluster.")
        self.instances, self.primary_name = util.get_compute_instance_specs(self.name_hyphenated)
        self.started = True

        # install NVIDIA drivers on machines per local kubectl
        if self.num_gpus > 0:
            print("+ Installing NVIDIA GPU drivers and k8s device plugins ...")
            util.syscall("kubectl create -f https://raw.githubusercontent.com/GoogleCloudPlatform/"
                         "container-engine-accelerators/k8s-1.9/daemonset.yaml")
            util.syscall("kubectl delete -f https://raw.githubusercontent.com/kubernetes/kubernetes/"
                         "release-1.9/cluster/addons/device-plugins/nvidia-gpu/daemonset.yaml")
            util.syscall("kubectl create -f https://raw.githubusercontent.com/kubernetes/kubernetes/"
                         "release-1.9/cluster/addons/device-plugins/nvidia-gpu/daemonset.yaml")

        print("+ Done. Cluster: {} created.".format(self.name_hyphenated))

    def delete(self):
        """
        Deletes (shuts down) this cluster in the cloud.
        """
        # delete the named cluster
        # don't wait for operation to finish
        print("+ Deleting cluster {} (async).".format(self.name_hyphenated))
        util.syscall("gcloud {} container clusters delete {} --quiet --async".
                     format("" if self.num_gpus == 0 else "beta", self.name))
        self.started = False
        self.deleted = True

    def get_spec(self):
        """
        Returns: Dict of the important settings of this Cluster.
        """

        return {
            "name": self.name,
            "machine_type": self.machine_type,
            "num_nodes": self.num_nodes,
            "num_gpus": self.num_gpus,
            "gpus_per_node": self.gpus_per_node,
            "gpu_type": self.gpu_type,
            "status": "RUNNING" if self.started else "???",
            "primary_name": self.primary_name,
            "location": self.location
        }

    def ssh_parallel(self, *items, **kwargs):
        """
        Runs commands via ssh and/or scp commands on all nodes in the cluster in parallel using multiple threads.

        Args:
            items (List[Union[str,tuple]]): List of commands to execute. Could be either of type str (ssh command)
                or a tuple/list of two items (`from` and `to`) for an scp command.
            kwargs (any):
                silent (bool): Whether to execute all commands silently (default: True).
        """
        threads = []
        # generate and start all threads
        for node, spec in self.instances.items():
            t = threading.Thread(target=self.ssh_parallel_target, args=(node, kwargs.get("silent", True), items))
            threads.append(t)
            t.start()
        # wait for all threads to complete
        for t in threads:
            t.join()

    def _ssh_parallel_target(self, node, silent, items):
        for item in items:
            # an ssh command to execute on the node
            if isinstance(item, str):
                _ = util.syscall("gcloud compute ssh {} {} --command \"{}\"".
                                 format(node, "--zone="+self.location if self.location else "", item),
                                 return_outputs=silent)
            # an scp command (copy from ... to ...)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                item = list(map(lambda i: re.sub(r'_NODE_', node, i), item))
                _ = util.syscall("gcloud compute scp {} {} {}".
                                 format("--zone="+self.location if self.location else "", item[0], item[1]),
                                 return_outputs=silent)
            else:
                raise util.TFCliError("ERROR: unknown ssh command structure. Needs to be str (ssh-command) "
                                      "or list/tuple of exactly 2 str (scp).")


def get_cluster_from_string(cluster, running_clusters=None):
    """
    Returns a Cluster object given a string of either a json file or an already running remote cluster's name.

    Args:
        cluster (str): The string to look for (either local json file or remote cluster's name)
        running_clusters (dict): Specs for already running cloud clusters by cluster name.

    Returns:
        The found Cluster object.
    """
    # no running clusters given -> get them now
    if not running_clusters:
        running_clusters = util.get_cluster_specs()

    # json file (get spec)
    if re.search(r'\.json$', cluster):
        cluster = Cluster(running_clusters=running_clusters, file=cluster, **util.read_json_spec(cluster, "clusters"))
    # cluster name (cluster must already exists in cloud)
    else:
        cluster_name = re.sub(r'_', '-', cluster)
        if cluster_name in running_clusters:
            cluster = Cluster(running_clusters=running_clusters, **running_clusters[cluster_name])
        else:
            raise util.TFCliError("ERROR: Given cluster {} not found in cloud!".format(cluster_name))
    return cluster
