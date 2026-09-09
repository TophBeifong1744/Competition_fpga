import tempfile
import unittest
from pathlib import Path
import numpy as np
from common import Differences, angle, sha, verify_entries, verify_package
from run_all import compare_tree


class Revision(unittest.TestCase):
    def test_manifest_missing_and_corrupt_file_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'run.log';p.write_bytes(b'original')
            entries={'run.log':sha(p)}
            verify_entries(root,entries)
            p.write_bytes(b'changed')
            with self.assertRaises(AssertionError):verify_entries(root,entries)
            p.unlink()
            with self.assertRaises(AssertionError):verify_entries(root,entries)

    def test_all_six_manifests(self):
        self.assertEqual(verify_package()['manifest_entries'],142)

    def test_stable_zero_and_scale_invariance(self):
        u=np.array([.8,.6,0.])
        self.assertEqual(angle(u,u),0.)
        self.assertAlmostEqual(angle(u,u*2),0.)
        self.assertAlmostEqual(angle(u,-u),180.)

    def test_roundoff_bound_not_classification_tolerance(self):
        d=Differences()
        d.numeric(8.537736462515939e-7,0.,'angle',angular=True)
        d.numeric(1.2074182697257333e-6,0.,'angle',angular=True)
        with self.assertRaises(AssertionError):d.numeric(1e-4,0.,'angle',angular=True)
        with self.assertRaises(AssertionError):d.numeric(5.000001,5.,'angle',angular=True)

    def test_discrete_changes_rejected(self):
        for a,b in [(dict(valid=True),dict(valid=False)),(dict(category='stable'),dict(category='unknown')),
                    (dict(count=563),dict(count=562)),([1,2],[2,1]),(dict(keys=[1,2]),dict(keys=[1]))]:
            with self.assertRaises(AssertionError):compare_tree(a,b)

    def test_input_hash_mismatch_never_means_equivalent(self):
        d=Differences();old=dict(condition='test',seed=1,**{k:'a' for k in ['input_sha256','target_sha256','noise_sha256','rir_sha256']})
        d.input(old,old)
        with self.assertRaises(AssertionError):d.input(old,old|dict(target_sha256='b'))
        self.assertFalse(d.inputs[-1]['hashes']['target_sha256']['equal'])

    def test_nonfinite_and_degenerate_rejected(self):
        for u in [[0,0,0],[float('nan'),1,0]]:
            with self.assertRaises(AssertionError):angle(u)
        with self.assertRaises(AssertionError):Differences().numeric(float('nan'),0.,'value')
