import unittest
import HET2

het = HET2.V00()

class MyTestCase(unittest.TestCase):

    def test_cnvmodes(self):
        self.assertEqual(HET2.cnv_modes('idle','CA'),'00')

    def test_cnvbias(self):
        self.assertEqual(HET2.cnv_bias(0),'00')

    def test_gencmd(self):
        self.assertEqual(het.gen_cmd_str(),'00000000140101')

    def test_run(self):
        het.set_devmode('run')
        het.set_bias(-1.1)
        het.set_rtia('200')
        het.set_period(2)
        self.assertEqual(het.gen_cmd_str(),'00001092010201')


if __name__ == '__main__':
    unittest.main()
