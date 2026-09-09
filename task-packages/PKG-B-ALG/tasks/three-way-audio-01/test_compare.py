import unittest
import numpy as np
import compare_audio as c
from audio_frames import adapt_six_mic_baseline
from fixed_das import POSITIONS

class Tests(unittest.TestCase):
    def segment(self):
        b=c.previous.localize.baseline;rng=np.random.default_rng(741);n=8192
        f=np.fft.rfftfreq(n,1/48000);s=np.fft.irfft(np.fft.rfft(rng.normal(size=n))*((f>300)&(f<4000)),n=n)
        x=b.render(s,np.array([1.,0,0]))[:,1024:-1024]
        return adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=POSITIONS,source_id='test',source_sha256='0'*64,first_sample_id=1024)

    def test_truth_change_cannot_change_automatic(self):
        seg=self.segment();a,_,rows,_,_=c.compare(seg,[1.,0,0]);b,_,other,_,_=c.compare(seg,[0.,1,0])
        np.testing.assert_array_equal(a['auto'],b['auto']);self.assertEqual(rows,other)
        self.assertGreater(np.max(np.abs(a['manual']-b['manual'])),.01)

    def test_manual_block_partition(self):
        seg=self.segment();a,v=c.fixed(seg.samples,[1,0,0],1024,512);b,w=c.fixed(seg.samples,[1,0,0],1024,137)
        np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(v,w)

    def test_replay_equal_and_components_linear(self):
        seg=self.segment();signals,_,rows,_,_=c.compare(seg,[1,0,0])
        np.testing.assert_array_equal(c.replay(seg.samples,1024,rows),signals['auto'])
        rng=np.random.default_rng(15);a=rng.normal(size=seg.samples.shape)*.1;b=seg.samples-a
        np.testing.assert_allclose(c.replay(a,1024,rows)+c.replay(b,1024,rows),signals['auto'],rtol=0,atol=2e-15)

    def test_reference_delay_and_length(self):
        x=np.zeros((20,6));x[3,0]=1;y=c.single(x)
        self.assertEqual(len(y),20);self.assertEqual(np.argmax(y),7)

    def test_metrics_use_common_mask(self):
        z=np.array([100.,1.,2.]);signals={k:z.copy() for k in ['single','manual','auto']};signals['auto'][0]=-100
        result=c.metrics(signals,np.array([False,True,True]))
        self.assertEqual(result['auto']['normalized_error_to_manual'],0)
        with self.assertRaises(ValueError):c.metrics(signals,np.array([False]*3))

if __name__=='__main__':unittest.main(verbosity=2)
