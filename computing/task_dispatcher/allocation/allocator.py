import copy
import pickle
import time
from queue import PriorityQueue

from collections import defaultdict


def recursive_defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: recursive_defaultdict_to_dict(v) for k, v in d.items()}
    return d


class Allocator:
    def __init__(self, task_list, edge_network, deploy_queue, bw_queue):
        # The task set
        self.task_list = task_list

        # The tasks need to be allocated
        self.candidates = [task for task in task_list]
        
        # Edge nodes
        self.nodes = edge_network.get_nodes
        
        # A list store the bandwidth among edge nodes
        self.bandwidth_map = {}

        # The queue to store allocated task and pass the allocation to deployment process
        self.deploy_queue = deploy_queue
        
        # The queue to store bandwidth and get the bandwidth from bandwidth monitor process
        self.bw_queue = bw_queue

        self.init = True

        self.update_comm_time()


    def update_comm_time(self):
        # Waiting for the bandwidth results for 1 min
        if self.init:
            time.sleep(60)
        # Read the bandwidth from bandwidth monitor process
        bw_dict = self.bw_queue.get()

        # Fill the bandwidth into bandwidth map
        for node in self.nodes.values():
            nodename = 'testbed-{0:02d}'.format(node.id)
            bandwidth_dict = pickle.loads(bw_dict[nodename])
            for dst_id, bandwidth in bandwidth_dict.items():
                self.bandwidth_map[(node.id, dst_id)] = bandwidth


    def get_task(self, task_id):
        for t in self.task_list:
            if t.task_id == task_id:
                return t


    # Calculate the communication delay
    def get_comm_time(self, src_id, dst_id, sensor):
        frame_size = sensor.sensor_status["frame_size"]
        comm_time = frame_size / self.bandwidth_map[(src_id, dst_id)]
        return comm_time


    # Calculate the execution time
    def get_exec_time(self, node, task):
        tasks = copy.copy(node.get_tasklist)
        tasks.append(task)

        execution = {}
        total_time = 0.
        for task in tasks:
            total_time += task.fps * task.opt_time[0]
        for task in tasks:
            execution[task.task_id] = total_time / task.fps
        
        return execution
    

    def allocate(self):
        ordered_queue = PriorityQueue()
        for task in self.candidates:
            ordered_queue.put((task.priority, task))

        while not ordered_queue.empty():
            # Get one task from queue
            _, task = ordered_queue.get()
            sensor_type = task.data_source
            sensor_id = task.sensor_id
            node_id = task.node_id

            # Calculate communication delay for each task on every edge node
            sensor = self.nodes[node_id].get_sensors[sensor_type][sensor_id]
            trans_delay = {}
            for dst_node in self.nodes.values():
                trans_delay[dst_node.id] = self.get_comm_time(node_id, dst_node.id, sensor)

            # Allocate task
            # Sort nodes by communication delay
            node_order = [k for k, v in sorted(trans_delay.items(), key=lambda item: item[1])]
  
            # Variable to store allocation results
            current_node = None
            current_workload = float("inf")

            temp_node = None
            temp_workload = None
            
            # From node with lowest communication delay to highest
            for i in node_order:
                node = self.nodes[i]
                trans_time = trans_delay[i]
                # If communication delay is larger than the deadline, stop searching
                if trans_time > task.deadline:
                    break
                
                # Execution time if allocating current task on the node
                exec_time = self.get_exec_time(node, task)
                # Get allocated tasks on that node
                tasks = copy.copy(node.get_tasklist)
                tasks.append(task)

                # Count to check how many tasks have been successfully allocated on the node
                allocated_task_num = 0
                for t in tasks:
                    # Total delay for the task
                    total_delay = exec_time[t.task_id] + trans_time
                    # If the total delay of the task is less than its deadline, allocating it on the node
                    if total_delay <= t.deadline:
                        allocated_task_num += 1
                        temp_node = node
                    else:
                        break

                # If there are multiple nodes can be selected, choose the one with the lowest workload
                if allocated_task_num == len(tasks):
                    temp_workload = sum([t.opt_time[0]/t.deadline for t in tasks])
                    if temp_workload < current_workload:
                        current_workload = temp_workload
                        current_node = temp_node
                    
            # Remove allocated task from the candidate list
            if current_node is not None:
                current_node.insert_task(task)
                self.candidates.remove(task)
        
        self.init = False
        
        # Deploy the allocated tasks
        self.deploy_tasks()


    def deploy_tasks(self):
        deployed_dict = defaultdict(lambda: defaultdict(list))

        for node in self.nodes.values():
            nodename = 'testbed-{0:02d}'.format(node.id)
            task_list = node.get_tasklist    
            for task in task_list:
               deployed_dict[nodename][task.sensor_id].append(task.task_id)
        
        deployed_dict = recursive_defaultdict_to_dict(deployed_dict)
        
        self.deploy_queue.put(deployed_dict)
        
        if self.deploy_queue.qsize() > 1:
            self.deploy_queue.get()

