import unittest
import numpy as np
from analyze import grid,choose,BOUNDS,G
class Controls(unittest.TestCase):
    def test_grid_legal_and_closed(self):
        t=grid();self.assertTrue(np.all(np.abs(t)<=BOUNDS+1e-12));self.assertTrue(np.allclose(t[:,0]+t[:,3],t[:,1]));self.assertTrue(np.allclose(t[:,1]+t[:,5],t[:,2]))
    def test_unique_consistent_peak(self):
        t=grid();goal=G@np.array([0,1,2,0]);ps=[]
        for k in range(6):
            l=np.arange(-int(np.ceil(BOUNDS[k])),int(np.ceil(BOUNDS[k]))+1);y=1-.01*(l-goal[k])**2
            ps.append(dict(correlation=y.tolist(),peak_height=1.,legal_search_lags=l.tolist()))
        picked,score,_=choose(ps,t);self.assertTrue(np.array_equal(picked,goal));self.assertAlmostEqual(score,1.)
    def test_flat_has_no_direction_evidence(self):
        t=grid();ps=[dict(correlation=[1.,1.],peak_height=1.,legal_search_lags=[-10,10]) for _ in range(6)]
        picked,score,_=choose(ps,t);self.assertTrue(np.array_equal(picked,t[0]));self.assertAlmostEqual(score,1.)
    def test_nonpositive_rejected(self):
        with self.assertRaises(ValueError):choose([dict(correlation=[0,0],peak_height=0,legal_search_lags=[-10,10])]*6,grid())
if __name__=='__main__':unittest.main()
