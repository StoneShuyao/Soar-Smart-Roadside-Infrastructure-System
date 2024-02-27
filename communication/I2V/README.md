# *Soar* I2V communication module

### Hardware
- Two Wi-Fi adaptors with RTL8814au driver, e.g., EDUP EP-AC1621
- GPS module
- (optinal) One Livox Horizon LiDAR

### Install
- Dependency: `sudo apt install cmake libpcap libpcap-dev`
- RTL8814au Installation: Follow the [guide](https://github.com/StoneShuyao/Soar-Smart-Roadside-Infrastructure-System/tree/main/communication/I2V/8814au/README.md)
- CMAKE Installation:
    ```
    mkdir build && cd build
    cmake ..
    make -j4
    sudo make install
    ```
  

### Network
- Install `wpa_supplicant`
- run `gps.py` to switch between different lamppost
- prepare `wpa_supplicant-{lamppost id}.conf` for each lamppost

### Test
- On both TX and RX device, turn on monitor mode. e.g.,
```
sudo killall hostapd
IFACE=$(iw dev | grep Interface | awk '$2 ~ "wlan1|wlx" {print $2}')
sudo ip link set $IFACE down
sudo iw dev $IFACE set monitor none
sudo ip link set $IFACE up
sudo iw dev $IFACE set channel 36
```

- On TX device, run `libroad_tx` with arguments
- On RX device, run `libroad_rx` with arguments
- Note: Livox LiDAR should connect to TX device, both TX and RX devices should connect with Wi-Fi adaptors 
