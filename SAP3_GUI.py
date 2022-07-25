import asyncio, time, csv
from bleak import BleakScanner
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
import bitstream as bs
from SAP3lib import *

SAP3 = SAP3Broadcaster()

test_data = "1a300aafff1020010021000189ab8e30d78bb0af88310724"

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

    ch1_data_v = []
    ch2_data_v = []

    amp_data = []
    ph_data = []
    packet_loss_log =[]

    app = QtGui.QApplication([])
    win = pg.GraphicsWindow(title='Custom Peripheral')
    win.resize(1280, 720)

    win.setWindowTitle('ASSIST SAP3')

    pg.setConfigOptions(antialias=True)

    ch1_plot = win.addPlot(row=1, col=1, colspan=6, title="Channel 1")
    ch2_plot = win.addPlot(row=2, col=1, colspan=6, title="Channel 2", pen = 'm')
    packet_plot = win.addPlot(row=3, col=1, colspan=6, title="Packet Loss", pen = 'r')
    time_0 = time.time()
    last_time = -5
    while 1:
        timestamp = time.time()-time_0
        if timestamp-last_time > 1: # 2 second debounce
            devices = await BleakScanner.discover(timeout = 0.5)
            for d in devices:
                # print(d.name)
                if d.name == 'H':
                    # print("Device Detected")
                    packet_header = list(d.metadata["manufacturer_data"].keys())[0]
                    if packet_header != 65535:
                        valid_pack = SAP3.parse_header(packet_header)
                        if valid_pack:
                            # print("Valid!")
                            new_packet = d.metadata["manufacturer_data"][packet_header]
                            print(SAP3.curr_packet, SAP3.last_packet, SAP3.total_subpack,
                                  SAP3.remaining_subpack, SAP3.data_len)
                            print(new_packet.hex())
                            SAP3.processed_sub += 1
                            SAP3.parse_packet(new_packet)
                            ch1_plot.plot(SAP3.amp_proc)
                            ch2_plot.plot(SAP3.pot_proc)
                            packet_plot.plot(SAP3.packet_loss)
                            pg.QtGui.QApplication.processEvents()

                            print(len(SAP3.amp_raw))
                            print(len(SAP3.pot_raw))
                            print(SAP3.amp_raw[-10::])
                            print(SAP3.amp_proc[-10::])
                            print(SAP3.pot_raw[-10::])
                            print(SAP3.pot_proc[-10::])

                            if(SAP3.packet_loss):
                                print(SAP3.packet_loss[-1])

                    # print(data)



            # with open(data_path, 'a', newline='') as csvfile:
            #     datawriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            #     for data in data_buffer:
            #         datawriter.writerow(data)
            # _ = plt.plot(counter)
            # plt.show()
                    # print(d.metadata["manufacturer_data"].keys()

asyncio.run(main())