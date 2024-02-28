import logging
import multiprocessing as mp
import pickle
import time
from multiprocessing import Queue

from allocation import master_server
from allocation.allocator import Allocator
from env.edgenode import EdgeNode, EdgeNodeNetwork, Sensor
from utils import taskreader

# The IP address of the cluster-level dispatcher
HOST = ""

# The port number of bandwidth monitor
BW_PORT=12345

# The port number of deployment service
DP_PORT=23451


# Define the sensor template
# sensor_template: A dictionary containing different types of sensors and their properties
# Each sensor is represented by a unique identifier and has a name (e.g. Lidar,  Thermal, etc.), type id, status, frame size in kb, and frames per second
sensor_template = {
    1: Sensor("Lidar", 1, {"frame_size": 400, "fps": 10}, -1),
    2: Sensor("Camera", 2, {"frame_size": 500, "fps": 20}, -1),
    3: Sensor("Thermal", 3, {"frame_size": 160, "fps": 20}, -1), 
}


def run(bw_queue, deploy_queue):
    # Start the allocator
    logging.info("Allocator starts")
    
    # Create a list to store EdgeNode objects
    nodes = []

    # Create EdgeNode objects and add them to the nodes list
    # Each EdgeNode object represent one soar node, which contains the node id, sensors and ip address
    node_1 = EdgeNode(1, [2], sensor_template, ip_addr="10.0.1.1")
    nodes.append(node_1)
    node_2 = EdgeNode(2, [2, 3], sensor_template, ip_addr="10.0.1.2")
    nodes.append(node_2)
    node_3 = EdgeNode(3, [3], sensor_template, ip_addr="10.0.1.3")
    nodes.append(node_3)


    # Build the connection map of the edge nodes
    edge_network = EdgeNodeNetwork(nodes)


    # Read all tasks from files
    
    db = taskreader.DBReader()
    task_list = db.task_list

    # Call allocator to dispatch tasks
    allocator = Allocator(task_list, edge_network, deploy_queue, bw_queue)
    # Update communication bandwidth among edge nodes
    allocator.update_comm_time()
    # Allocate tasks to edge nodes
    allocator.allocate()


# Collect the communication bandwidth among edge nodes
def bw_monitor(queue):
    logging.info("Bandwidth monitor launched.")
    host = HOST
    port = BW_PORT
    addr = (host, port)
    server = master_server.CrossThreadingTCPServer(addr, master_server.receive_handler, queue)
    server.serve_forever()


# The deployment process to send allocated tasks to edge nodes
def deploy_process(queue):
    logging.info("Deployment process launched.")
    host = HOST
    port = DP_PORT
    addr = (host, port)
    server = master_server.CrossThreadingTCPServer(addr, master_server.send_handler, queue)
    server.serve_forever()


if __name__ == '__main__':
    0
    bw_queue = Queue(maxsize=2)
    deploy_queue = Queue(maxsize=2)

    processes = []
    alloc_process = mp.Process(target=run, args=(bw_queue, deploy_queue))
    processes.append(alloc_process)

    bw_process = mp.Process(target=bw_monitor, args=(bw_queue))
    processes.append(bw_process)

    dp_process = mp.Process(target=deploy_process, args=(deploy_queue))
    processes.append(dp_process)

    [p.start() for p in processes]
    [p.join() for p in processes]
 