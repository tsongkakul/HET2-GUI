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
    '256k', '512k'] # this needs to match
period_values = [
     0.05, 0.1, 0.125, 0.1667, 0.25,
     0.5, 1, 2, 2.5, 5,
     10, 20, 25, 30, 50,
     60, 120, 150, 300, 600
    ]

pga_values = [1, 1.5, 2, 4, 9]


class HET2Device(CustomPeripheral):  # HET2 class compatible with SW version 0.0
    # ###
    # HET2 Object using UUIDs from custom peripheral
    #
    # Packet Structures
    # Syscfg- System config command
    # Char1- System Config Info (20 Bytes)
    # Char2- Electrochemical Data (81 Bytes)
    #
    # AMP-PH Mode

    def __init__(self):
        super(HET2Device, self).__init__()
        self.id = 0
        self.dev_mode = 'idle'
        self.dev_mode_new = self.dev_mode
        self.pstat_mode = 'CA_PH'
        self.pstat_mode_new = self.pstat_mode
        self.bias = 0 # between -1.27 and 1.27V
        self.bias_new = self.bias # between -1.27 and 1.27V
        self.r_tia = '100k'
        self.r_tia_new = self.r_tia
        self.period = 1 # index in lookup table
        self.period_new = self.period
        self.pga_gain = 1.5
        self.pga_gain_new = self.pga_gain
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

    def parse_info(self,packet):
        self.id = int(packet[0])
        self.dev_mode = dev_modes[int(packet[2]>>4)]
        self.pstat_mode = pstat_modes[int(packet[2] & 0x0F)]
        self.bias = (int(packet[3])-128)/100
        self.r_tia = rtia_values[int(packet[4])]
        self.period = period_values[int(packet[5])]

    def parse_data(self, packet, mode):
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
            self.pstat_mode_new = input
            return 1
        else:
            print("Invalid potentiostat mode.")
            return 0

    def set_bias(self, input):
        if (abs(input) < 1.28):
            self.bias_new = input
        else:
            print("Invalid bias, bias must be between -1.27 and 1.27")

    def set_rtia(self, input):
        if input in rtia_values:
            self.r_tia_new = input
            return 1
        else:
            print("Invalid RTIA value.")
            return 0

    def set_period(self, input):
        if input in period_values:
            self.period_new = input
            return 1
        else:
            print("Invalid period value.")

    def set_pga(self, input):
        if input in pga_values:
            self.pga_new = input
            return 1
        else:
            print("Invalid PGA value.")
            return 0

    def get_sender(self, sender):
        if sender in self.char_list:
            return self.char_list.index(sender)

    def gen_cmd_str(self):
        return '0c00' + cnv_modes(self.dev_mode_new, self.pstat_mode_new)  + cnv_tia(self.r_tia)+ cnv_bias(self.bias) + str(hex(self.period))[2:].zfill(2) + cnv_pga(self.pga_gain)

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

