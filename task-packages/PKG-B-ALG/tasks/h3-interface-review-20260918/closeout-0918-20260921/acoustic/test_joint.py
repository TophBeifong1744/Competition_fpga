import unittest
import numpy as np
from joint_candidate import JointCandidate

class Tests(unittest.TestCase):
    def setUp(self):
        self.pos=np.array([[0,0],[.04,0],[.04,.04],[0,.04]])
        self.pairs=[(i,j) for i in range(4) for j in range(i+1,4)]
        self.model=JointCandidate(self.pos,self.pairs)

    def fixture(self,angle):
        u=np.array([np.cos(np.deg2rad(angle)),np.sin(np.deg2rad(angle))])
        tau=self.model.matrix@u;lags=np.arange(-512,512)
        # Mathematical score fixture only, not simulated microphone audio.
        corr=np.zeros((6,1024))
        for k,t in enumerate(tau):corr[k,lags%1024]=-(lags-t)**2
        return [dict(bins=79,valid=True,tau_samples=float(t)) for t in tau],corr

    def test_full_direction_search(self):
        rows,corr=self.fixture(120);r=self.model.estimate(rows,corr)
        self.assertTrue(r['valid']);self.assertGreater(r['angle'],100)

    def test_measured_residual_not_self_fitted(self):
        rows,corr=self.fixture(0)
        for row in rows:row['tau_samples']=-row['tau_samples']
        self.assertFalse(self.model.estimate(rows,corr)['valid'])

    def test_flat_ties_reject(self):
        rows,corr=self.fixture(0);corr[:]=0
        self.assertEqual(self.model.estimate(rows,corr)['reason'],'TIED_SCORE')

    def test_insufficient_pairs(self):
        rows,corr=self.fixture(0)
        for row in rows[2:]:row['valid']=False
        self.assertFalse(self.model.estimate(rows,corr)['valid'])

if __name__=='__main__':unittest.main()
