import unittest
import numpy as np
import features as f
from audio_frames import adapt_six_mic_baseline,iter_frames
BANDS=[[300,1500],[1500,2700],[2700,4000]]
def frame(x):return next(iter_frames(adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=f.b.POS,source_id='test',source_sha256='0'*64)))
def candidate(deg=28,valid=True):return dict(valid=valid,unit_vector=f.b.unit(deg,0).tolist() if valid else None,pair_delays_samples=[0.]*15)
def measure(n,mass):return dict(removed_bins=[n]*15,removed_mass_fraction=[mass]*15,removed_f2_fraction=[mass]*15)

class EffectiveTests(unittest.TestCase):
    def setUp(self):
        self.impact=dict(minimum_removed_bins=3,minimum_removed_mass=.1,maximum_removed_mass=.8,minimum_qualified_pairs=5)
        self.loo=dict(minimum_comparable_deletions=2,minimum_joint_pairs_per_deletion=5,max_angle_change_deg=5.,max_median_pair_delay_change_samples=.5)

    def test_mass_partition_gain_and_nonmutation(self):
        x=np.random.default_rng(612).normal(size=(6,1024));old=x.copy();m=f.impacts(frame(x),BANDS);n=f.impacts(frame(x*2),BANDS)
        for key in ['removed_mass_fraction','removed_f2_fraction']:
            np.testing.assert_allclose(np.sum([v[key] for v in m],axis=0),1,atol=1e-14)
            np.testing.assert_allclose([v[key] for v in m],[v[key] for v in n],atol=1e-14)
        np.testing.assert_array_equal(x,old)

    def test_no_change_cannot_be_stability_support(self):
        full=candidate();deleted=[candidate(valid=False),candidate(),candidate()]
        before=f.old.assess(full,deleted,self.loo);after=f.assess(full,deleted,[measure(15,1),measure(0,0),measure(0,0)],self.impact,self.loo)
        self.assertEqual(before['category'],'stable');self.assertEqual(after['category'],'unknown')
        self.assertEqual(after['impact_statuses'],['uncomparable','no_change','no_change'])
        self.assertTrue(f.screen(full,after,True)['valid'])

    def test_weak_and_excessive_not_effective(self):
        d=f.assess(candidate(),[candidate()]*3,[measure(4,.09),measure(4,.81),measure(2,.3)],self.impact,self.loo)
        self.assertEqual(d['category'],'unknown');self.assertEqual(d['impact_statuses'],['weak_or_excessive']*3)

    def test_effective_boundaries_and_sensitive(self):
        d=f.assess(candidate(),[candidate(),candidate(36),candidate()],[measure(3,.1),measure(3,.8),measure(0,0)],self.impact,self.loo)
        self.assertEqual(d['category'],'sensitive');self.assertEqual(d['comparable_count'],2)

    def test_full_invalid_and_silence(self):
        d=f.assess(candidate(valid=False),[candidate()]*3,[measure(4,.4)]*3,self.impact,self.loo)
        self.assertEqual(d['category'],'full_rejected');self.assertFalse(f.screen(candidate(valid=False),d,True)['valid'])
        m=f.impacts(frame(np.zeros((6,1024))),BANDS)
        self.assertTrue(all(sum(r['removed_bins'])==0 and sum(r['removed_mass_fraction'])==0 for r in m))

    def test_shared_finite_pair_requirement(self):
        sparse=candidate();sparse['pair_delays_samples']=[0.]*4+[None]*11
        d=f.assess(candidate(),[candidate(),sparse,candidate(valid=False)],[measure(5,.3)]*3,self.impact,self.loo)
        self.assertEqual(d['category'],'unknown');self.assertEqual(d['impact_statuses'][1],'uncomparable')

if __name__=='__main__':unittest.main(verbosity=2)
