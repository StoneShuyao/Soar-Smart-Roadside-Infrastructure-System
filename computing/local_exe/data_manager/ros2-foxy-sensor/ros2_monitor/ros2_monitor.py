import os
import socket
import time
from configparser import ConfigParser

import psutil

from utils.configreader import AppConfig
from utils.crossqueue import CrossQueue
from prepro4call import preprocessing_run


def find_pid_by_cmdline(cmd):
    cmd = cmd.split()
    processes = []
    for proc in psutil.process_iter():
        if proc.cmdline()[-2:] == cmd[-2:]:
            processes.append(proc)
    return processes


def check_lock(path="/config/sensor.lock"):
    if os.path.exists(path):
        return True
    return False


def get_sensors(filepath, fileprefix, suffix):
    filenames = []
    for filename in os.listdir(filepath):
        if filename.split(".")[-1] == suffix:
            if filename.startswith(fileprefix):
                filenames.append(filename)
    return filenames


def start_preprocessing(app_id):
    client = 'sshpass -p %s ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no %s@%s -p %d' \
             % ("root", "root", "localhost", app_id)
    cmd = 'nohup python3 /start_up.py &'
    send_cmd = " ".join([client, cmd])
    response = 1
    while response != 0:
        response = os.system(send_cmd)
        time.sleep(0.01)


def start_shared_inference():
    client = 'sshpass -p %s ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no %s@%s -p %d' \
             % ("root", "root", "localhost", 22200)
    cmd = 'nohup python3 /start_up.py &'
    send_cmd = " ".join([client, cmd])
    response = 1
    while response != 0:
        response = os.system(send_cmd)
        time.sleep(0.01)


def clear_sharedmemory(path):
    app_config = AppConfig(path)
    q_key = app_config.appID  # Position __, Sensor __, Application __
    app_key = app_config.pre_msgkey
    data_shape = app_config.shape
    data_type = app_config.sensor_data_type
    pre_data_type = app_config.pre_data_type
    pre_data_shape = app_config.pre_datashape
    sensor_key = app_config.sensor_key
    data_size = app_config.data_size
    pre_data_size = app_config.pre_data_size

    # try:
    #     queue = CrossQueue(sensor_key, q_key, data_shape, data_type, data_size, max_length=5,
    #                        flag="IPC_CREX")
    #     queue.remove()
    # except:
    #     pass

    try:
        app_queue = CrossQueue(app_config.pre_start, app_key, pre_data_shape, pre_data_type,
                               max_data_size=pre_data_size, max_length=5, flag="IPC_CREX")
        app_queue.remove()
    except:
        pass

def kill_python_process(port):
    client = 'sshpass -p %s ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no %s@%s -p %d' \
             % ("root", "root", "localhost", port)
    cmd = 'pkill python3'
    send_cmd = " ".join([client, cmd])
    os.system(send_cmd)


def run():
    hostname = socket.gethostname()
    filenames = get_sensors("/config", "sensor", "ini")

    running = False

    for filename in filenames:
        filelock = "/config/" + filename.split(".")[0] + ".lock"
        if check_lock(filelock):
            # kill_python_process(22200)
            config_path = "/config/" + filename
            nodename = "_".join([hostname, filename.split(".")[0]]).replace("-", "_")
            cmd = "nohup ros2 run sensor_subscriber listener --ros-args -r __node:=" + nodename + " -p config_path:=" + config_path
            proc = find_pid_by_cmdline(cmd)
            if len(proc) > 0:
                [p.kill() for p in proc]
            time.sleep(0.1)
            config = ConfigParser()
            config.read(config_path)
            queue = eval(config['Queue']['QueueKey'])
            if len(queue) > 0:
                running = True
                cmd = cmd + " &"
                os.system(cmd)
                time.sleep(3)
                # for app_id in queue:
                #     path = "/config/app%d.ini" % int(str(app_id)[-2:])
                #     clear_sharedmemory(path)
                #     start_preprocessing(app_id)
            os.rename(filelock, "/config/" + filename.split(".")[0] + ".unlock")
        # For Debug
        # config_path = "/config/" + filename
        # nodename = "_".join([hostname, filename.split(".")[0]]).replace("-", "_")
        # cmd = "echo test at %s >> /config/ros2_monitor.py" % str(time.time())
        # proc = find_pid_by_cmdline(cmd)
        # if len(proc) > 0:
        #     [p.kill() for p in proc]
        # time.sleep(0.1)
        # config = ConfigParser()
        # config.read(config_path)
        # queue = eval(config['Queue']['QueueKey'])
        # if len(queue) > 0:
        #     running = True
        #     cmd = cmd + " &"
        #     os.system(cmd)
        #     time.sleep(3)

    if running:
        preprocessing_run()
        # Waiting for the launching of preprocessing
        # time.sleep(3)
        # start_shared_inference()





#
# def run():
#     hostname = socket.gethostname()
#     filenames = get_sensors("/config", "sensor", "ini")
#
#     running = False
#     is_lock = False
#     for filename in filenames:
#         filelock = "/config/" + filename.split(".")[0] + ".lock"
#         if check_lock(filelock):
#             is_lock = True
#             break
#     if is_lock:
#         for filename in filenames:
#             config_path = "/config/" + filename
#             config = ConfigParser()
#             config.read(config_path)
#             queue = eval(config['Queue']['QueueKey'])
#             if len(queue) > 1:
#                 for appid in queue:
#                     kill_python_process(int(appid))
#         kill_python_process(22200)
#         time.sleep(3)
#
#         for filename in filenames:
#             filelock = "/config/" + filename.split(".")[0] + ".lock"
#             config_path = "/config/" + filename
#             nodename = "_".join([hostname, filename.split(".")[0]]).replace("-", "_")
#             cmd = "nohup ros2 run sensor_subscriber listener --ros-args -r __node:=" + nodename + " -p config_path:=" + config_path
#             proc = find_pid_by_cmdline(cmd)
#             if len(proc) > 0:
#                 [p.kill() for p in proc]
#             time.sleep(3)
#             config = ConfigParser()
#             config.read(config_path)
#             queue = eval(config['Queue']['QueueKey'])
#             if len(queue) > 0:
#                 running = True
#                 cmd = cmd + " &"
#                 os.system(cmd)
#                 time.sleep(3)
#                 for app_id in queue:
#                     path = "/config/app%d.ini" % int(str(app_id)[-2:])
#                     clear_sharedmemory(path)
#                     start_preprocessing(app_id)
#             if check_lock(filelock):
#                 os.rename(filelock, "/config/" + filename.split(".")[0] + ".unlock")
#     if running:
#         start_shared_inference()
#         # Waiting for the launching of preprocessing
#         time.sleep(3)


if __name__ == "__main__":
    run()
