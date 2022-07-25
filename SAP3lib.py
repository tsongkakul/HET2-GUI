import bitstream as bs
from numpy import uint16

class SAP3Broadcaster():
    def __init__(self):
        super(SAP3Broadcaster,self).__init__()
        self.first_valid = 0
        self.last_packet = 0
        self.curr_packet = 0
        self.remaining_subpack  = None
        self.total_subpack = 0
        self.data_len = None
        self.processed_sub = 0
        self.packet_data = []
        self.packet_0 = 0
        self.packet_counter = 0
        self.packet_ovf = 0
        self.good_packets = 1
        self.timestamp = None
        self.t_samp = 1 # seconds

        self.packet_loss = []
        self.amp_raw = []
        self.pot_raw = []
        self.amp_proc = []
        self.pot_proc = []

    def parse_header(self,header):
        h_stream = bs.BitStream()
        h_stream.write(header, uint16)
        rem = int(str(h_stream.read(3)), 2)
        data_len = int(str(h_stream.read(5)), 2)
        count = int(str(h_stream.read(6)), 2)
        total = int(str(h_stream.read(2)), 2)

        # print(count, total, rem, data_len)
        if count != self.last_packet: # new packet received
            self.last_packet = self.curr_packet
            self.curr_packet = count
            # print(self.last_packet, self.curr_packet)
            if (total == rem) and (self.last_packet != self.curr_packet): # valid new packet
                # print("New pack!")

                if not self.first_valid:
                    self.packet_0 = self.curr_packet - 1
                    self.first_valid = 1
                if self.curr_packet<self.last_packet:
                    self.packet_ovf += 1
                self.packet_counter = (self.curr_packet+64*self.packet_ovf) - self.packet_0
                self.total_subpack = total
                self.remaining_subpack = rem
                self.data_len = data_len
                self.packet_data = [] # clear data
                self.processed_sub = 0
                return 1 # return 1 if valid packet
        elif count == self.curr_packet and self.first_valid: #subpacket received
            if(rem == (self.total_subpack - self.processed_sub)): # got expected next subpacket
                self.total_subpack = total
                self.remaining_subpack = rem
                self.data_len = data_len
                self.good_packets += 1
                self.packet_loss.append(self.packet_counter-self.good_packets + 1)
                return 1 # return 1 if valid packet
        return 0

    def parse_packet(self,packet):
        out = parse_bitstream(packet, self.data_len)
        self.packet_data += out
        if self.remaining_subpack == 0:
            self.amp_raw = []
            self.pot_raw = []
            amp_temp = []
            pot_temp = []
            for i,raw_data in enumerate(self.packet_data):
                if(i<10):
                    self.amp_raw.append(raw_data)
                    if i:
                        amp_temp.append(zigzag_decode(self.amp_raw[i])\
                                             + amp_temp[i-1])
                    else:
                        amp_temp.append(zigzag_decode(raw_data))
                else:
                    self.pot_raw.append(raw_data)
                    if i>10:
                        pot_temp.append(zigzag_decode(self.pot_raw[i-10])\
                                             + pot_temp[i-11])
                    else:
                        pot_temp.append(zigzag_decode(raw_data))
            self.amp_proc += [convert_amp(i) for i in amp_temp]
            self.pot_proc += [convert_pot(i) for i in pot_temp]

def parse_bitstream(packet, data_len):
    out = []
    d_stream = bs.BitStream()
    d_stream.write(packet)  # load data bitstream (rest of data)
    for i in range(data_len):
        l_str = str(d_stream.read(2))  # TRY EXCEPT HERE
        # read 2 bits from length bitstream and convert to len x
        data_len = (2 * int(l_str[0]) + int(l_str[1]) + 1) * 4
        # print(l_str, data_len)
        out.append(int(str(d_stream.read(data_len)), 2))  # read x bits from data bitstream
    return out

def zigzag_decode(i):
    return (i >> 1) ^ -(i & 1)

def convert_amp(i):
    return 32768-i

def convert_pot(i):
    return 32768-i
# receive data
# check if new packet
    # clear packet data
# check if first packet
    # parse bit stream
# check if next packet
    # parse bit stream
# else process data
