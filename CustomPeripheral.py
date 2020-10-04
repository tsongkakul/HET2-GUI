"""
Tanner Songkakul

Helper classes for CustomPeripheral devices and GUIs

Custom Peripheral
Contains UUIDs and parsing functions for basic custom peripheral.

CPPlot
Plot only object for plotting characteristic data on separate plots

Main Window
Full GUI with UI from QT Designer
"""

class CustomPeripheral(object):
    def __init__(self):
        self.NAME = "unknown"
        self.ADDR = "unknown"
        self.SYSCFG = "f000abcd-0451-4000-b000-000000000000"
        self.CHAR1 = "f00062d2-0451-4000-b000-000000000000"
        self.CHAR2 = "f00044dc-0451-4000-b000-000000000000"
        self.CHAR3 = "f0003c36-0451-4000-b000-000000000000"
        self.CHAR4 = "f0003a36-0451-4000-b000-000000000000"
        self.CHAR5 = "f00030d8-0451-4000-b000-000000000000"
        self.CHAR_LIST = [self.CHAR1, self.CHAR2, self.CHAR3, self.CHAR4, self.CHAR5]
        self.CHAR1_DATA =[]
        self.CHAR2_DATA =[]
        self.CHAR3_DATA =[]
        self.CHAR4_DATA =[]
        self.CHAR5_DATA =[]
        self.ALL_DATA = [self.CHAR1_DATA, self.CHAR2_DATA, self.CHAR3_DATA, self.CHAR4_DATA, self.CHAR5_DATA]
        self.datacount = 0
        self.CONNECTED = 0

    def parse_data(self, sender,data):
        """For basic custom peripheral with data in first byte only, extend/replace as needed"""
        if sender[4:8] == self.CHAR1[4:8]:
            self.CHAR1_DATA.append(int(data[0]))
            return 1
        elif sender[4:8] == self.CHAR2[4:8]:
            self.CHAR2_DATA.append(int(data[0]))
            return 2
        elif sender[4:8] == self.CHAR3[4:8]:
            self.CHAR3_DATA.append(int(data[0]))
            return 3
        elif sender[4:8] == self.CHAR4[4:8]:
            self.CHAR4_DATA.append(int(data[0]))
            return 4
        elif sender[4:8] == self.CHAR5[4:8]:
            self.CHAR5_DATA.append(int(data[0]))
            return 5