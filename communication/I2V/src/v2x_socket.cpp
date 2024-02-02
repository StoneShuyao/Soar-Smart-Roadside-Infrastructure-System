//
// Created by 黄轩 on 2022/12/30.
//

#include "v2x_socket.h"

#include <cstring>
#include <cassert>
#include <stdexcept>

v2x_socket::v2x_socket(char* iface, int mode) : mode(mode) {
    memcpy(this->iface, iface, strlen(iface));
    char err_buf[100];
    descr = pcap_open_live(iface, BUFSIZ, 0, 0, err_buf);
    if (descr == nullptr) {
        printf("pcap_open_live(): %s\n", err_buf);
    }

    if (mode == TX_MODE) {
        char mac_addr[6];
        get_mac_addr(iface, mac_addr);
        uint8_t* p = tx_buf;
        memcpy(p, radiotap_header, sizeof(radiotap_header));
        p += sizeof(radiotap_header);
        memcpy(p, ieee80211_header, sizeof(ieee80211_header));
        memcpy(p + TX_MAC, mac_addr, sizeof(mac_addr));
        memcpy(p + SRC_MAC, mac_addr, sizeof(mac_addr));
        p += sizeof(ieee80211_header);
        memcpy(p, llc_header, sizeof(llc_header));
    } else if (mode == RX_MODE) {
//        apply filter
        char filter[] = "type data and subtype data and (wlan addr3 e8:4e:06:9c:bd:94 or wlan addr3 e8:4e:06:9c:b9:e7 or wlan addr3 e8:4e:06:95:28:3e or wlan addr3 e8:4e:06:9c:be:74 or wlan addr3 e8:4e:06:9c:bb:dd or wlan addr3 e8:4e:06:8f:dc:33)";
        bpf_u_int32 netpf = 0;
        struct bpf_program pfp;
        if (pcap_compile(descr, &pfp, filter, 0, netpf) == -1) {
            printf("failed to compile Libpcap filter, %s\n", filter);
        }
        if (pcap_setfilter(descr, &pfp) == -1) {
            printf("failed to set libpcap filter, %s\n", filter);
        }
    } else {
        throw std::runtime_error("Unknown mode, TX_MODE: 0, RX_MODE: 1\n");
    }
}

v2x_socket::~v2x_socket() {
    pcap_close(descr);
}

void v2x_socket::send(char *data, size_t data_size, uint8_t data_rate) {
    int total_size = HEADER_LENGTH + data_size;
    assert(total_size <= MAX_PACKET_SIZE);
    tx_buf[RATE_OFFSET] = data_rate;
    memcpy(tx_buf+HEADER_LENGTH, data, data_size);
    if (pcap_inject(descr, tx_buf, total_size) != total_size) {
        throw std::runtime_error("Unable to inject packet\n");
    }
}

ssize_t v2x_socket::recv(char *data, size_t max_data_size, int* seqno, int* rate) {
    struct pcap_pkthdr* pcap_hdr;
    const uint8_t* packet;
    ssize_t data_size;
    int ret = pcap_next_ex(descr, &pcap_hdr, &packet);
    if (ret == PCAP_ERROR_BREAK) {
        throw std::runtime_error("pcap read error\n");
    }
    struct ieee80211_radiotap_header* radiotap_hdr;
    radiotap_hdr = (struct ieee80211_radiotap_header*) packet;
    if (rate != nullptr) {
        *rate = get_mcs(packet);
    }
    packet += radiotap_hdr->it_len;
    if (seqno != nullptr) {
        *seqno = get_seq_num(packet);
    }
    packet += sizeof(ieee80211_header);
    packet += sizeof(llc_header);
    data_size = pcap_hdr->len - radiotap_hdr->it_len - sizeof(ieee80211_header) - sizeof(llc_header) - 4;
    assert(data_size <= max_data_size);
    memcpy(data, packet, data_size);
    return data_size;
}

v2x_socket* v2xSocket_Init(char* iface, int mode) {
    return new v2x_socket(iface, mode);
}

void v2xSocket_Delete(v2x_socket* socket) {
    delete socket;
}

void v2xSocket_Send(v2x_socket* socket, char* data, size_t data_size) {
    socket->send(data, data_size);
}

ssize_t v2xSocket_Recv(v2x_socket* socket, char* data, size_t data_size) {
    return socket->recv(data, data_size);
}
