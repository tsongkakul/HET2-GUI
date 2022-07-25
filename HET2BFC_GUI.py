import asyncio, time, csv
from bleak import BleakScanner
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

async def main():
    timestr = time.strftime("%Y%m%d-%H%M%S")

    experiment = 'BFCTest'
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

    ch1_data_v = []
    ch2_data_v = []
    packet_loss_log =[]

    app = QtGui.QApplication([])
    win = pg.GraphicsWindow(title='Custom Peripheral')
    win.resize(1280, 720)

    win.setWindowTitle('ASSIST HET2 BFC v0')

    pg.setConfigOptions(antialias=True)

    ch1_plot = win.addPlot(row=1, col=1, colspan=6, title="Channel 1")
    ch2_plot = win.addPlot(row=2, col=1, colspan=6, title="Channel 2", pen = 'm')
    packet_plot = win.addPlot(row=3, col=1, colspan=6, title="Packet Loss", pen = 'r')
    time_0 = time.time()
    last_time = -5
    while 1:
        timestamp = time.time()-time_0
        if timestamp-last_time > 4: # 2 second debounce
            devices = await BleakScanner.discover(timeout = 0.5)
            for d in devices:
                # print(d)
                if(d.name == 'H'):
                    new_data = list(d.metadata["manufacturer_data"].values())[0]
                    print(new_data)
                    (new_count, new_ch1, new_ch2, new_ch1_v, new_ch2_v) = parse_packet(new_data)
                    print(new_count)
                    time_data.append(timestamp)
                    ch1_data.append(new_ch1)
                    ch2_data.append(new_ch2)
                    ch1_data_v.append(new_ch1_v)
                    ch2_data_v.append(new_ch2_v)
                    ch1_plot.plot(time_data, ch1_data_v, clear=True, name="Ch1", pen = 'g', symbol = 'o')
                    ch2_plot.plot(time_data, ch2_data_v, clear=True, name="Ch2", pen = 'm', symbol = 'o')
                    pg.QtGui.QApplication.processEvents()
                    last_time = timestamp

                    data_buffer = [timestamp, new_count, new_ch1, new_ch2, new_ch1_v, new_ch2_v]

                    with open(data_path, 'a', newline='') as csvfile:
                        datawriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                        for data in data_buffer:
                            datawriter.writerow(data_buffer)
            # # _ = plt.plot(counter)
            # plt.show()
                    # print(d.metadata["manufacturer_data"].keys())


def parse_packet(packet, vref = 1.804):
    count = packet[0]
    ch1 = int(packet[1:3][::-1].hex(),16)
    ch2 = int(packet[3:5][::-1].hex(),16)
    ch1_v = round(ch1/4095 * vref, 4) - 0.9
    ch2_v = round(ch2/4095*vref,4) - 0.9
    print("Ch1: {},Ch2: {}".format(ch1_v, ch2_v))
    # for i in range(6):
    #     # print(packet[i*4:i*4+2].hex())
    #     # print(packet[i*4+2:i*4+4].hex())
    #     time.append(counter*6+i*tsamp)
    #     ch1.append(int(packet[i*4:i*4+2][::-1].hex(),16))
    #     ch2.append(int(packet[i*4+2:i*4+4][::-1].hex(),16))
    #     ch1_v.append(round(ch1[-1]/4095*vref,4))
    #     ch2_v.append(round(ch2[-1]/4095*vref,4))
    # print(time)
    # print(count)
    # print(ch1_v)
    # print(ch2_v)
    return (count,ch1,ch2, ch1_v, ch2_v)


asyncio.run(main())