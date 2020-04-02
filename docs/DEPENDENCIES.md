# Dependencies

nefarious is best run via [Docker](https://docs.docker.com/install/) through [Docker Compose](https://docs.docker.com/compose/).

Install those two programs and you'll be all set. If your OS isn't listed in the Docker downloads, see the [OS specific instructions below](#os-specific-instructions) below.

## Post Install

Once you have **Docker** and **Docker Compose** installed, run the following commands:
    
    sudo systemctl start docker.service
    sudo systemctl enable docker.service
    sudo groupadd -f docker
    sudo usermod -aG docker $USER
    newgrp docker

This will:

- verify docker is initialized
- add the current user to the docker group
- update the current shell session to use new login group

You'll now be able to run Docker commands without needing to call `sudo` each time.

To ensure that docker is setup correctly,  run the following command which should respond with "success":

    docker run --rm -it --init alpine echo "success"
    
To ensure that docker-compose is installed correctly, just output the version:

    docker-compose --version

## OS specific instructions

Follow some guidelines for installing Docker and Docker Compose for various OS's.

#### Arch

You should be able to install docker and docker-compose from the default Software Center/repositories.

#### Solus OS

You should be able to install docker and docker-compose from the default Software Center/repositories.

#### Ubuntu/Debian

Ensure that git and curl are already installed, then run the following commands:

    sudo apt-get update
    sudo apt-get install -y docker.io
    # this commands refers to the current latest docker compose version of 1.18.0.  See latest versions at https://github.com/docker/compose/releases
    sudo curl -L https://github.com/docker/compose/releases/download/1.18.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

#### Fedora

Install the Docker repository and update metadata cache

    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    sudo dnf makecache

Install docker and docker-compose from repository

    sudo dnf install docker-ce
    sudo dnf -y install docker-compose

At the moment Docker-Compose doesn't fully work without modification on Fedora 31.  30,29,28, and so on should work however.  If you're running Fedora 31, use the following Reddit thread and most recent post at your own discretion. 
https://www.reddit.com/r/Fedora/comments/d8ukd0/has_anyone_managed_to_run_docker_ce_on_fedora_31/

#### Windows

You'll need to ensure that your PC is running a version of Windows 10 64-bit Professional, Education, or Enterprise.
Docker for Windows requires Hyper-V technology, which is not supported by Windows 10 Home.
You'll also need to ensure that your PC has Virtualization enabled in BIOS before attempting to install Docker for Windows.
While nefarious is not by any means a Linux exclusive application, it is much easier to setup on either a Linux based OS, or on a Linux Virtual Machine through your preferred VM software on any actively updated version of Windows.
Consult appropriate documentation relating to said software if you wish to setup folder shares between your Linux VM and your Windows install.  Docker Toolbox is also an option, as it runs docker commands on non-Hyper-V supported OSes by running them through an integrated Linux VM.
If you'd prefer to avoid using something like Virtualbox, VMWare, or other separate Virtualization software, this would would probably work best for you.
That being said, we'd recommend this only be done by experienced users of Docker software.
