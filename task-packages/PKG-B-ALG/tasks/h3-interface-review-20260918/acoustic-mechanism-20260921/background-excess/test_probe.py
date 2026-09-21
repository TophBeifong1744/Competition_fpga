import unittest
import numpy as np
from probe import excess,gate_weight
class ExcessTests(unittest.TestCase):
    def test_background_or_less_has_zero_weight(self):
        np.testing.assert_array_equal(excess(np.array([0.,1.,2.]),np.array([1.,1.,3.])),[0,0,0])
    def test_pair_needs_both_channels(self):
        self.assertEqual(gate_weight(np.array([[4.],[.5]]),np.ones((2,1)),0,1)[0],0)
    def test_known_excess_and_power_scale(self):
        p=np.array([[4.,2.],[4.,2.]]);n=np.ones((2,2));np.testing.assert_allclose(gate_weight(p,n,0,1),[.75,.5]);np.testing.assert_array_equal(gate_weight(p,n,0,1),gate_weight(p*16,n*16,0,1))
    def test_reference_not_updated_by_target(self):
        n=np.ones((2,3));saved=n.copy();gate_weight(np.full((2,3),100.),n,0,1);np.testing.assert_array_equal(n,saved)
if __name__=='__main__':unittest.main()
