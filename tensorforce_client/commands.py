"""
 -------------------------------------------------------------------------
 tensorforce-client - 
 commands.py
 
 !!TODO: add file description here!! 
  
 created: 2018/01/26 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from tensorforce_client.utils import syscall
import tensorforce_client.utils as util
from tensorforce_client.experiment import Experiment, get_experiment_from_string, get_local_experiments
from tensorforce_client.cluster import Cluster, get_cluster_from_string
import os
import re
import shutil
import json
import time


def cmd_init(args):
    # check if there is already a .tensorforce file in this folder
    if os.path.isfile(".tensorforce.json"):
        # TODO: read .tensorforce.json file to display project's name and other data
        if not args.force:
            print("WARNING: This directory already contains a tensorforce project. Would you like to overwrite it?")
            response = input(">")
            if response.upper() != "Y":
                quit()
        # erase the existing project and create a new one
        shutil.rmtree(".tensorforce.json")

    print("+ Creating project paths and copying sample spec files.")
    # add sub-dirs to it and write the main project file
    os.makedirs("clusters", exist_ok=True)
    os.makedirs("experiments", exist_ok=True)

    # copy all json example spec files from cloned github repo
    import tensorforce_client
    p = tensorforce_client.__path__._path[0] + "/configs"
    shutil.rmtree("configs/", ignore_errors=True)
    shutil.copytree("{}".format(p), "configs/")
    # add the experiment jinja file (k8s yaml template) into project's config dir
    shutil.copy("{}/experiment.yaml.jinja".format(p), "configs/")

    print("+ Checking requirements (gcloud and kubectl installations).")
    # check for installations of gcloud, then kubectl
    try:
        syscall("gcloud --version")
    except OSError:
        raise util.TFCliError("INIT ERROR: Installation of gcloud command line tool required.\nPlease install first:"
                              " https://cloud.google.com/sdk/docs/quickstarts")
    # we can install kubectl via gcloud: `gcloud components install kubectl`
    try:
        syscall("kubectl version")
    except OSError:
        print("++ Installing missing kubectl command line tool (this is necessary to manage your clusters via the"
              " Kubernetes tool):")
        syscall("gcloud components install kubectl")

    # login to google cloud
    print("+ Logging you into google cloud account.")
    # gcloud auth  [ACCOUNT] --key-file=KEY_FILE
    # TODO: have user enter this information (account and private key file)
    syscall("gcloud auth activate-service-account kubernetes-account@introkubernetes-191608.iam.gserviceaccount.com "
            "--key-file=l:/programming/privatekeys/MaRLEnE-bbad55cddab1.json")

    remote_project_id = None
    remote_project_name = None
    remote_projects_by_name, remote_projects_by_id = util.get_remote_projects()
    # if remote given -> only check for that one and exit if doesn't exist
    if args.remote_project_id:
        print("+ Checking for existing remote-project ID ({}).".format(args.remote_project_id))
        if args.remote_project_id not in remote_projects_by_id:
            raise util.TFCliError("ERROR: No remote project ID {} found in cloud!".format(args.remote_project_id))
        print("+ Found remote project ID {}.".format(args.remote_project_id))
        remote_project_id = args.remote_project_id
        remote_project_name = remote_projects_by_id[args.remote_project_id]["project-name"]
        # if no name -> take remote's name
        if not args.name:
            args.name = remote_project_name

    # look for existing project in cloud with same name and ask whether to use that one. If not, user can specify
    # a remote project name that may differ from the local project folder's name
    else:
        # if no name -> take folder name
        if not args.name:
            cwd = os.getcwd()
            args.name = re.sub(r'.+[/\\](\w+)$', '\\1', cwd)
            print("+ Name not given. Assuming folder name ({}) is project's name.".format(args.name))

        print("+ Checking name ({}) against existing projects in the cloud.".format(args.name))
        if args.name in remote_projects_by_name:
            remote_project_name = args.name
            remote_project_id = remote_projects_by_name[remote_project_name]["project-id"]
            print("++ Given project name ({}) already exists as a project in google cloud. "
                  "Will use remote project {} with ID {}.".format(args.name, args.name, remote_project_id))
        # TODO: service accounts cannot create projects without a parent
        else:
            remote_project_id = re.sub(r'_', '-', args.name)  # replace all underscores with hyphens
            remote_project_name = remote_project_id
            # what if id already exists -> use a modified one
            if remote_project_id in remote_projects_by_id:
                remote_project_id = remote_project_id + str(time.time())
            print("+ Project '{}' does not exist in cloud yet. Will create new project (with ID {}).".
                  format(args.name, remote_project_id))
            out, err = syscall("gcloud projects create {} --name {} --set-as-default".
                               format(remote_project_id, remote_project_name), return_outputs=True, merge_err=False)
            err_msg = err.raw.readall().decode("latin-1")
            if err_msg != b"":
                raise util.TFCliError(err_msg)

    # write project settings into .tensorforce dir
    util.write_project_file(args.name, remote_project_name, remote_project_id)


def cmd_experiment_new(args, project_id=None):
    # check for experiment already existing
    experiments = get_local_experiments()
    if args.name in experiments:
        raise util.TFCliError("ERROR: An experiment with the name {} already exists in this project!".
                              format(args.name))
    # setup the Experiment object
    experiment = Experiment(**args.__dict__)
    if args.start:
        if not project_id:
            raise util.TFCliError("ERROR: Cannot start experiment without remote project ID!")
        print("+ New experiment created. Starting ...")
        experiment.start(project_id)
    else:
        print("+ New experiment created. Use 'experiment start' to run.")


def cmd_experiment_list():
    # lists all of this project's experiments
    print("+ Getting experiment information ...")
    experiments = get_local_experiments(as_objects=True)
    print("LIST OF EXPERIMENTS:")
    print("{: >45}{: >16s}{: >20s}{: >16s}{: >14s}{: >15s}{: >12}".
          format("Experiment", "Agent", "Environment", "Run-Mode", "Num-Workers", "Cluster", "Status"))
    for e in experiments:
        print("{: >45}{: >16s}{: >20s}{: >16s}{: >14d}{: >15s}{: >12}".
              format(e.name_hyphenated, e.agent.get("type"), re.sub(r'^.+\.(\w+)$', '\\1', e.environment.get("type")),
                     e.run_mode, e.num_workers, e.cluster.get("name"), e.status))



def cmd_experiment_start(args, project_id):
    print("+ Loading experiment settings{}.".format(" (from running experiment)" if args.resume else ""))
    experiment = get_experiment_from_string(args.experiment, running=args.resume)
    experiment.start(project_id, resume=args.resume, cluster=args.cluster)


def cmd_experiment_pause(args, project_id):
    print("+ Loading experiment settings (from running experiment).")
    experiment = get_experiment_from_string(args.experiment, running=True)
    experiment.pause(project_id)


def cmd_experiment_stop(args):
    print("+ Loading experiment settings (from running experiment).")
    experiment = get_experiment_from_string(args.experiment, running=True)
    no_download = args.no_download
    experiment.stop(no_download)


def cmd_experiment_download(args):
    print("+ Loading experiment settings.")
    experiment = get_experiment_from_string(args.experiment)
    print("+ Downloading experiment's results ...")
    experiment.download()


def cmd_cluster_create(args):
    cluster = Cluster(**args.__dict__)
    cluster.create()
    return cluster


def cmd_cluster_delete(args):
    if args.all:
        clusters = util.get_cluster_specs()
        for c in clusters.values():
            cluster = Cluster(**c)
            cluster.delete()
        print("+ All clusters deleted.")
    else:
        if not args.cluster:
            raise util.TFCliError("ERROR: Cluster name (-c option) not given!")
        print("+ Looking for clusters ...")
        cluster = get_cluster_from_string(args.cluster)
        if not isinstance(cluster, Cluster):
            raise util.TFCliError("ERROR: No cluster with name {} found!".format(args.cluster))
        cluster.delete()


def cmd_cluster_list():
    print("+ Getting cluster information ...")
    clusters = util.get_cluster_specs()
    print("LIST OF CLUSTERS:")
    print("{: >45}{: >15s}{: >16s}{: >8s}{: >10s}{: >10s}".
          format("Cluster", "Location", "Machine-Type", "Nodes", "GPUs/Node", "Status"))
    for name, cluster in clusters.items():
        print("{: >45}{: >15s}{: >16s}{: >8d}{: >10d}{: >10s}".
              format(name, cluster.get("location"), cluster.get("machine_type"), cluster.get("num_nodes"),
                     cluster.get("gpus_per_node"), cluster.get("status")))

