import unittest
import numpy as np
import guard as g
from audio_frames import adapt_six_mic_baseline,iter_frames

def frame(x):
    segment=adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=g.b.POS,source_id='guard-test',source_sha256='0'*64)
    return next(iter_frames(segment))

class GuardTests(unittest.TestCase):
    def test_fallback_matches_selected_original_algorithm(self):
        rng=np.random.default_rng(441)
        for x in [rng.normal(size=(6,1024)),np.tile(np.sin(2*np.pi*1000*np.arange(1024)/48000),(6,1))+.01*rng.normal(size=(6,1024))]:
            f=frame(x);r=g.localize(f,'fallback035');expected=g.weighted.localize(f,1 if r['guard_trigger'] else .75)
            for k in ['valid','unit_vector','pair_delays_samples','rejection_reasons']:self.assertEqual(r[k],expected[k])
        self.assertTrue(r['guard_trigger'])

    def test_caps_clean_directions(self):
        x=g.b.source(np.random.default_rng(882))
        for az,el in [(0,10),(28,0),(0,28),(32,0),(-28,0)]:
            samples=g.b.render(x,g.b.unit(az,el))[:,1536:2560];r=g.localize(frame(samples),'cap150')
            self.assertTrue(r['valid']);self.assertLess(g.b.angle(np.array(r['unit_vector']),g.b.unit(az,el)),3)

    def test_input_immutable_and_common_gain(self):
        x=np.random.default_rng(555).normal(size=(6,1024));old=x.copy()
        self.assertAlmostEqual(g.concentration(x),g.concentration(3*x))
        np.testing.assert_allclose(g.capped_gcc(x),g.capped_gcc(3*x),atol=1e-10,equal_nan=True)
        np.testing.assert_array_equal(x,old)

    def test_silence_and_bad_method(self):
        f=frame(np.zeros((6,1024)))
        for method in ['cap150','fallback035']:self.assertFalse(g.localize(f,method)['valid'])
        with self.assertRaises(ValueError):g.localize(f,'unknown')

    def test_generator_reproducible_no_label_mutation(self):
        import study as s
        p=s.s.read(s.ROOT/'payload/config/robustness-sweep.json');p=dict(p,duration_samples=4096,episodes=[dict(start=500,stop=3000)])
        for noise in ['tone700','band','pink','narrow_target']:
            a,m=s.generate(p,noise,dict(name='test',az=28,el=0),p['rooms'][0],2026091300)
            b,n=s.generate(p,noise,dict(name='test',az=28,el=0),p['rooms'][0],2026091300)
            self.assertEqual(m,n);np.testing.assert_array_equal(a.samples,b.samples)

if __name__=='__main__':unittest.main(verbosity=2)
