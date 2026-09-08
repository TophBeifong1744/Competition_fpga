import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

PACKAGE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PACKAGE/'payload/model/python'))
import batch_presence as batch
from sector_tracker import Config


def metric_row(scope,fresh=False,error=None,stale=False):
    return dict(scope=scope,fresh_valid=fresh,error_deg=error,stale=stale)


class PresenceTests(unittest.TestCase):
    def test_exact_presence_and_transition_labels(self):
        env=np.array([[0,0,.5,1,1,0,0],[0,0,0,0,0,1,1]])
        directions=[np.array([1.,0,0]),np.array([0.,1,0])]
        self.assertEqual(batch.label_frame(env,0,2,directions)['scope'],'target_absent')
        self.assertEqual(batch.label_frame(env,2,4,directions)['scope'],'transition')
        self.assertEqual(batch.label_frame(env,3,5,directions)['episode'],0)
        self.assertEqual(batch.label_frame(env,5,7,directions)['episode'],1)
        switch=batch.label_frame(env,4,6,directions)
        self.assertEqual(switch['scope'],'transition');self.assertIsNone(switch['target_unit_vector'])

    def test_cosine_envelope_boundaries(self):
        values=batch.envelope(np.arange(11),2,8,2)
        np.testing.assert_allclose(values,[0,0,0,.5,1,1,1,.5,0,0,0],atol=1e-15)

    def test_metrics_exclude_transitions_and_hold_from_false_outputs(self):
        rows=[metric_row('target_active',True,0),metric_row('target_active',True,30),
              metric_row('target_active',True,60),metric_row('target_active'),
              metric_row('target_absent',True),metric_row('target_absent',False,stale=True),
              metric_row('target_absent'),metric_row('transition',True)]
        result=batch.summarize(rows)
        self.assertEqual(result['active_fresh_rate'],.75)
        self.assertEqual(result['active_wrong_over30'],1)
        self.assertEqual(result['active_wrong_rate_all'],.25)
        self.assertEqual(result['active_wrong_rate_fresh'],1/3)
        self.assertEqual(result['absent_false_output_rate'],1/3)
        self.assertEqual(result['absent_hold_display_frames'],1)
        self.assertEqual(result['transition_fresh_outputs'],1)
        self.assertAlmostEqual(result['p95_error_deg'],57)

    def test_zero_denominators_are_null(self):
        result=batch.summarize([metric_row('target_absent')])
        self.assertIsNone(result['active_fresh_rate']);self.assertIsNone(result['p95_error_deg'])
        self.assertEqual(result['absent_false_output_rate'],0)
        result=batch.summarize([metric_row('target_active')])
        self.assertEqual(result['active_fresh_rate'],0)
        self.assertIsNone(result['active_wrong_rate_fresh']);self.assertIsNone(result['absent_false_output_rate'])
        json.dumps(result,allow_nan=False)


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.plan=batch.load_plan(PACKAGE/'payload/config/batch-presence.json')

    def small(self):
        plan=copy.deepcopy(self.plan)
        plan.update(seeds=[11,12],scenarios=['drop_return','interferer_only'],duration_samples=12000,edge_samples=128,
                    episodes=[dict(start=1000,stop=5000,azimuth_deg=0,elevation_deg=10),
                              dict(start=7000,stop=11000,azimuth_deg=-10,elevation_deg=10)])
        return plan

    def test_frozen_plan_ten_seeds_and_five_scenarios(self):
        self.assertEqual(len(self.plan['seeds']),10)
        self.assertEqual(self.plan['scenarios'],batch.SCENARIOS)
        self.assertEqual(self.plan['duration_samples'],240000)

    def test_generation_reproducible_but_seed_changes_waveform(self):
        plan=self.small()
        a,labels,directions=batch.generate(plan,'drop_return',11)
        b,labels2,_=batch.generate(plan,'drop_return',11)
        c,labels3,_=batch.generate(plan,'drop_return',12)
        np.testing.assert_array_equal(a.samples,b.samples)
        np.testing.assert_array_equal(labels,labels2);np.testing.assert_array_equal(labels,labels3)
        self.assertNotEqual(a.provenance['samples_sha256'],c.provenance['samples_sha256'])

    def test_annotations_never_enter_estimator_or_tracker(self):
        segment,env,directions=batch.generate(self.small(),'drop_return',11)
        rows,_=batch.evaluate(segment,env,directions,Config())
        altered=np.zeros_like(env)
        changed,labels=batch.evaluate(segment,altered,directions,Config())
        for a,c in zip(rows,changed):
            for key in ['method','fresh_valid','state','reason','estimate_x','estimate_y','estimate_z']:
                self.assertEqual(a[key],c[key])
        self.assertTrue(all(a['scope']=='target_absent' for a in labels))

    def test_interferer_only_all_frames_absent(self):
        segment,env,directions=batch.generate(self.small(),'interferer_only',11)
        rows,labels=batch.evaluate(segment,env,directions,Config())
        self.assertTrue(all(a['scope']=='target_absent' for a in labels))
        self.assertTrue(all(r['error_deg'] is None for r in rows))
        self.assertTrue(all(not item['applicable'] for item in batch.latencies(rows,self.small())))

    def test_methods_share_identical_frames_and_annotation(self):
        segment,env,directions=batch.generate(self.small(),'drop_return',11)
        rows,labels=batch.evaluate(segment,env,directions,Config())
        self.assertEqual(len(rows),3*len(labels))
        for i,label in enumerate(labels):
            group=rows[i*3:i*3+3]
            self.assertEqual([r['method'] for r in group],batch.METHODS)
            self.assertTrue(all(r['frame_index']==label['frame_index'] and r['scope']==label['scope'] for r in group))
            self.assertFalse(any(r['fresh_valid'] and r['stale'] for r in group))

    def test_full_pipeline_reproducible_smoke_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);a,b=root/'a',root/'b'
            with patch('builtins.print'):
                batch.run(self.small(),Config(),a)
                batch.run(self.small(),Config(),b)
            for name in ['frames.csv','pooled.json','per-seed.csv','paired-differences.csv','latencies.csv','run.json']:
                self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())
            run=json.loads((a/'run.json').read_text(encoding='utf-8'))
            self.assertEqual(run['trials'],4)
            for name,digest in run['artifact_sha256'].items():self.assertEqual(batch.entry.sha256(a/name),digest)
            with self.assertRaises(ValueError):batch.run(self.small(),Config(),a)

    def test_bad_plan_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'plan.json'
            for update in [dict(seeds=[1,1]),dict(seeds=[True]),dict(scenarios=['bad']),dict(edge_samples=0),
                           dict(duration_samples=100),dict(margin_samples=1),dict(episodes=[]),dict(extra=1)]:
                path.write_text(json.dumps(self.plan|update),encoding='utf-8')
                with self.subTest(update=update),self.assertRaises(ValueError):batch.load_plan(path)


if __name__=='__main__':unittest.main()
