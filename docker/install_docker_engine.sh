#!/bin/sh
#setup the repository
sudo apt-get update
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    gnupg-agent \
    software-properties-common

#add docker's official GPG key:
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# setup the stable repository for docker
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

#install docker engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
