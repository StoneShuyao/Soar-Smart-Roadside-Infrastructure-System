import logging
import pickle
import time
from socketserver import BaseRequestHandler, ThreadingTCPServer

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] [%(processName)s] [%(threadName)s] : %(message)s',
    level=logging.INFO)

BUF_SIZE = 1024

def get_etc_hostnames():
    """
    Reads the '/etc/hosts' file and extracts hostnames and their corresponding IP addresses.
    
    Returns:
        dict: A dictionary mapping IP addresses to lists of hostnames.
    """
    with open('/etc/hosts', 'r') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines
             if not line.startswith('#') and line.strip() != '']
    hosts = {}
    for line in lines:
        ip = line.split('#')[0].split()[0]
        hostnames = line.split('#')[0].split()[1:]
        hosts[ip] = hostnames
    return hosts

class CrossThreadingTCPServer(ThreadingTCPServer):
    """
    A subclass of ThreadingTCPServer that adds a queue and a shared dictionary.
    """
    def __init__(self, server_address, RequestHandlerClass, queue):
        super().__init__(server_address, RequestHandlerClass)
        self.queue = queue
        self.shared_dict = {}


class receive_handler(BaseRequestHandler):
    """
    Request handler for receiving data from clients.
    """
    def handle(self):
        address, pid = self.client_address
        hosts = get_etc_hostnames()
        queue = self.server.queue
        logging.info('%s connected' % hosts[address][0])
        data = b''
        while True:
            tmp = self.request.recv(BUF_SIZE)
            if len(tmp) > 0:
                data += tmp
            else:
                logging.info('%s closed' % hosts[address][0])
                break
        self.server.shared_dict[hosts[address][0]] = data
        queue.put(self.server.shared_dict)
        if queue.qsize() > 1:
            queue.get()


class send_handler(BaseRequestHandler):
    """
    Request handler for sending data to clients.
    """
    def handle(self):
        address, pid = self.client_address
        hosts = get_etc_hostnames()
        queue = self.server.queue
        nodename = hosts[address][0]
        logging.info('%s connected' % nodename)

        while True:
            if not queue.empty():
                self.server.shared_dict = queue.get()
                logging.info(self.server.shared_dict)
            if nodename in self.server.shared_dict:
                deployed_task = self.server.shared_dict[nodename]
                self.request.sendall(pickle.dumps(deployed_task))
                break
            time.sleep(0.01)


if __name__ == '__main__':
    from queue import Queue

    hosts = get_etc_hostnames()
    print(hosts)

    host = '10.0.0.2'
    port = 12345
    addr = (host, port)
    queue = Queue(maxsize=2)
    sever = CrossThreadingTCPServer(addr, receive_handler, queue)
    print('Listening')
    sever.serve_forever()
    print(sever)
