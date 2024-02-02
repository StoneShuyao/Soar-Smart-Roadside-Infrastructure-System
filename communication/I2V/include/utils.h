//
// Created by 黄轩 on 2023/1/5.
//

#ifndef LIBROAD_UTILS_H
#define LIBROAD_UTILS_H

#include <sys/socket.h>
#include <cstdint>
#include <cstring>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>

enum MGN_RATE {
    MGN_1M		= 0x02,
    MGN_2M		= 0x04,
    MGN_5_5M	= 0x0B,
    MGN_6M		= 0x0C,
    MGN_9M		= 0x12,
    MGN_11M	= 0x16,
    MGN_12M	= 0x18,
    MGN_18M	= 0x24,
    MGN_24M	= 0x30,
    MGN_36M	= 0x48,
    MGN_48M	= 0x60,
    MGN_54M	= 0x6C,
    MGN_MCS32	= 0x7F,
    MGN_MCS0,
    MGN_MCS1,
    MGN_MCS2,
    MGN_MCS3,
    MGN_MCS4,
    MGN_MCS5,
    MGN_MCS6,
    MGN_MCS7,
    MGN_MCS8,
    MGN_MCS9,
    MGN_MCS10,
    MGN_MCS11,
    MGN_MCS12,
    MGN_MCS13,
    MGN_MCS14,
    MGN_MCS15,
    MGN_MCS16,
    MGN_MCS17,
    MGN_MCS18,
    MGN_MCS19,
    MGN_MCS20,
    MGN_MCS21,
    MGN_MCS22,
    MGN_MCS23,
    MGN_MCS24,
    MGN_MCS25,
    MGN_MCS26,
    MGN_MCS27,
    MGN_MCS28,
    MGN_MCS29,
    MGN_MCS30,
    MGN_MCS31,
    MGN_VHT1SS_MCS0,
    MGN_VHT1SS_MCS1,
    MGN_VHT1SS_MCS2,
    MGN_VHT1SS_MCS3,
    MGN_VHT1SS_MCS4,
    MGN_VHT1SS_MCS5,
    MGN_VHT1SS_MCS6,
    MGN_VHT1SS_MCS7,
    MGN_VHT1SS_MCS8,
    MGN_VHT1SS_MCS9,
    MGN_VHT2SS_MCS0,
    MGN_VHT2SS_MCS1,
    MGN_VHT2SS_MCS2,
    MGN_VHT2SS_MCS3,
    MGN_VHT2SS_MCS4,
    MGN_VHT2SS_MCS5,
    MGN_VHT2SS_MCS6,
    MGN_VHT2SS_MCS7,
    MGN_VHT2SS_MCS8,
    MGN_VHT2SS_MCS9,
    MGN_VHT3SS_MCS0,
    MGN_VHT3SS_MCS1,
    MGN_VHT3SS_MCS2,
    MGN_VHT3SS_MCS3,
    MGN_VHT3SS_MCS4,
    MGN_VHT3SS_MCS5,
    MGN_VHT3SS_MCS6,
    MGN_VHT3SS_MCS7,
    MGN_VHT3SS_MCS8,
    MGN_VHT3SS_MCS9,
    MGN_VHT4SS_MCS0,
    MGN_VHT4SS_MCS1,
    MGN_VHT4SS_MCS2,
    MGN_VHT4SS_MCS3,
    MGN_VHT4SS_MCS4,
    MGN_VHT4SS_MCS5,
    MGN_VHT4SS_MCS6,
    MGN_VHT4SS_MCS7,
    MGN_VHT4SS_MCS8,
    MGN_VHT4SS_MCS9,
    MGN_UNKNOWN
};

#define RATE_OFFSET 8

static uint8_t radiotap_header[]  __attribute__((unused)) = {
        0x00, 0x00, // <-- radiotap version
        0x0b, 0x00, // <- radiotap header length
        0x04, 0x0c, 0x00, 0x00, // <-- bitmap
        MGN_24M, // <-- rate
        0x0c, //<-- tx power
        0x01 //<-- antenna
};

static uint8_t ieee80211_header[] __attribute__((unused)) = {
        0x08, 0x02, 0x30, 0x00,               // data frame, not protected, from DS to a STA via AP
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,   // receiver is broadcast
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,   // tx will be filled
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,   // src will be filled
        0x00, 0x00,                           // (seq_num << 4) + fragment_num
};

#define HEADER_LENGTH (sizeof(radiotap_header) + sizeof(ieee80211_header) + sizeof(llc_header))
#define SRC_MAC 16
#define TX_MAC 10

static uint8_t llc_header[] __attribute__((unused)) = {
        0xaa,                               // DSAP
        0xbb,                               // SSAP
        0xcc, 0xdd                          // control field
};

struct ieee80211_radiotap_header {
    uint8_t it_version;          /* Version 0. Only increases
                                 * for drastic changes,
                                 * introduction of compatible
                                 * new fields does not count.
                                 */
    uint8_t it_pad;
    uint16_t it_len;          /* length of the whole
                                 * header in bytes, including
                                 * it_version, it_pad,
                                 * it_len, and data fields.
                                 */
    uint32_t it_present;      /* A bitmap telling which
                                 * fields are present. Set bit 31
                                * (0x80000000) to extend the
                                 * bitmap by another 32 bits.
                                 * Additional extensions are made
                                 * by setting bit 31.
                                 */
} __attribute__ ((packed));

#ifdef __APPLE__
#define SIOCGIFHWADDR SIOCGIFCONF
#define ifr_hwaddr ifr_addr
#endif

inline void get_mac_addr(char* iface, char* mac_addr) {
    int fd;
    struct ifreq ifr;
    fd = socket(AF_INET, SOCK_DGRAM, 0);
    ifr.ifr_addr.sa_family = AF_INET;
    strncpy((char *)ifr.ifr_name , (const char *)iface , IFNAMSIZ-1);
    ioctl(fd, SIOCGIFHWADDR, &ifr);
    close(fd);
    memcpy(mac_addr, (char *)ifr.ifr_hwaddr.sa_data, 6);
}

inline int get_channel_freq(struct ieee80211_radiotap_header* radiotap_hdr) {
    int offset = 0;
    if (radiotap_hdr->it_present & (1 << 0)) { // TSFT
        offset += 8;
    }
    if (radiotap_hdr->it_present & (1 << 1)) { // Flags
        offset += 1;
    }
    if (radiotap_hdr->it_present & (1 << 2)) { // Rate
        offset += 1;
    }
    uint8_t* p = (uint8_t*)radiotap_hdr+8+offset;
    return p[0] + (p[1] << 8);
}

inline int get_seq_num(const u_char *payload) {
    const u_char *psn = payload + 22;
    return (uint16_t) ((uint8_t) (*psn) >> 4) | ((uint8_t) *(psn + 1) << 4);
}

inline int get_mcs(const u_char *payload) {
    const u_char *mcs = payload + 23;
    return *mcs >> 4;
}

#endif //LIBROAD_UTILS_H
