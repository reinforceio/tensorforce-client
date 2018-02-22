# Copyright 2017 reinforce.io. All Rights Reserved.
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

"""
This script will run along the tensorflow/tensorforce libs in a Docker container in a cluster.
The docker container(s) will be managed by Kubernetes. Depending on the Docker CMD command line parameters,
the script will build either a 'ps' task or a 'worker' task.

TODO: implement multi-threaded Runner experiment (to be run on single node with many CPUs).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import logging
import os
import numpy as np
import copy
import re

import tensorflow as tf

from tensorforce import TensorForceError
from tensorforce.agents import Agent
from tensorforce.environments import Environment
from tensorforce.execution import SingleRunner, DistributedTFRunner, ThreadedRunner, WorkerAgentGenerator


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-E', '--experiment-spec', required=True, help="Experiment's json configuration file.")
    parser.add_argument('-w', '--worker-hosts', help="Comma-separated string of [host:port] for the worker hosts.")
    parser.add_argument('-p', '--ps-hosts', help="Comma-separated string of [host:port] for the parameter-server hosts.")
    parser.add_argument('-j', '--job', help="'ps' or 'worker'")
    parser.add_argument('-i', '--task-index', type=int, default=0, help="Task index")
    parser.add_argument('-D', '--debug', action='store_true', help="Show debug outputs")
    parser.add_argument('-r', '--repeat-actions', type=int, default=1,
                        help="How many times should an action be repeated in each step through the environment?")
    parser.add_argument('--saver-dir', help="The root dir where all model data should go.")
    parser.add_argument('--summary-dir', help="The root dir where all tensorboard summary data should go.")
    parser.add_argument('-L', '--load', action="store_true", help="Load model from a previous or paused "
                                                                  "run of this experiment.")

    args = parser.parse_args()

    # configure our logging facility
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='[%(levelname)s] - %(message)s')  # no need for timestamp (will be added by google)
    logger = logging.getLogger(__name__)

    # create summary/saver dirs if they don't exist
    if args.saver_dir and not os.path.isdir(args.saver_dir):
        logger.info("Creating saver directory: {}".format(args.saver_dir))
        os.makedirs(args.saver_dir)
    if args.summary_dir and not os.path.isdir(args.summary_dir):
        logger.info("Creating summary directory: {}".format(args.summary_dir))
        os.makedirs(args.summary_dir)

    with open(args.experiment_spec) as fp:
        experiment_spec = json.load(fp=fp)

    run_mode = experiment_spec.get("run_mode", "distributed")

    if run_mode == "distributed":
        ps_hosts = args.ps_hosts.split(",")
        worker_hosts = args.worker_hosts.split(",")  # []
        cluster = {'ps': ps_hosts, 'worker': worker_hosts}
        cluster_spec = tf.train.ClusterSpec(cluster)
    else:
        cluster_spec = None

    if "environment" not in experiment_spec:
        raise TensorForceError("No 'environment' configuration found in experiment-spec.")
    environment_spec = experiment_spec["environment"]
    # check for remote env and log it (remote envs are put into a separate container)
    is_remote = environment_spec.pop("remote", False)

    if is_remote:
        img = environment_spec.pop("image", "default")
        logger.info("Experiment is run with RemoteEnvironment {} (in separate container).".format(img))

    if run_mode != "multi-threaded":
        environments = [Environment.from_spec(experiment_spec["environment"], {})]
    else:
        # For remote-envs in multi-threaded mode, we need to set a sequence of ports as all envs will be running
        # in the same pod. For single mode: Use the default port.
        environments = [Environment.from_spec(experiment_spec["environment"], {})]
        for i in range(1, experiment_spec.get("num_workers", 5)):
            environments.append(Environment.from_spec(experiment_spec["environment"],
                                                      {"port": environments[0].port + i} if is_remote else {}))

    saver_freq = experiment_spec.get("saver_frequency", "600s")
    mo = re.match(r'^(\d+)([ste])?$', str(saver_freq))
    if not mo:
        raise TensorForceError("ERROR: Experiment's saver_frequency has wrong format! "
                               "Needs to be int plus unit (s|t|e).")
    saver_freq = int(mo.group(1))
    saver_freq_unit = mo.group(2) or "s"

    summary_freq = experiment_spec.get("summary_frequency", "120s")
    mo = re.match(r'^(\d+)([st])?$', str(summary_freq))
    if not mo:
        raise TensorForceError("ERROR: Experiment's summary_frequency has wrong format! "
                               "Needs to be int plus unit (s|t).")
    summary_freq = int(mo.group(1))
    summary_freq_unit = mo.group(2) or "s"

    network = experiment_spec.get("network")
    if not network:
        logger.info("No 'network' configuration provided.")

    if "agent" not in experiment_spec:
        raise TensorForceError("No 'agent' configuration found in experiment-spec.")
    agent_config = experiment_spec["agent"]

    # in case we do epsilon annealing/decay with different values: fix-up agent-config here
    if run_mode == "multi-threaded":
        agent_configs = []
        for i in range(experiment_spec.get("num_workers")):
            worker_config = copy.deepcopy(agent_config)
            worker_config = vary_epsilon_anneal(worker_config)
            agent_configs.append(worker_config)
    else:
        agent_configs = [agent_config]

    agent = Agent.from_spec(
        spec=agent_configs[0],
        kwargs=dict(
            states=environments[0].states,
            actions=environments[0].actions,
            network=network,
            # distributed tensorflow spec?
            distributed=dict(
                cluster_spec=cluster_spec,
                task_index=args.task_index,
                parameter_server=(args.job == "ps"),
                device=('/job:{}/task:{}'.format(args.job, args.task_index)),  # '/cpu:0'
            ) if run_mode == "distributed" else None,
            # Model saver spec (only 1st worker will ever save).
            # - don't save for multi-threaded (ThreadedRunner will take care of this)
            saver=dict(
                load=args.load,  # load from an existing checkpoint?
                directory=args.saver_dir,
                # basename="model.ckpt"  # use default
                steps=saver_freq if saver_freq_unit == "t" else None,
                seconds=saver_freq if saver_freq_unit == "s" else None,
            ) if args.saver_dir and run_mode != "multi-threaded" else None,
            # tf tensorboard summary spec (all workers)
            summarizer=dict(
                directory=args.summary_dir,
                # create a tensorboard summary every n sec/steps
                steps=summary_freq if summary_freq_unit == "t" else None,
                seconds=summary_freq if summary_freq_unit == "s" else None,
                labels=("variables", "losses", "states", "actions", "rewards"),  # 'regularization' missing
            ) if args.summary_dir else None
        )
    )
    # TODO: test for run-type=distributed
    if args.load:
        agent.restore_model(args.saver_dir)

    agents = [agent]

    if run_mode == "multi-threaded":
        for i in range(experiment_spec.get("num_workers") - 1):
            config = agent_configs[i]
            agent_type = config.pop("type", None)
            logger.info("creating agent {} with network_spec={}".format(i, network))
            worker = WorkerAgentGenerator(agent_type)(
                states=environments[0].states,
                actions=environments[0].actions,
                network=network,
                model=agent.model,
                **config
            )
            agents.append(worker)

    logger.info("Starting agent(s) for env: {}".format(str(environments[0])))
    logger.info("Config:")
    logger.info(agent_configs[0])

    if run_mode == "distributed":
        runner = DistributedTFRunner(
            agent=agents[0],
            environment=environments[0],
            repeat_actions=args.repeat_actions
        )
    elif run_mode == "multi-threaded":
        runner = ThreadedRunner(
            agent=agents,
            environment=environments,
            repeat_actions=args.repeat_actions,
            save_path=args.saver_dir+"/model",
            save_frequency=saver_freq,
            save_frequency_unit=saver_freq_unit
        )
    else:
        runner = SingleRunner(
            agent=agents[0],
            environment=environments[0],
            repeat_actions=args.repeat_actions
        )

    if args.debug:
        report_episodes = 1
    else:
        report_episodes = 100

    def episode_finished(runner_, worker_=0):
        if runner_.global_episode % report_episodes == 0:
            steps_per_second = runner_.episode_timesteps[-1] / runner_.episode_times[-1]
            logger.info("Worker/Thread {} done with global episode {} in {} steps (SPS={}; global timesteps={})".format(
                worker_,
                runner_.global_episode,
                runner_.episode_timesteps[-1],
                steps_per_second,
                runner_.global_timestep)
            )
            logger.info("Last episode's return: {}".format(runner_.episode_rewards[-1]))

            num_completed_episodes = len(runner_.episode_rewards)
            if num_completed_episodes >= 100:
                reward_list = runner_.episode_rewards[-100:]
                logger.info("Average/Max return of last 100 episodes: {}/{}".
                            format(sum(reward_list) / min(100, num_completed_episodes), np.max(reward_list)))
            else:
                logger.info("Average/Max return of all episodes: {}/{}".
                            format(sum(runner_.episode_rewards) / num_completed_episodes,
                                   np.max(runner_.episode_rewards)))
            if num_completed_episodes >= 500:
                reward_list = runner_.episode_rewards[-500:]
                logger.info("Average/Max return of last 500 episodes: {}/{}".
                            format(sum(reward_list) / min(500, num_completed_episodes), np.max(reward_list)))
        return True

    runner.run(
        num_episodes=experiment_spec.get("episodes", 1000),
        num_timesteps=experiment_spec.get("timesteps", 1000000),
        max_episode_timesteps=experiment_spec.get("max_timesteps_per_episode", 1000),
        deterministic=experiment_spec.get("deterministic", False),
        episode_finished=episode_finished
    )
    runner.close()


# TODO: move this into BaseRunner?
def vary_epsilon_anneal(agent_config):
    # Optionally overwrite epsilon values with randomly picked items from a given list
    if "explorations_spec" in agent_config:
        if agent_config["explorations_spec"]["type"] == "epsilon_anneal":
            if isinstance(agent_config["explorations_spec"]["epsilon_final"], (list, tuple)):
                epsilon_final = np.random.choice(agent_config["explorations_spec"]["epsilon_final"])  # p=[0.3, 0.4, 0.3]
                agent_config["explorations_spec"]["epsilon_final"] = epsilon_final
        elif agent_config["explorations_spec"]["type"] == "epsilon_decay":
            if isinstance(agent_config["explorations_spec"]["initial_epsilon"], (list, tuple)):
                epsilon_start = np.random.choice(agent_config["explorations_spec"]["initial_epsilon"])
                agent_config["explorations_spec"]["initial_epsilon"] = epsilon_start
            if isinstance(agent_config["explorations_spec"]["final_epsilon"], (list, tuple)):
                epsilon_final = np.random.choice(agent_config["explorations_spec"]["final_epsilon"])
                agent_config["explorations_spec"]["final_epsilon"] = epsilon_final
    return agent_config


if __name__ == '__main__':
    main()

