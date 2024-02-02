//
// Created by 黄轩 on 2023/2/21.
//

#ifndef LIBROAD_LDPC_H
#define LIBROAD_LDPC_H

#include "config.h"
#include "RandGenerator.h"
#include "FiniteField.h"

struct codingHdr {
    uint8_t nodeId;
    uint16_t batchId;
    uint16_t coefId:6, nin:5, nout:5;
} __attribute__ ((packed));

const int kMaxCodingSize = 100;

class LDPC {
public:
    LDPC();
    ~LDPC();

    void encode(SymbolType **inputPkts, SymbolType **outputPkts, int batchId, int pktSize, int nin, int nout);
    bool decode(SymbolType **inputPkts, SymbolType **outputPkts, int numInput, int pktSize);

    RandGenerator psrand;
    SymbolType **G;
    SymbolType **A;
    SymbolType **Y;
};


#endif //LIBROAD_LDPC_H
