"""
Tanner Songkakul

CustomPeripheralGUI.py

Uses bleak and PyQT to connect to a CC2642 Launchpad running Custom Peripheral
and plot data on each characteristics.

Requires bleak, pyqt, qasync and included customperipheral library
"""
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from os import getcwd

import sys
import asyncio
import asyncqt

import bleak

from bleak import BleakClient, discover
from het2 import HET2Device
from het2 import odr_values

cp = HET2Device()


def notification_handler(sender, data):
    """Handle incoming packets."""
    # TODO this still drops packets...implement buffer
    print("Data received from {}".format(sender))
    if sender[4:8] == cp.CHAR2[4:8]:
        print(len(data))
        print(data)
        cp.parse_data(data, "AMPPH")
    if sender[4:8] == cp.CHAR1[4:8]:
        cp.info_packet = data


class MainWindow(QMainWindow):
    """Main Window."""
    client: BleakClient = None

    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        # Initialize objects and variables
        self.scan_list = []
        self.device_name = "None"
        self.filepath = getcwd()+'\Data'
        self.filename = "Experiment"
        cp.set_file_info(self.filepath, self.filename)
        # Load the UI Page and QTimer
        uic.loadUi('HET2_Gui-v2.ui', self)  # From QTDesigner
        self.filepathDisp.setText(self.filepath)
        self.expEntry.setText(self.filename)
        self.line_array = []
        for i in range(5):
            self.line_array.append(self.CAplotWidget.plot([], pen=(i, 5)))
        self.CAplotWidget.addLegend()
        self.plot_mode = "CA_PH"
        self.set_plotmode(self.plot_mode)
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot)
        # BLE management variables
        self.loop = loop
        self.connected = False
        self.connected_device = None
        self.new_config = False
        # Attach button/menu callbacks
        # Config
        self.browseButton.clicked.connect(self.get_filepath)
        # Scan and Connect
        self.scanButton.clicked.connect(self.scan_callback)
        self.scanBox.activated.connect(self.select_device)
        self.connectButton.clicked.connect(self.connect_callback)
        self.actionQuit.triggered.connect(self.close)  # File->Quit

        # initialize values from combo box

    def get_settings(self):
        cp.set_devmode(self.devModeCombo.currentText())
        cp.set_pstatmode(self.pstatModeCombo.currentText())
        cp.set_odr(float(self.ODRCombo.currentText()))
        print(cp.odr_new)
        cp.set_bias(float(self.biasEntry.text()))
        cp.set_rtia(self.gainCombo.currentText())
        print("ODR: {}, Bias: {}, RTIA: {}".format(cp.odr_new, cp.bias_new, cp.r_tia_new))

    async def update_config(self, client):
        self.get_settings()
        syscfg_string = bytearray.fromhex(cp.gen_cmd_str().ljust(cp.SYSCFGLEN * 2, '0'))
        print(syscfg_string)
        await client.write_gatt_char(cp.SYSCFG, syscfg_string)

    def get_filepath(self):
        self.filepath = QFileDialog.getExistingDirectory(self, "Select folder for saving data...",
                                                         options=QFileDialog.DontUseNativeDialog)
        self.filepathDisp.setText(self.filepath)
        self.filename = self.expEntry.text()
        cp.set_file_info(self.filepath, self.filename)

    async def device_scan(self):
        self.display_status("Scanning...")
        # print('Scanning for devices')
        if not cp.CONNECTED:
            self.scanBox.clear()
            self.scan_list = []
            devices = await discover(10)
            # print('scan returns...')
            for i, device in enumerate(devices):
                if device.name[0:3] == "HET":
                    self.scanBox.addItem(device.name)
                    self.scan_list.append(device)
                # print(f"{i}: {device.name}")
            if self.scan_list:
                cp.NAME = self.scan_list[0].name  # required for case when CP is first in list
                cp.ADDR = self.scan_list[0].address
                self.display_status("Scan complete!")
            else:
                self.display_status("No devices found!")

    def scan_callback(self):
        scan_task = self.device_scan()
        asyncio.ensure_future(scan_task, loop=loop)

    async def connect_task(self):
        self.display_status("Connecting to {}".format(cp.NAME))
        async with BleakClient(cp.ADDR, loop=loop) as client:
            try:
                x = await client.is_connected()  # Attempt device connection TODO add error messages
                win.display_status("Enabling CHAR1")
                await client.start_notify(cp.CHAR1, notification_handler)
                win.display_status("Enabling CHAR2")
                await client.start_notify(cp.CHAR2, notification_handler)
                win.display_status("Connected")
                await self.start_task(client)
                await self.main(client)
            except AttributeError:
                win.display_status("Unable to connect!")
            except bleak.exc.BleakDotNetTaskError:
                win.display_status("Could not get GATT characteristics")
            # except:
            #     win.display_status("Error")

    def connect_callback(self):
        connect_task = self.connect_task()
        asyncio.ensure_future(connect_task, loop=loop)

    def select_device(self):
        if not cp.CONNECTED:
            cp.NAME = self.scan_list[self.scanBox.currentIndex()].name
            cp.ADDR = self.scan_list[self.scanBox.currentIndex()].address
            print(cp.NAME)
            print(cp.ADDR)

    async def start_task(self, client):
        # try:
        #     win.display_status("Starting Device")
        #     syscfg_string = bytearray.fromhex('{:>20d}'.format(cp.gen_cmd_str()))
        #     print(syscfg_string)
        #     await client.write_gatt_char(cp.SYSCFG, syscfg_string)
        #     win.display_status("Started!")
        # except ValueError:
        #     win.display_status("Error!")
        win.display_status("Starting Device")
        self.get_settings()
        syscfg_string = bytearray.fromhex(cp.gen_cmd_str().ljust(cp.SYSCFGLEN * 2, '0'))
        print(syscfg_string)
        await client.write_gatt_char(cp.SYSCFG, syscfg_string)
        win.display_status("Started!")

    async def main(self, client):
        while True:  # main loop
            if cp.data_buffer:
                cp.save_data()
            await asyncio.sleep(1)
            await self.update_plot()


    def display_status(self, msg):
        """Display messages"""
        self.statusDisp.setText(msg)

    def set_plotmode(self, new_mode):
        if new_mode == "CA_PH":
            self.plot_mode = "CA_PH"
            self.CAplotWidget.setLabel(axis="left", text="Current (uA)")
            self.CAplotWidget.setLabel(axis="bottom", text="Samples")
            self.VPlotWidget.setLabel(axis="left", text="Voltage (V)")
            self.VPlotWidget.setLabel(axis="bottom", text="Samples")
            self.AccelPlotWidget.setLabel(axis="left", text="Motion")
            self.AccelPlotWidget.setLabel(axis="bottom", text="Samples")
            self.plot1 = self.CAplotWidget.plot([], name='CA (uA)', pen='y')
            self.plot2 = self.VPlotWidget.plot([], name='pH (V)', pen='m')
            self.plot3 = self.VPlotWidget.plot([], name='Temp (V)', pen='c')
            self.plot4 = self.AccelPlotWidget.plot([], name='Accelerometer X Data', pen='y')
            self.plot5 = self.AccelPlotWidget.plot([], name='Accelerometer Y Data', pen='m')
            self.plot6 = self.AccelPlotWidget.plot([], name='Accelerometer Z Data', pen='c')
            # TODO add second axes for pH
        elif new_mode == "CV":
            self.plot_mode = "CV"
            self.CAplotWidget.setLabel(axis="left", text="Current (uA)")
            self.CAplotWidget.setLabel(axis="bottom", text="Bias Voltage (V)")
            self.plot1 = self.CAplotWidget.plot([], name='CA Data (uA)', pen='y')
            self.plot2 = self.VPlotWidget.plot([], name='pH Data (V)', pen='m')
            self.plot3 = self.VPlotWidget.plot([], name='Temp Data (V)', pen='c')
            self.plot4 = self.AccelPlotWidget.plot([], name='Accelerometer X Data', pen='y')
            self.plot5 = self.AccelPlotWidget.plot([], name='Accelerometer Y Data', pen='m')
            self.plot6 = self.AccelPlotWidget.plot([], name='Accelerometer Z Data', pen='c')

    def update_info(self, het):
        self.devNumDisp.setText(str(het.id))
        self.devStatusDisp.setText(het.dev_mode)
        self.devModeDisp.setText(het.pstat_mode)
        self.devBiasDisp.setText(str(het.bias_new)) #TODO fix this spaghetti
        self.devGainDisp.setText(het.r_tia_new)
        self.devODRDisp.setText(str(het.odr_new))

    async def update_plot(self):
        # fast update of all data
        # print("Update plot.")
        self.update_info(cp)
        if self.plot_mode == "CA_PH":
            if len(cp.amp_data) > 300:
                self.plot1.setData(cp.amp_data[-300:])
                self.plot2.setData(cp.ph_data[-300:])
                self.plot3.setData(cp.temp_data[-300:])
                self.plot4.setData(cp.xl_x_data[-100:])
                self.plot5.setData(cp.xl_y_data[-100:])
                self.plot6.setData(cp.xl_z_data[-100:])
            else:
                self.plot1.setData(cp.amp_data)
                self.plot2.setData(cp.ph_data)
                self.plot3.setData(cp.temp_data)
                self.plot4.setData(cp.xl_x_data)
                self.plot5.setData(cp.xl_y_data)
                self.plot6.setData(cp.xl_z_data)
        elif self.plot_mode == "CV":
            self.plot1.setData(cp.cv_voltage, cp.cv_data)
            self.plot2.setData([])

    def on_disconnect(self, client: BleakClient):
        self.connected = False
        # Put code here to handle what happens on disconnet.
        print("Disconnected.")


app = QApplication(sys.argv)
loop = asyncqt.QEventLoop(app)
asyncio.set_event_loop(loop)  # NEW must set the event loop
win = MainWindow()
win.show()
with loop:
    sys.exit(loop.run_forever())
