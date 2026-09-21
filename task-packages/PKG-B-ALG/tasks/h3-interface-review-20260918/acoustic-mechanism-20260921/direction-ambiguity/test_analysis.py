import unittest
import numpy as np
from analyze import separation,competitor
class Controls(unittest.TestCase):
    def test_wrap(self):self.assertEqual(separation(179,-179),2)
    def test_exact_boundary_and_invalid(self):
        self.assertEqual(competitor(np.array([1,.99,.98,1.]),np.array([0,14.9,15,90]),np.array([True,True,True,False]),0),2)
    def test_absent(self):self.assertIsNone(competitor(np.array([1,.9]),np.array([0,10]),np.array([True,True]),0))
    def test_flat_ambiguity(self):
        scores=np.ones(3);j=competitor(scores,np.array([0,20,-20]),np.ones(3,dtype=bool),0);self.assertEqual(j,1);self.assertEqual(scores[0]-scores[j],0)
if __name__=='__main__':unittest.main()
