import copy
from datetime import datetime, timezone
import tempfile
from pathlib import Path
import unittest
from helpers import PKG, task, read
from ftw_common import Refusal
from model_policy import recommend, inspect_settings, stop_reason

class ModelTests(unittest.TestCase):
    def setUp(self): self.config=read(PKG/'assets/project.example.yaml')
    def test_M01_automatic_and_nonmodel(self):
        for kind in ('script_only','human_only'):
            r=recommend(self.config,task(execution_kind=kind))
            self.assertIsNone(r['recommended']['model_id']);self.assertEqual(r['availability_status'],'NOT_APPLICABLE')
        self.assertEqual(recommend(self.config,task())['recommended']['model_id'],'gpt-6-sol')
    def test_M02_fixed_execution(self):
        r=recommend(self.config,task(activity='fixed_execution',trusted_entry=True))
        self.assertEqual(r['recommended']['routing_profile'],'execution')
    def test_M03_checker_activity_over_title(self):
        r=recommend(self.config,task(title='仿真',activity='checker_design'))
        self.assertEqual(r['recommended']['routing_profile'],'analysis')
    def test_M04_recommend_only_has_no_write(self):
        before=copy.deepcopy(self.config)
        r=recommend(self.config,task(keep_current_model=True))
        self.assertFalse(r['settings_modified']);self.assertEqual(self.config,before)
    def test_M05_observation_sources(self):
        for source,status in [('prompt','UNKNOWN'),('config','UNKNOWN'),('runtime_metadata','UNKNOWN'),('user_report','USER_REPORTED')]:
            r=inspect_settings({'schema_version':1,'main':{'model_id':'gpt-6-sol','source_kind':source}})
            self.assertEqual(r['observed']['main']['observation_status'],status)
    def test_M06_unavailable_actor(self):
        caps={'schema_version':1,'actor_ref':'author','source_ref':'fixture','checked_at':datetime.now(timezone.utc).isoformat(),'complete':True,'models':{'gpt-6-luna':['high']}}
        r=recommend(self.config,task(),caps)
        self.assertEqual(r['availability_status'],'UNAVAILABLE');self.assertEqual(r['alternatives'],[])
        caps['actor_ref']='another-member'
        self.assertEqual(recommend(self.config,task(),caps)['availability_status'],'UNKNOWN')
    def test_M07_role_override_not_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'reviewer.toml';p.write_text('model="gpt-6-astra"\nmodel_reasoning_effort="xhigh"\n')
            r=inspect_settings(roles=[p],requested={'model_id':'gpt-6-sol','reasoning_effort':'medium'})
            self.assertTrue(r['role_overrides'][0]['differs_from_requested'])
            self.assertEqual(r['observed']['subagents'],[])
    def test_M08_effort_validation(self):
        self.config['model_policy']['routing_profiles']['deep']['reasoning_effort']='ultra'
        with self.assertRaises(Refusal): recommend(self.config,task())
    def test_M09_escalation_keeps_budget(self):
        t=task(complex_cross_layer=True,specific_uncertainty='CDC transaction loss',repair={'rounds':2,'finding_id':'F-1'})
        r=recommend(self.config,t)
        self.assertEqual(r['recommended']['routing_profile'],'deep');self.assertEqual(r['repair']['rounds'],2)
    def test_M10_counterexample_stops_vote(self):
        r=recommend(self.config,task(blocking_counterexample='120+20 should be 127, got -116',model_consensus='PASS'))
        self.assertEqual(r['status'],'BLOCKED')
    def test_M11_no_model_bypass(self):
        with self.assertRaises(Refusal): recommend(self.config,task(execution_kind='script_only',requires_engineering_reasoning=True))
    def test_M12_model_change_keeps_stop(self):
        for phase in ('implementation','review'):
            r=recommend(self.config,task(phase=phase,repair={'rounds':3,'finding_id':'original-F1'}))
            self.assertEqual(r['status'],'BLOCKED');self.assertEqual(r['repair']['rounds'],3)
    def test_M14_short_script_does_not_apply(self):
        r=recommend(self.config,task(activity='fixed_execution',trusted_entry=True,remaining_steps=1))
        self.assertEqual(r['application_status'],'RECOMMENDATION_ONLY');self.assertFalse(r['settings_modified'])
    def test_M15_conditions_not_guessed(self):
        r=recommend(self.config,task(missing_conditions=['board','contract']))
        self.assertEqual(r['status'],'BLOCKED')
    def test_M16_policy_version_is_separate(self):
        self.config['model_policy']['policy_version']='0.2.0'
        r=recommend(self.config,task())
        self.assertEqual(r['policy_version'],'0.2.0');self.assertFalse(r['settings_modified'])
    def test_M17_legacy_and_unknown_schema(self):
        self.config.pop('model_policy')
        self.assertFalse(recommend(self.config,task())['policy_configured'])
        self.config['model_policy']={'schema_version':99}
        with self.assertRaises(Refusal):recommend(self.config,task())
    def test_M18_unknown_usage_null(self):
        self.assertIsNone(recommend(self.config,task())['usage']['value'])
    def test_M19_cannot_fake_calibration(self):
        self.config['model_policy']['quality_status']='VALIDATED_FOR_SCOPE'
        with self.assertRaises(Refusal): recommend(self.config,task())
    def test_phase_difference(self):
        r=recommend(self.config,task(phase='review'))
        self.assertEqual(r['recommended']['reasoning_effort'],'high')
    def test_capability_expiry(self):
        caps={'schema_version':1,'actor_ref':'author','source_ref':'fixture','checked_at':'2000-01-01T00:00:00Z','complete':True,'models':{'gpt-6-sol':['medium']}}
        self.assertEqual(recommend(self.config,task(),caps)['availability_status'],'UNKNOWN')
