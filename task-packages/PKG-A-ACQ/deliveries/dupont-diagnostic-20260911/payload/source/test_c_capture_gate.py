"""Synthetic byte/log fixtures only; no microphone recording is generated."""
import struct
import unittest
from export_c_capture import verify, CONFIG

class CaptureGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=b''.join(struct.pack('<IIiiiiII',i+4096,0,12,-24,36,-48,0,0) for i in range(32000))
        digest=2166136261
        for b in cls.raw:
            digest=((digest^b)*16777619)&0xffffffff
        cls.serial='TEST FIXTURE ONLY\nFOUR PDM capture '+CONFIG+'\n'
        cls.serial+=''.join(f'DONE packet={i} actual_bytes=8000 DMA_SR=00001002\n' for i in range(128))
        cls.serial+='FOUR_CAPTURE_INTEGRITY_PASS groups=32000 bytes=1024000 packets=128 clip_groups=0\n'
        cls.serial+=f'first_id_hex={4096:016X} last_id_hex={36095:016X}\n'
        cls.serial+=f'DMA_SR=00001002 SOURCE_STATUS=0000000A sync_error=0 overflow=0 fnv1a32={digest:08X}\n'
        cls.fnv=digest
    def test_valid_fixture(self):
        self.assertEqual(verify(self.raw,self.serial),self.fnv)
    def test_truncated(self):
        with self.assertRaises(ValueError):verify(self.raw[:-1],self.serial)
    def test_wrong_bin(self):
        with self.assertRaises(ValueError):verify(b'\xff'+self.raw[1:],self.serial)
    def test_missing_packet(self):
        with self.assertRaises(ValueError):verify(self.raw,self.serial.replace('DONE packet=7 ','LOST packet=7 '))
    def test_failed_capture(self):
        with self.assertRaises(ValueError):verify(self.raw,self.serial+'FOUR_CAPTURE_FAIL\n')
    def test_old_config(self):
        with self.assertRaises(ValueError):verify(self.raw,self.serial.replace(CONFIG,'mono-v1'))
    def test_duplicate_log(self):
        with self.assertRaises(ValueError):verify(self.raw,self.serial*2)
    def test_wrong_source_status(self):
        with self.assertRaises(ValueError):verify(self.raw,self.serial.replace('SOURCE_STATUS=0000000A','SOURCE_STATUS=0000002A'))
    def test_dma_error(self):
        with self.assertRaises(ValueError):verify(self.raw,self.serial.replace('DMA_SR=00001002','DMA_SR=00004010'))

if __name__=='__main__':unittest.main(verbosity=2)
