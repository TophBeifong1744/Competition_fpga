import unittest
import numpy as np
from probe import fit_score,PAIRS
class PhaseTests(unittest.TestCase):
    def test_matched_delay_sign(self):
        bins=np.arange(7,86);tau=np.array([2,3,1,1,-1,-2]);u=np.exp(-2j*np.pi*tau[:,None]*bins/1024);w=np.ones(len(bins))
        self.assertAlmostEqual(fit_score(u,bins,tau,w)['unweighted'],1)
        self.assertLess(fit_score(u,bins,-tau,w)['unweighted'],.9)
    def test_random_spectra_still_close(self):
        rng=np.random.default_rng(23);sp=rng.normal(size=(4,79))+1j*rng.normal(size=(4,79));z=np.array([sp[i]*sp[j].conj() for i,j in PAIRS]);u=z/np.abs(z)
        np.testing.assert_allclose(u[0]*u[3]*u[1].conj(),1,atol=1e-14)
    def test_identical_channel_is_not_target_proof(self):
        bins=np.arange(7,86);u=np.ones((6,79),dtype=complex)
        self.assertEqual(fit_score(u,bins,np.zeros(6),np.ones(79))['unweighted'],1)
    def test_nonuniform_weight_no_sign_change(self):
        bins=np.arange(7,86);tau=np.arange(6);u=np.exp(-2j*np.pi*tau[:,None]*bins/1024)
        self.assertAlmostEqual(fit_score(u,bins,tau,np.linspace(.02,1,79))['weighted'],1)
if __name__=='__main__':unittest.main()
