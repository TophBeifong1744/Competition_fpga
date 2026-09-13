"""Numerical identities and failure guards, not four-mic acoustic simulation."""
import unittest
import numpy as np
import run as model

class DiagnosticTests(unittest.TestCase):
    def test_cross_sign_and_swap(self):
        # Direct sample-delay identity: first sequence arrives three samples later.
        x = np.zeros(1024); y = x.copy(); x[203] = 1; y[200] = 1
        a, b = np.fft.rfft(x), np.fft.rfft(y)
        corr = np.fft.irfft(a*b.conj(), n=1024)
        self.assertEqual(model.quality(corr, 5.6, False)['peak'], 3)
        self.assertEqual(model.quality(np.fft.irfft(b*a.conj(), n=1024), 5.6, False)['peak'], -3)

    def test_physical_edge_reject(self):
        corr = np.zeros(1024); corr[6] = 1
        p = model.quality(corr, 5.597667638, False)
        self.assertTrue(p['edge_peak']); self.assertFalse(p['valid'])

    def test_integer_subsample(self):
        corr = np.zeros(1024, dtype=np.int64); corr[2:5] = [4,10,8]
        p = model.quality(corr, 5.6, True)
        self.assertEqual(p['tau_q12'], 3*4096+1024)

    def test_zero_rejected(self):
        rows, _ = model.floating(np.zeros((1024,4)), [5.6]*6)
        self.assertTrue(all(not r['valid'] for r in rows))
        p = model.chain.phat.phat_pair([(0,0)]*513, [(0,0)]*513, model.chain.BAND)
        self.assertEqual(p['reason'], 'FEWER_THAN_12_BINS')

    def test_upstream_overflow(self):
        p = model.chain.phat.phat_pair([(1,0)]*513, [(1,0)]*513, model.chain.BAND, True)
        self.assertEqual(p['reason'], 'UPSTREAM_IP_OVERFLOW')

    def test_projection_sign_algebra(self):
        pos = np.array([[0,0,0],[.04,0,0],[.04,.04,0],[0,.04,0]])
        u = np.array([.6,-.8,0])
        rows = [dict(valid=True,tau_samples=float((pos[j]-pos[i])@u*48000/343)) for i,j in model.PAIRS]
        result = model.projection(rows,pos,48000,343)
        np.testing.assert_allclose(result['projection_xy'],u[:2],atol=1e-14)
        self.assertFalse(result['direction_accepted'])

    def test_insufficient_pairs(self):
        r = model.projection([dict(valid=False)]*6,np.zeros((4,3)),48000,343)
        self.assertEqual(r['reason'],'INSUFFICIENT_PAIRS')

    def test_rank_deficient(self):
        r = model.projection([dict(valid=True,tau_samples=0)]*6,np.zeros((4,3)),48000,343)
        self.assertEqual(r['reason'],'RANK_DEFICIENT')

    def test_ifft_overflow_invalidates_frame(self):
        class Engine:
            def transform(self, codes, forward):
                out=np.zeros((1024,2),dtype=np.int64)
                if forward: out[:,0]=100
                return out, not forward
        rows, _, flags = model.fixed(np.zeros((1024,4),dtype=np.int64),[5.6]*6,Engine())
        self.assertTrue(all(flags['ifft_overflow']))
        self.assertTrue(all(r['reason']=='FRAME_IFFT_OVERFLOW' and not r['valid'] for r in rows))

    def test_pcm_window_bounds(self):
        for value in [-2**23, 2**23-1, 0]:
            for coefficient in model.chain.COEFFICIENTS:
                out = model.chain.window.window_sample(value,coefficient)[0]
                self.assertTrue(-2**23 <= out < 2**23)

if __name__ == '__main__':
    unittest.main(verbosity=2)
