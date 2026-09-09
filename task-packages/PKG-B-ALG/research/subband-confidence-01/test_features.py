import unittest
import numpy as np
import features as f
from audio_frames import adapt_six_mic_baseline,iter_frames

def frame(x):
    return next(iter_frames(adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=f.b.POS,source_id='test',source_sha256='0'*64)))

def candidate(deg,valid=True,offset=0):
    return dict(valid=valid,unit_vector=f.b.unit(deg,0).tolist() if valid else None,pair_delays_samples=[offset]*15)

class FeatureTests(unittest.TestCase):
    def setUp(self):self.c=dict(minimum_valid_subbands=2,minimum_joint_finite_pairs=5,maximum_direction_spread_deg=5.,maximum_median_delay_span_samples=.5)

    def test_full_band_reproduces_phat_delays(self):
        x=f.b.render(f.b.source(np.random.default_rng(171)),f.b.unit(28,0))[:,1536:2560]
        r=f.subband_candidates(frame(x),[[300,4000]])[0]
        expected=f.solve_delays(f.b.gcc(x))
        for key in ['valid','unit_vector','pair_delays_samples']:self.assertEqual(r[key],expected[key])

    def test_disjoint_bins_and_nonmutation(self):
        x=np.random.default_rng(121).normal(size=(6,1024));old=x.copy();fr=frame(x)
        parts=f.subband_candidates(fr,[[300,1500],[1500,2700],[2700,4000]])
        whole=f.subband_candidates(fr,[[300,4000]])[0]
        np.testing.assert_array_equal(np.sum([p['retained_bins'] for p in parts],axis=0),whole['retained_bins'])
        np.testing.assert_array_equal(x,old)

    def test_supported_boundary_and_unsupported_are_distinct(self):
        self.assertEqual(f.assess(candidate(28),[candidate(28),candidate(29),candidate(0,False)],self.c)['category'],'inside_supported')
        self.assertEqual(f.assess(candidate(28),[candidate(29),candidate(31)],self.c)['category'],'boundary_uncertain')
        self.assertEqual(f.assess(candidate(28),[candidate(29),candidate(0,False)],self.c)['category'],'unsupported')
        self.assertEqual(f.assess(candidate(30),[candidate(30),candidate(30)],self.c)['category'],'inside_supported')

    def test_inconsistent_and_sparse_pairs(self):
        self.assertEqual(f.assess(candidate(28),[candidate(10),candidate(29)],self.c)['category'],'inconsistent')
        self.assertEqual(f.assess(candidate(28),[candidate(28),candidate(28,offset=1)],self.c)['category'],'inconsistent')
        sparse=candidate(28);sparse['pair_delays_samples']=[0]*4+[None]*11
        self.assertEqual(f.assess(candidate(28),[candidate(28),sparse],self.c)['category'],'unsupported')

    def test_screens_only_veto_and_do_not_mutate(self):
        full=candidate(28);d=f.assess(full,[candidate(29),candidate(31)],self.c)
        self.assertEqual(f.screened(full,d),full)
        self.assertFalse(f.screened(full,d,True)['valid']);self.assertTrue(full['valid'])
        invalid=candidate(0,False);d=f.assess(invalid,[candidate(28),candidate(28)],self.c)
        self.assertEqual(d['category'],'full_rejected');self.assertFalse(f.screened(invalid,d)['valid'])

    def test_silence_has_no_usable_subband(self):
        subs=f.subband_candidates(frame(np.zeros((6,1024))),[[300,1500],[1500,2700],[2700,4000]])
        self.assertTrue(all(not s['valid'] for s in subs))

if __name__=='__main__':unittest.main(verbosity=2)
