"""Synthetic negative tests; no fixture is presented as hardware evidence."""
import struct
import unittest
from mono_delivery import ORIGINAL, RECORDS, build, decode, verify, ROOT

def fnv(raw):
    value = 2166136261
    for byte in raw:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return f'{value:08X}'

class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ORIGINAL / 'quiet_music/quiet_03.bin').read_bytes()

    def test_two_archived_captures(self):
        for label in RECORDS:
            with self.subTest(label=label):
                _, meta = build(label)
                self.assertEqual(meta['sample_count'], 48000)
                self.assertEqual(meta['source_kind'], 'user-reported-hardware-audio')
                self.assertFalse(meta['loaded_identity_verified'])
                self.assertIsNone(meta['measured_sample_rate_hz'])

    def test_export_matches_original(self):
        self.assertEqual(verify(ROOT / 'data')['result'], 'PASS')

    def test_truncation(self):
        with self.assertRaisesRegex(ValueError, '768000'):
            decode(self.raw[:-1], RECORDS['quiet_03'][1])

    def test_wrong_checksum(self):
        with self.assertRaisesRegex(ValueError, 'FNV'):
            decode(self.raw, '00000000')

    def test_bad_sign(self):
        raw = bytearray(self.raw)
        struct.pack_into('<i', raw, 8, 8388608)
        with self.assertRaisesRegex(ValueError, 'signed24'):
            decode(raw, fnv(raw))

    def test_id_gap(self):
        raw = bytearray(self.raw)
        struct.pack_into('<I', raw, 16, 42)
        with self.assertRaisesRegex(ValueError, 'Discontinuous'):
            decode(raw, fnv(raw))

    def test_overflow_flag(self):
        raw = bytearray(self.raw)
        struct.pack_into('<I', raw, 12, 1)
        with self.assertRaisesRegex(ValueError, 'flags'):
            decode(raw, fnv(raw))

    def test_unknown_flag(self):
        raw = bytearray(self.raw)
        struct.pack_into('<I', raw, 12, 4)
        with self.assertRaisesRegex(ValueError, 'flags'):
            decode(raw, fnv(raw))

    def test_saturation_retained(self):
        raw = bytearray(self.raw)
        struct.pack_into('<iI', raw, 8, 8388607, 2)
        self.assertEqual(decode(raw, fnv(raw))[0][1:], (8388607, 2))

    def test_id_low_word_carry(self):
        raw = bytearray(self.raw)
        for i in range(48000):
            sid = 0xfffffff8 + i
            struct.pack_into('<II', raw, i * 16, sid & 0xffffffff, sid >> 32)
        rows = decode(raw, fnv(raw))
        self.assertEqual(rows[8][0], 0x100000000)

if __name__ == '__main__':
    unittest.main(verbosity=2)
