from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'payload/model/python'))
import six_mic_baseline_core as b
import weighted_gcc as candidate
import candidate_quality_research as study
import batch_presence as batch
from audio_frames import adapt_six_mic_baseline,iter_frames
from sector_tracker import Config


def segment(x):
    return adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=b.POS,source_id='weighted-gcc-test',source_sha256='0'*64)


class WeightedGccTests(unittest.TestCase):
    def test_beta_one_matches_original_across_nine_scenarios(self):
        for scene in b.SCENARIOS:
            for az,el in [(0,0),(35,25),(180,-35)]:
                _,target,noise=b.make_trial(az,el,0,scene);x=(target+noise)[:,1536:2560]
                with self.subTest(scene=scene,az=az):
                    np.testing.assert_array_equal(candidate.gcc(x,1),b.gcc(x))

    def test_axis_signs_and_oblique_both_exponents(self):
        for az,el in [(0,0),(90,0),(180,0),(270,0),(0,90),(0,-90),(35,25)]:
            u=b.unit(az,el);x=b.render(b.source(np.random.default_rng(8)),u)[:,1536:2560]
            for beta in [.5,.75]:
                r=candidate.localize(next(iter_frames(segment(x))),beta)
                self.assertTrue(r['valid']);self.assertLess(b.angle(np.array(r['unit_vector']),u),3)

    def test_silence_stays_invalid(self):
        for beta in [.5,.75,1]:
            r=candidate.localize(next(iter_frames(segment(np.zeros((6,1024))))),beta)
            self.assertFalse(r['valid']);self.assertIsNone(r['unit_vector'])
            self.assertEqual(r['pair_delays_samples'],[None]*15)

    def test_common_positive_gain_does_not_change_delays(self):
        _,target,noise=b.make_trial(35,25,0,'band_noise0');x=(target+noise)[:,1536:2560]
        for beta in [.5,.75]:
            np.testing.assert_allclose(candidate.gcc(x,beta),candidate.gcc(x*10,beta),atol=1e-12,rtol=0,equal_nan=True)

    def test_channel_swap_is_not_silently_corrected(self):
        x=b.render(b.source(np.random.default_rng(8)),b.unit(35,25))[:,1536:2560]
        a=candidate.gcc(x,.75);swapped=x.copy();swapped[[0,1]]=swapped[[1,0]]
        c=candidate.gcc(swapped,.75)
        self.assertFalse(np.allclose(a,c,equal_nan=True))

    def test_input_not_modified(self):
        x=np.random.default_rng(9).normal(size=(6,1024));before=x.copy()
        candidate.gcc(x,.75);np.testing.assert_array_equal(x,before)

    def test_invalid_inputs(self):
        for beta in [True,0,-1,2,float('nan'),'0.75']:
            with self.assertRaises(ValueError):candidate.gcc(np.zeros((6,1024)),beta)
        for x in [np.zeros((4,1024)),np.zeros((1024,6)),np.full((6,1024),np.inf),np.zeros((6,1024),dtype=int)]:
            with self.assertRaises(ValueError):candidate.gcc(x,.75)

    def test_overflow_reports_error(self):
        frame=next(iter_frames(segment(np.full((6,1024),1e308))))
        with self.assertRaises(ValueError):candidate.localize(frame,.75)

    def test_truth_does_not_enter_candidate_or_capture(self):
        x=b.render(b.source(np.random.default_rng(8)),b.unit(0,10))[:,1024:3072]
        s=segment(x);env=np.ones((1,x.shape[1]));directions=[b.unit(0,10)]
        a,_=study.evaluate(s,env,directions,Config(),[dict(name='gcc_beta075',beta=.75)])
        c,_=study.evaluate(s,np.zeros_like(env),[b.unit(90,0)],Config(),[dict(name='gcc_beta075',beta=.75)])
        for r,t in zip(a,c):
            for key in ['fresh_valid','state','reason','estimate_x','estimate_y','estimate_z','candidate_valid']:self.assertEqual(r[key],t[key])

    def test_new_seeds_disjoint_from_prior_research(self):
        plan=study.read(study.PROTOCOL);prior=study.read(ROOT/'payload/config/capture-research-protocol.json')
        old=set(prior['development_seeds']+prior['validation_seeds'])
        self.assertFalse(old&set(plan['development_seeds']+plan['validation_seeds']))
        self.assertFalse(set(plan['development_seeds'])&set(plan['validation_seeds']))


if __name__=='__main__':unittest.main()
