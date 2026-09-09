"""Independent cohort recount and paired artifact checks."""
import gzip, json, hashlib, unittest
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;R=H.parents[1];P=R/'research/effective-perturbation-01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def cone(u):return float(np.degrees(np.arccos(np.clip(np.array(u)[0]/np.linalg.norm(u),-1,1))))
class Audit(unittest.TestCase):
    def test_cohort_independent_recount(self):
        inputs={(x['condition'],x['seed']):x for x in read(P/'evidence/inputs.json')};keys=set();cross=0
        with gzip.open(P/'evidence/features.jsonl.gz','rt',encoding='utf-8') as stream:
            for line in stream:
                x=json.loads(line);m=inputs[x['condition'],x['seed']]
                if x['scope']=='target_active' and not m['allowed'] and x['full']['valid'] and cone(x['full']['unit_vector'])<=30+1e-10 and x['diagnostic']['category']=='stable':
                    keys.add((x['condition'],x['seed'],x['frame']))
                    cross+=any(cone(x['deleted'][k]['unit_vector'])>30+1e-10 for k in x['diagnostic']['comparable_indices'])
        cohort=read(H/'cohort.json')
        self.assertEqual(keys,{(x['condition'],x['seed'],x['frame']) for x in cohort})
        self.assertEqual((len(keys),cross),(563,317))
    def test_paired_controls(self):
        rows=read(H/'controls.json');ix={(x['condition'],x['seed'],x['frame'],x['control']):x for x in rows}
        self.assertEqual(len(rows),2252);self.assertEqual(len(ix),2252)
        for x in read(H/'cohort.json'):
            key=(x['condition'],x['seed'],x['frame']);a=ix[key+('original',)];b=ix[key+('dry_no_noise',)]
            self.assertAlmostEqual(a['cone_deg'],x['cone_deg'],places=10)
            self.assertTrue(b['valid']);self.assertFalse(b['wrong_incone'])
            if x['room']=='dry':
                for left,right in [('original','dry'),('no_noise','dry_no_noise')]:
                    self.assertEqual(ix[key+(left,)]['cone_deg'],ix[key+(right,)]['cone_deg'])
    def test_summary_denominators(self):
        rows=read(H/'controls.json');s=read(H/'summary.json')
        for method,rooms in s['controls'].items():
            for room,v in rooms.items():
                g=[x for x in rows if x['control']==method and (room=='all' or x['room']==room)]
                self.assertEqual(v['n'],len(g));self.assertEqual(v['wrong_incone'],sum(x['wrong_incone'] for x in g))
                self.assertEqual(v['wrong_stable'],sum(x['wrong_incone'] and x['category']=='stable' for x in g))
    def test_prior_unchanged(self):
        for n,h in read(H/'fixed-files.json').items():self.assertEqual(hashlib.sha256((R/n).read_bytes()).hexdigest(),h,n)
    def test_geometric_counterexample(self):
        u=lambda d:np.array([np.cos(np.radians(d)),np.sin(np.radians(d)),0.])
        self.assertLess(cone(u(29)),30)
        self.assertGreater(cone(u(32)),30)
        self.assertLess(np.degrees(np.arccos(u(29)@u(31))),5)
if __name__=='__main__':unittest.main(verbosity=2)
