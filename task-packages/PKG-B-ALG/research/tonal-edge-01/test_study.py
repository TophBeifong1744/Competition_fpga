import unittest
import numpy as np
import study as d

class DiagnosisTests(unittest.TestCase):
    def test_background_decomposition_and_controls(self):
        plan=d.s.read(d.s.PLAN)
        for seed in plan['seeds']:
            a=d.backgrounds(plan,seed,240000)
            np.testing.assert_allclose(a['original_tone'],d.s.noise(plan,'tonal',seed,240000),rtol=0,atol=1e-14)
            np.testing.assert_allclose(np.sqrt(np.mean(a['equal_rms_band']**2,axis=1)),1,atol=1e-14)
            self.assertLess(np.sqrt(np.mean(a['tone_removed']**2)),.08)
            b=d.backgrounds(plan,seed,240000)
            for k in a:np.testing.assert_array_equal(a[k],b[k])

    def test_spectrum_and_nonmutation(self):
        p=d.s.read(d.s.PLAN);x=d.backgrounds(p,p['seeds'][0],2048)['original_tone']
        segment=d.adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=d.s.batch.b.POS,source_id='test',source_sha256=d.s.entry.sha256(__file__))
        f=next(d.iter_frames(segment));before=d.to_six_mic_baseline(f).copy();v=d.spectral(f)
        np.testing.assert_array_equal(before,d.to_six_mic_baseline(f))
        self.assertEqual(v[1]['mask_bins_mean'],v[.75]['mask_bins_mean'])
        self.assertGreaterEqual(v[.75]['tone_weight_share'],v[1]['tone_weight_share'])

    def test_mutually_exclusive_buckets(self):
        self.assertEqual(d.bucket({'valid':False},{'fresh_valid':False}),'baseline_rejected')
        for degree,expected in [(28,'tracker_wait_or_jump'),(32,'outside_cone')]:
            c={'valid':True,'unit_vector':d.s.batch.b.unit(degree,0).tolist()}
            self.assertEqual(d.bucket(c,{'fresh_valid':False}),expected)
        self.assertEqual(d.bucket({'valid':True,'unit_vector':[1,0,0]},{'fresh_valid':True}),'fresh')

if __name__=='__main__':unittest.main(verbosity=2)
