import unittest
from calculate_budget import calculate, evaluate

class BudgetTests(unittest.TestCase):
    def test_frame_clock_floor(self):
        self.assertEqual(evaluate(4,61440000)['cycles_per_hop_floor'],655360)
        self.assertEqual(evaluate(6,100000000)['cycles_per_hop_floor'],1066666)
    def test_transforms(self):
        self.assertEqual(evaluate(4,100000000)['fft_service_cycles_proposed'],80000)
        self.assertEqual(evaluate(6,100000000)['fft_service_cycles_proposed'],168000)
    def test_margin_not_capability(self):
        x=evaluate(6,61440000)
        self.assertEqual(x['non_fft_cycles_after_proposed_margin'],356288)
    def test_binary_payload_not_csv(self):
        x=evaluate(4,100000000)
        self.assertEqual(x['pcm_int32_payload_Bps'],768000)
        self.assertEqual(x['illustrative_record_Bps'],1344000)
        self.assertEqual(x['full_overlap_frame_reads_int32_Bps'],1536000)
    def test_six_buffers(self):
        x=evaluate(6,100000000)['buffers_int32_complex32_components_bytes']
        self.assertEqual(x['retained_half_spectra'],24624)
        self.assertEqual(x['one_full_complex_ifft_assembly'],8192)
    def test_initial_lock_not_refresh(self):
        self.assertEqual(calculate()['initial_five_accepted_frames_best_case_ms'],64)
    def test_fifo_not_deadline(self):
        x=calculate()['mono_diagnostic']
        self.assertAlmostEqual(x['fifo_empty_to_full_ms_no_service'],21.3333333333333)
        self.assertTrue(x['payload_and_guard_fit'])
        self.assertFalse(x['continuous_stream_or_output_proven'])
    def test_cic_group_delay(self):
        self.assertAlmostEqual(calculate()['cic3_R64_group_delay_pcm_samples'],1.4765625)
    def test_cycle_log(self):
        self.assertEqual(calculate()['fft_archive']['stressed_job_duration'],7641)
    def test_unsupported_scope(self):
        with self.assertRaises(ValueError): evaluate(7,100000000)
        with self.assertRaises(ValueError): evaluate(4,0)
    def test_no_fabricated_full_budget(self):
        x=calculate()
        self.assertIsNone(x['whole_system_DSP_allocation'])
        self.assertIsNone(x['whole_system_BRAM_allocation'])
        self.assertIsNone(x['end_to_end_audio_latency_limit_ms'])

if __name__ == '__main__': unittest.main(verbosity=2)
