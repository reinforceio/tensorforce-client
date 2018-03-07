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
import subprocess as sp
import re
import subprocess
import jinja2
import shlex


class TFCliError(Exception):
    """
    TensorForceClient error
    """
    pass


def set_project_dir():
    """
    Looks for a .tensorforce.json file in the cwd and then all parent dirs (until root is hit) and sets
    the cwd to the first dir found.
    """
    path = ""
    while True:
        if os.path.isfile(path + ".tensorforce.json"):
            if path != "":
                os.chdir(path)
            return path
        elif path != "" and not os.path.isdir(path):
            return False
        path += "../"


def read_json_spec(file, typ_=None):
    full_filename = file
    # file does not exists
    if not os.path.isfile(full_filename):
        # file given without extension -> add .json
        if re.search(r'^[\w\-/\\]+$', full_filename):
            full_filename += ".json"
        # single filename given (no directory) -> try default config dir
        if typ_ and re.match(r'^\w+\.json$', full_filename):
            full_filename = "configs/" + typ_ + "/" + full_filename

    if not os.path.isfile(full_filename):
        raise TFCliError("ERROR: Specification json file ({}) does not exist!".format(full_filename))

    with open(full_filename) as f:
        return json.load(f)  # return object


def write_project_file(name, remote_name, remote_id):
    project = {"name": name, "remote_name": remote_name, "remote_id": remote_id, "cloud_provider": "google"}
    with open(".tensorforce.json", "w") as f:
        json.dump(project, f)


def write_kubernetes_yaml_file(experiment, file="experiment.yaml", gpus_per_container=0):
    """
    Writes the yaml file (from our jinja2 template) to create the k8s Service based on the Experiment object passed in.
    Args:
        experiment (Experiment): The Experiment object containing all necessary information about the experiment to run.
        file (str): The yaml path+filename to write to.
        gpus_per_container (int): The number of GPUs to set as limit per container.
    """
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))
    template = env.get_template("configs/experiment.yaml.jinja")

    with open(file, "w") as f:
        f.write(
            template.render(
                name=experiment.name_hyphenated,
                experiment_spec="/experiment/"+experiment.running_json_file,
                image="ducandu/tfcli_experiment:{}".
                    format("gpu" if experiment.cluster.get("gpus_per_node", 0) > 0 else "cpu"),
                image_remote_env="" if not experiment.environment.get("remote", False)
                    else experiment.environment.get("image", "ducandu/ue4_alien_invaders:exec"),
                num_workers=experiment.num_workers,
                num_parameter_servers=experiment.num_parameter_servers,
                debug_logging=experiment.debug_logging,
                run_mode=experiment.run_mode,
                gpus_per_container=gpus_per_container,
                repeat_actions=experiment.repeat_actions
            )
        )


def get_remote_projects():
    """
    Returns: A dict of project dicts by project name. Supported fields per project, see code below.
    """
    projects_by_name = {}
    projects_by_id = {}
    out = syscall("gcloud projects list", return_outputs=True)
    while True:
        line = out.readline()
        if line == b"":
            break
        mo = re.match(r'([\w\-.]+)\s+([\w\-.]+)\s+([\d.]+)', line.decode("latin-1"))
        if mo:
            id_ = mo.group(1)
            name = mo.group(2)
            if name in projects_by_name:
                raise TFCliError("ERROR: At least 2 projects found with name {} in your google cloud account. "
                                 "Please make sure project names (just like project IDs) are unique.")
            projects_by_name[name] = {
                "project-id": id_,
                "project-number": mo.group(3)
            }
            projects_by_id[id_] = {
                "project-name": name,
                "project-number": mo.group(3)
            }
    return projects_by_name, projects_by_id


def get_cluster_specs():
    """
    Returns: A dict of cluster dicts by cluster name. Supported fields per cluster, see code below.
    """
    clusters = {}
    out = syscall("gcloud container clusters list --format json", return_outputs=True)
    try:
        json_out = json.load(out)
    except json.decoder.JSONDecodeError as e:
        # raise as TFCli Error
        print("ERROR: Could not load cluster list from cloud!")
        raise e

    if not isinstance(json_out, list):
        raise TFCliError("ERROR: List of clusters is not a json-list!")

    for c in json_out:
        node_config = c.get("nodeConfig", {})
        gpus_per_node = 0
        gpu_type = None
        accelerators = node_config.get("accelerators")
        if accelerators:
            gpu_type = accelerators[0].get("acceleratorType")
            if gpu_type == "nvidia-tesla-k80":  # or gpu_type == "nvidia-":
                gpus_per_node = int(accelerators[0].get("acceleratorCount"))
        clusters[c.get("name")] = {
            "name": c.get("name"),
            "name_hyphenated": c.get("name"),
            "location": c.get("zone"),
            "master_version": c.get("currentMasterVersion"),
            "master_ip": c.get("endpoint"),
            "machine_type": node_config.get("machineType"),
            "node_version": c.get("currentMasterVersion"),
            "num_nodes": c.get("currentNodeCount"),
            "status": c.get("status"),
            "gpus_per_node": gpus_per_node,
            "gpu_type": gpu_type
        }

    return clusters


def get_disks():
    """
    Returns: A dict of Disk objects by disk name.
    """
    disks = {}
    out = syscall("gcloud compute disks list", return_outputs=True)
    while True:
        line = out.readline()
        if line == b"":
            break
        mo = re.match(r'([\w\-.]+)\s+([\w\-.]+)\s+(\d+)\s+([\w\-.]+)\s+([A-Z\-]+)',
                      line.decode("latin-1"))
        if mo:
            disks[mo.group(1)] = Disk(mo.group(1), size=int(mo.group(3)), zone=mo.group(2),
                                      type_=mo.group(4), status=mo.group(5))
    return disks


def get_compute_instance_specs(cluster):
    """
    Returns: A dict of compute instances (for a certain cluster name) by instance name.
    Supported fields per cluster, see code below.

    Args:
        cluster (str): The name of the cluster to return instances for.
    """
    nodes = {}
    primary_name = None
    out = syscall("gcloud compute instances list --format json", return_outputs=True)
    json_out = json.load(out)

    if not isinstance(json_out, list):
        raise TFCliError("ERROR: List of nodes is not a json-list!")

    for c in json_out:
        name = c.get("name")
        if not re.search(r'-{}-'.format(cluster[:20]), name):
            continue
        network = c.get("networkInterfaces")[0]
        nodes[name] = {
            "name": name,
            "name_hyphenated": name,
            "zone": re.sub(r'^.+/', "", c.get("zone")),
            "machine_type": re.sub(r'^.+/', "", c.get("machineType")),
            "internal-ip": network.get("networkIP"),
            "external-ip": network.get("accessConfigs")[0].get("natIP"),
            "status": c.get("status"),
        }
        if not primary_name:
            primary_name = c.get("name")

    return None if len(nodes) == 0 else nodes, primary_name


def syscall(command, return_outputs=False, merge_err=True):
    """
    Args:
        command (str): The command to execute in the shell.
        return_outputs (Union[bool|str]): True if we should capture and return outputs (stdout and stderr).
            Alternatively: set this to "as_str" if you want to get the outputs as whole strings rather than
            as BufferedReader object(s).
        merge_err (bool): Whether to merge stderr with stdout.

    Returns:
        None OR (stdout/err) OR tuple(stdout, stderr) where stdout/err are either BufferedReader or strings depending
        on the value of return_outputs.
    """
    if return_outputs:
        if os.name == "nt":
            out = sp.Popen("cmd /c {}".format(command),
                           stdout=sp.PIPE, stderr=sp.STDOUT if merge_err else sp.PIPE)
            if merge_err:
                return out.stdout if return_outputs is True else out.stdout.raw.readall().decode("latin-1")
            else:
                return (out.stdout, out.stderr) if return_outputs is True \
                    else (out.stdout.raw.readall().decode("latin-1"), out.stderr.raw.readall().decode("latin-1"))
        else:
            out = sp.Popen(shlex.split(command),
                           stdout=sp.PIPE, stderr=sp.STDOUT if merge_err else sp.PIPE)

            if merge_err:
                return out.stdout if return_outputs is True else out.stdout.read().decode("latin-1")
            else:
                return (out.stdout, out.stderr) if return_outputs is True \
                    else (out.stdout.read().decode("latin-1"), out.stderr.read().decode("latin-1"))

    args = ["cmd", "/c"] if os.name == 'nt' else []
    args.extend(shlex.split(command))
    subprocess.call(args)

