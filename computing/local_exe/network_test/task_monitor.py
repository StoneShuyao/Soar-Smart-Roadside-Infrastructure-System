import os
import pickle
import socket
import time
from configparser import ConfigParser


def get_sensors(filepath, fileprefix, suffix):
    filenames = []
    for filename in os.listdir(filepath):
        if filename.split(".")[-1] == suffix:
            if filename.startswith(fileprefix):
                filenames.append(filename)
    return filenames


class TaskMonitor:
    def __init__(self, host, port, file_prefix):
        self.host = host
        self.port = port
        self.file_prefix = file_prefix
        self.sock = None
        self.connected = False

    def _connect(self):
        while not self.connected:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                self.connected = True
            except socket.error:
                exit()

    def write2file(self):
        self._connect()
        recv_data = self.sock.recv(4096)
        recv_dict = pickle.loads(recv_data)
        self._close_socket()

        new_task_flag = False
        for key in recv_dict:
            filepath = self.file_prefix + str(key) + ".ini"
            lockfile = self.file_prefix + str(key)
            config = ConfigParser()
            config.read(filepath)
            if config['Queue']['QueueKey'] == str(recv_dict[key]):
                continue
            else:
                if not os.path.exists(lockfile + ".unlock"):
                    with open(lockfile + ".unlock", "w") as f:
                        pass
            new_task_flag = True

        if new_task_flag:
            for key in recv_dict:
                filepath = self.file_prefix + str(key) + ".ini"
                lockfile = self.file_prefix + str(key)
                config = ConfigParser()
                config.read(filepath)
                os.rename(lockfile + ".unlock", lockfile + ".lock")
                config['Queue']['QueueKey'] = str(recv_dict[key])
                with open(filepath, "w") as o:
                    config.write(o)
            os.system("rm /opt/aiot/config/*.json")

    def _close_socket(self):
        self.sock.close()
        self.connected = False


if __name__ == "__main__":
    host = "10.0.0.2"
    port = 23452
    fileprefix = "/opt/aiot/config/sensor"
    monitor = TaskMonitor(host, port, fileprefix)
    monitor.write2file()
