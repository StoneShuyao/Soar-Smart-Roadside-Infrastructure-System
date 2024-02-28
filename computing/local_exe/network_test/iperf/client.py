#!/usr/bin/env python3
import pickle
import socket

import iperf3

hostnames = ["n-p2-%d" % (i + 1) for i in range(12)]
int_hostnames = ["int.node-p2-%d" % (i + 1) for i in range(12)]
node_ids = [i + 1 for i in range(12)]


def bandwidth_test():
    bandwidth = {}
    clients = []
    hostname = socket.gethostname()
    hostport = 5200 + hostnames.index(hostname)
    for i in range(len(hostnames)):
        client = iperf3.Client()
        client.duration = 1
        client.port = hostport
        clients.append(client)

    for i in range(len(hostnames)):
        host = int_hostnames[i]
        client = clients[i]
        client.server_hostname = host
        print('Connecting to {0}:{1}'.format(client.server_hostname, client.port))
        result = client.run()
        if result.error:
            print(result.error)
        else:
            print('')
            print('Test completed:')
            print('  started at         {0}'.format(result.time))
            print('  bytes transmitted  {0}'.format(result.sent_bytes))
            print('  retransmits        {0}'.format(result.retransmits))
            print('  avg cpu load       {0}%\n'.format(result.local_cpu_total))

            print('Average transmitted data in all sorts of networky formats:')
            print('  bits per second      (bps)   {0}'.format(result.sent_bps))
            print('  Kilobits per second  (kbps)  {0}'.format(result.sent_kbps))
            print('  Megabits per second  (Mbps)  {0}'.format(result.sent_Mbps))
            print('  KiloBytes per second (kB/s)  {0}'.format(result.sent_kB_s))
            print('  MegaBytes per second (MB/s)  {0}'.format(result.sent_MB_s))
            bandwidth[node_ids[i]] = result.sent_kB_s
    return bandwidth


if __name__ == '__main__':
    HOST = "137.189.97.26"
    COMM_PORT = 12345
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, COMM_PORT))
    except socket.error:
        exit()
    bandwidth = bandwidth_test()
    sock.send(pickle.dumps(bandwidth))
    sock.close()
