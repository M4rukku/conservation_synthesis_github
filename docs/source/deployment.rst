Setup
************************

Deploying the application
=========================

This writeup summarize the process of deploying the application onto a
computer. I try to be as detailed as possible, but if you run into any
trouble, please tell me.

    This writeup assume you have sufficient hardware, and due to the
    nature of ``CUDA`` runtime requirement, the machine hardware must
    consists of a ``CUDA`` compatiable graphics card with sufficient
    VRAM (>4G, strongle recomend >= 6G) and should be at least GTX 900
    series.

Installing Ubuntu on Your Computer
==================================

For compatiability reason, this writeup chooses ``ubuntu 18.04LTS`` and
non-headless desktop image, but if you want to work only with CLI
interface than ubuntu server could be fine as well.

Please download the Ubuntu release image from `ubuntu download
page <https://releases.ubuntu.com/18.04.5/>`__ and follow the
installation guide from
`here <https://ubuntu.com/tutorials/install-ubuntu-desktop#1-overview>`__.

Please note that due to the image size, I recomend at least provision
**100G** of hard drive for the ubuntu system.

Installing NVIDIA Driver on Ubuntu
==================================

This is a rather painful step because the NVIDIA driver is propriteary
to NVIDIA. We need to install this so that the NGC container can work.

For reference, you can see this
`writeup <https://gist.github.com/wangruohui/df039f0dc434d6486f5d4d098aa52d07>`__

The following writeup would try a easier way with default driver
installable from ubuntu repository. We will use the well maintained
graphics-driver ppa for the latest nvidia driver.

.. code:: bash

    sudo add-apt-repository ppa:graphics-drivers/ppa
    sudo apt update

auto install the recommended drivers

.. code:: bash

    sudo ubuntu-drivers autoinstall

After the install finished, **reboot** your system.

installing CUDA toolkit with latest version. you can check `nvidia quick
start
guide <https://docs.nvidia.com/cuda/cuda-quick-start-guide/index.html#ubuntu-x86_64-run>`__
as well.

.. code:: bash

    wget https://developer.download.nvidia.com/compute/cuda/11.2.1/local_installers/cuda_11.2.1_460.32.03_linux.run
    sudo sh cuda_11.2.1_460.32.03_linux.run

You can check that the NVIDIA Driver and CUDA runtime are install
successfully with nvidia-smi:

.. code:: bash

    nvidia-smi

which should give you a table like this:

::

    +-----------------------------------------------------------------------------+
    | NVIDIA-SMI 375.66                 Driver Version: 375.66                    |
    |-------------------------------+----------------------+----------------------+
    | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
    | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
    |===============================+======================+======================|
    |   0  Tesla K80           Off  | 0000:00:04.0     Off |                    0 |
    | N/A   33C    P8    29W / 149W |      0MiB / 11439MiB |      0%      Default |
    +-------------------------------+----------------------+----------------------+

    +-----------------------------------------------------------------------------+
    | Processes:                                                       GPU Memory |
    |  GPU       PID  Type  Process name                               Usage      |
    |=============================================================================|
    |  No running processes found                                                 |
    +-----------------------------------------------------------------------------+

Deploying the application
=========================

Following the step, the deployment of the application is made relatively
painless. simply head to the code folder and deploy follow the
instruction

The following provide an example of bash console command, assuming that
the code provided is under your home folder ``~``

.. code:: bash

    cd ~/conservation_synthesis_github
    cd docker
    docker-compose up -d

after the initalization process is finished(which takes some time due to
the large amount of docker containers pulled), you can use the
webservice now on http://127.0.0.1:5000

for the computer other than the host to visit the webservice, you can
use http://YOUR\_IP\_ADDRESS:5000

Execution
*******************************

Deploying with docker
=====================

This project use NGC docker image to deploy.

Please install docker-compose and docker-engine if you haven'd done so

::

    ./install_docker_engine.sh

deploying the webapp from docker-compose

::

    #this comand is not production ready yet.
    docker-compose up

After the docker finished initalization(it takes quite long first time
as ngc docker image are large), you can checkout the webapp that would
be running at `website <http://127.0.0.1:5000>`__