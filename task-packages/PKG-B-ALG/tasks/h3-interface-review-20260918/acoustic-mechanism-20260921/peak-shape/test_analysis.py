import unittest
from analyze import shape
class ShapeTests(unittest.TestCase):
    def test_sharp_and_flat(self):
        a=shape([-1,0,1],[0,1,0],0);b=shape([-1,0,1],[1,1,1],0)
        self.assertEqual(a,dict(curvature=2.,width=1,censored=False));self.assertEqual(b,dict(curvature=0.,width=3,censored=True))
    def test_edge_has_unknown_curvature(self):
        a=shape([0,1,2],[1,.6,0],0);self.assertIsNone(a['curvature']);self.assertTrue(a['censored'])
    def test_nonpositive_and_nonfinite(self):
        self.assertIsNone(shape([-1,0,1],[-1,0,-1],0)['width'])
        with self.assertRaises(ValueError):shape([-1,0,1],[0,float('nan'),0],0)
    def test_scale_invariance(self):
        self.assertEqual(shape([-1,0,1],[.2,1,.3],0),shape([-1,0,1],[2,10,3],0))
if __name__=='__main__':unittest.main()
