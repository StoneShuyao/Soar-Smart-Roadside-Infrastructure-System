import os
import time
import serial
import serial.tools.list_ports
import geopy.distance
import time


class Lamppost:
    def __init__(self, nid, lid, lat, log, channel):
        self.pos = (lat, log)
        self.channel = channel
        self.id = lid
        self.nid = nid


port_gps = '/dev/ttyACM0'   # change name by device

# monitor mode
# lampposts = [
#     Lamppost(1, 'pi-1', 22.690100, 114.208610, 36),
#     Lamppost(2, 'pi-2', 22.690420, 114.208940, 104),
#     Lamppost(3, 'pi-3', 22.690730, 114.209260, 153),
#     Lamppost(4, 'pi-4', 22.691050, 114.209580, 48),
#     Lamppost(5, 'pi-5', 22.691390, 114.209890, 124),
#     Lamppost(6, 'pi-6', 22.691680, 114.210200, 40),
# ]

# AP mode
lampposts = [
    Lamppost(1, 'pi-1', 22.690100, 114.208610, 36),
    Lamppost(2, 'pi-2', 22.690420, 114.208940, 161),
    Lamppost(3, 'pi-3', 22.690730, 114.209260, 153),
    Lamppost(4, 'pi-4', 22.691050, 114.209580, 149),
    Lamppost(5, 'pi-5', 22.691390, 114.209890, 48),
    Lamppost(6, 'pi-6', 22.691680, 114.210200, 40),
]


def get_lamppost(cur_location):
    min_dis = 1e9
    ret = None
    for lamppost in lampposts:
        dis = geopy.distance.geodesic(lamppost.pos, cur_location).meters
        if dis < min_dis:
            min_dis = dis
            ret = lamppost
    return ret


if __name__ == '__main__':
    os.system('cls')
    serial_portlist = list(serial.tools.list_ports.comports())
    if len(serial_portlist) <= 0:
        print('No serial port!')
    else:
        for i in range(len(serial_portlist)):
            print(serial_portlist[i])
    ser = serial.Serial(port_gps, 115200, timeout=2)

    #----------------------------------------------

    os.system('cls')
    init = 3
    cur_channel = 1
    dir_name = "/home/shuyao/Documents/"
    os.system("mkdir %s" % dir_name)
    f = open("%s/test.txt" % dir_name, "w")
    while True:
        try:
            #print(ser.in_waiting)
            if ser.in_waiting > 0:

                # time.sleep(0.6)

                if init:   # skip the first three data
                    print('Stablely Receiving %d' % init)
                    init = init - 1
                    continue

                line = str(ser.readline().decode("utf-8"))

                GETSTR_List = []
                GETSTR_List.append(line)
                GPRMC_List = GETSTR_List[0].split(',')

                # Only read GNRMC string
                if GPRMC_List[0] != '$GNRMC':
                    continue

                if len(GPRMC_List) != 13:
                    print('Incompleted Data!')
                    continue
                #------------------------------------------------
                # print('')
                if GPRMC_List[2] == 'V':
                    print('Invalid Localization!')
                elif GPRMC_List[2] == 'A':
                    # print('Normal Localization.')
                    # print(GETSTR_List[0])
                    # print('')

                    #--------------------------------------------
                    #UTC Time
                    UTC = GPRMC_List[1][0:2] + ':' + GPRMC_List[1][2:4] + ':' + GPRMC_List[1][4:6]
                    UTC = UTC +' '+ GPRMC_List[9][0:2] + '/' + GPRMC_List[9][2:4] + '/20' + GPRMC_List[9][4:6]
                    # print('UTC Time:'+UTC)

                    #---------------------------------------------
                    # Geo Location
                    latitude_xy = int(GPRMC_List[3][0:2])+float(GPRMC_List[3][2:11])/60
                    longitude_xy = int(GPRMC_List[5][0:3])+float(GPRMC_List[5][3:12])/60
                    cur_location = (latitude_xy, longitude_xy)

                    
                    f.write("%f %f %f\n" % (latitude_xy, longitude_xy, time.time()))
                    # print(latitude_xy, longitude_xy, time.time())

                    lamppost = get_lamppost(cur_location)
                    if lamppost.channel != cur_channel:
                        cur_channel = lamppost.channel
                        os.system("sudo killall wpa_supplicant")
                        time.sleep(0.1)
                        os.system("sudo wpa_supplicant -B -i wlxe84e069cbe74 -c wpa_supplicant-%d.conf" % lamppost.nid)
                        # os.system("sudo ifconfig wlxe84e068fdc33 169.254.0.100")
                        print("Connect to %s, channel=%s" % (lamppost.id, lamppost.nid))
                else:
                    print('Error Data! Refreshing...')
        except Exception as e:
            print(e)
            continue
