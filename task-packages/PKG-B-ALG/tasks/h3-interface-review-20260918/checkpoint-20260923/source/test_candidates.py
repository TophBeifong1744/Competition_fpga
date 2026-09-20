import unittest
import numpy as np
from common import config
from candidates import features,BandActivity,direction_summary,wrapped_error
from audio_candidate import mix_fast,mixer,render,POSITIONS

class GateTests(unittest.TestCase):
    def tone(self,f,a=10000,dc=0):
        x=np.rint(dc+a*np.sin(2*np.pi*f*np.arange(1024)/48000)).astype(np.int64)
        return np.tile(x[:,None],(1,4))

    def test_dc_removed(self):
        f=features(np.full((1024,4),10000,dtype=np.int64))
        self.assertEqual(f['centered_rms'],[0]*4)
        self.assertEqual(f['band_power'],[0]*4)

    def test_band_rejects_50hz(self):
        low=features(self.tone(50))['band_power'][0]
        voice=features(self.tone(1500))['band_power'][0]
        self.assertLess(low/voice,1e-4)

    def test_parseval_scale_and_dc_invariance(self):
        a=features(self.tone(1500)); b=features(self.tone(1500,dc=200000))
        np.testing.assert_allclose(a['band_power'],b['band_power'],rtol=0,atol=0)
        self.assertAlmostEqual(a['band_power'][0]/(10000**2/2),1,places=3)

    def test_amplitude_squared(self):
        x=self.tone(1500,a=500)
        np.testing.assert_allclose(np.asarray(features(2*x)['band_power']),4*np.asarray(features(x)['band_power']),rtol=0,atol=0)

    def test_attack_release_and_reset(self):
        g=BandActivity([1e6]*4,config())
        self.assertEqual([g.update([4e6]*4) for _ in range(3)],[False,False,True])
        self.assertEqual([g.update([1e6]*4) for _ in range(3)],[True,True,False])
        for _ in range(3):g.update([4e6]*4)
        self.assertFalse(g.update([4e6]*4,True))
        self.assertFalse(g.update([4e6]*4))

    def test_short_click_and_minimum_channels(self):
        g=BandActivity([1e6]*4,config())
        self.assertFalse(g.update([1e9]*4))
        self.assertFalse(g.update([0]*4))
        self.assertEqual([g.update([1e9,1e9,0,0]) for _ in range(5)],[False]*5)

    def test_bad_shape_nonfinite_and_range(self):
        for x in [np.zeros((1023,4),dtype=int),np.zeros((1024,4)),np.full((1024,4),2**23,dtype=int)]:
            with self.assertRaises(ValueError):features(x)
        g=BandActivity([0]*4,config())
        with self.assertRaises(ValueError):g.update([float('nan')]*4)

class MetricsTests(unittest.TestCase):
    def test_wrap_and_denominators(self):
        self.assertEqual(wrapped_error(-179,179),2)
        r=direction_summary([{'a':None},{'a':0},{'a':20}],0,'a')
        self.assertEqual(r['eligible_frames'],3)
        self.assertEqual(r['output_frames'],2)
        self.assertEqual(r['nominal_gt15_over_outputs'],.5)
        self.assertEqual(r['nominal_gt15_over_eligible'],1/3)

    def test_empty_and_background_not_fake_truth(self):
        self.assertIsNone(direction_summary([],0,'a')['nominal_deviation_p50_deg'])
        self.assertIsNone(direction_summary([{'a':10}],None,'a')['nominal_gt15_count'])

    def test_component_metric_known_six_db(self):
        from reference_metrics import component_snr
        signs=np.array([[(-1)**((r&c).bit_count()) for c in range(8)] for r in range(8)])
        noise=np.tile(signs[:,1:5],(100,1)).astype(float)
        target=np.ones(800)
        r=component_snr({'single':target,'manual':target},{'single':noise[:,0],'manual':noise.mean(axis=1)},
            np.ones(800,dtype=bool),reference_kind='synthetic_test')
        self.assertAlmostEqual(r['branches']['manual']['delta_snr_db_vs_mic0'],10*np.log10(4))

    def test_source_wav_is_not_component_reference(self):
        from reference_metrics import component_snr
        with self.assertRaises(ValueError):component_snr({}, {}, np.ones(10,dtype=bool),reference_kind='playback_wav')

class AudioTests(unittest.TestCase):
    def test_fast_mixer_matches_frozen_with_expiry_and_release(self):
        bank=np.random.default_rng(4).normal(size=(3,4096))*.001
        events=[dict(ready=100,target=1,fresh=True,valid_through=1300),
                dict(ready=1000,target=2,fresh=True,valid_through=2400),
                dict(ready=1800,target=0,fresh=False,valid_through=None)]
        old,w,_=mixer.mix_timeline(bank,8,4104,events,480)
        new,v=mix_fast(bank,8,4104,events,480)
        np.testing.assert_allclose(new,old,rtol=0,atol=2e-18)
        np.testing.assert_allclose(v,w,rtol=0,atol=2e-15)
        np.testing.assert_array_equal(new[:92],bank[0,:92])
        np.testing.assert_array_equal(new[2394:],bank[0,2394:])

    def test_single_clock_gain_and_no_wrap(self):
        x=np.full((5000,4),12345,dtype=np.int64)
        out,info=render(x,45,[],config())
        for y in out.values():np.testing.assert_allclose(y,12345/2**23,atol=1e-18,rtol=0)
        self.assertEqual(info['reference_rows'],[8,4992])
        self.assertEqual(info['physical_emit_rows'],[16,5000])

    def test_manual_delay_sign(self):
        x=np.zeros((100,4),dtype=np.int64)
        # +X has channels 1,2 arrive ~5.6 samples earlier. Integer surrogate 6.
        x[40,0]=x[40,3]=10000
        x[34,1]=x[34,2]=10000
        out,_=render(x,0,[],config())
        self.assertEqual(int(np.argmax(out['manual']))+8,40)

    def test_future_event_cannot_change_past(self):
        x=np.random.default_rng(5).integers(-10000,10000,size=(5000,4))
        out,_=render(x,0,[dict(ready=2000,angle=0,fresh=True,valid_through=4000)],config())
        np.testing.assert_array_equal(out['automatic'][:1992],out['single'][:1992])

class NumericTests(unittest.TestCase):
    def test_integer_dc_zero_and_width(self):
        from integer_gate import stage
        for v in [0,2**23-1,-2**23]:
            a,d=stage(np.full((1024,4),v,dtype=np.int64))
            self.assertFalse(d['overflow'])
            np.testing.assert_array_equal(a['band_power'],[0]*4)

    def test_integer_gate_boundary_and_invalid(self):
        from integer_gate import IntegerActivity
        g=IntegerActivity([2**30]*4,config())
        self.assertFalse(g.update([4*2**30-1]*4))
        self.assertEqual([g.update([4*2**30]*4) for _ in range(3)],[False,False,True])
        self.assertTrue(g.update([2*2**30]*4))
        self.assertFalse(g.update([2*2**30]*4,invalid=True))
        with self.assertRaises(ValueError):IntegerActivity([-1]*4,config())
        with self.assertRaises(ValueError):IntegerActivity([1]*4,config()|{'attack_frames':1})

    def test_direction_synthetic_sign_at_three_angles(self):
        from run import diag,BOUNDS
        frequencies=np.arange(500,3500,75)
        phases=np.random.default_rng(19).uniform(0,2*np.pi,len(frequencies))
        for angle in [-45,0,45]:
            u=np.array([np.cos(np.deg2rad(angle)),np.sin(np.deg2rad(angle)),0])
            t=np.arange(1024)[:,None]/48000+(POSITIONS@u)[None,:]/343
            x=np.rint(sum(500*np.sin(2*np.pi*f*t+p) for f,p in zip(frequencies,phases))).astype(np.int64)
            pairs,_=diag.floating(x,BOUNDS)
            proj=diag.projection(pairs,POSITIONS,48000,343)
            self.assertTrue(proj.get('advisory_consistent'),proj)
            self.assertLess(wrapped_error(proj['advisory_azimuth_deg'],angle),3)

if __name__=='__main__':unittest.main()
