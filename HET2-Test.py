import unittest
import het2

het = het2.HET2Device()
test_array = [0] * 80
amp_sol = list(range(0,20,2))
ph_sol = list(range(1,20,2))
for i in range(0,80):
    if i%4 == 0:
        test_array[i+3] = int(i/4)
print(test_array)

class HET2Tests(unittest.TestCase):

    def test_cnvmodes(self):
        self.assertEqual(het2.cnv_modes('idle','CA'),'00')

    def test_cnvbias(self):
        self.assertEqual(het2.cnv_bias(0),'00')

    def test_gencmd(self):
        self.assertEqual(het.gen_cmd_str(),'00000000140101')

    def test_run(self):
        het.set_devmode('run')
        het.set_bias(-1.1)
        het.set_rtia('200')
        het.set_period(2)
        self.assertEqual(het.gen_cmd_str(),'00001092010201')

    def test_amp_parsing(self):
        het.parse_het(bytearray(test_array),"AMPPH")
        self.assertEqual(amp_sol, het.amp_data)

    def test_ph_parsing(self):
        het.ph_data = []
        het.parse_het(bytearray(test_array),"AMPPH")
        self.assertEqual(ph_sol, het.ph_data)

if __name__ == '__main__':
    unittest.main()
