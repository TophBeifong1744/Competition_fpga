import unittest
import numpy as np
import robustness_sweep as r


class RobustnessTests(unittest.TestCase):
    def setUp(self):
        self.p=r.read(r.PLAN)

    def test_causal_fractional_convolution(self):
        h=np.zeros((6,20));r.fractional_tap(h[0],3.25,2)
        x=np.zeros(64);x[60]=1
        y=r.convolve(x,h,64)
        self.assertAlmostEqual(y[0,63],1.5)
        np.testing.assert_allclose(y[:,:60],0,atol=1e-14)

    def test_rir_support_and_reproducibility(self):
        for d in self.p['directions']:
            for room in self.p['rooms']:
                h,m=r.make_rir(self.p,d,room,self.p['seeds'][0])
                h2,m2=r.make_rir(self.p,d,room,self.p['seeds'][0])
                np.testing.assert_array_equal(h,h2);self.assertEqual(m,m2)
                self.assertTrue(np.isfinite(h).all())
                self.assertGreater(m['support_first'],0)
                self.assertEqual(m['support_last'],h.shape[1]-1)
                for i,p in enumerate(m['paths']):
                    self.assertEqual(p['first_tap'],int(np.floor(p['direct_delay_samples'])))
                if room['tail_relative_l2']:
                    other,_=r.make_rir(self.p,d,room,self.p['seeds'][1])
                    self.assertFalse(np.array_equal(h,other))

    def test_noise_rms_and_seed(self):
        for kind in self.p['noise_types']:
            a=r.noise(self.p,kind,123,4096)
            np.testing.assert_array_equal(a,r.noise(self.p,kind,123,4096))
            self.assertFalse(np.array_equal(a,r.noise(self.p,kind,124,4096)))
            self.assertTrue(np.isfinite(a).all())
            np.testing.assert_allclose(np.sqrt(np.mean(a*a,axis=1)),self.p['noise_nominal_rms'])

    def test_received_presence_and_tail_boundaries(self):
        p=dict(self.p,episodes=[dict(start=100,stop=1000)],edge_samples=10)
        support=dict(support_first=5,support_last=50);d=self.p['directions'][0]
        def label(a,b):return r.labels(p,a,b,support,d)
        self.assertEqual(label(0,106)['scope'],'target_absent')
        self.assertEqual(label(106,160)['scope'],'transition')
        self.assertEqual(label(160,996)['scope'],'target_active')
        self.assertEqual(label(160,997)['scope'],'transition')
        self.assertTrue(label(1000,1050)['tail_possible_after_emission'])
        self.assertEqual(label(1050,1100)['scope'],'target_absent')

    def test_clean_direct_direction(self):
        from audio_frames import adapt_six_mic_baseline,iter_frames
        for d in self.p['directions']:
            h,_=r.make_rir(self.p,d,self.p['rooms'][0],123)
            x=r.batch.probe(np.random.default_rng(123),8192)
            segment=adapt_six_mic_baseline(r.convolve(x,h,len(x)),sample_rate_hz=48000,positions_m=r.batch.b.POS,source_id='test',source_sha256=r.entry.sha256(__file__))
            errors=[]
            for f in list(iter_frames(segment))[2:]:
                c=r.entry.localize_frame(f)
                if c['valid']:
                    errors.append(r.batch.b.angle(np.array(c['unit_vector']),r.batch.b.unit(d['az'],d['el'])))
            self.assertGreater(len(errors),5)
            self.assertLess(max(errors),3)

    def test_frozen_references(self):
        r.verify_fixed()


if __name__=='__main__':unittest.main()
