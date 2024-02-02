//
// Created by 黄轩 on 2023/1/5.
//

#include "v2x_receiver.h"

#include <chrono>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <string>
#include <cstring>
#include <getopt.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

struct pktHdr {
    uint8_t nodeId;
    uint32_t pktId : 24;
} __attribute__ ((packed));

void printHelp()
{
    std::cout <<
              "--iface <val>:       Set wifi interface (e.g., wlan1)\n"
              "--scheme <val>:      Set scheme (our, our_code, baseline_uc)\n"
              "--output <path>:     Set output path\n"
              "--data:              Write raw data\n"
              "--help:              Show help\n";
    exit(1);
}

const option long_opts[] = {
        {"iface", required_argument, nullptr, 'f'},
        {"scheme", required_argument, nullptr, 's'},
        {"output", required_argument, nullptr, 'o'},
        {"data", no_argument, nullptr, 'd'},
        {"quiet", no_argument, nullptr, 'q'},
        {"help", no_argument, nullptr, 'h'},
        {nullptr, no_argument, nullptr, 0}
};

int main(int argc, char* argv[]) {
    int opt, scheme = -1, write_data = 0, quiet = 0;
    std::string output_path;
    char iface[100];
    while ((opt = getopt_long(argc, argv, "h", long_opts, nullptr)) != -1) {
        switch (opt) {
            case 'f':
                strcpy(iface, optarg);
                break;
            case 'o':
                output_path = std::string(optarg);
                break;
            case 'd':
                write_data = 1;
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
            case 'q':
                quiet = 1;
                break;
            case 'h':
            default:
                printHelp();
                break;
        }
    }

    int buf_size = 1362;
    void* receiver;
    int sock;
    struct sockaddr_in addr;
    if (scheme == SCHEME_OUR) {
        receiver = new v2x_socket(iface, RX_MODE);
    } else if (scheme == SCHEME_OUR_CODE) {
        receiver = new v2x_receiver(new v2x_socket(iface, RX_MODE), buf_size+sizeof(pktHdr));
    } else {
        sock = socket(AF_INET, SOCK_DGRAM, 0);
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = INADDR_ANY;
        addr.sin_port = htons(UDP_PORT);
        if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            printf("bind error: %s\n", std::strerror(errno));
            exit(0);
        }
    }

    std::ofstream out(output_path+"result.csv");
    out << "timestamp" << "," << "nodeId" << "," << "pktId" << "," << "seqno" << "," << "mcs" << std::endl;
    std::ofstream dataOut;
    if (write_data) {
        dataOut.open(output_path+"data", std::ios::binary);
    }

    int cur_size = 0;
    auto start = std::chrono::system_clock::now();
    double ts;
    int nodeId, pktId;
    int seqno;
    int mcs;
    for (;;) {
        if (scheme == SCHEME_OUR) {
            uint8_t buf[MAX_PACKET_SIZE];
            ((v2x_socket*)receiver)->recv((char*)buf, buf_size+sizeof(pktHdr), &seqno, &mcs);
            cur_size += buf_size;
            ts = std::chrono::duration_cast<std::chrono::duration<double>>(
                    std::chrono::system_clock::now().time_since_epoch()).count();
            nodeId = ((pktHdr*)buf)->nodeId;
            pktId = ((pktHdr*)buf)->pktId;
            out << std::setprecision(16) << ts << "," << nodeId << "," << pktId << "," << seqno << "," << mcs << std::endl;
            if (write_data) {
                dataOut.write((char*)buf+sizeof(pktHdr), buf_size);
            }
        } else if (scheme == SCHEME_OUR_CODE) {
            uint8_t** buf = ((v2x_receiver*)receiver)->recv(&seqno, &mcs);
            int num_pkt = ((v2x_receiver*)receiver)->nin;
            cur_size += buf_size * num_pkt;
            ts = std::chrono::duration_cast<std::chrono::duration<double>>(
                    std::chrono::system_clock::now().time_since_epoch()).count();
            nodeId = ((pktHdr *) (buf[0]))->nodeId;
            for (int i = 0; i < num_pkt; i ++) {
                pktId = ((pktHdr *) (buf[i]))->pktId;
                out << std::setprecision(16) << ts << "," << nodeId << "," << pktId << "," << seqno << "," << mcs << std::endl;
                if (write_data) {
                    dataOut.write((char*)(buf[i])+sizeof(pktHdr), buf_size);
                }
            }
        } else {
            uint8_t buf[MAX_PACKET_SIZE];
            socklen_t len;
            int recv_size = recvfrom(sock, (char*)buf, MAX_PACKET_SIZE, 0, (struct sockaddr *) &addr, &len);
            if (recv_size < 0) {
                printf("recv error: %s\n", std::strerror(errno));
                exit(0);
            }
            cur_size += buf_size;
            ts = std::chrono::duration_cast<std::chrono::duration<double>>(
                    std::chrono::system_clock::now().time_since_epoch()).count();
            nodeId = ((pktHdr*)buf)->nodeId;
            pktId = ((pktHdr*)buf)->pktId;
            out << std::setprecision(16) << ts << "," << nodeId << "," << pktId << "," << -1 << "," << -1 << std::endl;
            if (write_data) {
                dataOut.write((char*)buf+sizeof(pktHdr), buf_size);
            }
        }

        if (!quiet && cur_size > 136200) {
            auto end = std::chrono::system_clock::now();
            std::cout << (double)cur_size*8 / (std::chrono::duration_cast<std::chrono::microseconds>(end-start)).count() << "Mbps" << std::endl;
            start = end;
            cur_size = 0;
        }
        // usleep(10);
    }

    return 0;
}