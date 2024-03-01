import os
import time

import psutil
from configparser import ConfigParser

def get_sensors(filepath, fileprefix, suffix):
    filenames = []
    for filename in os.listdir(filepath):
        if filename.split(".")[-1] == suffix:
            if filename.startswith(fileprefix):
                filenames.append(filename)
    return filenames


def update_deployed_app():
    #  for test
    filenames = get_sensors("/config", "sensor", "ini")
    deployed_app = []
    for filename in filenames:
        filepath = "/config/" + filename
        config = ConfigParser()
        config.read(filepath)
        queue = eval(config['Queue']['QueueKey'])
        for app_id in queue:
            deployed_app.append(app_id)
    return deployed_app


def find_pid_by_cmdline(cmd):
    cmd = cmd.split()
    processes = []
    for proc in psutil.process_iter():
        if proc.cmdline()[-1:] == cmd[-1:]:
            processes.append(proc)
    return processes


def preprocessing_run():
    # num_tasks = 2
    # for i in range(num_tasks):
    #     cmd = "nohup python3 /config/pre_processing/pre_processing.py %d" % (i + 1)
    #     proc = find_pid_by_cmdline(cmd)
    #     if len(proc) > 0:
    #         [p.terminate() for p in proc]
    #     cmd = cmd + " &"
    #     os.system(cmd)

    deployed_app = update_deployed_app()
    for app in deployed_app:
        cmd = "nohup python3 /pre_processing/pre_processing.py %d" % (app)
        proc = find_pid_by_cmdline(cmd)
        if len(proc) > 0:
            [p.terminate() for p in proc]
        cmd = cmd + " &"
        os.system(cmd)

    time.sleep(1)
    #cmd = "nohup python3 /local_scheduler/control.py"
    cmd = "nohup python3 /local_scheduler/control.py"
    proc = find_pid_by_cmdline(cmd)
    if len(proc) > 0:
        [p.terminate() for p in proc]
    time.sleep(1)
    cmd = cmd + " &"
    os.system(cmd)


if __name__ == "__main__":
    preprocessing_run()
