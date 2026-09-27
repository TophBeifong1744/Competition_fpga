import unittest
import numpy as np
from fixed_das import FixedDAS,FS,C,POSITIONS

def unit(az,el=0):
    a,e=np.deg2rad([az,el]);return np.array([np.cos(e)*np.cos(a),np.cos(e)*np.sin(a),np.sin(e)])

class Tests(unittest.TestCase):
    def test_arbitrary_blocks_identical_to_one_block(self):
        x=np.random.default_rng(81).normal(size=(4097,6));u=unit(28,17)
        expected,mask=FixedDAS(u).process(x,first_sample_id=900)
        b=FixedDAS(u);ys=[];vs=[];start=0
        for size in [1,2,511,1024,3,512,2044]:
            y,v=b.process(x[start:start+size],first_sample_id=900+start);ys.append(y);vs.append(v);start+=size
        self.assertEqual(start,len(x));np.testing.assert_array_equal(np.concatenate(ys),expected);np.testing.assert_array_equal(np.concatenate(vs),mask)

    def test_impulse_matches_independent_convolution(self):
        x=np.zeros((80,6));x[20]=[1,2,3,4,5,6];b=FixedDAS(unit(-41,23))
        y,_=b.process(x,first_sample_id=0);ref=np.zeros(len(x))
        for m,d in enumerate(b.describe()['channel_delay_samples']):
            k=int(np.floor(d));a=d-k;h=np.zeros(k+2);h[k]=1-a;h[k+1]=a
            ref+=np.convolve(x[:,m],h)[:len(x)]/6
        np.testing.assert_allclose(y,ref,rtol=0,atol=1e-15)
        self.assertTrue(np.all(y[:20]==0));self.assertAlmostEqual(y.sum(),3.5)

    def test_plane_wave_sign_and_delay_six_axes(self):
        n=np.arange(6000);w=2*np.pi*1000/FS
        for u in [unit(0),unit(90),unit(180),unit(-90),unit(0,90),unit(0,-90)]:
            q=POSITIONS@u*FS/C;x=np.sin(w*(n[:,None]+q))
            b=FixedDAS(u);y,valid=b.process(x,first_sample_id=0)
            expected=np.sin(w*(n-b.common_delay_samples))
            self.assertLess(np.sqrt(np.mean((y[valid]-expected[valid])**2)),.003)
            wrong,_=FixedDAS(-u).process(x,first_sample_id=0)
            self.assertGreater(np.sqrt(np.mean((wrong[valid]-expected[valid])**2)),.03)

    def test_constant_unity_gain(self):
        y,v=FixedDAS(unit(28,10)).process(np.ones((100,6))*.25,first_sample_id=0)
        np.testing.assert_allclose(y[v],.25,rtol=0,atol=1e-15)

    def test_gap_overlap_rejected_without_changing_state(self):
        x=np.random.default_rng(2).normal(size=(32,6));b=FixedDAS(unit(0));b.process(x,first_sample_id=100)
        for bad in [100,131,133]:
            with self.assertRaises(ValueError):b.process(x,first_sample_id=bad)
        y,v=b.process(x,first_sample_id=132)
        ref=FixedDAS(unit(0));a,mask=ref.process(np.concatenate([x,x]),first_sample_id=100)
        np.testing.assert_array_equal(y,a[32:]);np.testing.assert_array_equal(v,mask[32:])

    def test_reset_clears_previous_segment(self):
        b=FixedDAS(unit(0));b.process(np.ones((20,6)),first_sample_id=1);b.reset()
        y,v=b.process(np.zeros((20,6)),first_sample_id=900)
        self.assertFalse(np.any(y));self.assertEqual(np.count_nonzero(~v),b.history_samples)

    def test_invalid_inputs(self):
        for u in [[0,0,0],[2,0,0],[np.nan,0,0],[1,0]]:
            with self.assertRaises(ValueError):FixedDAS(u)
        b=FixedDAS(unit(0))
        for x in [np.zeros((6,20)),np.zeros((0,6)),np.ones((2,6),dtype=int),np.full((2,6),np.inf)]:
            with self.assertRaises(ValueError):b.process(x,first_sample_id=0)
        for i in [True,-1,2**64]:
            with self.assertRaises(ValueError):b.process(np.zeros((2,6)),first_sample_id=i)

    def test_causal_prefix(self):
        x=np.random.default_rng(1).normal(size=(512,6));changed=x.copy();changed[200:]*=100
        a,_=FixedDAS(unit(0,28)).process(x,first_sample_id=0);b,_=FixedDAS(unit(0,28)).process(changed,first_sample_id=0)
        np.testing.assert_array_equal(a[:200],b[:200])

if __name__=='__main__':unittest.main(verbosity=2)
