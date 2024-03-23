import copy
from queue import PriorityQueue

from computing.task_dispatcher.env.edgenode import EdgeNode, Sensor, EdgeNodeNetwork
from computing.task_dispatcher.utils import taskreader
from computing.task_dispatcher.utils.taskreader import Task

sensor_template = {
    1: Sensor("Lidar", 1, {"frame_size": 400, "fps": 10}, -1),
    2: Sensor("Camera", 2, {"frame_size": 500, "fps": 20}, -1),
    3: Sensor("Thermal", 3, {"frame_size": 160, "fps": 20}, -1),
}

n_node = 12
bw_link = 1e4
bw_self = 1e9
bw_2hops = 1e-9

nodes = []
sensor_install_list = [[], [1, 2], [2], [1, 3], [3], [2, 3], [], [1, 2], [], [1], [2], [1], []]
bandwidth_map = dict()


def bandwidth_map_setup():
    for i in range(1, n_node + 1):
        bandwidth_map[(i, i)] = bw_self
        bandwidth_map[(i, i + 1)] = bw_link
        bandwidth_map[(i + 1, i)] = bw_link

        for j in range(i + 2, n_node + 1):
            bandwidth_map[(i, j)] = bw_2hops
            bandwidth_map[(j, i)] = bw_2hops


def get_exec_time(node: EdgeNode, task: Task) -> dict[int, float]:
    tasks: list[Task] = copy.copy(node.get_tasklist)
    tasks.append(task)

    execution: dict[int, float] = {}
    total_time = 0.
    for task in tasks:
        total_time += task.fps * task.opt_time[0]
    for task in tasks:
        execution[task.task_id] = total_time / task.fps

    return execution


def get_comm_time(src_id, dst_id, sensor):
    frame_size = sensor.sensor_status["frame_size"]
    comm_time = frame_size / bandwidth_map[(src_id, dst_id)]
    return comm_time


def allocate(candidates: list[Task], nodes: dict[EdgeNode]):
    ordered_queue = PriorityQueue()
    for task in candidates:
        ordered_queue.put((task.priority, task))

    alloc_result: dict[int, tuple[Task, int]] = {c.task_id: (c, -1) for c in candidates}

    while not ordered_queue.empty():
        # Get one task from queue
        _, task = ordered_queue.get()
        sensor_type = task.data_source
        sensor_id = task.sensor_id
        node_id = task.node_id

        # Calculate communication delay for each task on every edge node
        sensor = nodes[node_id].get_sensors[sensor_type][sensor_id]
        trans_delay = {}
        for dst_node in nodes.values():
            trans_delay[dst_node.id] = get_comm_time(node_id, dst_node.id, sensor)

        # Allocate task
        # Sort nodes by communication delay
        node_order = [k for k, v in sorted(trans_delay.items(), key=lambda item: item[1])]

        # Variable to store allocation results
        current_node = None
        current_workload = float("inf")

        temp_node = None
        temp_workload = None

        # From node with the lowest communication delay to highest
        for i in node_order:
            node = nodes[i]
            trans_time = trans_delay[i]
            # If communication delay is larger than the deadline, stop searching
            if trans_time > task.deadline:
                break

            # Execution time if allocating current task on the node
            exec_time = get_exec_time(node, task)
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
                temp_workload = sum([t.opt_time[0] / t.deadline for t in tasks])
                if temp_workload < current_workload:
                    current_workload = temp_workload
                    current_node = temp_node

        # Remove allocated task from the candidate list
        if current_node is not None:
            current_node.insert_task(task)
            candidates.remove(task)
            alloc_result[task.task_id] = (task, current_node.id)

    # formatted result output
    id_w, src_w, dst_w, task_w = 8, 5, 5, max(len(v[0].model_id) for v in alloc_result.values()) + 2
    width = id_w + src_w + dst_w + task_w
    print(f'#{"allocation result":-^{width}s}#')
    print(f'{"taskid":^{id_w}s}{"src":^{src_w}s}{"dst":^{dst_w}s}{"task":^{task_w}s}')
    for k, v in alloc_result.items():
        print(
            f'{f"{k:06d}":^{id_w}s}{f"{v[0].node_id:02d}":^{src_w}s}{f"{v[1]:02d}":^{dst_w}s}{f"{v[0].model_id:s}":<{task_w}s}')
    print(f'#{"end":-^{width}s}#')


if __name__ == '__main__':
    # build up nodes
    for n in range(1, n_node + 1):
        nodes.append(EdgeNode(n, sensor_install_list[n], sensor_template, ip_addr=f"10.0.1.{n:d}"))

    # build up node network
    edge_network = EdgeNodeNetwork(nodes)
    bandwidth_map_setup()

    # set up tasks
    db = taskreader.DBReader()
    task_list = db.task_list

    # execute allocation
    allocate(task_list, edge_network.get_nodes)
