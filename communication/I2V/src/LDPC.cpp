//
// Created by 黄轩 on 2023/2/21.
//

#include "LDPC.h"

LDPC::LDPC() {
    G = newMat(kMaxCodingSize, kMaxCodingSize);
    A = new SymbolType*[kMaxCodingSize];
    Y = new SymbolType*[kMaxCodingSize];
}

LDPC::~LDPC() {
    delMat(G, kMaxCodingSize);
    delete[] A;
    delete[] Y;
}

void LDPC::encode(SymbolType **inputPkts, SymbolType **outputPkts, int batchId, int pktSize, int nin, int nout) {
    psrand.seed(batchId);
    SymbolType c;
    SymbolType* payload;
    codingHdr* hdr;

    for (int j = 0; j < nin+nout; j ++) {
        memset(outputPkts, 0, pktSize+sizeof(codingHdr));
        hdr = (codingHdr*)outputPkts[j];
        hdr->batchId = batchId;
        hdr->coefId = j;
        hdr->nin = nin;
        hdr->nout = nout;
    }

    for (int i = 0; i < nin; i ++) {
        payload = outputPkts[i] + sizeof(codingHdr);
        memcpy(payload, inputPkts[i], pktSize);
    }
    for (int i = 0; i < nin; i ++) {
        SymbolType* pkt = inputPkts[i];
        for (int j = 0; j < nout; j ++) {
            c = (SymbolType)(psrand.randInt(FIELD_SIZE));
            payload = outputPkts[j+nin] + sizeof(codingHdr);
            FiniteField::addMulVec(payload, pkt, c, pktSize);
        }
    }
}

bool LDPC::decode(SymbolType **inputPkts, SymbolType **outputPkts, int numInput, int pktSize) {
    codingHdr* hdr;
    hdr = (codingHdr*)inputPkts[0];
    int nin = hdr->nin, nout = hdr->nout;
    psrand.seed(hdr->batchId);
    for (int i = 0; i < nin; i ++) {
        memset(G[i], 0, nin);
        G[i][i] = 1;
    }
    for (int i = 0; i < nin; i ++) {
        for (int j = 0; j < nout; j ++) {
            G[j+nin][i] = (SymbolType)(psrand.randInt(FIELD_SIZE));
        }
    }
    for (int i = 0; i < numInput; i ++) {
        hdr = (codingHdr*)inputPkts[i];
        A[i] = G[hdr->coefId];
        Y[i] = inputPkts[i] + sizeof(codingHdr);
    }
    int rank = FiniteField::gaussianSolve(A, Y, outputPkts, nin, numInput, pktSize);
    return rank >= nin;
}