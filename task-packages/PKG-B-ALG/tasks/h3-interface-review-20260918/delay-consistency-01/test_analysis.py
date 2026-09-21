import unittest
import numpy as np
from analyze import expected
class Convention(unittest.TestCase):
 def test_axis_sign(self):
  x=expected(0);self.assertAlmostEqual(x[0],.04*48000/343);self.assertAlmostEqual(x[2],0);self.assertAlmostEqual(x[5],-.04*48000/343)
 def test_reversal(self):self.assertTrue(np.allclose(expected(180),-expected(0)))
 def test_graph_identity(self):
  for a in (-45,0,45):
   x=expected(a);self.assertAlmostEqual(x[0]+x[3],x[1]);self.assertAlmostEqual(x[1]+x[5],x[2])
if __name__=='__main__':unittest.main()
