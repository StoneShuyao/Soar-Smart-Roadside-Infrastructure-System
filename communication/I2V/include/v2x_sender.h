//
// Created by 黄轩 on 2023/2/21.
//

#ifndef LIBROAD_V2X_SENDER_H
#define LIBROAD_V2X_SENDER_H

#include "v2x_socket.h"
#include "LDPC.h"

class v2x_sender {
public:
    v2x_sender(v2x_socket* sock, int pktSize, int nin, int nout, int nodeId);
    ~v2x_sender();

    void send(char* data, int mcs);

    v2x_socket* sock;
    int pktSize;
    int nin, nout;
    uint8_t batchId;
    LDPC* coder;
    SymbolType **inputPkts;
    SymbolType **outputPkts;
    int pktNum;
    int nodeId;
};


#endif //LIBROAD_V2X_SENDER_H
