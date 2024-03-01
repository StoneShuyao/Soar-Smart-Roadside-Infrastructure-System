import copy
from dataclasses import dataclass


@dataclass
# Each sensor is represented by a unique identifier (sensor_type) and has a name (e.g. Lidar,  Thermal, etc.), type id, status, position, frame size in kb, and frames per second
class Sensor:
    name: str
    sensor_type: int
    sensor_status: dict
    position: int
    sensor_id: int = -1


class EdgeNode:
    def __init__(self, node_id: int, sensors: list, sensor_template, tasklist: list = None, ip_addr=None):
        self.id = node_id
        self._sensordict = {}
        self._generate_sensor_dict(sensors, sensor_template)
        self._tasklist = [] if tasklist is None else tasklist
        self._lasttasklist = []
        self._update_flag = False
        self._connection = []
        self._bandwidth = {}
        self.ip_addr = ip_addr  # add ip address when initialize node
        self.workload = 0

    def _generate_sensor_dict(self, sensors, sensor_template):
        last_type = None
        count = 0

        for i in range(len(sensors)):
            _sensor = copy.deepcopy(sensor_template[sensors[i]])
            _sensor.position = self.id
            if sensors[i] != last_type:
                count = 0
                last_type = sensors[i]
            # ID sensor (outdoor)
            _sensor.sensor_id = _sensor.position*10000 + sensors[i] * 100 + count + 1
            count += 1
           

            if sensors[i] in self._sensordict:
                self._sensordict[sensors[i]][_sensor.sensor_id] = _sensor
            else:
                self._sensordict[sensors[i]] = {_sensor.sensor_id: _sensor}

    @property
    def get_sensors(self) -> dict:
        return self._sensordict

    def insert_task(self, task):
        if not self._update_flag:
            self._lasttasklist = copy.copy(self._tasklist)
        if task in self._tasklist:
            return
        self._update_flag = True
        self._tasklist.append(task)

    def remove_task(self, task):
        if not self._update_flag:
            self._lasttasklist = copy.copy(self._tasklist)
        if task in self._tasklist:
            self._update_flag = True
            self._tasklist.remove(task)

    @property
    def get_tasklist(self):
        return self._tasklist

    def clear_tasklist(self):
        self._tasklist = []

    def is_changed(self):
        if self._update_flag:
            self._update_flag = False
            new_list = [t.task_id for t in self._tasklist]
            old_list = [t.task_id for t in self._lasttasklist]
            return not set(new_list) == set(old_list)
        return False

    def update_tasklist(self, tasklist):
        self._tasklist = tasklist

    @property
    def get_connection(self):
        return self._connection

    @property
    def get_bandwidth(self):
        return self._bandwidth


class EdgeNodeNetwork:
    def __init__(self, nodes) -> object:
        if isinstance(nodes, dict):
            self._nodes = nodes
        else:
            self._node_list2dict(nodes)

        self.connection_map = None
        self.bandwidth_map = None
        self._sensor_positions = {}
        self._update_sensor_position()

    def _node_list2dict(self, lampposts):
        self._nodes = {}
        for _lamppost in lampposts:
            lamppost_id = _lamppost.id
            self._nodes[lamppost_id] = _lamppost


    def _update_sensor_position(self):
        for _node_id, _node in self._nodes.items():
            sensors = _node.get_sensors
            for sensor in sensors:
                self._sensor_positions[_node_id] = {
                    sensor: len(sensors[sensor])}

    @property
    def get_sensor_positions(self) -> dict:
        return self._sensor_positions

    @property
    def get_nodes(self):
        return self._nodes

    def set_workload(self, value):
        self.workload = value
