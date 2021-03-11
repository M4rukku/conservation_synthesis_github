# Deploying the application 

This writeup summarize the process of deploying the application onto a computer. 
I try to be as detailed as possible, but if you run into any trouble, please tell me.

> This writeup assume you have sufficient hardware, and due to the nature of `CUDA` runtime requirement, the machine hardware must consists of a `CUDA` compatiable graphics card with sufficient VRAM (>4G, strongle recomend >= 6G) and should be at least GTX 900 series.

# Installing Ubuntu on Your Computer

For compatiability reason, this writeup chooses `ubuntu 18.04LTS` and non-headless desktop image, but if you want to work only with CLI interface than ubuntu server could be fine as well.

Please download the Ubuntu release image from [ubuntu download page](https://releases.ubuntu.com/18.04.5/) and follow the installation guide from [here](https://ubuntu.com/tutorials/install-ubuntu-desktop#1-overview).

Please note that due to the image size, I recomend at least provision **100G** of hard drive for the ubuntu system.

# Installing NVIDIA Driver on Ubuntu

This is a rather painful step because the NVIDIA driver is propriteary to NVIDIA. We need to install this so that the NGC container can work.

For reference, you can see this [writeup](https://gist.github.com/wangruohui/df039f0dc434d6486f5d4d098aa52d07)

The following writeup would try a easier way with default driver installable from ubuntu repository. We will use the well maintained graphics-driver ppa for the latest nvidia driver.

```bash
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update
```
auto install the recommended drivers
```bash
sudo ubuntu-drivers autoinstall
```
After the install finished, **reboot** your system.

installing CUDA toolkit with latest version. 
you can check [nvidia quick start guide](https://docs.nvidia.com/cuda/cuda-quick-start-guide/index.html#ubuntu-x86_64-run) as well.

```bash
wget https://developer.download.nvidia.com/compute/cuda/11.2.1/local_installers/cuda_11.2.1_460.32.03_linux.run
sudo sh cuda_11.2.1_460.32.03_linux.run
```

You can check that the NVIDIA Driver and CUDA runtime are install successfully with nvidia-smi:
```bash
nvidia-smi
```
which should give you a table like this:
```
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
```

# Deploying the application

Following the step, the deployment of the application is made relatively painless. simply head to the code folder and deploy follow the instruction


The following provide an example of bash console command, assuming that the code provided is under your home folder `~` 

```bash
cd ~/conservation_synthesis_github
cd docker
docker-compose up -d
```

after the initalization process is finished(which takes some time due to the large amount of docker containers pulled), you can use the webservice now on [http://127.0.0.1:5000](http://127.0.0.1:5000)


for the computer other than the host to visit the webservice, you can use http://YOUR_IP_ADDRESS:5000