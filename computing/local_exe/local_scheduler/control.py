import logging
import multiprocessing as mp
import os
import pickle
import socket
import time
from configparser import ConfigParser

from local_scheduler import scheduler_execution
from model_inference import model_execution
from utils.configreader import DBReader
# from utils.crossqueue import CrossQueue
from inferqueue import InferQueue as CrossQueue


logging.basicConfig(
    filename="/config/local_scheduler.log",
    filemode="a",
    format='[%(asctime)s] [%(levelname)s] [%(processName)s] [%(threadName)s] : %(message)s',
    level=logging.DEBUG)


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


def upload_miss_rate(miss_queue):
    HOST = "10.0.0.2"
    PORT = 23451
    # sock.connect((HOST, PORT))
    while True:
        if miss_queue.empty():
            time.sleep(1)
            continue
        MISSING_RATE = miss_queue.get()
        miss_rate = {}
        for app_id, value in MISSING_RATE.items():
            miss_rate[app_id] = value[1] / value[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.sendall(pickle.dumps(miss_rate))
        time.sleep(1)
        sock.close()


def run():
    # Read all configs from path and build raw_data dict (key: appid)
    db = DBReader(path="/config", config_name="app*.ini")

    # HOST = "137.189.97.26"
    # PORT = 2345
    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.connect((HOST, PORT))
    deployed_app = update_deployed_app()

    # Group them by model
    task_pool = {}
    index = 0
    for app in deployed_app:
        task_pool[db.appdb[app]["appID"]] = [db.appdb[app]]

    manager = mp.Manager()
    # Signal among processes
    start_flag_init = manager.Array("i", [0] * len(task_pool)*2)
    start_lock = manager.Condition()
    end_flag_init = manager.Array("i", [0] * len(task_pool)*2)
    end_lock = manager.Condition()

    # Init process
    # Number of Processes = Number of Models + one Local Scheduler + one updater
    process_pool = mp.Pool(len(task_pool)*2 + 2)

    task_index = 0
    for task in task_pool:
        CrossQueue(task_pool[task][0]['post_start'],
                   task_pool[task][0]['post_msgkey'],
                   task_pool[task][0]['post_datashape'],
                   task_pool[task][0]['post_data_type'],
                   max_data_size=task_pool[task][0]['post_data_size'],
                   max_length=5,
                   flag="IPC_CREX")
        queue_lock = manager.Condition()
        process_pool.apply_async(model_execution, args=(
            task_index, 1, task_pool[task], start_flag_init, start_lock, end_flag_init, end_lock, queue_lock))
        process_pool.apply_async(model_execution, args=(
            task_index, 2, task_pool[task], start_flag_init, start_lock, end_flag_init, end_lock, queue_lock))
        task_index += 1

    # Start local scheduler
    # Pool cannot manage the multiprocessing queue, must use manager.Queue()
    miss_queue = manager.Queue()
    process_pool.apply_async(scheduler_execution,
                             args=(task_pool, start_lock, start_flag_init,
                                   end_lock, end_flag_init, miss_queue))

    # Update Missing rate
    process_pool.apply_async(upload_miss_rate, args=(miss_queue,))
    process_pool.close()
    process_pool.join()

    time.sleep(10)
    logging.info("End All")


if __name__ == "__main__":
    run()
