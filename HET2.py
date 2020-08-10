# define constants here
dev_modes = ['idle', 'run', 'save', 'dump']
pstat_modes = ['CA', 'CV']
rtia_values = [
    'External', '200', '1k', '2k', '3k',
    '4k', '6k', '8k', '10k', '12k',
    '16k', '20k', '24k', '30k', '32k',
    '40k', '48k', '64k', '85k', '96k',
    '100k', '120k', '128k', '160k', '196k',
    '256k', '512k']
pga_values = [1, 1.5, 2, 4, 9]


class HET2Device(CustomPeripheral):  # HET2 class compatible with SW version 0.0
    SYSCFG_UUID = "f000abcd-0451-4000-b000-000000000000"
    CHAR1_UUID = "f00062d2-0451-4000-b000-000000000000"
    CHAR2_UUID = "f00044dc-0451-4000-b000-000000000000"
    CHAR3_UUID = "f0003c36-0451-4000-b000-000000000000"
    CHAR4_UUID = "f0003a36-0451-4000-b000-000000000000"
    CHAR5_UUID = "f00030d8-0451-4000-b000-000000000000"

    def __init__(self):
        self.id = 0
        self.dev_mode = 'idle'
        self.pstat_mode = 'CA'
        self.bias = 0 # between -1.27 and 1.27V
        self.r_tia = '100k'
        self.period = 1 # seconds
        self.pga_gain = 1.5
        self.v_ref = 1.82
        self.amp_data = []
        self.ph_data = []
        self.batt = []

    def add_amp(self, data):
        self.amp_data.append(calc_amp(data))

    def add_ph(self, data):
        self.ph_data.append(calc_v(data))

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

    def set_period(self,input):
        self.period = int(input)

    def set_pga(self,input):
        if input in pga_values:
            self.dev_mode = input
            return 1
        else:
            print("Invalid PGA value.")
            return 0

    def gen_cmd_str(self):
        return '0000' + cnv_modes(self.dev_mode, self.pstat_mode) + cnv_bias(self.bias) + cnv_tia(self.r_tia) + str(hex(self.period))[2:].zfill(2) + cnv_pga(self.pga_gain)

def calc_v(raw_data, r_tia, pga_gain, v_ref):
    return (raw_data - 32768) / 32768 * (v_ref / pga_gain) * (1.835 / 1.82)


def calc_amp(raw_data, r_tia, pga_gain, v_ref):
    return calc_v(raw_data, r_tia, pga_gain, v_ref) * -1000000


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
    bias_bin = twos_complement(int(bias * 100), 8)
    return str(bias_bin)[2:].zfill(2)


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


def get_command():
    global global_command, state
    print('Enter \'help\' for a list of possible commands and \'info\' to get current device status.')
    global_command = raw_input('Please enter a command:')
    global_command = global_command.rstrip()
    # print(global_command)
    return


def twos_complement(value, bitLength):
    return hex(value & (2 ** bitLength - 1))
