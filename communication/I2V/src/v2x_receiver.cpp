//
// Created by 黄轩 on 2023/2/21.
//

#include "v2x_receiver.h"

v2x_receiver::v2x_receiver(v2x_socket *sock, int pktSize) :
    sock(sock), pktSize(pktSize) {
    coder = new LDPC();
    recv_buf = new char[pktSize];
    inputPkts = newMat(kMaxCodingSize, pktSize + sizeof(codingHdr));
    outputPkts = newMat(kMaxCodingSize, pktSize);
    curBatchId = -1;
    curNodeId = -1;
    pktNum = 0;
    decoded = false;
    history.clear();
}

v2x_receiver::~v2x_receiver() {
    delete coder;
    delete[] recv_buf;
    delMat(inputPkts, kMaxCodingSize);
    delMat(outputPkts, kMaxCodingSize);
}

uint8_t** v2x_receiver::recv(int* seq_num, int* rate) {
    ssize_t recv_size;
    codingHdr* hdr;
    while (true) {
        recv_size = sock->recv(recv_buf, pktSize+sizeof(codingHdr), &seqno, &mcs);
        if (recv_size != pktSize+sizeof(codingHdr)) continue;
        hdr = (codingHdr*)recv_buf;
        uint8_t batchId = hdr->batchId;
        nin = hdr->nin;
        nout = hdr->nout;
        if (hdr->nodeId != curNodeId) {
            curNodeId = hdr->nodeId;
            curBatchId = -1;
            pktNum = 0;
            decoded = false;
            history.clear();
        }
        for (auto i : history) {
            if (batchId == i) {
//                printf("misorder: %d, %d\n", curBatchId, batchId);
                continue;
            }
        }
        if (batchId != curBatchId) {
            history.push_back(curBatchId);
            if (history.size() >= kMaxHistorySize) {
                history.pop_front();
            }
//            if (!decoded) {
//                printf("decode fail: %d, pktNum: %d\n", curBatchId, pktNum);
//            }
            curBatchId = batchId;
            decoded = false;
            pktNum = 0;
        }
        if (decoded) continue;
        memcpy(inputPkts[pktNum++], recv_buf, pktSize+sizeof(codingHdr));
        if (pktNum >= hdr->nin) {
            if (coder->decode(inputPkts, outputPkts, pktNum, pktSize)) {
                decoded = true;
                break;
            }
        }
    }
    if (seq_num != nullptr) {
        *seq_num = seqno;
    }
    if (rate != nullptr) {
        *rate = mcs;
    }
    return outputPkts;
}