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
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include "livox_sdk.h"

std::queue<uint8_t*> packet_queue;
std::mutex mut;
std::condition_variable cv_pop, cv_push;
int nodeId;

struct pktHdr {
    uint8_t nodeId;
    uint32_t pktId : 24;
} __attribute__ ((packed));

typedef enum {
    kDeviceStateDisconnect = 0,
    kDeviceStateConnect = 1,
    kDeviceStateSampling = 2,
} DeviceState;

typedef struct {
    uint8_t handle;
    DeviceState device_state;
    DeviceInfo info;
} DeviceItem;

DeviceItem devices[kMaxLidarCount];


const option long_opts[] = {
        {"iface", required_argument, nullptr, 'f'},
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

const int max_queue_size = 100;

void printHelp()
{
    std::cout <<
              "--iface <val>:       Set wifi interface (e.g., wlan1)\n"
              "--scheme <val>:      Set scheme (our, our_code, baseline_uc)\n"
              "--nin <val>:         Set coding nin (1, 15, ...)\n"
              "--nout <val>:        Set coding nin (0, 7, ...)\n"
              "--mcs <val>:         Set mcs if choose our/our_code, -1 for probe mode\n"
              "--quiet:             Set quiet mode\n"
              "--help:              Show help\n";
    exit(1);
}

/** Callback function of starting sampling. */
void OnSampleCallback(livox_status status, uint8_t handle, uint8_t response, void *data) {
    printf("OnSampleCallback statue %d handle %d response %d \n", status, handle, response);
    if (status == kStatusSuccess) {
        if (response != 0) {
            devices[handle].device_state = kDeviceStateConnect;
        }
    } else if (status == kStatusTimeout) {
        devices[handle].device_state = kDeviceStateConnect;
    }
}

/** Callback function of stopping sampling. */
void OnStopSampleCallback(livox_status status, uint8_t handle, uint8_t response, void *data) {
}

/** Query the firmware version of Livox LiDAR. */
void OnDeviceInformation(livox_status status, uint8_t handle, DeviceInformationResponse *ack, void *data) {
    if (status != kStatusSuccess) {
        printf("Device Query Informations Failed %d\n", status);
    }
    if (ack) {
        printf("firm ver: %d.%d.%d.%d\n",
               ack->firmware_version[0],
               ack->firmware_version[1],
               ack->firmware_version[2],
               ack->firmware_version[3]);
    }
}

void LidarConnect(const DeviceInfo *info) {
    uint8_t handle = info->handle;
    QueryDeviceInformation(handle, OnDeviceInformation, NULL);
    if (devices[handle].device_state == kDeviceStateDisconnect) {
        devices[handle].device_state = kDeviceStateConnect;
        devices[handle].info = *info;
    }
}

void LidarDisConnect(const DeviceInfo *info) {
    uint8_t handle = info->handle;
    devices[handle].device_state = kDeviceStateDisconnect;
}

void LidarStateChange(const DeviceInfo *info) {
    uint8_t handle = info->handle;
    devices[handle].info = *info;
}

/** Receiving error message from Livox Lidar. */
void OnLidarErrorStatusCallback(livox_status status, uint8_t handle, ErrorMessage *message) {
    static uint32_t error_message_count = 0;
    if (message != NULL) {
        ++error_message_count;
        if (0 == (error_message_count % 100)) {
            printf("handle: %u\n", handle);
            printf("temp_status : %u\n", message->lidar_error_code.temp_status);
            printf("volt_status : %u\n", message->lidar_error_code.volt_status);
            printf("motor_status : %u\n", message->lidar_error_code.motor_status);
            printf("dirty_warn : %u\n", message->lidar_error_code.dirty_warn);
            printf("firmware_err : %u\n", message->lidar_error_code.firmware_err);
            printf("pps_status : %u\n", message->lidar_error_code.device_status);
            printf("fan_status : %u\n", message->lidar_error_code.fan_status);
            printf("self_heating : %u\n", message->lidar_error_code.self_heating);
            printf("ptp_status : %u\n", message->lidar_error_code.ptp_status);
            printf("time_sync_status : %u\n", message->lidar_error_code.time_sync_status);
            printf("system_status : %u\n", message->lidar_error_code.system_status);
        }
    }
}


/** Callback function of changing of device state. */
void OnDeviceInfoChange(const DeviceInfo *info, DeviceEvent type) {
    if (info == NULL) {
        return;
    }

    uint8_t handle = info->handle;
    if (handle >= kMaxLidarCount) {
        return;
    }
    if (type == kEventConnect) {
        LidarConnect(info);
        printf("[WARNING] Lidar sn: [%s] Connect!!!\n", info->broadcast_code);
    } else if (type == kEventDisconnect) {
        LidarDisConnect(info);
        printf("[WARNING] Lidar sn: [%s] Disconnect!!!\n", info->broadcast_code);
    } else if (type == kEventStateChange) {
        LidarStateChange(info);
        printf("[WARNING] Lidar sn: [%s] StateChange!!!\n", info->broadcast_code);
    }

    if (devices[handle].device_state == kDeviceStateConnect) {
        printf("Device Working State %d\n", devices[handle].info.state);
        if (devices[handle].info.state == kLidarStateInit) {
            printf("Device State Change Progress %u\n", devices[handle].info.status.progress);
        } else {
            printf("Device State Error Code 0X%08x\n", devices[handle].info.status.status_code.error_code);
        }
        printf("Device feature %d\n", devices[handle].info.feature);
        SetErrorMessageCallback(handle, OnLidarErrorStatusCallback);
        if (devices[handle].info.state == kLidarStateNormal) {
            LidarStartSampling(handle, OnSampleCallback, NULL);
            devices[handle].device_state = kDeviceStateSampling;
        }
    }
}

/** Receiving point cloud data from Livox LiDAR. */
void GetLidarData(uint8_t handle, LivoxEthPacket *data, uint32_t data_num, void *client_data) {
    // const int max_queue_size = 100;
    static int pktId = 0;
    if (data && data ->data_type == kExtendCartesian) {
        auto tx_buf = new uint8_t[MAX_PACKET_SIZE];
        int data_size = sizeof(LivoxEthPacket) + data_num * sizeof(LivoxExtendRawPoint) - 1;
        memcpy(tx_buf+sizeof(pktHdr), data, data_size);
        pktHdr* hdr = (pktHdr*)tx_buf;
        int nodeId = *((int*)(devices[handle].info.broadcast_code+12));
        hdr->nodeId = nodeId;
        hdr->pktId = pktId ++;
        std::unique_lock<std::mutex> lk(mut, std::defer_lock);
        lk.lock();
        cv_push.wait(lk, []{ return packet_queue.size() < max_queue_size; });
        packet_queue.push(tx_buf);
        lk.unlock();
        cv_pop.notify_all();
    }
}

/** Callback function when broadcast message received.
 * You need to add listening device broadcast code and set the point cloud data callback in this function.
 */
void OnDeviceBroadcast(const BroadcastDeviceInfo *info) {
    if (info == NULL || info->dev_type == kDeviceTypeHub) {
        return;
    }
    printf("Receive Broadcast Code %s\n", info->broadcast_code);

    bool result = false;
    uint8_t handle = 0;
    result = AddLidarToConnect(info->broadcast_code, &handle);
    if (result == kStatusSuccess) {
        /** Set the point cloud data for a specific Livox LiDAR. */
        SetDataCallback(handle, GetLidarData, NULL);
        devices[handle].handle = handle;
        devices[handle].device_state = kDeviceStateDisconnect;
    }
}

void recv_result(int res_sock) {
    char buffer[1024];
    while (true) {
        ssize_t num_bytes = recv(res_sock, buffer, sizeof(buffer)-1, 0);
        if (num_bytes < 0) {
            std::cerr << "Failed to receive data" << std::endl;
            break;
        }
        std::unique_lock<std::mutex> lk(mut, std::defer_lock);
        lk.lock();
        cv_push.wait(lk, []{ return packet_queue.size() < max_queue_size; });
        packet_queue.push((uint8_t*)buffer);
        lk.unlock();
        cv_pop.notify_all();
    }
}

int main(int argc, char* argv[]) {
    int opt, mcs = -1, scheme = -1, quiet = 0, nin = -1, nout = -1;
    char iface[100];
    while ((opt = getopt_long(argc, argv, "h", long_opts, nullptr)) != -1) {
        switch (opt) {
            case 'f':
                std::strcpy(iface, optarg);
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

    printf("Livox SDK initializing.\n");
    /** Initialize Livox-SDK. */
    if (!Init()) {
        return -1;
    }
    printf("Livox SDK has been initialized.\n");
    memset(devices, 0, sizeof(devices));

    /** Set the callback function receiving broadcast message from Livox LiDAR. */
    SetBroadcastCallback(OnDeviceBroadcast);

    /** Set the callback function called when device state change,
     * which means connection/disconnection and changing of LiDAR state.
     */
    SetDeviceStateUpdateCallback(OnDeviceInfoChange);

    /** Start the device discovering routine. */
    if (!Start()) {
        Uninit();
        return -1;
    }
    printf("Start discovering device.\n");

    const int buf_size = 1362;
    void* sender;
    int sock;
    struct sockaddr_in addr;
    if (scheme == SCHEME_OUR) {
        sender = new v2x_socket(iface, TX_MODE);
    } else if (scheme == SCHEME_OUR_CODE) {
        sender = new v2x_sender(new v2x_socket(iface, TX_MODE), buf_size+sizeof(pktHdr), nin, nout, nodeId);
    } else {
        sock = socket(AF_INET, SOCK_DGRAM, 0);
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = inet_addr("192.168.123.100");
        addr.sin_port = htons(UDP_PORT);
    }

    int res_sock;
    res_sock = socket(AF_UNIX, SOCK_DGRAM, 0);
    struct sockaddr_un server_addr;
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, "/tmp/result.sock", sizeof(server_addr.sun_path) - 1);
    if (bind(res_sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) == -1) {
        std::cerr << "Failed to bind socket" << std::endl;
        close(res_sock);
        return 1;
    }

    std::thread res_t(recv_result, res_sock);
    res_t.start();


    int cur_size = 0;
    uint8_t* buf;
    auto start = std::chrono::system_clock::now();
    std::unique_lock<std::mutex> lk(mut, std::defer_lock);
    while (true) {
        lk.lock();
        cv_pop.wait(lk, []{ return !packet_queue.empty(); });
        buf = packet_queue.front();
        packet_queue.pop();
        lk.unlock();
        cv_push.notify_all();
        if (scheme == SCHEME_OUR) {
            ((v2x_socket *) sender)->send((char *) buf, buf_size + sizeof(pktHdr), mcs);
        } else if (scheme == SCHEME_OUR_CODE) {
            ((v2x_sender*)sender)->send((char*)buf, mcs);
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

    res_t.join();
    return 0;
}