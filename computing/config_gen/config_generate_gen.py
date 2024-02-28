import os
import json
import json5
import argparse
from configparser import ConfigParser
import configparser
from dataclasses import dataclass
import numpy as np
import math


node_allocation_file_name = "node-allocation-indoor.json"
deadline = [249,301,245,248,252]   # len( number of tasks)
prioprity_index = np.argsort(np.array(deadline))
print(prioprity_index)
prioprity = [0] * len(deadline)
for index in range(len(deadline)):
    prioprity[index] = np.where(prioprity_index==index)[0][0] + 1
print(prioprity)
mis_bound = (0.1*np.ones(len(deadline))).tolist()
fps = [math.ceil(1 / int(app_deadline) *1000) for app_deadline in deadline] # len( number of tasks)
class SensorIni:
    sensor_type: str = "thermal-1" # "sensor type"-"number of thermal on the sensor"
    sensor_name: str
    sensor_position: str ## node name
    sensor_status: dict
    sensor_id: int = -1

@dataclass
class TaskInit:
    deadline: int = 100
    priority: int = 1
    miss_bound: float = 0.1
    app_template_name: str = "thermal-app.ini"

@dataclass
class Sensor:
    name: str
    sensor_type: int
    sensor_status: dict
    position: int = -1
    sensor_template_name: str = "thermal-sensor.ini"
    sensor_app_template_name: str = "thermal-app.ini"


## structure for node-sensor, task:

# @dataclass
class SensorIni:
    sensor_type: str = "thermal-1" # "sensor type"-"number of thermal on the sensor"
    sensor_name: str
    sensor_position: str ## node name
    sensor_status: dict
    sensor_id: int = -1

@dataclass
class Task:
    task_id: int
    model_id: str
    data_source: int  # Lidar: 0, Radar: 1, Thermal: 2
    deadline: float  # Deadline for each job, depends on for what kind of tasks (e.g. Detection, Tracking)
    node_id: int  # node_id
    sensor_id: int  # sensor id on that node
    miss_bound: float  # TODO: add initialization of miss rate bound
    opt_batch: int
    opt_time: list
    fps: float = None
    miss_weight: int = 1
    priority: int = None  # Higher priority has smaller value
    last_deploy: str = None

def gen_sensor_config(modelname1,modelname2):
    parser = argparse.ArgumentParser(description="generate application config file")
    parser.add_argument("--template_path", default="template", type=str, help="template path")
    parser.add_argument("--save_path", default="save_path", type=str, help="save path")
    args = parser.parse_args()
    abs_path = os.path.abspath('.')
    config_file = abs_path + '/template/thermal-sensor.ini'
    config_data = configparser.ConfigParser()
    config_data.sections()
    config_data.read(config_file)
    config_data.get('Application', 'modelname1')
    config_data.get('Application', 'modelname2')
    config_data.items('Application')
    config_data.set('Application', 'modelname1', modelname1)
    config_data.set('Application', 'modelname2', modelname2)
    with open(config_file, 'w') as configfile:
        config_data.write(configfile)
    print(config_data.get('Application', 'modelname1'))
    print(config_data.get('Application', 'modelname2'))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="generate app and sensor  config file")
    parser.add_argument("--template_path", default="template", type=str, help="template path")
    parser.add_argument("--save_path", default="save_path", type=str, help="save path")
    args = parser.parse_args()
    save_paths = os.path.join(args.save_path,node_allocation_file_name[:-5])
    if not os.path.exists(save_paths):
        os.mkdir(save_paths)
    #load node allocation json file
    abs_path = os.path.abspath('.')
    # node_allocation_json = os.path.join(args.template_path,"node-allocation.json")
    with open(os.path.join(args.template_path,node_allocation_file_name)) as node_allocate_file:
        node_allocation = json5.load(node_allocate_file)
    sensor_template = {
    # TODO: modify according to the experiments setting
    1: Sensor("Lidar", 1, {"frame_size": 300, "fps": 10}, -1,"lidar-sensor.ini","lidar-app.ini"),
    2: Sensor("Camera", 2, {"frame_size": 200, "fps": 25}, -1,"camera-sensor.ini","camera-app.ini"),
    3: Sensor("Thermal", 3, {"frame_size": 20, "fps": 20}, -1,"thermal-sensor.ini","thermal-app.ini")
    }
    # sensor
    sensor_lists = []
    sensor_num_node_per_type = []
    sensor_type_ini = []
    sensor_position =[]
    sensor_type = []
    sensor_node_number =[]
    sensor_num_all =[]
    task_lists =[]
    task_lists_node_num =[]
    task_lists_sensor_num =[]
    task_lists_sensor_type=[]
    ## get the related sensor and node_structure

    for node in node_allocation:
        sensor_numer_on_node_lidar = 0
        sensor_numer_on_node_camera = 0
        sensor_numer_on_node_thermal = 0

        for sensors in node_allocation[node]:
            if "sensor" in sensors:
                sensor_lists.append(sensors)
                sensor_position.append(node_allocation[node]["name"])
                sensor_type.append(node_allocation[node][sensors]["sensortype"])
                sensor_node_number.append(node)
                # sensor_lists_per_node.append(sensors)
                if node_allocation[node][sensors]["sensortype"] == "1":
                    sensor_numer_on_node_lidar  = sensor_numer_on_node_lidar +1
                    sensor_num_node_per_type.append(sensor_numer_on_node_lidar)
                    tmpt = 'lidar-' + str(sensor_numer_on_node_lidar)
                    sensor_type_ini.append(tmpt)
                elif node_allocation[node][sensors]["sensortype"] == "2":
                    sensor_numer_on_node_camera  = sensor_numer_on_node_camera +1
                    tmpt = 'camera-' + str(sensor_numer_on_node_camera)
                    sensor_type_ini.append(tmpt)
                    sensor_num_node_per_type.append(sensor_numer_on_node_camera)
                else:
                    sensor_numer_on_node_thermal  = sensor_numer_on_node_thermal +1
                    tmpt = 'thermal-' + str(sensor_numer_on_node_thermal)
                    sensor_type_ini.append(tmpt)
                    sensor_num_node_per_type.append(sensor_numer_on_node_thermal)

                if isinstance(node_allocation[node][sensors]["tasklists"],list):
                    for task_per_sensor in node_allocation[node][sensors]["tasklists"]:
                        task_lists.append(task_per_sensor)
                        task_lists_node_num.append(node)
                        task_lists_sensor_num.append(sensors)
                        task_lists_sensor_type.append(node_allocation[node][sensors]["sensortype"])
                else:
                    task_lists.append(node_allocation[node][sensors]["tasklists"])
                    task_lists_node_num.append(node)
                    task_lists_sensor_num.append(sensors)
                    task_lists_sensor_type.append(node_allocation[node][sensors]["sensortype"])

    # get the sensor number on the  node
    sensor_ids = []
    sensor_starts =[]
    for num_sensor_config in range(len(sensor_lists)):
        # sensor filename：sensor_id = sensor.position（which node） *10000 + sensor_type_id * 100 + sensor node - sensor id
        senser_id = int(sensor_node_number[num_sensor_config].strip('node')) * 10000 + int(sensor_type[num_sensor_config])* 100 + int(sensor_num_node_per_type[num_sensor_config])
        sensor_ids.append(senser_id)
        sensor_type_config = sensor_type_ini[num_sensor_config]
        start = int(sensor_lists[num_sensor_config].strip('sensor')) * 1000
        sensor_starts.append(start)
        abs_path = os.path.abspath('.')
        sensor_type_id = int(sensor_type[num_sensor_config])
        sensor_config_file_name = sensor_template[sensor_type_id].sensor_template_name
        config_file = abs_path + '/template/' + sensor_config_file_name
        sensor_config_file = 'sensor' + str(senser_id) + '.ini'
        gen_sensor_config = abs_path + '/' + save_paths + '/' + sensor_config_file

        config_data = configparser.ConfigParser()
        config_data.read(config_file)
        # config_data.set('Sensor', 'type',sensor_type_config) # Modify sensor type in sensor.ini
        config_data.set('Sensor', 'position', sensor_position[num_sensor_config])
        config_data.set('Queue', 'start',str(start))
        with open(gen_sensor_config, 'w') as configfile:
            config_data.write(configfile)

    for task_num in range(len(task_lists)):
        #appid =  Node_id * 10000 +sensor type * 100 + task_id
        appid = int(task_lists_node_num[task_num].strip('node'))* 10000 + int(task_lists_sensor_type[task_num])* 100 + int(task_lists[task_num].strip('task'))
        # print(appid)
        app_miss_bound = mis_bound[task_num]
        app_deadline = deadline[task_num]
        app_fps = fps[task_num]
        # app_fps = math.ceil(1 / int(app_deadline) *1000)
        app_priority = prioprity[task_num]
        app_node_id = task_lists_node_num[task_num].strip('node')
        app_sensortype = task_lists_sensor_type[task_num]

        loc = sensor_lists.index(task_lists_sensor_num[task_num])
        task_sensor_id = sensor_ids[loc]
        app_sensor_start = sensor_starts[loc]

        pre_msgkey = str(appid) + str(1)
        pre_start = str(app_priority) + str(100)
        infer_msgkey = str(appid) + str(2)
        infer_start =  str(app_priority) + str(200)
        post_msgkey = str(appid) + str(3)
        post_start = str(app_priority) + str(300)

        abs_path = os.path.abspath('.')
        sensor_type_id = int(task_lists_sensor_type[task_num])
        app_config_file_name = sensor_template[sensor_type_id].sensor_app_template_name
        config_file = abs_path + '/template/' + app_config_file_name
        app_config_file = 'app' + str(appid) + '.ini'

        gen_app_config = abs_path + '/' + save_paths + '/' + app_config_file

        config_data = configparser.ConfigParser()
        config_data.read(config_file)
        config_data.set('Application', 'appid', str(appid))
        config_data.set('Application', 'deadline', str(app_deadline))
        config_data.set('Application', 'fps', str(app_fps))
        config_data.set('Application', 'miss_bound', str(app_miss_bound))
        config_data.set('Application', 'priority', str(app_priority))
        config_data.set('Application', 'sensorid', str(task_sensor_id))
        config_data.set('Application', 'nodeid', str(app_node_id))
        config_data.set('Application', 'sensortype', str(app_sensortype))

        config_data.set('Queue', 'sensor_start', str(app_sensor_start))
        config_data.set('Queue', 'pre_msgkey', str(pre_msgkey))
        config_data.set('Queue', 'infer_msgkey', str(infer_msgkey))
        config_data.set('Queue', 'infer_start', str(infer_start))
        config_data.set('Queue', 'post_msgkey', str(post_msgkey))
        config_data.set('Queue', 'post_start', str(post_start))
        config_data.set('Queue', 'pre_start', str(pre_start))

        with open(gen_app_config, 'w') as configfile:
            config_data.write(configfile)