import unittest
from unittest.mock import patch
import numpy as np
import probe

class TestGraphSelection(unittest.TestCase):
    def fixture(self, corrupt=False, zero=False):
        xy=np.array([[0,0],[1,0],[1,1],[0,1]])*1920/343
        direction=np.zeros(2) if zero else np.array([.5,.5])
        rows=[]
        for k,(i,j) in enumerate(((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))):
            good=float((xy[j]-xy[i])@direction)
            bad=good+2 if corrupt and k==0 else good
            opts=[dict(lag=0,tau=bad,score=1.,original=True)]
            if corrupt and k==0:opts.append(dict(lag=1,tau=good,score=.9,original=False))
            rows.append(dict(valid=True,pair=[i,j],tau_samples=bad,options=opts))
        return dict(pairs=rows)

    def test_existing_consistent_preserved(self):
        with patch.object(probe,'options',lambda p:p['options']):r=probe.probe(self.fixture())
        self.assertTrue(r['valid']);self.assertFalse(r['changed'])

    def test_inconsistent_main_can_use_weaker_peak(self):
        with patch.object(probe,'options',lambda p:p['options']):r=probe.probe(self.fixture(corrupt=True))
        self.assertTrue(r['valid']);self.assertTrue(r['changed']);self.assertGreater(r['original_cycle_rms'],.5)

    def test_closed_but_zero_norm_still_rejected(self):
        with patch.object(probe,'options',lambda p:p['options']):r=probe.probe(self.fixture(zero=True))
        self.assertFalse(r['valid']);self.assertEqual(r['status'],'PLANE_REJECT')

    def test_unresolved_cycle_rejected(self):
        f=self.fixture(corrupt=True);f['pairs'][0]['options']=f['pairs'][0]['options'][:1]
        with patch.object(probe,'options',lambda p:p['options']):r=probe.probe(f)
        self.assertFalse(r['valid']);self.assertEqual(r['status'],'NO_GRAPH_CONSISTENT_COMBINATION')

    def test_secondary_peak_generation(self):
        p=dict(valid=True,peak=0,tau_samples=0.,peak_height=2.,legal_search_lags=list(range(-3,4)),correlation=[0,1,0,2,0,1,0],bound_samples=2.5)
        r=probe.options(p);self.assertEqual([x['lag'] for x in r],[0,-2,2]);self.assertEqual(r[0]['tau'],0)

if __name__=='__main__':unittest.main()
