import asyncio, time, csv
from bleak import BleakScanner
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

async def main():
    timestr = time.strftime("%Y%m%d-%H%M%S")

    experiment = 'Test'
    data_path = 'ScanData/' + experiment + '-' + timestr + '.csv'
    new_count = 0
    last_count = 0
    dropped_packets = 0
    dropped_packets_init = 0
    dropped_packet_pct = 0
    packet_0 = 0
    overflow = 0
    t_samp = 1 # sampling time in seconds

    time_data = []
    ch1_data = []
    ch2_data = []
    ch3_data = []

    ch1_data_v = []
    ch2_data_v = []
    ch3_data_v = []
    packet_loss_log =[]

    app = QtGui.QApplication([])
    win = pg.GraphicsWindow(title='Custom Peripheral')
    win.resize(1280, 720)

    win.setWindowTitle('ASSIST HET2 BFC v0')

    pg.setConfigOptions(antialias=True)

    ch1_plot = win.addPlot(row=1, col=1, colspan=6, title="Channel 1")
    ch2_plot = win.addPlot(row=2, col=1, colspan=6, title="Channel 2", pen = 'm')
    packet_plot = win.addPlot(row=3, col=1, colspan=6, title="Packet Loss", pen = 'r')


    while 1:
        devices = await BleakScanner.discover(timeout = 1)
        for d in devices:
            if(d.name == 'H'):
                raw_count = list(d.metadata["manufacturer_data"].keys())[0]

                # DEBUG!
                # Manufacturer data contains a numerical "keys" value and the contents of the manufacturer data.

                # Extracts numerical "keys" value (seems to strip dictionary and list structures)
                dbg_keys_value = list(d.metadata["manufacturer_data"].keys())[0]
                #print("Manufacturer data KEYS: ", dbg_keys_value, sep=None)

                # Extracts the contents of manufacturer data in a bytes object
                dbg_manu_value = d.metadata["manufacturer_data"][dbg_keys_value]
                #print("Manufacturer data DATA: ", dbg_manu_value, sep=None)
                print("Manufacturer data DATA (hex): ", dbg_manu_value.hex(), sep=None)
                print("new_data extracted (hex): ", d.metadata["manufacturer_data"][raw_count].hex(), sep=None)
                # DEBUG!

                new_count = int(raw_count/256)+overflow*255

                new_packet = d.metadata["manufacturer_data"][raw_count]
                # print(new_packet.hex())
                if not dropped_packets_init:
                    if new_count == 255:
                        last_count = -1
                    else:
                        last_count = new_count-1
                        packet_0 = new_count
                    dropped_packets_init = 1
                #print("\nNew packet!")
                #print("New Count: ", new_count, sep=None)
                if new_count != last_count:
                    new_data = d.metadata["manufacturer_data"][raw_count]
                    if new_count - last_count < 0:
                        overflow = overflow + 1
                        new_count = new_count + 255*overflow
                    if new_count != last_count+1:
                        dropped_packets = dropped_packets + new_count-last_count-1
                        print("Dropped Packets: {}, Total Packets: {}".format(dropped_packets,new_count-packet_0))
                    last_count = new_count
                    (new_time, new_ch1, new_ch2, new_ch1_v, new_ch2_v) = parse_packet(new_count, new_data)
                    time_data = time_data + new_time
                    ch1_data = ch1_data + new_ch1
                    ch2_data = ch2_data + new_ch2
                    ch1_data_v = ch1_data_v + new_ch1_v
                    ch2_data_v = ch2_data_v + new_ch2_v
                    try:
                        dropped_packet_pct = dropped_packets / (new_count-packet_0)
                    except ZeroDivisionError:
                        dropped_packet_pct = 0
                    packet_loss_log = packet_loss_log + [dropped_packet_pct]*6

                    ch1_plot.plot(time_data, ch1_data_v, clear=True, name="Ch1", pen = 'g')
                    ch2_plot.plot(time_data, ch2_data_v, clear=True, name="Ch2", pen = 'm')
                    #packet_plot.plot(time_data,packet_loss_log, clear=True, name="Packet Loss", pen = 'r')
                    pg.QtGui.QApplication.processEvents()

                    data_buffer = zip(new_time, new_ch1, new_ch2, new_ch1_v, new_ch2_v)

                    with open(data_path, 'a', newline = '') as csvfile:
                        datawriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                        for data in data_buffer:
                            datawriter.writerow(data)

                break
                    # print(time_data)
                    # print(ch1_data)

        # _ = plt.plot(counter)
        # plt.show()
                # print(d.metadata["manufacturer_data"].keys())

def parse_packet(counter, packet, vref = 1.804, tsamp=1):
    print("\nPacket: ", packet.hex(), sep=None)
    print("Length: ", len(packet), sep=None)
    time = []
    ch1 = []
    ch2 = []
    ch3 = []
    ch1_v = []
    ch2_v = []
    ch3_v = []
    for i in range(2):
        # print(packet[i*4:i*4+2].hex())
        # print(packet[i*4+2:i*4+4].hex())

        # DEBUG !

        #print("Calculating time with:", "\tcounter = ", counter, "\ti = ", i, "\ttsamp = ", tsamp, sep=None)
        #print("Calculating ch1 with: ", "\tpacket[i*4:i*4+2][::-1].hex() = ", packet[i*4:i*4+2][::-1].hex(), "\tint(packet[i*4:i*4+2][::-1].hex()) = ", int(packet[i*4:i*4+2][::-1].hex()), sep=None)
        #print("Calculating ch2 with: ", "\tpacket[i*4+2:i*4+4][::-1].hex() = ", packet[i * 4+2:i * 4 + 4][::-1].hex(), "\tint(packet[i*4:i*4+2][::-1].hex()) = ", int(packet[i * 4+2:i * 4 + 4][::-1].hex()), sep=None)

        # DEBUG !
        time.append(counter * 6 + i * tsamp)
        ch1.append(int(packet[i*12:i*12+4][::-1].hex(), 16))
        ch2.append(int(packet[i*12+4:i*12+8][::-1].hex(), 16))
        ch3.append(int(packet[i*12+8:i*12+12][::-1].hex(), 16))
        ch1_v.append(round(ch1[-1]/4095*vref, 4))
        ch2_v.append(round(ch2[-1]/4095*vref, 4))
        ch3_v.append(round(ch3[-1]/4095*vref, 4))
        #ch1.append(int(packet[i*4:i*4+2][::-1].hex(), 16))
        #ch2.append(int(packet[i*4+2:i*4+4][::-1].hex(), 16))
        #ch1_v.append(round(ch1[-1]/4095*vref, 4))
        #ch2_v.append(round(ch2[-1]/4095*vref, 4))
    print("Time: ", time, sep=None)
    print("Channel #1: ", ch1, sep=None)
    print("Channel #2: ", ch2, sep=None)
    print("Channel #3: ", ch3, sep=None)
    print()
    print("Channel (V) #1: ", ch1_v, sep=None)
    print("Channel (V) #2: ", ch2_v, sep=None)
    print("Channel (V) #3: ", ch3_v, sep=None)

    return (time,ch1,ch2, ch1_v, ch2_v)


asyncio.run(main())