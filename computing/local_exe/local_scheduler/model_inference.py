import ctypes
import logging
import sys

import numpy as np

from model.detect import Detect
# from utils.crossqueue import CrossQueue
from inferqueue import InferQueue as CrossQueue

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] [%(processName)s] [%(threadName)s] : %(message)s',
    level=logging.DEBUG)
libc = ctypes.CDLL("libc.so.6")


def model_execution(task_index, mv_flag, app, start_flag, start_lock, end_flag, end_lock, queue_lock):
    try:
        logging.info("Start Process of Model Inference %d" % task_index)
        model_infer = ModelInfer(task_index, mv_flag, app)
        model_infer.run_model_infer(
            start_flag, start_lock, end_flag, end_lock, queue_lock)

    except Exception as err:
        logging.info(err)


class ModelInfer:
    def __init__(self, task_index, mv_flag, apps):
        logging.info("Initialize Model Inference")
        self.task_id = task_index
        self.queues = {}
        self.mv_flag = mv_flag
        for app in apps:
            self.appid = int(app["appID"])
            modelname_tmp = "model_name%d" % mv_flag
            enginename_tmp = "engine%d" % mv_flag
            self.model_name = app[modelname_tmp]
            self.engine_path = app[enginename_tmp]
            self.queues[int(app["appID"])] = CrossQueue(
                app["pre_start"],
                app["pre_msgkey"],
                app["pre_datashape"],
                app["pre_data_type"],
                app["pre_data_size"]
            )
            self.engine_input = app["engineinput"]
            if self.model_name == "pointpillar":
                self.post_queue = CrossQueue(
                    app['post_start'],
                    app['post_msgkey'],
                    app['post_datashape'],
                    app['post_data_type'],
                    max_data_size=app['post_data_size'],
                )
            else:
                self.post_queue = None
        self._load_model()

    def run_model_infer(self, start_flag, start_lock, end_flag, end_lock, queue_lock):
        thread_id = self.task_id * 2 + self.mv_flag - 1
        # print("threadid: %d" %thread_id)
        logging.info("Start model inference for thread %d" % thread_id)
        while True:
            # Waiting for start signal
            try:
                start_lock.acquire()
                start_lock.wait_for(lambda: start_flag[thread_id] == 1)
                start_flag[thread_id] = 0
                start_lock.release()
            except Exception as err:
                logging.info(err)
                raise err

            # with queue_lock:
            x, start_time = self._read_data()
            # logging.info("Read data")
            # for test
            logging.info("Start model for task %d" % self.task_id)
            y = self.model.detect(*x)
            if self.model_name == "pointpillar":
                y = np.concatenate(y, axis=None)
                self.post_queue.put(y, start_time)
            else:
                y = y[0]
            logging.info("Finish model for task %d" % self.task_id)

            # Notify end signal
            try:
                end_lock.acquire()
                end_flag[thread_id] = 1
                end_lock.notify()
                end_lock.release()
            except Exception as err:
                raise err

            libc.usleep(1)

    def _load_model(self):
        self.model = Detect(self.engine_path, self.engine_input)
        logging.info("Finish loading model %s for task %d" %
                     (self.model_name, self.task_id))

    def _read_data(self):
        rawdata, start_time = self.queues[self.appid].get()
        if self.model_name.startswith("pointpillar"):
            features = rawdata[:3200000]
            coors = rawdata[3200000:].astype(int)
            voxel_num = 10000
            return (features, coors, voxel_num), start_time
        return (rawdata, ), start_time
