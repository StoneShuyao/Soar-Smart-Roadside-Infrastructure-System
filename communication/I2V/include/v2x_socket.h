//
// Created by 黄轩 on 2022/12/30.
//

#ifndef LIBROAD_V2X_SOCKET_H
#define LIBROAD_V2X_SOCKET_H

#include <cstdint>
#include <pcap/pcap.h>
#include "utils.h"

#define MAX_PACKET_SIZE 1510
#define TX_MODE 0
#define RX_MODE 1

class v2x_socket {
public:
    v2x_socket(char* iface, int mode);
    ~v2x_socket();
    void send(char* data, size_t data_size, uint8_t data_rate=MGN_24M);
    ssize_t recv(char* data, size_t max_data_size, int* seqno=nullptr, int* rate=nullptr);

    char iface[100];
    pcap_t* descr;
    int mode;
    uint8_t tx_buf[MAX_PACKET_SIZE];
    uint8_t rx_buf[MAX_PACKET_SIZE];
};


v2x_socket* v2xSocket_Init(char* iface, int mode);
void v2xSocket_Delete(v2x_socket* socket);
void v2xSocket_Send(v2x_socket* socket, char* data, size_t data_size);
ssize_t v2xSocket_Recv(v2x_socket* socket, char* data, size_t data_size);



#endif //LIBROAD_V2X_SOCKET_H
