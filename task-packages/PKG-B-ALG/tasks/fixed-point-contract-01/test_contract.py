"""Draft/schema tests only; these do not execute fixed-point arithmetic."""
import copy,unittest
import evaluate_contract as e
class Tests(unittest.TestCase):
    def setUp(self):self.config=e.read(e.HERE/'contract.json')
    def test_unknowns_remain_unknown(self):
        result=e.evaluate(self.config)
        self.assertIsNone(result['cycles_available_per_hop']);self.assertIsNone(result['serial_fft_ifft_cycles']);self.assertIsNone(result['selected_candidate'])
    def test_parameterized_cycle_expressions(self):
        self.config['pending_A'].update(processing_clock_hz=100000000,fft_cycles_per_transform=1024,ifft_cycles_per_transform=2048)
        r=e.evaluate(self.config);self.assertAlmostEqual(r['cycles_available_per_hop'],100000000*512/48000);self.assertEqual(r['serial_fft_ifft_cycles'],36864)
    def test_insufficient_cross_width_rejected(self):
        self.config['candidates'][0]['formats']['cross_component']['W']=68
        with self.assertRaises(AssertionError):e.evaluate(self.config)
    def test_unknown_clock_not_coerced_from_boolean(self):
        self.config['pending_A']['processing_clock_hz']=True
        with self.assertRaises(AssertionError):e.evaluate(self.config)
    def test_storage_and_endpoint_ranges(self):
        r=e.evaluate(self.config)
        for c in r['candidates']:
            t=c['partial_totals'];self.assertLessEqual(t['bit_packed_bytes'],t['byte_aligned_element_bytes']);self.assertLessEqual(t['byte_aligned_element_bytes'],t['software_container_bytes'])
            self.assertGreaterEqual(c['ranges']['audio_weight']['max'],1)
        self.assertEqual(e.storage(3,34)['software_container_bytes'],24)
if __name__=='__main__':unittest.main(verbosity=2)
