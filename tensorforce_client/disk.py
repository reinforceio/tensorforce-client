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


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import tensorforce_client.utils as util


class Disk(object):
    """
    A disk object. Exists independently of a cluster. An experiment links to a certain (shared) disk to store
    its tensorboard and model information.
    """
    def __init__(self, name, size=200, type_="pd-standard", zone="europe-west1-d", status="READY"):
        self.name = name  # the unique cloud name of this disk
        self.size = size  # in Gb
        self.type = type_
        self.zone = zone
        self.status = status

    def create(self):
        util.syscall("gcloud compute disks create {} --size {}".format(self.name, self.size))

    def delete(self):
        util.syscall("gcloud compute disks delete {}".format(self.name))

