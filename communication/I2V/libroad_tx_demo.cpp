//
// Created by 黄轩 on 2023/1/4.
//

#include "v2x_sender.h"

#include <chrono>
#include <iostream>
#include <unistd.h>
#include <fstream>
#include <thread>
#include <cstring>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <algorithm>
#include <getopt.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

typedef struct {
    uint8_t version;              /**< Packet protocol version. */
    uint8_t slot;                 /**< Slot number used for connecting LiDAR. */
    uint8_t id;                   /**< LiDAR id. */
    uint8_t rsvd;                 /**< Reserved. */
    uint32_t err_code;      /**< Device error status indicator information. */
    uint8_t timestamp_type;       /**< Timestamp type. */
    /** Point cloud coordinate format, refer to \ref PointDataType . */
    uint8_t data_type;
    uint8_t timestamp[8];         /**< Nanosecond or UTC format timestamp. */
    uint8_t data[1];              /**< Point cloud data. */
} LivoxEthPacket;


std::queue<uint8_t*> packet_queue;
std::mutex mut;
std::condition_variable cv_pop, cv_push;
int nodeId;

struct pktHdr {
    uint8_t nodeId;
    uint32_t pktId : 24;
} __attribute__ ((packed));

void simulate_data(int rate) {
    const int max_queue_size = 100;
    int buf_size = 1362;
    int duration = buf_size*8e3/rate - 1000; // unit: ns
    uint8_t *buf;
    uint32_t pktId = 0;
    pktHdr* hdr;
    auto start = std::chrono::system_clock::now();
    std::unique_lock<std::mutex> lk(mut, std::defer_lock);
    while (true) {
        buf = new uint8_t[MAX_PACKET_SIZE];
        hdr = (pktHdr*)buf;
        hdr->nodeId = nodeId;
        hdr->pktId = pktId ++;
        while (true) {
            auto end = std::chrono::system_clock::now();
            if (duration < (std::chrono::duration_cast<std::chrono::nanoseconds>(end - start)).count()) {
                start = end;
                break;
            }
        }
        lk.lock();
        cv_push.wait(lk, []{ return packet_queue.size() < max_queue_size; });
        packet_queue.push(buf);
        lk.unlock();
        cv_pop.notify_all();
    }
}

void simulate_data2(int rate) {
    const int max_queue_size = 100;
    int buf_size = 1362;
    int duration;
    if (rate == 10) {
        duration = buf_size*8/rate-90;
    } else if (rate == 20) {
        duration = buf_size*8/rate-85;
    } else if (rate == 30) {
        duration = buf_size*8/rate-82;
    } else if (rate == 40) {
        duration = buf_size*8/rate-79;
    } else {
        duration = buf_size*8/rate; // unit: us
    }
    uint8_t *buf;
    uint32_t pktId = 0;
    pktHdr* hdr;
    std::unique_lock<std::mutex> lk(mut, std::defer_lock);
    while (true) {
        buf = new uint8_t[MAX_PACKET_SIZE];
        hdr = (pktHdr*)buf;
        hdr->nodeId = nodeId;
        hdr->pktId = pktId ++;
        usleep(duration);
        lk.lock();
        cv_push.wait(lk, []{ return packet_queue.size() < max_queue_size; });
        packet_queue.push(buf);
        lk.unlock();
        cv_pop.notify_all();
    }
}

const option long_opts[] = {
        {"rate", required_argument, nullptr, 'r'},
        {"mcs", required_argument, nullptr, 'm'},
        {"scheme", required_argument, nullptr, 's'},
        {"nin", required_argument, nullptr, 'i'},
        {"nout", required_argument, nullptr, 'o'},
        {"cpu", no_argument, nullptr, 'c'},
        {"quiet", no_argument, nullptr, 'q'},
        {"help", no_argument, nullptr, 'h'},
        {nullptr, no_argument, nullptr, 0}
};

void printHelp()
{
    std::cout <<
              "--scheme <val>:      Set scheme (our, our_code, baseline_uc)\n"
              "--rate <val>:        Set data rate (10, 20, 30, 40, 100)\n"
              "--nin <val>:         Set coding nin (1, 15, ...)\n"
              "--nout <val>:        Set coding nin (0, 7, ...)\n"
              "--mcs <val>:         Set mcs if choose our/our_code, -1 for probe mode\n"
              "--cpu:               Set cpu friendly sender\n"
              "--quiet:             Set quiet mode\n"
              "--help:              Show help\n";
    exit(1);
}

int main(int argc, char* argv[]) {
    int opt, rate = -1, mcs = -1, scheme = -1, quiet = 0, nin = -1, nout = -1, cpu = 0;
    while ((opt = getopt_long(argc, argv, "h", long_opts, nullptr)) != -1) {
        switch (opt) {
            case 'r':
                rate = std::stoi(optarg);
                break;
            case 'i':
                nin = std::stoi(optarg);
                break;
            case 'o':
                nout = std::stoi(optarg);
                break;
            case 's':
                if (strcmp(optarg, "our") == 0) {
                    scheme = SCHEME_OUR;
                } else if (strcmp(optarg, "our_code") == 0) {
                    scheme = SCHEME_OUR_CODE;
                } else if (strcmp(optarg, "baseline_uc") == 0) {
                    scheme = SCHEME_BASELINE_UC;
                } else if (strcmp(optarg, "baseline_bc") == 0) {
                    scheme = SCHEME_BASELINE_BC;
                } else {
                    printf("Scheme Unknown: %s\n", optarg);
                }
                break;
            case 'm':
                mcs = std::stoi(optarg);
                switch (mcs) {
                    case 0:
                        mcs = MGN_VHT2SS_MCS0;
                        break;
                    case 1:
                        mcs = MGN_VHT2SS_MCS1;
                        break;
                    case 2:
                        mcs = MGN_VHT2SS_MCS2;
                        break;
                    case 3:
                        mcs = MGN_VHT2SS_MCS3;
                        break;
                    case 4:
                        mcs = MGN_VHT2SS_MCS4;
                        break;
                    case 5:
                        mcs = MGN_VHT2SS_MCS5;
                        break;
                    case 6:
                        mcs = MGN_VHT2SS_MCS6;
                        break;
                    case 7:
                        mcs = MGN_VHT2SS_MCS7;
                        break;
                    case 8:
                        mcs = MGN_VHT2SS_MCS8;
                        break;
                }
                break;
            case 'q':
                quiet = 1;
                break;
            case 'c':
                cpu = 1;
                break;
            case 'h':
            default:
                printHelp();
                break;
        }
    }

    char hostname[100];
    gethostname(hostname, 100);
    if (hostname[0] == 'p') {
        nodeId = hostname[3] - '0';
    } else {
        nodeId = hostname[5] - '0';
    }

    int buf_size = 1362;
    if (cpu) {
        std::thread t(simulate_data2, rate);
        t.detach();
    } else {
        std::thread t(simulate_data, rate);
        t.detach();
    }


    void* sender;
    int sock;
    struct sockaddr_in addr;
    if (scheme == SCHEME_OUR) {
        sender = new v2x_socket("wlan1", TX_MODE);
    } else if (scheme == SCHEME_OUR_CODE) {
        sender = new v2x_sender(new v2x_socket("wlan1", TX_MODE), buf_size+sizeof(pktHdr), nin, nout, nodeId);
    } else {
        sock = socket(AF_INET, SOCK_DGRAM, 0);
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = inet_addr("192.168.123.100");
        addr.sin_port = htons(UDP_PORT);
    }

    int cur_size = 0;
    uint8_t* buf;
    auto start = std::chrono::system_clock::now();
    auto mcs_start = std::chrono::system_clock::now();
    int cur_mcs = 0, mcs_cnt = 0;
    std::unique_lock<std::mutex> lk(mut, std::defer_lock);
    while (true) {
        lk.lock();
        cv_pop.wait(lk, []{ return !packet_queue.empty(); });
        buf = packet_queue.front();
        packet_queue.pop();
        lk.unlock();
        cv_push.notify_all();
        if (scheme == SCHEME_OUR) {
            if (mcs < 0) {
                mcs_cnt ++;
                if (mcs_cnt == 10) {
                    auto mcs_end = std::chrono::system_clock::now();
                    if ((std::chrono::duration_cast<std::chrono::milliseconds>(mcs_end - mcs_start)).count() > 200) {
                        cur_mcs = (cur_mcs + 1) % 9;
                        mcs_start = mcs_end;
                    }
                    mcs_cnt = 0;
                }
                ((v2x_socket *) sender)->send((char *) buf, buf_size + sizeof(pktHdr), cur_mcs+MGN_VHT2SS_MCS0);
            } else {
                ((v2x_socket *) sender)->send((char *) buf, buf_size + sizeof(pktHdr), mcs);
            }
        } else if (scheme == SCHEME_OUR_CODE) {
            if (mcs < 0) {
                auto mcs_end = std::chrono::system_clock::now();
                if ((std::chrono::duration_cast<std::chrono::milliseconds>(mcs_end-mcs_start)).count() > 100) {
                    cur_mcs = (cur_mcs+1) % 9;
                    mcs_start = mcs_end;
                }
                ((v2x_sender*)sender)->send((char*)buf, cur_mcs+MGN_VHT2SS_MCS0);
            } else {
                ((v2x_sender*)sender)->send((char*)buf, mcs);
            }
        } else {
            sendto(sock, (char*)buf, buf_size+sizeof(pktHdr), 0, (struct sockaddr *) &addr, sizeof(addr));
        }
        delete[] buf;
        cur_size += buf_size;
        if (!quiet && cur_size > 136200) {
            auto end = std::chrono::system_clock::now();
            std::cout << (double)cur_size*8 / (std::chrono::duration_cast<std::chrono::microseconds>(end-start)).count() << "Mbps" << std::endl;
            start = end;
            cur_size = 0;
        }
    }
    return 0;
}