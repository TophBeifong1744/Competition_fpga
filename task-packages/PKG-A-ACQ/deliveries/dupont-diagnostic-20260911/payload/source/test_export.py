import csv
import json
import struct
import tempfile
import unittest
from pathlib import Path
from export_four import RECORD, decode, export

def record(n=0, values=(-8388608,8388607,0,-513), flags=0, reserved=0):
    return RECORD.pack(n & 0xffffffff, n >> 32, *values, flags, reserved)

class ExportTests(unittest.TestCase):
    def test_signed_order(self): self.assertEqual(decode(record())[0], [0,-8388608,8388607,0,-513,0,''])
    def test_uint64(self): self.assertEqual(decode(record(2**64-1))[0][0], 2**64-1)
    def test_carry(self): self.assertEqual(decode(record(2**32-1)+record(2**32))[1][0], 2**32)
    def test_gap(self): self.assertEqual(decode(record(9)+record(11))[1][-2:], [1,'drop'])
    def test_clips(self):
        for flag in range(1,16): self.assertEqual(decode(record(flags=flag))[0][-2:], [1,'unknown'])
    def test_gap_clip(self): self.assertEqual(decode(record()+record(2,flags=8))[1][-1], 'drop;unknown')
    def test_invalid(self):
        for raw in (b'',record()[:-1],record(flags=16),record(reserved=1),record(values=(8388608,0,0,0)),record()+record(),record(2)+record(1),record(2**64-1)+record()):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError): decode(raw)
    def test_export_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'input.bin';raw.write_bytes(record())
            kw=dict(acquisition_id='test-1',config_version='test-v1',source_kind='synthetic-code',provenance='unit fixture, not recording',capture_point='software fixture')
            meta=export(raw,root/'out',**kw)
            self.assertEqual(meta['evidence_level'],'synthetic')
            self.assertIsNone(meta['coordinates_m'])
            self.assertEqual((root/'out/raw.bin').read_bytes(),raw.read_bytes())
            with self.assertRaises(FileExistsError): export(raw,root/'out',**kw)
            kw['provenance']=''
            with self.assertRaises(ValueError): export(raw,root/'bad',**kw)

if __name__=='__main__': unittest.main(verbosity=2)
