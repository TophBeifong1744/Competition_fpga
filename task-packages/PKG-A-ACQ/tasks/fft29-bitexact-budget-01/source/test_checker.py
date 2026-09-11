import unittest
import numpy as np
from prepare import rne
from check import compare


class CheckerTests(unittest.TestCase):
    def fixture(self):
        expected = np.arange(2048,dtype=np.int64).reshape(1,1024,2)-1024
        rows = np.column_stack([np.zeros(1024,dtype=np.int64),np.arange(1024),expected[0]])
        status = np.array([[0,7500,0]],dtype=np.int64)
        return rows, expected, status, [{'expected_overflow':False}]

    def test_exact(self):
        self.assertTrue(compare(*self.fixture())['pass'])

    def test_one_code(self):
        r,e,s,j = self.fixture(); r[70,3] += 1
        out = compare(r,e,s,j)
        self.assertFalse(out['pass']); self.assertEqual(out['mismatched_components'],1)

    def test_swapped_bins(self):
        r,e,s,j = self.fixture(); r[[0,1]] = r[[1,0]]
        self.assertIn('bin_order',compare(r,e,s,j)['issues'])

    def test_wrong_job(self):
        r,e,s,j = self.fixture(); r[:,0]=1
        self.assertIn('job_order',compare(r,e,s,j)['issues'])

    def test_truncation(self):
        r,e,s,j = self.fixture()
        self.assertIn('output_shape',compare(r[:-1],e,s,j)['issues'])

    def test_overflow(self):
        r,e,s,j = self.fixture(); s[0,2]=1
        self.assertIn('overflow',compare(r,e,s,j)['issues'])

    def test_missing_status(self):
        r,e,s,j = self.fixture()
        self.assertIn('status_shape',compare(r,e,s[:0],j)['issues'])

    def test_rne_signed_ties(self):
        x = np.arange(-16,17,dtype=np.int64)
        for shift in range(5):
            # Small exactly representable rationals; Python round is nearest-even.
            np.testing.assert_array_equal(rne(x,shift),[round(int(v)/(1<<shift)) for v in x])

    def test_rne_s25_boundary(self):
        x = np.array([-(1<<25),(1<<25)-1,(1<<25)-2],dtype=np.int64)
        np.testing.assert_array_equal(rne(x,1),[-(1<<24),1<<24,(1<<24)-1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
