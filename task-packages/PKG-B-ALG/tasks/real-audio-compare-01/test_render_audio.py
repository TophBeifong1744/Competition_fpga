"""Delay identities and numerical/output guards, not acoustic scene simulation."""
import unittest
import numpy as np
from render_audio import delays_for,render_interval,encode_pcm24

class RenderTests(unittest.TestCase):
    def test_zero_delay_identity(self):
        x=np.arange(40,dtype=float).reshape(10,4)/100
        a,b,start,stop=render_interval(x,[0]*4)
        np.testing.assert_array_equal(a,x[:,0])
        np.testing.assert_array_equal(b,x.mean(axis=1))
        self.assertEqual((start,stop),(0,10))

    def test_compensation_sign_integer_impulses(self):
        x=np.zeros((30,4)); d=np.array([0,2,-3,1])
        for ch in range(4): x[15-d[ch],ch]=1
        a,b,start,stop=render_interval(x,d)
        np.testing.assert_array_equal(a,b)
        self.assertEqual(int(np.argmax(b))+start,15)

    def test_fractional_ramp_and_crop(self):
        d=np.array([0,1.25,-2.75,.5]); n=np.arange(20)
        x=n[:,None]+d[None,:]
        a,b,start,stop=render_interval(x,d)
        np.testing.assert_allclose(a,b,rtol=0,atol=1e-14)
        self.assertEqual((start,stop),(2,17))

    def test_geometry_sign_and_translation(self):
        pos=np.array([[0,0,0],[.04,0,0],[.04,.04,0],[0,.04,0]])
        d=delays_for(pos,0,-45,0,48000,343)
        self.assertGreater(d[1],0); self.assertLess(d[3],0)
        np.testing.assert_allclose(d,delays_for(pos+2,0,-45,0,48000,343),atol=1e-12)

    def test_constant_and_no_wrap(self):
        x=np.ones((30,4))*.25
        a,b,_,_=render_interval(x,[0,3.9,0,-3.9])
        np.testing.assert_array_equal(a,b)
        x[:]=0; x[0]=1
        _,b,_,_=render_interval(x,[0,3.9,0,-3.9])
        self.assertTrue(np.all(b[-5:]==0))

    def test_invalid_input(self):
        for x,d in [(np.ones((2,4)),[0,5,0,-5]),(np.full((10,4),np.nan),[0]*4),(np.ones((10,3)),[0]*4)]:
            with self.assertRaises(ValueError): render_interval(x,d)

    def test_pcm24_endpoints_saturation(self):
        signal=np.array([-2,-1,0,(2**23-1)/2**23,2])
        raw,count=encode_pcm24(signal)
        self.assertEqual(count,2)
        decoded=[int.from_bytes(raw[i:i+3],'little',signed=True) for i in range(0,len(raw),3)]
        self.assertEqual(decoded,[-2**23,-2**23,0,2**23-1,2**23-1])

    def test_rne_ties(self):
        raw,count=encode_pcm24(np.array([.5,1.5,-.5,-1.5])/2**23)
        self.assertEqual(count,0)
        self.assertEqual([int.from_bytes(raw[i:i+3],'little',signed=True) for i in range(0,len(raw),3)],[0,2,0,-2])

if __name__=='__main__': unittest.main(verbosity=2)
