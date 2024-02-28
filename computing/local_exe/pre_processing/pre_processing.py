#!/usr/bin/python3

import ctypes
import json
import sys
import time

from utils.configreader import AppConfig
from utils.crossqueue import CrossQueue


from data_processer import DataProcesser

libc = ctypes.CDLL("libc.so.6")

RESULTS = {}
COUNT = 0


def run():
    # os.sched_setaffinity(os.getpid(), {1, 2})
    app_id = sys.argv[1:][0]
    initial = True
    config_path = "/config/app%s.ini" % str(app_id)
    app_config = AppConfig(config_path)
    q_key = app_config.appID  # Position __, Sensor __, Application __
    app_key = app_config.pre_msgkey
    data_shape = app_config.shape
    data_type = app_config.sensor_data_type
    pre_data_type = app_config.pre_data_type
    pre_data_shape = app_config.pre_datashape
    sensor_key = app_config.sensor_key
    data_size = app_config.data_size
    deadline = app_config.deadline / 1000.
    # queue = CrossQueue(sensor_key, q_key, data_shape, data_type,
    #    data_size, max_length=5, flag="IPC_CREAT")
    last_stamp = 99999

    data_processer = DataProcesser(img_size=pre_data_shape)

    queue = CrossQueue(sensor_key, q_key, data_shape, data_type,
                       data_size, max_length=5, flag="IPC_CREAT")
    mem_queues = [queue]

    while True:
        data, timestamp = queue.get()
        # For container
        if timestamp - last_stamp >= deadline or last_stamp == 99999:
            # FPS = 10
            # if timestamp - last_stamp > 0.1 or last_stamp == 99999:
            s1 = time.time()
            pre_data = data_processer.processer(data)
            # e1 = time.time()
            # t1 = e1 - s1
            last_stamp = timestamp
        else:
            libc.usleep(10)
            continue
        if initial:
            max_length = 5  # 2 if is_lidar else 5
            app_queue = CrossQueue(app_config.pre_start, app_key, pre_data.shape, pre_data_type,
                                   max_data_size=sys.getsizeof(pre_data), max_length=max_length, flag="IPC_CREX")
            mem_queues.append(app_queue)
            # signal.signal(signal.SIGINT, sensor_signal_handler(mem_queues))
            # signal.signal(signal.SIGTERM, sensor_signal_handler(mem_queues))
            initial = False

        # s1 = time.time()
        app_queue.put(pre_data, timestamp)
        e1 = time.time()
        # t2 = e1 - s1
        write_to_results(q_key, timestamp, s1, e1)
        libc.usleep(10)


def write_to_results(appid, start_time, recv_time, end_time):
    global RESULTS
    global COUNT
    if not isinstance(RESULTS, dict):
        RESULTS = {}
    if start_time not in RESULTS:
        RESULTS[start_time] = [recv_time, end_time]
    COUNT += 1

    if COUNT % 100 == 0:
        with open("/config/pre_" + str(time.time()) + "_" + str(appid) + "_" + str(COUNT) + ".json", "w") as output:
            json.dump(RESULTS, output)


if __name__ == "__main__":
    run()
