from utils.crossqueue import CrossQueue,  write_to_memory, read_from_memory, NULL_CHAR
import ctypes
import sysv_ipc
NULL_CHAR = b'\END'

libc = ctypes.CDLL("libc.so.6")


class InferQueue(CrossQueue):
    def __init__(self, data_key, address_keys, shape, data_type, max_data_size, max_length=5, flag="IPC_CREAT"):
        super().__init__(data_key, address_keys, shape,
                         data_type, max_data_size, max_length, flag)

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

        self.front_locks[address_key].acquire()
        try:
            self.fronts[address_key] = int(
                read_from_memory(self.front_memories[address_key]))
        except:
            pass

        data_memory = sysv_ipc.SharedMemory(
            self.data_queue[self.fronts[address_key]])
        time_memory = sysv_ipc.SharedMemory(
            self.time_queue[self.fronts[address_key]])
        data = read_from_memory(data_memory, self.data_type)
        timestamp = float(read_from_memory(time_memory))

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
