# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain raw_data copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import array
import configparser
import ctypes
import json
import socket
import sys
import time

import cv2
import numpy as np
import rclpy
import ros2_numpy as rnp
import sysv_ipc
from cv_bridge import CvBridge
from numpy.lib import recfunctions as rfn
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import PointCloud2, CompressedImage

libc = ctypes.CDLL("libc.so.6")
# import os.path

NULL_CHAR = b'\END'
RESULTS = {}
COUNT = 0


def create_shared_memory(key, data_size, flag="IPC_CREAT"):
    if flag == "IPC_CREAT":
        memory = sysv_ipc.SharedMemory(key, sysv_ipc.IPC_CREAT, mode=0o604, size=data_size)
        if memory.size != data_size:
            memory.remove()
            memory = sysv_ipc.SharedMemory(key, sysv_ipc.IPC_CREAT, mode=0o604, size=data_size)
    elif flag == "IPC_CREX":
        try:
            memory = sysv_ipc.SharedMemory(key)
            memory.remove()
        except:
            pass
        memory = sysv_ipc.SharedMemory(key, sysv_ipc.IPC_CREX, mode=0o604, size=data_size)
    return memory


class CrossContainerLock:
    def __init__(self, lock_key, flag=None):
        if flag == "IPC_CREX":
            try:
                sem = sysv_ipc.Semaphore(lock_key)
                sem.remove()
            except:
                pass
            self.lock = sysv_ipc.Semaphore(lock_key, sysv_ipc.IPC_CREX, initial_value=1)
        else:
            self.lock = sysv_ipc.Semaphore(lock_key)

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()
        libc.usleep(10)


# One producer and multiple consumers
class CrossQueue:
    def __init__(self, data_key, address_keys, shape, data_type, max_data_size, max_length=5, flag="IPC_CREAT"):
        # Shared Memory keys for data
        self.max_length = max_length
        self.data_queue = [data_key + i for i in range(max_length)]
        # Only for delete memories
        self._memories = []
        for data_key in self.data_queue:
            self._memories.append(create_shared_memory(
                data_key, max_data_size, flag=flag))
        # Shared Memory keys for time_stamp
        self.time_queue = [data_key + max_length +
                           i for i in range(max_length)]
        for time_key in self.time_queue:
            self._memories.append(
                create_shared_memory(time_key, 32, flag=flag))

        # Flag: rear of queue
        self.rear = 0
        self.rear_key = data_key + 2 * max_length + 1
        self.rear_memory = create_shared_memory(self.rear_key, 32, flag=flag)
        self._memories.append(self.rear_memory)
        # Check whether is writing flag or not
        self.rear_flag = data_key + 2 * max_length + 2
        self.rear_lock = CrossContainerLock(self.rear_flag, flag=flag)
        self._memories.append(self.rear_lock.lock)

        self.data_type = data_type
        self.shape = shape

        if isinstance(address_keys, int):
            self.front_keys = [address_keys]
        else:
            self.front_keys = address_keys

        self.fronts = {}
        self.front_locks = {}
        self.front_memories = {}
        for front_key in self.front_keys:
            # Flag: head of queue
            self.fronts[front_key] = 0
            self.front_memories[front_key] = create_shared_memory(
                front_key, 32, flag=flag)
            self._memories.append(self.front_memories[front_key])
            # Check whether is writing flag or not
            front_flag = front_key
            self.front_locks[front_key] = CrossContainerLock(
                front_flag, flag=flag)
            self._memories.append(self.front_locks[front_key].lock)

    def put(self, data, timestamp):
        # sec, nanosec, timeset=None):
        self.rear_lock.acquire()
        try:
            self.rear = int(read_from_memory(self.rear_memory))
        except:
            pass

        data_memory = sysv_ipc.SharedMemory(self.data_queue[self.rear])
        time_memory = sysv_ipc.SharedMemory(self.time_queue[self.rear])

        # if timeset:
        #     timeset = np.array(timeset)
        #     # Serialize time
        #     timeset[-1, 1] = write_to_memory(data_memory, data)
        #     # End time
        #     timeset[-1, 2] = time.time()
        #     timeset = tuple(map(tuple, timeset))
        #
        #     sign = str((timeset, sec, nanosec))
        # else:
        write_to_memory(data_memory, data)
        write_to_memory(time_memory, str(timestamp))
        # self.rear_lock.release()

        # if self.isFull():
        for front_key in self.front_keys:
            self.front_locks[front_key].acquire()
            try:
                self.fronts[front_key] = int(
                    read_from_memory(self.front_memories[front_key]))
            except:
                pass
            if (self.rear + 1) % self.max_length == self.fronts[front_key]:
                self.fronts[front_key] = (
                    self.fronts[front_key] + 1) % self.max_length
                write_to_memory(self.front_memories[front_key], str(
                    self.fronts[front_key]))
            self.front_locks[front_key].release()

        # Update rear key value
        # self.rear_lock.acquire()
        try:
            self.rear = int(read_from_memory(self.rear_memory))
        except:
            pass
        self.rear = (self.rear + 1) % self.max_length
        write_to_memory(self.rear_memory, str(self.rear))
        self.rear_lock.release()

    # sec: second nanosec: nanosecond, only for one consumer
    def get(self, address_key=None):
        if address_key:
            address_key = address_key
        else:
            assert len(self.front_keys) == 1
            address_key = self.front_keys[0]

        while self.isEmpty(address_key=address_key):
            libc.usleep(10)
            continue

        data_memory = sysv_ipc.SharedMemory(
            self.data_queue[self.fronts[address_key]])
        time_memory = sysv_ipc.SharedMemory(
            self.time_queue[self.fronts[address_key]])

        data = read_from_memory(data_memory, self.data_type)
        timestamp = float(read_from_memory(time_memory))

        # Update front key value for consumer with one key
        self.front_locks[address_key].acquire()
        try:
            self.fronts[address_key] = int(
                read_from_memory(self.front_memories[address_key]))
        except:
            pass
        self.fronts[address_key] = (
            self.fronts[address_key] + 1) % self.max_length
        write_to_memory(self.front_memories[address_key], str(
            self.fronts[address_key]))
        self.front_locks[address_key].release()
        try:
            data = data.reshape(self.shape)
        except:
            data, timestamp = self.get(address_key=address_key)

        return data, timestamp

    # TODO: empty and full queue handler
    def gettime(self, address_key=None, top=1):
        if address_key:
            address_key = address_key
        else:
            assert len(self.front_keys) == 1
            address_key = self.front_keys[0]

        self.front_locks[address_key].acquire()
        try:
            self.fronts[address_key] = int(
                read_from_memory(self.front_memories[address_key]))
        except:
            pass
        self.front_locks[address_key].release()

        self.rear_lock.acquire()
        try:
            self.rear = int(read_from_memory(self.rear_memory))
        except:
            pass
        self.rear_lock.release()

        time_front = self.fronts[address_key]
        time_rear = self.rear

        times = []
        for i in range(top):
            if time_front == time_rear:
                return times
            time_memory = sysv_ipc.SharedMemory(self.time_queue[time_front])
            timestamp = float(read_from_memory(time_memory))
            times.append(timestamp)
            time_front = (time_front + 1) % self.max_length
        return times

    def isFull(self):
        for front_key in self.front_keys:
            self.front_locks[front_key].acquire()
            try:
                self.fronts[front_key] = int(
                    read_from_memory(self.front_memories[front_key]))
            except:
                pass
            self.front_locks[front_key].release()
            self.rear_lock.acquire()
            try:
                self.rear = int(read_from_memory(self.rear_memory))
            except:
                pass
            self.rear_lock.release()
            if (self.rear + 1) % self.max_length == self.fronts[front_key]:
                return True
        return False

    def isEmpty(self, address_key=None):
        if address_key:
            address_keys = [address_key]
        else:
            address_keys = self.front_keys
        
        self.rear_lock.acquire()
        for front_key in address_keys:
            self.front_locks[front_key].acquire()
            try:
                self.fronts[front_key] = int(
                    read_from_memory(self.front_memories[front_key]))
            except:
                pass
            
            try:
                self.rear = int(read_from_memory(self.rear_memory))
            except:
                pass
            
            if self.rear == self.fronts[front_key]:
                self.rear_lock.release()
                self.front_locks[front_key].release()
                return True
            self.front_locks[front_key].release()
        self.rear_lock.release()
        return False

    def size(self, address_key=None):
        if address_key:
            address_keys = [address_key]
        else:
            address_keys = self.front_keys

        for front_key in address_keys:
            self.front_locks[front_key].acquire()
            try:
                self.fronts[front_key] = int(
                    read_from_memory(self.front_memories[front_key]))
            except:
                pass
            self.front_locks[front_key].release()
            self.rear_lock.acquire()
            try:
                self.rear = int(read_from_memory(self.rear_memory))
            except:
                pass
            self.rear_lock.release()

        if len(self.fronts) == 0:
            return 0
        elif len(self.fronts) == 1:
            return (self.rear - self.fronts[self.front_keys[0]] + self.max_length) % self.max_length
        else:
            return [(self.rear - i + self.max_length) % self.max_length for i in self.front_keys]

    def remove(self):
        for _memory in self._memories:
            if isinstance(_memory, sysv_ipc.SharedMemory):
                try:
                    _memory.detach()
                except:
                    pass
            _memory.remove()


def read_from_memory(memory, data_type=None):
    if not memory.attached:
        memory.attach()
    s = memory.read()
    memory.detach()
    # s = s.decode()
    i = s.find(NULL_CHAR)
    if i != -1:
        s = s[:i]
    if data_type:
        return np.frombuffer(s, dtype=data_type)
    else:
        return s.decode("utf-8")


def write_to_memory(memory, s):
    # print("writing %s " % s)
    start = time.time()
    if isinstance(s, (np.ndarray, array.array, list)):
        s = s.tobytes()
    elif isinstance(s, str):
        s = s.encode("utf-8")
    end = time.time()
    s += NULL_CHAR
    # s = s.encode()
    if not memory.attached:
        memory.attach()
    memory.write(s)
    memory.detach()
    return end - start

# apply outdoor trace, unit: second
use_trace = False
class TraceSim:
    def __init__(self, trace_path):
        self.comm_trace = np.load(trace_path)
        self.queue_ts = 0

    def apply_delay(self, size, tx, rx):
        if tx == rx:
            return
        cur_ts = time.time()
        trace_id = int(cur_ts) % self.comm_trace.shape[0]
        delay = size * 8 / 1e6 / self.comm_trace[trace_id, tx-1, rx-1] # transmission time
        delay += max(self.queue_ts - cur_ts, 0) # queueing time
        self.queue_ts = cur_ts + delay
        libc.usleep(int(delay*1e6))


if use_trace:
    trace_path = '/sensor_subscriber/trace_678.npy'
    trace_sim = TraceSim(trace_path)

class SensorSubscriber(Node):
    def __init__(self, nodename):
        super().__init__(nodename)
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,
            history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST,
            depth=1
        )

        self.declare_parameter("config_path")
        config_path = self.get_parameter("config_path").get_parameter_value().string_value
        config = configparser.ConfigParser()
        config.read(config_path)

        # nodename = config["Sensor"]["Position"] + "_" + config["Sensor"]["Type"]
        # nodename = nodename.replace("-", "_")

        topic = "/" + config["Sensor"]["Position"] + "/" + config["Sensor"]["Type"]
        self.topic = topic.replace("-", "_")

        _max_message_size = 5
        _address_keys = eval(config["Queue"]["QueueKey"])  # Position __, Sensor __, Application __
        self.queues = CrossQueue(int(config["Queue"]["Start"]), _address_keys, eval(config["Sensor"]["DataShape"]),
                                 eval(config["Sensor"]["DataType"]), int(config["Sensor"]["DataSize"]),
                                 max_length=_max_message_size, flag="IPC_CREX")

        msg_type = None
        
        if config["Sensor"]["MsgType"] == "CompressedImage":
            msg_type = CompressedImage
            # Used to convert between ROS and OpenCV images
            self.br = CvBridge()
            self.listener_callback = self.camera_callback

        if msg_type:
            self.subscription = self.create_subscription(
                msg_type,
                self.topic,
                self.listener_callback,
                qos_profile=qos_profile)
            # prevent unused variable warning
            self.subscription

        self.target_pos = int(config["Sensor"]["Position"][-1])
        self.cur_pos = int(socket.gethostname()[-1])

    def camera_callback(self, msg):
        if use_trace:
            if self.topic[:-2].endswith('camera'):
                size = 180*1e3
            else:
                size = 148*1e3
            trace_sim.apply_delay(size, self.cur_pos, self.target_pos)

        recv_time = time.time()
        # Serialization Time, used for evaluation
        # serialize_time = -1

        sec = int(msg.header.stamp.sec)
        nanosec = int(msg.header.stamp.nanosec)
        start_time = sec + nanosec * 10 ** -9

        data = np.array(msg.data, copy=False, dtype="uint8")
        cv_image = cv2.imdecode(data, cv2.IMREAD_COLOR)

        self.queues.put(cv_image, start_time)
        end_time = time.time()
        write_to_results(self.topic, start_time, recv_time, end_time)
        libc.usleep(10)
        # self.get_logger().info('I heard: "%s"' % msg.data)


def write_to_results(topic, start_time, recv_time, end_time):
    global RESULTS
    global COUNT
    topic = topic.replace("/", "_")
    if not isinstance(RESULTS, dict):
        RESULTS = {}
    if start_time not in RESULTS:
        RESULTS[start_time] = [recv_time, end_time]
    COUNT += 1

    if COUNT % 100 == 0:
        with open("/config/%s_%s_%s.json" % (str(time.time()), topic, str(COUNT)), "w") as output:
            json.dump(RESULTS, output)


def sensor_signal_handler(sensor_subscriber):
    def signal_handler(signum, frame):
        sensor_subscriber.queues.remove()
        sensor_subscriber.destroy_node()
        rclpy.shutdown()
        sys.exit()

    return signal_handler


def main(args=None):
    rclpy.init(args=args)

    hostname = socket.gethostname()
    nodename = hostname + "_sensor_sub"
    nodename = nodename.replace("-", "_")

    sensor_subscriber = SensorSubscriber(nodename)
    # signal.signal(signal.SIGINT, sensor_signal_handler(sensor_subscriber))
    # signal.signal(signal.SIGTERM, sensor_signal_handler(sensor_subscriber))

    rclpy.spin(sensor_subscriber)
    sensor_subscriber.queues.remove()
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    sensor_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
