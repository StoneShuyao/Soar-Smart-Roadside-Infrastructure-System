# *Soar* I2V communication module

### Hardware
- Two Wi-Fi adaptors with RTL8814au driver, e.g., EDUP EP-AC1621
- GPS module
- (optinal) One Livox Horizon LiDAR

### Install
- Dependency: `sudo apt install cmake libpcap libpcap-dev`
- RTL8814au Installation: Follow the guide in `8814au`
- CMAKE Installation:
    ```
    mkdir build && cd build
    cmake ..
    make -j4
    sudo make install
    ```
  

### Network
- Install `wpa_supplicant`
- Prepare `wpa_supplicant-{lamppost id}.conf` for each lamppost
- On the receiver side, run `gps.py` to switch between different lamppost


### Turn on the Monitor Mode
- On both TX and RX device, turn on monitor mode and set the channel. e.g.,
```
sudo killall hostapd
IFACE=$(iw dev | grep Interface | awk '$2 ~ "wlan1|wlx" {print $2}')
sudo ip link set $IFACE down
sudo iw dev $IFACE set monitor none
sudo ip link set $IFACE up
sudo iw dev $IFACE set channel 36
```
- Or,
```
bash ./monitor_mode.sh
```


### Demo
- On the TX side, run `libroad_tx_demo` with arguments that set the transmission scheme (i.e., w/ or w/o network coding), data rate, and MCS. 
```angular2html
sudo ./libroad_tx_demo --scheme [scheme] --rate [data rate] --mcs [MCS]
```
e.g.,
```angular2html
sudo ./libroad_tx_demo --scheme our --rate 30 --mcs 3
```

- - On the RX side, run `libroad_rx` with arguments that set the receiving scheme (i.e., w/ or w/o network coding), Wi-Fi interface, and the output. 
```angular2html
sudo ./libroad_rx --scheme [scheme] --iface [Wi-Fi interface name] --output [output path] --data (whether to save the received data)
```
e.g.,
```angular2html
sudo ./libroad_rx --scheme our --iface wlxe84e069cb9e7 --output ./ --data
```
A file named `result.csv` that logs the received packets and a file named `data` that contains the received data (if enabled) will be saved in the output path.

### Real-world operation (e.g., transmitting the Livox LiDAR data)
- On TX device, run `libroad_tx` with arguments
- On RX device, run `libroad_rx` with arguments
- Note: Livox LiDAR should connect to TX device, both TX and RX devices should connect with Wi-Fi adaptors 

### Result
Next step show how to plot Fig.13 and Fig.17
- go to directory `result`
- Dependency: Python3.9 and `pip install -r requirements.txt`
- Run: `python multicar_plot.py` and `python coding_plot.py`