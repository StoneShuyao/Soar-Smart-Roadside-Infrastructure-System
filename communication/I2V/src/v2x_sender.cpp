//
// Created by 黄轩 on 2023/2/21.
//

#include "v2x_sender.h"

v2x_sender::v2x_sender(v2x_socket *sock, int pktSize, int nin, int nout, int nodeId) :
        sock(sock), pktSize(pktSize), nin(nin), nout(nout), nodeId(nodeId) {
    coder = new LDPC();
    inputPkts = newMat(kMaxCodingSize, pktSize);
    outputPkts = newMat(kMaxCodingSize, pktSize + sizeof(codingHdr));
    pktNum = 0;
    batchId = 0;
}

v2x_sender::~v2x_sender() {
    delete coder;
    delMat(inputPkts, kMaxCodingSize);
    delMat(outputPkts, kMaxCodingSize);
}

void v2x_sender::send(char *data, int mcs) {
    uint8_t* pkt = inputPkts[pktNum++];
    memcpy(pkt, data, pktSize);

    if (pktNum < nin) return;

//    Start coding
    coder->encode(inputPkts, outputPkts, batchId++, pktSize, nin, nout);
    codingHdr* hdr;
    for (int i = 0; i < nin + nout; i ++) {
        hdr = (codingHdr*)outputPkts[i];
        hdr->nodeId = nodeId;
        sock->send((char*)outputPkts[i], pktSize+sizeof(codingHdr), mcs);
        usleep(5);
    }
    pktNum = 0;
}