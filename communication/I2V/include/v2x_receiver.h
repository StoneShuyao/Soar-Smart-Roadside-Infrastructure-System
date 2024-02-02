//
// Created by 黄轩 on 2023/2/21.
//

#ifndef LIBROAD_V2X_RECEIVER_H
#define LIBROAD_V2X_RECEIVER_H

#include <deque>

#include "LDPC.h"
#include "v2x_socket.h"

const int kMaxHistorySize = 5;

class v2x_receiver {
public:
    v2x_receiver(v2x_socket* sock, int pktSize);
    ~v2x_receiver();

    uint8_t** recv(int* seq_num=nullptr, int* rate=nullptr);

    v2x_socket* sock;
    int pktSize;
    int nin, nout;
    LDPC* coder;
    SymbolType **inputPkts;
    SymbolType **outputPkts;
    int seqno;
    int mcs;
    char* recv_buf;
    uint8_t curBatchId;
    int curNodeId;
    int pktNum;
    bool decoded;
    std::deque<uint8_t> history;
};


#endif //LIBROAD_V2X_RECEIVER_H
