sudo killall hostapd
IFACE=$(iw dev | grep Interface | awk '$2 ~ "wlan1|wlx" {print $2}')
sudo ip link set $IFACE down
sudo iw dev $IFACE set monitor none
sudo ip link set $IFACE up
sudo iw dev $IFACE set channel 36