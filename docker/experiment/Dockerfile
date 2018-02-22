# this is a container for running tfcli experiments (also via pycharm) against tensorforce on k8s

# set this to empty string (--build-arg gpu="") if you want to build without GPU
ARG gpu="-gpu"

FROM tensorflow/tensorflow:latest${gpu}-py3

RUN echo "GPU=$gpu (empty for cpu)"

# the GPU image needs to be built on a ubuntu machine (no Win support yet from NVIDIA)
# - use the following steps:
# - start a GPU cluster via tfcli in google cloud (this will already install the GPU drivers as well as get k8s ready
# - ssh into any node of the new cluster
# - install docker ce
# $apt-get remove docker docker-engine docker.io
# $apt-get update
# $apt-get install apt-transport-https ca-certificates curl software-properties-common
# $curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# $add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
# $apt-get update
# $apt-get install docker-ce

# remove old nvidia-docker version
# $docker volume ls -q -f driver=nvidia-docker | xargs -r -I{} -n1 docker ps -q -a -f volume={} | xargs -r docker rm -f
# $apt-get purge nvidia-docker

# install nvidia-docker2
# $curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
# $curl -s -L https://nvidia.github.io/nvidia-docker/ubuntu16.04/amd64/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
# $apt-get update
# $apt-get install nvidia-docker2
# $pkill -SIGHUP dockerd

RUN apt-get update -y
RUN apt-get install -y zlib1g-dev
RUN apt-get install -y --no-install-recommends tzdata python3 python3-dev python3-pip python3-setuptools git dos2unix net-tools iproute2 iputils-ping telnet lsb-release curl
RUN apt-get install -y python3-setuptools --upgrade
RUN apt-get install -y build-essential cmake
RUN pip3 install --upgrade pip
RUN pip3 install wheel numpy msgpack msgpack-numpy pydevd dm-sonnet cached_property scipy cython matplotlib pygame msgpack-python pillow virtualenv virtualenvwrapper python-dateutil gym
RUN pip3 install gym[atari]

## link python3
#RUN ln -s /usr/bin/python3 /usr/bin/python

# install tensorforce manually (to support latest dev branch)
RUN echo "b"
RUN git clone https://github.com/ducandu/tensorforce
WORKDIR tensorforce
RUN git checkout master
RUN git pull
RUN python setup.py install
WORKDIR ../

# add the experiment script
RUN mkdir /run_container
COPY experiment.py /run_container/
WORKDIR /run_container

CMD ["bash"]
