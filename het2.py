from customperipheral import CustomPeripheral
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
from ctypes import *
from os import getcwd
import csv, time, string

# define constants here
dev_modes = ['idle', 'run', 'save', 'dump']
pstat_modes = ['CA_PH', 'CV']
rtia_values = [
    'External', '200', '1k', '2k', '3k',
    '4k', '6k', '8k', '10k', '12k',
    '16k', '20k', '24k', '30k', '32k',
    '40k', '48k', '64k', '85k', '96k',
    '100k', '120k', '128k', '160k', '196k',
    '256k', '512k']
pga_values = [1, 1.5, 2, 4, 9]


class HET2Device(CustomPeripheral):  # HET2 class compatible with SW version 0.0
    # ###
    # HET2 Object using UUIDs from custom peripheral
    #
    # Packet Structures
    # Char1- System Config Data v(10 Bytes)
    #
    #
    # Char2- Electrochemical Data (81 Bytes)
    #
    # AMP-PH Mode

    def __init__(self):
        super(HET2Device, self).__init__()
        self.id = 0
        self.dev_mode = 'idle'
        self.pstat_mode = 'CA_PH'
        self.bias = 0 # between -1.27 and 1.27V
        self.r_tia = '100k'
        self.period = 1 # seconds
        self.pga_gain = 1.5
        self.v_ref = 1.82
        self.amp_data = []
        self.ph_data = []
        self.batt_data = []
        self.cv_voltage = []
        self.cv_data = []
        self.char_list = [self.CHAR1,self.CHAR2,self.CHAR3,self.CHAR4,self.CHAR5]
        self.file_loc =""
        self.data_buffer =[['CA', 'pH']]

    def update_char_list(self):
        self.char_list = [self.CHAR1,self.CHAR2,self.CHAR3,self.CHAR4,self.CHAR5]

    def parse_het(self, packet, mode):
        if self.pstat_mode == 'CA_PH':
            for i in range(0, 80, 4):
                data = packet[i:i + 4]
                if (i/4)%2 == 0: #even packets contain pH data
                    self.amp_data.append(hex2float(data[::-1].hex()))
                else:
                    self.ph_data.append(hex2float(data[::-1].hex()))
                    self.data_buffer.append([self.amp_data[-1], self.ph_data[-1]])

        elif self.pstat_mode == "CV":
            pass

    def add_batt(self, data):
        self.batt.append(data)

    def set_devmode(self, input):
        if input in dev_modes:
            self.dev_mode = input
            return 1
        else:
            print("Invalid device mode.")
            return 0

    def set_pstatmode(self, input):
        if input in pstat_modes:
            self.pstat_mode = input
            self.data_buffer = ['CA','pH']
            return 1
        else:
            print("Invalid potentiostat mode.")
            return 0

    def set_bias(self, input):
        if (abs(input) < 1.28):
            self.bias = input
        else:
            print("Invalid bias, bias must be between -1.27 and 1.27")

    def set_rtia(self, input):
        if input in rtia_values:
            self.r_tia = input
            return 1
        else:
            print("Invalid RTIA value.")
            return 0

    def set_period(self, input):
        self.period = int(input)

    def set_pga(self, input):
        if input in pga_values:
            self.dev_mode = input
            return 1
        else:
            print("Invalid PGA value.")
            return 0

    def get_sender(self, sender):
        if sender in self.char_list:
            return self.char_list.index(sender)

    def gen_cmd_str(self):
        return '0000' + cnv_modes(self.dev_mode, self.pstat_mode) + cnv_bias(self.bias) + cnv_tia(self.r_tia) + str(hex(self.period))[2:].zfill(2) + cnv_pga(self.pga_gain)

    def set_file_info(self,path,file):
        self.file_loc = ''.join((path, '/', file, time.strftime("%Y%m%d-%H%M%S"), '.csv'))

    def save_data(self):
        with open(self.file_loc, 'a', newline='') as csvfile:
            datawriter = csv.writer(csvfile, delimiter=',')
            datawriter.writerows(self.data_buffer)
            self.data_buffer = []


def cnv_modes(dev_mode, pstat_mode):
    try:
        dev_str = str(dev_modes.index(dev_mode))
    except ValueError:
        print("Value error, Invalid device mode.")
    try:
        pstat_str = str(pstat_modes.index(pstat_mode))
    except ValueError:
        print("Invalid pstat mode.")
    return dev_str + pstat_str


def cnv_bias(bias):
    return str(hex(int(bias*100)+128)[2:]).zfill(2)


def cnv_tia(rtia):
    try:
        tia_str = str(hex(rtia_values.index(rtia)))[2:].zfill(2)
    except ValueError:
        print("Invalid pstat mode.")
    return tia_str

def cnv_pga(pga):
    try:
        pga_str = str(hex(pga_values.index(pga)))[2:].zfill(2)
    except ValueError:
        print("Invalid  PGA.")
    return pga_str


def twos_complement(value, bitLength):
    return hex(value & (2 ** bitLength - 1))


def hex2float(s):
    i = int(s, 16)                   # convert from hex to a Python int
    cp = pointer(c_int(i))           # make this into a c integer
    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
    return fp.contents.value         # dereference the pointer, get the float



class HETWindow(QtWidgets.QMainWindow):
    #TODO add characteristic and packet printouts
    def __init__(self, *args, **kwargs):
        super(HETWindow, self).__init__(*args, **kwargs)
        # Load the UI Page
        uic.loadUi('HET2_Gui.ui', self)  # From QTDesigner
        self.plotWidget.addLegend()

        self.connectButton.clicked.connect(self.get_device)  # Connect button
        self.actionQuit.triggered.connect(self.close) # File->Quit

        self.connect_button = 0
        self.update_button = 0
        self.start_button = 0
        self.stop_button = 0
        self.device_name = "None"
        self.plot_mode = "CA_PH"
        self.set_plotmode(self.plot_mode)
        self.filepath = getcwd()
        self.filename = "TestExperiment"

    def set_plotmode(self,new_mode):
        if new_mode == "CA_PH":
            self.plot_mode == "CA_PH"
            self.plotWidget.setLabel(axis="left", text="Current (mA)")
            self.plotWidget.setLabel(axis="bottom", text="Samples")
            self.plot1 = self.plotWidget.plot([], name='CA Data (mA)', pen='y')
            self.plot2 = self.plotWidget.plot([], name='pH Data (V)', pen='m')
            # TODO add second axes for pH
        elif new_mode == "CV":
            self.plot_mode == "CV"
            self.plotWidget.setLabel(axis="left", text = "Current (mA)")
            self.plotWidget.setLabel(axis="bottom", text="Bias Voltage (V)")
            self.plot1 = self.plotWidget.plot([], name='Chronoamp Data (mA)', pen='y')
            self.plot2 = self.plotWidget.plot([], name='pH Data (V)', pen='m')

    def update_plot(self, het):
        if self.plot_mode == "CA_PH":
            self.plot1.setData(het.amp_data)
            self.plot2.setData(het.ph_data)
        elif self.plot_mode == "CV":
            self.plot1.setData(het.cv_voltage, het.cv_data)
            self.plot2.setData([])

    def get_device(self):
        """Connect button press callback, retrieves device name from text box and sets flag"""
        self.connect_button = 1
        self.device_name = self.deviceEntry.text()

    def get_filepath(self):
        self.filepath = QFileDialog.getExistingDirectory(self,"Select folder for saving data...", options=QFileDialog.DontUseNativeDialog)
        self.filepathDisp.setText(self.filepath)
        self.filename = self.expEntry.text()

    def update_settings(self):
        self.update_button = 1

    def start_requested(self):
        self.start_button = 1

    def stop_requested(self):
        self.stop_button = 1

    def button_ack(self,button):
        """Clear button press flag"""
        if button == "connect":
            self.connect_button = 0
        elif button == "update":
            self.update_button = 0
        elif button == "start":
            self.start_button = 0
        elif button == "stop":
            self.stop_button = 0

    def display_status(self, msg):
        """Display messages"""
        self.statusDisp.setText(msg)


