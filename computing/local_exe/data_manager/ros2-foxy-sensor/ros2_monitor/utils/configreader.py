import fnmatch
import os
from configparser import ConfigParser

import numpy as np

np.__version__


class AppConfig:
    def __init__(self, config_path):
        config = ConfigParser()
        config.read(config_path)

        self.appID = int(config["Application"]["AppID"])
        self.shape = eval(config["Application"]["DataShape"])
        self.pre_datashape = eval(config["Application"]["PreDataShape"])
        self.model_name1 = config["Application"]["ModelName1"]
        self.model_name2 = config["Application"]["ModelName2"]
        self.deadline = int(config["Application"]["Deadline"])
        self.data_size = int(config["Application"]["DataSize"])
        self.pre_data_size = int(config["Application"]["PreDataSize"])

        self.sensor_data_type = eval(config["Application"]["SensorDataType"])
        self.pre_data_type = eval(config["Application"]["PreDataType"])

        self.sensor_key = int(config["Queue"]["Sensor_Start"])
        self.pre_msgkey = int(config["Queue"]["Pre_MsgKey"])
        self.pre_start = int(config["Queue"]["Pre_Start"])
        self.infer_msgkey = int(config["Queue"]["Infer_MsgKey"])
        self.infer_start = int(config["Queue"]["Infer_Start"])

        self.profile = eval(config["Profile"]["BatchedExecution"])
        self.engine1 = config["Profile"]["EnginePath1"]
        self.engine2 = config["Profile"]["EnginePath2"]

        self.optbatch = int(config["Profile"]["optbatch"])


class DBReader:
    def __init__(self, path="config/system-test", config_name="app*.ini"):
        self._path = path
        self._config_name = config_name
        self.appdb = {}
        self._read_from_config()

    def _read_from_config(self):
        # model_name_list = []
        # pre_data_shapes = []
        # queue_keys = []
        # deadlines = []
        # profiles = []
        # sensor_data_types = []
        # pre_data_types = []
        # sensor_start_keys = []

        f_names = []
        for f_name in os.listdir(self._path):
            if fnmatch.fnmatch(f_name, self._config_name):
                f_names.append(f_name)

        f_names.sort(key=lambda x: (int(x[3:-4])))
        for f_name in f_names:
            f_name = os.path.join(self._path, f_name)
            app = AppConfig(f_name)
            self.appdb[app.appID] = app.__dict__


if __name__ == "__main__":
    db = DBReader(path="../config/node-1")
    deployed_app = [10201, 10202]
    model_pool = {}
    max_batch_size = 0
    for app in deployed_app:
        if len(db.appdb[app]["profile"]) > max_batch_size:
            max_batch_size = len(db.appdb[app]["profile"])
        if db.appdb[app]["model_name"] not in model_pool:
            model_pool[db.appdb[app]["model_name"]] = [db.appdb[app]]
        else:
            model_pool[db.appdb[app]["model_name"]].append(db.appdb[app])
        print(db.appdb[app]["optbatch"])
