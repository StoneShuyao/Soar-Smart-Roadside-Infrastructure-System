//
// Created by 黄轩 on 2023/2/21.
//

#ifndef LIBROAD_CONFIG_H
#define LIBROAD_CONFIG_H

// LDPC coding
typedef unsigned char SymbolType;
#define FIELD_ORDER 8
#define FIELD_SIZE (1 << FIELD_ORDER)

#define RATE_MAX 1
#define RATE_LIDAR 2
#define RATE_RESULT 3
#define SCHEME_OUR 1
#define SCHEME_OUR_CODE 2
#define SCHEME_BASELINE_UC 3
#define SCHEME_BASELINE_BC 4
#define UDP_PORT 8123

const int kLidarIn = 15, kLidarOut = 7;
const int kResultIn = 1, kResultOut = 9;
const int kMaxIn = 1, kMaxOut = 0;

#endif //LIBROAD_CONFIG_H
