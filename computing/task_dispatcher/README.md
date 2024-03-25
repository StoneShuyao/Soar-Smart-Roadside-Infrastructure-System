## A Quick Demo of Cluster-level Task Dipatching

### demo.py

- Set the number of nodes and the sensor configuration of each node, e.g.,
```
sensor_template = {
    1: Sensor("Lidar", 1, {"frame_size": 400, "fps": 10}, -1),
    2: Sensor("Camera", 2, {"frame_size": 500, "fps": 20}, -1),
    3: Sensor("Thermal", 3, {"frame_size": 160, "fps": 20}, -1),
}

n_node = 12
nodes = []
sensor_install_list = [[], [1, 2], [2], [1, 3], [3], [2, 3], [], [1, 2], [], [1], [2], [1], []]
```

- Set the tasks to execute by add config files in the ./config/.

- Manually set the bandwidth between each pair of Soar nodes in the cluster. 
(In real-world experiments, each node periodically measures the I2I bandwidth to others and update it to the server to maintain the bandwidth map)
```
bandwidth_map = dict()
bw_link = 1e4
bw_self = 1e9
bw_2hops = 1e-9

def bandwidth_map_setup():
    for i in range(1, n_node + 1):
        bandwidth_map[(i, i)] = bw_self
        bandwidth_map[(i, i + 1)] = bw_link
        bandwidth_map[(i + 1, i)] = bw_link

        for j in range(i + 2, n_node + 1):
            bandwidth_map[(i, j)] = bw_2hops
            bandwidth_map[(j, i)] = bw_2hops
```

- Run the demo.
```
python demo.py
```