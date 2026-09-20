"""Raw/UART association tests using copies in memory; no board or configuration work."""
from pathlib import Path
import struct,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import finish_scene as s
class SceneExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=s.HERE/'delivery-01/c-scene-20260917-01'
        cls.raw=(p/'raw.bin').read_bytes();cls.log=(p/'serial.log').read_text(encoding='utf-8-sig')
    def reject(self,raw,log):
        with self.assertRaises(ValueError):s.verify(raw,log)
    def test_valid_real_pair(self):
        r=s.verify(self.raw,self.log);self.assertEqual(r['fnv1a32'],'9494D645');self.assertEqual(r['groups'],288250)
    def test_truncation(self):self.reject(self.raw[:-1],self.log)
    def test_duplicate_id(self):
        raw=bytearray(self.raw);raw[32:40]=raw[:8];self.reject(raw,self.log)
    def test_invalid_signed24(self):
        raw=bytearray(self.raw);struct.pack_into('<i',raw,8,8388608);self.reject(raw,self.log)
    def test_bad_checksum(self):self.reject(self.raw,self.log.replace('fnv1a32=9494D645','fnv1a32=9494D644'))
    def test_inconsistent_statistics(self):self.reject(self.raw,self.log.replace('zeros=999','zeros=998'))
    def test_wrong_success_cursor(self):self.reject(self.raw,self.log.replace('bad_value=00000B80','bad_value=00000B81'))
    def test_wrong_dump_length(self):self.reject(self.raw,self.log.replace('words=2306000','words=2306001'))
    def test_duplicate_pass_from_two_runs(self):
        line=next(x for x in self.log.splitlines() if x.startswith('SCENE_INTEGRITY_PASS'))
        self.reject(self.raw,self.log+'\n'+line+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
