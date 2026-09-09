import unittest
import numpy as np
import features as f
from audio_frames import adapt_six_mic_baseline,iter_frames
import sys
sys.path.insert(0,str(f.ROOT/'research/narrowband-guard-01'))
import guard
BANDS=[[300,1500],[1500,2700],[2700,4000]]

def frame(x):return next(iter_frames(adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=f.b.POS,source_id='test',source_sha256='0'*64)))
def c(deg=28,valid=True,offset=0):return dict(valid=valid,unit_vector=f.b.unit(deg,0).tolist() if valid else None,pair_delays_samples=[offset]*15)

class LooTests(unittest.TestCase):
    def setUp(self):self.cfg=dict(minimum_comparable_deletions=2,minimum_joint_pairs_per_deletion=5,max_angle_change_deg=5.,max_median_pair_delay_change_samples=.5)

    def test_full_candidate_exactly_matches_frozen_cap(self):
        rng=np.random.default_rng(499)
        cases=[rng.normal(size=(6,1024)),np.zeros((6,1024))]
        for az in [0,28,30,32]:cases.append(f.b.render(f.b.source(rng),f.b.unit(az,0))[:,1536:2560])
        for x in cases:
            fr=frame(x);a=f.estimates(fr,BANDS)[0];b=guard.localize(fr,'cap150')
            for k in ['valid','unit_vector','pair_delays_samples','rejection_reasons']:self.assertEqual(a[k],b[k])

    def test_delete_counts_preserve_complement_and_input(self):
        x=np.random.default_rng(61).normal(size=(6,1024));before=x.copy();e=f.estimates(frame(x),BANDS)
        np.testing.assert_array_equal(np.sum([r['retained_bins'] for r in e[1:]],axis=0),2*np.array(e[0]['retained_bins']))
        np.testing.assert_array_equal(x,before)

    def test_common_gain_invariance(self):
        x=np.random.default_rng(57).normal(size=(6,1024));a=f.estimates(frame(x),BANDS);b=f.estimates(frame(2*x),BANDS)
        for r,t in zip(a,b):
            u=[np.nan if v is None else v for v in r['pair_delays_samples']];v=[np.nan if z is None else z for z in t['pair_delays_samples']]
            np.testing.assert_allclose(u,v,atol=1e-10,equal_nan=True)

    def test_unknown_is_not_confidence_and_full_invalid_stays_invalid(self):
        full=c();d=f.assess(full,[c(),c(valid=False),c(valid=False)],self.cfg)
        self.assertEqual(d['category'],'unknown');self.assertFalse(f.screen(full,d)['valid']);self.assertTrue(f.screen(full,d,True)['valid'])
        bad=c(valid=False);d=f.assess(bad,[c(),c(),c()],self.cfg)
        self.assertFalse(f.screen(bad,d,True)['valid']);self.assertTrue(full['valid'])

    def test_angle_delay_and_crossing_are_separate(self):
        d=f.assess(c(),[c(29),c(31)],self.cfg)
        self.assertEqual(d['category'],'stable');self.assertEqual(d['cone_crossings'],1)
        self.assertEqual(f.assess(c(),[c(29),c(36)],self.cfg)['category'],'sensitive')
        self.assertEqual(f.assess(c(),[c(offset=.7),c()],self.cfg)['category'],'sensitive')

    def test_insufficient_shared_pairs_means_unknown(self):
        sparse=c();sparse['pair_delays_samples']=[0]*4+[None]*11
        self.assertEqual(f.assess(c(),[sparse,c(),c(valid=False)],self.cfg)['category'],'unknown')

if __name__=='__main__':unittest.main(verbosity=2)
