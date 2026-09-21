import unittest
from analyze import aggregate
class Counts(unittest.TestCase):
    def test_unknown_is_not_success_or_failure(self):
        r=aggregate([dict(bound=True,bound_pairs=2,cycle=None,valid_pairs=2)])
        self.assertEqual(r['cycle_analyzable'],0);self.assertEqual(r['cycle_fail'],0);self.assertEqual(r['pair_tau_bound'],2)
    def test_cross_tab_and_strict_threshold(self):
        r=aggregate([dict(bound=b,bound_pairs=int(b),cycle=c,valid_pairs=5) for b,c in [(True,.6),(False,.6),(True,.5),(False,0)]])
        self.assertEqual((r['cycle_fail'],r['cycle_fail_with_bound'],r['cycle_fail_without_bound']),(2,1,1));self.assertEqual(r['cycle_analyzable'],4)
    def test_empty(self):
        self.assertEqual(aggregate([])['frames'],0)
if __name__=='__main__':unittest.main()
