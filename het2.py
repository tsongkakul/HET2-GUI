from customperipheral import CustomPeripheral
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
from ctypes import *
from os import getcwd
import csv, time, string

# define constants here
dev_modes = ['Idle', 'Unused', 'Stream', 'Duty Cycle']
pstat_modes = ['CA', 'CV']
rtia_values = [
    'External', '200', '1k', '2k', '3k',
    '4k', '6k', '8k', '10k', '12k',
    '16k', '20k', '24k', '30k', '32k',
    '40k', '48k', '64k', '85k', '96k',
    '100k', '120k', '128k', '160k', '196k',
    '256k', '512k']  # this needs to match preset options from AD5940.h
odr_values = [
    0.05, 0.1, 0.125, 0.1667, 0.25,
    0.5, 1, 2, 2.5, 5,
    10, 20, 25, 30, 50,
    60, 120, 150, 300, 600
] # this needs to match GUI options

pga_values = [1, 1.5, 2, 4, 9] # this needs to match preset options from AD5940.h

duty_timeon_values = [10, 30, 60, 120, 180, 300, 600, 3600]

duty_pct_values = [100, 50, 33.33, 20, 16.67, 10, 8.333, 5, 2, 1]

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
        self.dev_mode = 'Idle'
        self.dev_mode_new = self.dev_mode
        self.pstat_mode = 'CA'
        self.pstat_mode_new = self.pstat_mode
        self.bias = 0  # between -1.27 and 1.27V
        self.bias_new = self.bias  # between -1.27 and 1.27V
        self.r_tia = '100k'
        self.r_tia_new = self.r_tia
        self.odr = 1
        self.odr_new = self.odr
        self.pga_gain = 1.5
        self.pga_gain_new = self.pga_gain
        self.duty_timeon = 5
        self.duty_timeon_new = self.duty_timeon
        self.duty_pct = 1
        self.duty_pct_new = self.duty_pct
        self.v_ref = 1.82
        self.packet_data = []
        self.time_data = []
        self.amp_data = []
        self.ph_data = []
        self.temp_data = []
        self.xl_x_data = []
        self.xl_y_data = []
        self.xl_z_data = []
        self.batt_data = []
        self.cv_voltage = []
        self.cv_data = []
        self.char_list = [self.CHAR1, self.CHAR2, self.CHAR3, self.CHAR4, self.CHAR5]
        self.file_loc = ""
        self.info_packet = ''
        self.packet_buffer  = []
        self.data_buffer = [['Packet','CA', 'pH', 'Temperature','Device','Bias','Gain','Period']]
        #self.data_buffer = [['Packet', 'Time','CA', 'Device', 'Bias', 'Gain', 'Period']]
        self.num_duty_cycles = 0

    def update_char_list(self):
        self.char_list = [self.CHAR1, self.CHAR2, self.CHAR3, self.CHAR4, self.CHAR5]

    def parse_info(self, packet):
        print(packet)
        self.id = int(packet[0])
        self.dev_mode = dev_modes[int(packet[2] >> 4)]
        self.pstat_mode = pstat_modes[int(packet[2] & 0x0F)]
        self.bias = (int(packet[3]) - 128) / 100
        self.r_tia = rtia_values[int(packet[4])]
        self.odr = odr_values[int(packet[5])]

    def parse_data(self, packet, mode: "CA", time):
        if self.pstat_mode == "CA":
            packet_count = int(packet[-2:].hex(),16)
            print(packet_count)

            for i in range(0, 132, 4):
                data = packet[i:i + 4]
                if i<120:
                # packets alternate between CA, pH, and temp data
                    if (i / 4) % 3 == 0:
                        #self.time_data.append(time.total_seconds()-odr_values[self.odr]*(10-i/4))
                        self.time_data.append(packet_count)
                        self.amp_data.append(hex2float(data[::-1].hex()))
                    elif (i / 4) % 3 == 1:
                        self.ph_data.append(hex2float(data[::-1].hex()))
                    else:
                        self.temp_data.append(hex2float(data[::-1].hex()))
                        # self.data_buffer.append([self.amp_data[-1], self.id, self.bias_new,
                        #                          self.r_tia_new, self.odr_new])
                        self.data_buffer.append([self.time_data[-1], self.amp_data[-1], self.ph_data[-1],
                                                 self.temp_data[-1], self.id, self.bias_new,
                                                 self.r_tia_new, self.odr_new])
                # else:
                #     if i == 120:
                #         self.xl_x_data.append(hex2float(data[::-1].hex()))
                #     elif i == 124:
                #         self.xl_y_data.append(hex2float(data[::-1].hex()))
                #     elif i == 128:
                #         self.xl_z_data.append(hex2float(data[::-1].hex()))

        elif self.pstat_mode == "CV":
            pass

    def add_batt(self, data):
        self.batt.append(data)

    def set_devmode(self, try_input):
        if try_input in dev_modes:
            self.dev_mode_new = try_input
            return 1
        else:
            print("Invalid device mode.")
            return 0

    def set_pstatmode(self, try_input):
        if try_input in pstat_modes:
            self.pstat_mode_new = try_input
            return 1
        else:
            print("Invalid potentiostat mode:"+ str(input))
            return 0

    def set_bias(self, try_input):
        if abs(try_input) < 1.28:
            self.bias_new = try_input
        else:
            print("Invalid bias, bias must be between -1.27 and 1.27")

    def set_rtia(self, try_input):
        if try_input in rtia_values:
            self.r_tia_new = try_input
            return 1
        else:
            print("Invalid RTIA value.")
            return 0

    def set_odr(self, try_input):
        if try_input in odr_values:
            self.odr_new = odr_values.index(try_input)
            return 1
        else:
            print("Invalid ODR value.")

    def set_pga(self, try_input):
        if try_input in pga_values:
            self.pga_gain_new = try_input
            return 1
        else:
            print("Invalid PGA value.")
            return 0

    def set_duty_timeon(self, try_input):
        print("timeon", try_input)
        if int(try_input) in duty_timeon_values:
            self.duty_timeon_new = duty_timeon_values.index(int(try_input))
            return 1
        else:
            print("Invalid Duty Time On value:" + str(try_input))
            return 0

    def set_duty_pct(self, try_input):
        if int(try_input) in duty_pct_values:
            self.duty_pct_new = duty_pct_values.index(int(try_input))
            return 1
        else:
            print("Invalid Duty % value:" + str(try_input))
            return 0

    def get_sender(self, sender):
        if sender in self.char_list:
            return self.char_list.index(sender)

    def gen_cmd_str(self):
        return '0c00' + cnv_modes(self.dev_mode_new) + cnv_bias(self.bias_new) + \
               cnv_tia(self.r_tia_new) + str(hex(self.odr_new))[2:].zfill(2) + cnv_pga(self.pga_gain_new) + \
               '0000'+str(self.duty_timeon_new)[0]+str(self.duty_pct_new)[0]

    def set_file_info(self, path, file):
        self.file_loc = ''.join((path, '/', file, time.strftime("%Y%m%d-%H%M%S"), '.csv'))

    def save_data(self):
        with open(self.file_loc, 'a', newline='') as csvfile:
            datawriter = csv.writer(csvfile, delimiter=',')
            datawriter.writerows(self.data_buffer)
            self.data_buffer = []


def cnv_modes(dev_mode):
    try:
        dev_str = str(dev_modes.index(dev_mode))
    except ValueError:
        print("Value error, Invalid device mode.")
    return dev_str.zfill(2)


def cnv_bias(bias):
    print("Bias: {}".format(bias))
    return str(hex(int(bias * 100) + 128)[2:]).zfill(2)


def cnv_tia(rtia):
    try:
        tia_str = str(hex(rtia_values.index(rtia)))[2:].zfill(2)
    except ValueError:
        print("Invalid TIA.")
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
    i = int(s, 16)  # convert from hex to a Python int
    cp = pointer(c_int(i))  # make this into a c integer
    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
    return fp.contents.value  # dereference the pointer, get the float
