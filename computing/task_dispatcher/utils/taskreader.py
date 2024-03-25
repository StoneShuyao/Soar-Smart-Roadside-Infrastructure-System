import fnmatch
import os
from configparser import ConfigParser

import numpy as np
from dataclasses import dataclass

# Bypass library not using warning
np.__version__


@dataclass
class Task:
    task_id: int
    # model name
    model_id: str
    # sensor type: Lidar: 0, Radar: 1, Thermal: 2
    data_source: int
    # Deadline (ms) for each job, depends on for what kind of tasks (e.g. Detection, Tracking)
    deadline: float
    # Edge node id
    node_id: int 
    # Sensor id on the node
    sensor_id: int
    miss_bound: float  # TODO: add initialization of miss rate bound
    opt_batch: int
    opt_time: list
    fps: float = None
    miss_weight: int = 1
    priority: int = None  # Higher priority has smaller value
    last_deploy: str = None


class AppConfig:
    def __init__(self, config_path):
        config = ConfigParser()
        config.read(config_path)

        self.appID = int(config["Application"]["AppID"])
        self.shape = eval(config["Application"]["DataShape"])
        self.pre_datashape = eval(config["Application"]["PreDataShape"])
        self.model_name = config["Application"]["ModelName1"]
        self.deadline = float(config["Application"]["Deadline"])
        self.data_size = int(config["Application"]["DataSize"])
        self.pre_data_size = int(config["Application"]["PreDataSize"])

        self.sensor_data_type = eval(config["Application"]["SensorDataType"])
        self.pre_data_type = eval(config["Application"]["PreDataType"])

        self.missbound = float(config["Application"]["Miss_bound"])
        self.priority = int(config["Application"]["Priority"])
        self.sensor_type = int(config["Application"]["SensorType"])

        self.sensor_key = int(config["Queue"]["Sensor_Start"])
        self.pre_msgkey = int(config["Queue"]["Pre_MsgKey"])
        self.pre_start = int(config["Queue"]["Pre_Start"])
        self.infer_msgkey = int(config["Queue"]["Infer_MsgKey"])
        self.infer_start = int(config["Queue"]["Infer_Start"])

        self.profile = eval(config["Profile"]["BatchedExecution"])
        self.engine = config["Profile"]["EnginePath1"]

        self.sensor_id = int(config["Application"]["SensorID"])
        self.node_id = int(config["Application"]["NodeID"])

        self.fps = float(config["Application"]["FPS"])
        self.opt_time = eval(config["Profile"]["OptTime"])


class DBReader:
    def __init__(self, path="config", config_name="app*.ini"):
        self._path = path
        self._config_name = config_name
        self.task_list = []
        self._read_task_from_config()

    def _read_task_from_config(self):
        f_names = []
        for f_name in os.listdir(self._path):
            if fnmatch.fnmatch(f_name, self._config_name):
                f_names.append(f_name)

        f_names.sort(key=lambda x: (int(x[3:-4])))
        for f_name in f_names:
            f_name = os.path.join(self._path, f_name)
            app = AppConfig(f_name)

            task = Task(
                task_id=app.appID,
                model_id=app.model_name,
                data_source=app.sensor_type,
                deadline=app.deadline / 1000.,
                node_id=app.node_id,
                sensor_id=app.sensor_id,
                miss_bound=app.missbound,
                opt_batch=1,
                opt_time=app.opt_time,
                fps=app.fps,
                # miss_weight: int = 1
                priority=app.priority
            )
            self.task_list.append(task)


if __name__ == "__main__":
    db = DBReader(path="../config")

    from collections import OrderedDict
    model2index = {}
    model_index = 0
    for task in db.task_list:
        if task.model_id not in model2index:
            model2index[task.model_id] = model_index
            model_index += 1
    print(model2index)
