import ctypes
import json
import logging
import sys
import time

import numpy as np
import copy

# from utils.crossqueue import CrossQueue
from inferqueue import InferQueue as CrossQueue
from collections import OrderedDict

logging.basicConfig(
    filename="/config/local_scheduler.log",
    filemode="a",
    format='[%(asctime)s] [%(levelname)s] [%(processName)s] [%(threadName)s] : %(message)s',
    level=logging.DEBUG)
libc = ctypes.CDLL("libc.so.6")

RESULTS = {}
COUNT = 0
MISSING_RATE = {}


def sensor_signal_handler(local_scheduler):
    def signal_handler(signum, frame):
        # dict [key: model index, value: {app1 id: queue 1, app2 id: queue 2 }}
        for value in local_scheduler.queues.values():
            for queue in value.values():
                queue.remove()
        sys.exit()

    return signal_handler


def scheduler_execution(task_pool, start_lock, start_flag, end_lock, end_flag,
                        miss_queue):
    try:
        local_scheduler = LocalScheduler(task_pool)
        local_scheduler.local_scheduling(
            start_lock, start_flag, end_lock, end_flag, miss_queue)
    except Exception as err:
        logging.info(err)
    logging.info("End Local Scheduling")


class LocalScheduler:
    # model_order: dict {"model_name": model_index}
    def __init__(self, task_pool):
        logging.info("LocalScheduler Initialization.")
        # Number of model
        self.task_num = len(task_pool)
        # Deadline of all tasks
        # dict {key: task index, value: task relativen ddl, ddl unit: 1ms
        self.ddl_all = {}
        self.posttime = {}
        self.priority = np.zeros(self.task_num)
        # dict [key: task index, value: task queue}
        self.queues = {}
        self.profiles = [None] * self.task_num
        self.task_pool = OrderedDict(task_pool)
        self.task_ids = {}

        task_index = 0
        for taskid, tasklist in self.task_pool.items():
            task = tasklist[0]
            self.task_ids[task_index] = taskid
            self.profiles[task_index] = task["profile"]
            self.posttime[task_index] = task["posttime"]/1000.0
            # logging.info("PostTime %s." % str(self.posttime[task_index]))
            self.ddl_all[task_index] = int(task["deadline"])
            self.priority[task_index] = int(task["priority"])
            self.queues[task_index] = CrossQueue(
                task["pre_start"],
                task["pre_msgkey"],
                task["pre_datashape"],
                task["pre_data_type"],
                task["pre_data_size"]
            )
            task_index += 1

        # Model Start Time-> The most urgent app in the model group
        self.start_time = np.zeros(self.task_num)
        self.next_start_time = np.zeros(self.task_num)
        # Processed app id of each model
        # self.model_address = np.zeros(self.task_num, dtype=np.integer)

        self.time_set = {}

        self._initial = True
        self.selected_task = -1
        self.next_selected_task = -1
        self.selected_task_id = -1
        self.next_remain_time = 0.0
        logging.info("Finish Initialization of Local Scheduler.")

    def local_scheduling(self, start_lock, start_flag, end_lock, end_flag, miss_queue):
        logging.info("Start Local Scheduling.")

        while True:
            recv_time = time.time()
            method_selection = 1  # 1: our methods EDF, 2: our methods without back-off, 3: Baseline-EDF
            selected_mv = 0
            if method_selection in [1, 2, 3]:
                if method_selection == 1:
                    next_flag = self._select_model4mv_backoff()
                else:
                    next_flag = self._select_model()
                if next_flag == -1:
                    libc.usleep(10)
                    continue
                elif next_flag - self.profiles[self.selected_task][1] < 0:
                    self.queues[self.selected_task].get()
                    end_time = time.time()
                    selected_mv = 0
                    ddl = self.ddl_all[self.selected_task] / 1000.0
                    write_to_results(
                        self.selected_task_id, self.start_time[self.selected_task], recv_time, end_time, selected_mv, miss_queue, ddl=ddl, missing=-1)
                    continue

                if method_selection == 1:
                    selected_mv, start_time = self._select_model_variant_4backoff()
                elif method_selection == 2:
                    selected_mv, start_time = self._select_model_variant()
                    if selected_mv == -1:
                        self.queues[self.selected_task].get()
                        end_time = time.time()
                        selected_mv = -1
                        ddl = self.ddl_all[self.selected_task] / 1000.0
                        write_to_results(
                            self.selected_task_id, self.start_time[self.selected_task], recv_time, end_time, selected_mv, miss_queue, ddl=ddl, missing=-1)
                        continue
                else:
                    selected_mv = 0
                    start_time = self.start_time[self.selected_task]

            # -----------------start inference-------------------------------#
            logging.info("Dispatch start signal to task %d" %
                         (self.selected_task))
            logging.info("Dispatch start signal to model %d" % (selected_mv))
            # Start Execution
            recv_time = time.time()
            try:
                start_lock.acquire()
                # Put current batchsize in the shared array to share with selected model execution process
                selected_thread_id = self.selected_task * 2 + selected_mv
                start_flag[selected_thread_id] = 1
                start_lock.notify_all()
                start_lock.release()
            except Exception as err:
                logging.info(err)
                exit()

            # logging.info("Dispatch data to model %d" % self.selected_task)

            # Waiting for the finish signal
            try:
                end_lock.acquire()
                logging.info(
                    "Waiting for the finish signal of task %d" % self.selected_task)
                end_lock.wait_for(lambda: end_flag[selected_thread_id] == 1)
                end_time = time.time()
                ddl = self.ddl_all[self.selected_task] / 1000.0
                write_to_results(self.selected_task_id, start_time,
                                 recv_time, end_time, selected_mv, miss_queue, ddl=ddl)
                logging.info("Finish inference of task %d" %
                             self.selected_task)
                end_flag[selected_thread_id] = 0
                end_lock.release()
            except Exception as err:
                logging.info(err)
                exit()

            libc.usleep(10)

    def _select_model(self):
        # logging.info(self.queues)
        none_times = 0
        for task_index in range(self.task_num):
            queuesize = self.queues[task_index].size()
            if queuesize == 0:
                self.start_time[task_index] = 0
                none_times += 1
                self.next_start_time[task_index] = 0
            elif queuesize == 1:
                queue_times = self.queues[task_index].gettime()
                self.start_time[task_index] = queue_times[0]
                self.next_start_time[task_index] = 0
            else:
                queue_times = self.queues[task_index].gettime(top=2)
                self.start_time[task_index] = queue_times[0]
                self.next_start_time[task_index] = queue_times[1]

        if none_times == self.task_num:
            return -1

        # calculating remain time
        remain_times = []
        inf_times = 0
        cur_time = time.time()
        logging.info("Current time for model selection. %s" % str(cur_time))
        for task_index in range(self.task_num):
            if self.start_time[task_index] == 0:
                remain_times.append(float("inf"))
                inf_times += 1
            else:
                remain_time = self.ddl_all[task_index] / \
                    1000.0 + self.start_time[task_index] - cur_time
                remain_times.append(remain_time)

        # select task
        self.selected_task = np.argmin(np.array(remain_times))
        self.selected_task_id = self.task_ids[self.selected_task]

        logging.info("Start time after selecting task. %s" %
                     str(self.start_time[self.selected_task]))
        return remain_times[self.selected_task]

    def _select_model4mv_backoff(self):
        # logging.info(self.queues)
        none_times = 0
        for task_index in range(self.task_num):
            queuesize = self.queues[task_index].size()
            if queuesize == 0:
                self.start_time[task_index] = 0
                none_times += 1
                self.next_start_time[task_index] = 0
            elif queuesize == 1:
                queue_times = self.queues[task_index].gettime()
                self.start_time[task_index] = queue_times[0]
                self.next_start_time[task_index] = 0
            else:
                queue_times = self.queues[task_index].gettime(top=2)
                self.start_time[task_index] = queue_times[0]
                self.next_start_time[task_index] = queue_times[1]

        if none_times == self.task_num:
            return -1

        # calculating remain time
        remain_times = []
        inf_times = 0
        cur_time = time.time()
        logging.info("Current time for model selection. %s" % str(cur_time))
        for task_index in range(self.task_num):
            if self.start_time[task_index] == 0:
                remain_times.append(float("inf"))
                inf_times += 1
            else:
                remain_time = self.ddl_all[task_index] / \
                    1000.0 + self.start_time[task_index] - cur_time
                remain_times.append(remain_time)

        # select task
        self.selected_task = np.argmin(np.array(remain_times))
        self.selected_task_id = self.task_ids[self.selected_task]

        # ------------------flag for back-off mechanism-------------------------------#
        if remain_times[self.selected_task] < 0:
            return remain_times[self.selected_task]

        next_remain_times = remain_times
        if self.next_start_time[self.selected_task] == 0.0:
            next_remain_times[self.selected_task] = float("inf")
        else:
            next_remain_times[self.selected_task] = self.ddl_all[self.selected_task] / \
                1000.0 + self.next_start_time[self.selected_task] - cur_time

        for task_index in range(self.task_num):
            if next_remain_times[task_index] < 0:
                next_remain_times[task_index] = float("inf")

        # logging.info("Remain time for next task. %s" %str(next_remain_times))
        self.next_selected_task = np.argmin(np.array(next_remain_times))
        logging.info("Remain time for next selected task. %s" %
                     str(next_remain_times[self.next_selected_task]))
        if next_remain_times[self.next_selected_task] == float("inf"):
            self.next_selected_task = -1
        else:
            self.next_remain_time = next_remain_times[self.next_selected_task]

        return remain_times[self.selected_task]

    def _select_model_variant(self):
        start_time = -1
        original_exetime = self.profiles[self.selected_task][0]
        backoff_exetime = self.profiles[self.selected_task][1]
        start_time = self.start_time[self.selected_task]
        ddl = self.ddl_all[self.selected_task]

        current_time = time.time()
        logging.info("Current time for model variant selection. %s" %
                     str(current_time))
        # check if original model execution can meet rt requirements of current inference
        mv_id = 0
        post_time = self.posttime[self.selected_task]
        if current_time + original_exetime + post_time <= start_time + ddl/1000.0:
            mv_id = 0
        else:
            mv_id = 1
            logging.info("SELECT small model because of cur exe")
        return mv_id, start_time

    def _select_model_variant_4backoff(self):
        start_time = -1
        original_exetime = self.profiles[self.selected_task][0]
        backoff_exetime = self.profiles[self.selected_task][1]
        start_time = self.start_time[self.selected_task]
        ddl = self.ddl_all[self.selected_task]

        current_time = time.time()
        logging.info("Current time for model variant selection. %s" %
                     str(current_time))
        # check if original model execution can meet rt requirements of current inference
        mv_id = 0
        post_time = self.posttime[self.selected_task]
        if current_time + original_exetime + post_time <= start_time + ddl/1000.0:
            mv_id = 0
            # ------------------flag for back-off mechanism-------------------------------#
            if self.next_selected_task != -1:
                if self.next_selected_task == self.selected_task:
                    nexttask_exetime = original_exetime
                    nexttask_start_time = self.next_start_time[self.next_selected_task]
                    next_ddl = self.ddl_all[self.next_selected_task]
                else:
                    nexttask_exetime = self.profiles[self.next_selected_task][0]
                    nexttask_start_time = self.start_time[self.next_selected_task]
                    next_ddl = self.ddl_all[self.next_selected_task]
                logging.info("current_time. %f" % current_time)
                logging.info("original_exetime. %f" % original_exetime)
                logging.info("nexttask_backofff_exetime. %f" %
                             nexttask_exetime)
                logging.info("nexttask_start_time. %f" % nexttask_start_time)
                logging.info("next_ddl. %f" % next_ddl)
                if original_exetime + nexttask_exetime > self.next_remain_time:
                    logging.info(
                        "SELECT small model because of backoff. %f" % next_ddl)
                    mv_id = 1
        else:
            mv_id = 1
            logging.info("SELECT small model because of cur exe")
        return mv_id, start_time


def write_to_results(appid, start_time, recv_time, end_time, select_mv, miss_queue, ddl=None, missing=1):
    global RESULTS
    global COUNT
    global MISSING_RATE

    if not isinstance(RESULTS, dict):
        RESULTS = {}

    if appid not in MISSING_RATE:
        MISSING_RATE[appid] = [0, 0]
    MISSING_RATE[appid][0] += 1
    data = [appid, recv_time, end_time, select_mv, missing]
    RESULTS[start_time] = [data]

    if missing == 2:
        MISSING_RATE[appid][1] += 1
    elif end_time - start_time > ddl:
        MISSING_RATE[appid][1] += 1

    COUNT += 1

    if COUNT % 100 == 0:
        with open("/config/infer_" + str(time.time()) + "_" + str(COUNT) + ".json", "w") as output:
            json.dump(RESULTS, output)

    if COUNT % 500 == 0:
        miss_queue.put(MISSING_RATE.copy())
        MISSING_RATE[appid] = [0, 0]
