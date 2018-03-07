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
from __future__ import division
from __future__ import print_function

import os
import argparse
import tensorforce_client.utils as util
import tensorforce_client.commands as commands


def main():
    parser = argparse.ArgumentParser(prog="tfcli", usage="%(prog)s")
    subparsers = parser.add_subparsers(dest="command", help="command help")
    # add subparsers for sub commands e.g. cluster, experiment
    project_parser = subparsers.add_parser("init",
                                           help="Initializes a new tensorforce project in the current directory")
    project_parser.add_argument("-f", "--force", action="store_true",
                                help="Force-erase a possibly already existing project in this folder.")
    project_parser.add_argument("-n", "--name", help="The name of the project.")
    project_parser.add_argument("-r", "--remote-project-id",
                                help="The remote project ID (e.g. gcloud) to link this project to.")

    cluster_parser = subparsers.add_parser("cluster", help="Main command for controlling clusters in the cloud.")
    cluster_subparsers = cluster_parser.add_subparsers(dest="sub_command", help="sub-command help")
    cluster_create_parser = cluster_subparsers.add_parser("create", help="Creates a new cluster in the cloud.")
    cluster_create_parser.add_argument('-f', '--file',
                                       help="The json file to get all information from for the new cluster.")
    cluster_create_parser.add_argument('-n', '--name',
                                       help="The name of the Kubernetes cluster (must be all lower case).")
    cluster_create_parser.add_argument('-s', '--size', default=3,
                                       help="The number of nodes for this cluster (default: 3).")
    cluster_create_parser.add_argument('-m', '--machine-type',
                                       help="The type of the machines to use (e.g. n1-standard-1 or custom-1-17920).")
    cluster_create_parser.add_argument('-d', '--disk-size', default=100,
                                       help="The boot disk size in Gb per node (default: 100Gb).")

    cluster_delete_parser = cluster_subparsers.add_parser("delete", help="Deletes (shuts down) a cluster in the cloud.")
    cluster_delete_parser.add_argument('-c', '--cluster',
                                       help="The name of the Kubernetes cluster to delete (shut down).")
    cluster_delete_parser.add_argument('-A', '--all', action="store_true",
                                       help="Whether to delete all existing (running) clusters.")

    cluster_list_parser = cluster_subparsers.add_parser("list", help="Lists all running clusters in the cloud.")

    experiment_parser = subparsers.add_parser("experiment", help="Main command for controlling experiments.")
    exp_subparsers = experiment_parser.add_subparsers(dest="sub_command", help="sub-command help")
    exp_list_parser = exp_subparsers.add_parser("list", help="Lists all running experiments.")
    exp_new_parser = exp_subparsers.add_parser("new", help="Creates a new experiment locally, without starting it.")
    exp_new_parser.add_argument("-f", "--file",
                                help="The json file to get all information from for the new experiment.")
    exp_new_parser.add_argument('-n', '--name', help="The name of the new experiment.")
    exp_new_parser.add_argument('-A', '--agent',
                                help="The TensorForce Agent spec (json) file to use for the experiment.")
    exp_new_parser.add_argument('-M', '--network',
                                help="The TensorForce Network spec (json) file to use for the experiment.")
    exp_new_parser.add_argument('-E', '--environment',
                                help="The TensorForce Environment spec (json) file to use for the experiment.")
    exp_new_parser.add_argument('-C', '--cluster', default=None,
                                help="The cluster spec (json) file to use for this experiment.")
    #exp_new_parser.add_argument('-D', '--disk', default=None,
    #                            help="The disk spec (json) file to use for this experiment.")
    #exp_new_parser.add_argument('-Ds', '--disk-size', default=None,
    #                            help="The shared disk-size to use for this experiment.")
    exp_new_parser.add_argument('-s', '--start', action="store_true",
                                help="Whether to start this experiment right away.")
    exp_new_parser.add_argument('-e', '--episodes', type=int, help="The number of episodes to run in total.")
    exp_new_parser.add_argument('-t', '--total-timesteps', type=int,
                                help="The max. number of timesteps to run in total.")
    exp_new_parser.add_argument('--max-timesteps-per-episode', type=int,
                                help="The max. number of timesteps per episode.")
    exp_new_parser.add_argument('-d', '--deterministic', action="store_true", help="Whether to not use exploration.")
    exp_new_parser.add_argument('-w', '--num-workers', type=int, help="The number of workers to use.")
    exp_new_parser.add_argument('-p', '--num-parameter-servers', type=int,
                                help="The number of parameter-servers to use.")

    exp_start_parser = exp_subparsers.add_parser("start", help="Starts an already existing experiment by running it in the cloud.")
    exp_start_parser.add_argument('-e', '--experiment', required=True, help="The name of the experiment to start.")
    exp_start_parser.add_argument('-R', '--resume', action="store_true",
                                  help="Whether to resume a paused experiment on a running cluster.")
    exp_start_parser.add_argument('-c', '--cluster', help="The name of the (already running) cluster to use.")

    exp_pause_parser = exp_subparsers.add_parser("pause")
    exp_pause_parser.add_argument('-e', '--experiment', required=True, help="The name of the experiment to pause.")

    exp_stop_parser = exp_subparsers.add_parser("stop")
    exp_stop_parser.add_argument('-e', '--experiment', required=True, help="The name of the experiment to stop.")
    exp_stop_parser.add_argument('--no-download', action="store_true",
                                 help="Whether to not download any results prior to stopping.")

    exp_download_parser = exp_subparsers.add_parser("download")
    exp_download_parser.add_argument('-e', '--experiment', required=True,
                                     help="The name of the experiment for which to download results (so far).")

    # parse all args at once
    args = parser.parse_args()

    # logging.basicConfig(filename="logfile.txt", level=logging.INFO)
    #logging.basicConfig(stream=sys.stderr)
    #logger = logging.getLogger(__name__)
    #logger.setLevel(logging.DEBUG)
    """
    tfcli init -n [name of the project]
    tfcli experiment 
    """

    # process commands and sub-commands
    if not args.command:
        print("USAGE ERROR: You have to provide a command after `tfcli`: E.g.: `tfcli experiment --help`")
        parser.print_help()
        quit()

    # help
    if args.command == "help":
        parser.print_help()
    # create a new TFCli project (in the current folder)
    elif args.command == "init":
        commands.cmd_init(args)
        # sets up a new experiment (only local for now (until experiment is started))
    else:
        # look for our base parent project directory (we may be in some sub dir) and set the cwd to that parent dir
        if util.set_project_dir() is False:
            print("ERROR: No tensorforce-client project directory found in any parent dir of the "
                             "current one ({})! Please make sure you are in some project directory. Create a new "
                             "project with `tfcli init`.".format(os.getcwd()))
            parser.print_help()
            quit()

        # experiment command
        if args.command == "experiment":
            if args.sub_command == "new":
                commands.cmd_experiment_new(args, None if not args.start else get_remote_project_id())
            elif args.sub_command == "list":
                commands.cmd_experiment_list()
            # start the experiment on a cloud cluster
            elif args.sub_command == "start":
                commands.cmd_experiment_start(args, get_remote_project_id())
            # pauses the experiment on the cluster
            elif args.sub_command == "pause":
                commands.cmd_experiment_pause(args, get_remote_project_id())
            # stops the experiment on the cluster
            elif args.sub_command == "stop":
                commands.cmd_experiment_stop(args)  # TODO: experiment stop
            # downloads the tensorboard and logs from the cluster
            elif args.sub_command == "download":
                commands.cmd_experiment_download(args)  # TODO: experiment download
            # invalid sub-command
            else:
                print("USAGE ERROR: Invalid sub-command ({}) for command 'experiment'. "
                      "Allowed are [new|start|stop|pause|download|list].".format(args.sub_command))
                parser.print_help()
        elif args.command == "cluster":
            # starts a Kubernetes cloud cluster with google
            if args.sub_command == "create":
                commands.cmd_cluster_create(args)
            # stops (deletes) a Kubernetes cloud cluster with google
            elif args.sub_command == "delete":
                commands.cmd_cluster_delete(args)
            # list all currently existing clusters
            elif args.sub_command == "list":
                commands.cmd_cluster_list()
            else:
                print("USAGE ERROR: Invalid sub-command ({}) for command 'cluster'. "
                      "Allowed are [create|delete|list].".format(args.sub_command))
                parser.print_help()


def get_remote_project_id():
    project_spec = util.read_json_spec(file=".tensorforce.json")
    return project_spec["remote_id"]


if __name__ == "__main__":
    main()


