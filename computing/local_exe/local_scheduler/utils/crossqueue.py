import array
import ctypes
import time

import numpy as np
import sysv_ipc

NULL_CHAR = b'\END'

libc = ctypes.CDLL("libc.so.6")


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


def create_shared_memory(key, data_size, flag="IPC_CREAT"):
    if flag == "IPC_CREAT":
        initial = True
        while initial:
            try:
                memory = sysv_ipc.SharedMemory(
                    key, sysv_ipc.IPC_CREAT, mode=0o604, size=data_size)
                initial = False
            except:
                libc.usleep(10)
                continue
        if memory.size != data_size:
            memory.remove()
            memory = sysv_ipc.SharedMemory(
                key, sysv_ipc.IPC_CREAT, mode=0o604, size=data_size)
    elif flag == "IPC_CREX":
        try:
            memory = sysv_ipc.SharedMemory(key)
            memory.remove()
        except:
            pass
        memory = sysv_ipc.SharedMemory(
            key, sysv_ipc.IPC_CREX, mode=0o604, size=data_size)
    return memory


class CrossContainerLock:
    def __init__(self, lock_key, flag=None):
        if flag == "IPC_CREX":
            try:
                sem = sysv_ipc.Semaphore(lock_key)
                sem.remove()
            except:
                pass
            self.lock = sysv_ipc.Semaphore(
                lock_key, sysv_ipc.IPC_CREX, initial_value=1)
        else:
            initial = True
            while initial:
                try:
                    self.lock = sysv_ipc.Semaphore(lock_key)
                    initial = False
                except:
                    libc.usleep(10)
                    continue

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()
        libc.usleep(1)


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
        write_to_memory(data_memory, data)
        write_to_memory(time_memory, str(timestamp))

        for front_key in self.front_keys:
            self.front_locks[front_key].acquire()
            try:
                self.fronts[front_key] = int(
                    read_from_memory(self.front_memories[front_key]))
            except:
                pass
            # If full
            if (self.rear + 1) % self.max_length == self.fronts[front_key]:
                self.fronts[front_key] = (
                    self.fronts[front_key] + 1) % self.max_length
                write_to_memory(self.front_memories[front_key], str(
                    self.fronts[front_key]))
            self.front_locks[front_key].release()

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


    def gettime(self, address_key=None, top=1):
        if address_key:
            address_key = address_key
        else:
            assert len(self.front_keys) == 1
            address_key = self.front_keys[0]

        self.rear_lock.acquire()
        try:
            self.rear = int(read_from_memory(self.rear_memory))
        except:
            pass

        self.front_locks[address_key].acquire()
        try:
            self.fronts[address_key] = int(
                read_from_memory(self.front_memories[address_key]))
        except:
            pass

        time_front = self.fronts[address_key]
        time_rear = self.rear

        times = []
        for i in range(top):
            if time_front == time_rear:
                self.front_locks[address_key].release()
                self.rear_lock.release()
                return times
            time_memory = sysv_ipc.SharedMemory(self.time_queue[time_front])
            timestamp = float(read_from_memory(time_memory))
            times.append(timestamp)
            time_front = (time_front + 1) % self.max_length
        self.front_locks[address_key].release()
        self.rear_lock.release()
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


if __name__ == "__main__":
    config_path = "/home/nvidia/local_scheduling"
