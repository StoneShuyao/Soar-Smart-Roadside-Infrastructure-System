# Soar-Computing

## Hardware

Master side:
A minimum master node configuration is:
4 CPU cores
8GB RAM
40GB hard disk space in the /var directory

Edge side:
NVIDIA Jetson TX2 (8GB) + 300GB storage or above

## Installation

Following the [website](https://kubeedge-docs.readthedocs.io/en/latest/setup/kubeedge_install.html) to install KubeEdge on master side and edge side.

Set up the [iperf3](https://iperf.fr/iperf-doc.php) server and testing script (.\local_exe\network_test\iperf) on the edge nodes by using crontab.

Set up the connection by running .\local_exe\task_monitor.py between master node and edge nodes.

### Build containers

On edge node,

```bash
sudo docker build -t testbed-master:5000/system:v0.0.1 -f ./local_exe/Dockerfile .
```

After building, push the container to the server,

```bash
sudo docker push testbed-master:5000/system:v0.0.1
```

Pull containers from the server,

```bash
sudo docker image list

sudo docker pull testbed-master:5000/system:v0.0.1
```

Deploy containers on each edge node,

```bash
kubectl apply -f test.yaml

kubectl apply -f testbed_code/src/application/container-baseline.yaml
```

### Run

On edge nodes,

```bash
ros2 run img_publisher img_publisher
```

On the server,

```bash
python3 run.py
```
