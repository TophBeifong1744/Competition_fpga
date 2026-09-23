import copy
from pathlib import Path
import tempfile
import unittest
from helpers import facts, PKG, read, task
from ftw_common import file_hash
from workflow_ops import delivery_gate, evidence_inspect, handoff
from model_policy import recommend

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'run.json').write_text('{"schema_version":1,"fixture":true}')
        self.ids={k:k+'-identity' for k in ('requirements','sources','constraints','parameters','dependencies','checker','reference','input_data','tool','entry')}
        self.index={'schema_version':1,'identities':self.ids.copy(),'profile':'FUNCTIONAL_ACCEPTANCE',
                    'run_inputs_stable':True,'run_result':'PASS','independent_basis_ref':'fixture:original-contract',
                    'checker_activity':12,'negative_canary':'DETECTED',
                    'raw_records':[{'schema_version':1,'local_path':'run.json','sha256':file_hash(self.root/'run.json')}]}
        self.current={'schema_version':1,'identities':self.ids.copy()}
    def inspect(self):return evidence_inspect(self.index,self.current,self.root)
    def test_A01_two_members_no_third_signer(self):
        r=delivery_gate(facts());self.assertTrue(r['mechanics_eligible']);self.assertEqual(r['qualified_reviewers'],['reviewer'])
        self.assertFalse(r['delivery_approved'])
    def test_A02_six_members_no_all_sign(self):
        r=delivery_gate(facts(members=['a','b','c','d','e','f']))
        self.assertEqual(len(r['qualified_reviewers']),1)
    def test_A03_only_author_cannot_approve(self):
        r=delivery_gate(facts(reviews=[{'actor':'author','state':'APPROVED','commit':'a'*40}]))
        self.assertFalse(r['mechanics_eligible'])
    def test_G03_merge_not_board_acceptance(self):
        r=delivery_gate(facts(merged=True,needs_board=True,board_pass=False))
        self.assertFalse(r['should_close_issue']);self.assertFalse(r['mechanics_eligible'])
    def test_G04_new_combination_and_stale_review(self):
        self.assertFalse(delivery_gate(facts(candidate_commit='c'*40))['mechanics_eligible'])
        self.assertFalse(delivery_gate(facts(head_commit='d'*40))['mechanics_eligible'])
    def test_G05_no_platform_protection_claim(self):
        r=delivery_gate(facts(branch_protection_permission=False))
        self.assertEqual(r['approval_authenticity'],'UNVERIFIED_IMPORTED_FACTS');self.assertFalse(r['delivery_approved'])
    def test_R01_reuse_candidate_not_retest(self):
        r=self.inspect();self.assertEqual(r['decision'],'REUSE_CANDIDATE');self.assertFalse(r['technical_approval'])
    def test_R02_assumption_change_invalidates_same_hash(self):
        self.current['assumption_conflicts']=['wrong numerical contract']
        self.assertEqual(self.inspect()['decision'],'INVALID')
    def test_R03_shared_wraparound_error(self):
        # Original requirement is signed 8-bit saturation; hand-derived counterexample is independent of DUT/checker.
        expected=127;dut=-116;reference=-116
        self.assertEqual(dut,reference);self.assertNotEqual(dut,expected)
        self.current['assumption_conflicts']=[{'requirement':'signed 8-bit saturation','input':[120,20],'expected':expected,'observed':dut}]
        self.assertEqual(self.inspect()['status'],'BLOCKED')
    def test_R04_zero_activity_and_bad_checker(self):
        self.index['checker_activity']=0;self.assertEqual(self.inspect()['decision'],'INVALID')
        self.index['checker_activity']=20;self.index['negative_canary']='MISSED'
        self.assertEqual(self.inspect()['decision'],'UNKNOWN')
    def test_R05_reproduction_is_purpose_bound(self):
        r=self.inspect();self.assertIn('uncertainty',r['rerun']);self.assertFalse(r['technical_approval'])
    def test_R06_missing_raw_report(self):
        (self.root/'run.json').unlink()
        self.assertEqual(self.inspect()['decision'],'UNKNOWN')
    def test_R07_contributor_cannot_self_sign(self):
        self.assertFalse(delivery_gate(facts(contributors=['reviewer']))['mechanics_eligible'])
    def test_R08_document_handoff_no_eda_commands(self):
        r=handoff(facts(scope='documentation'),read(PKG/'assets/project.example.yaml'),task(activity='documentation'))
        self.assertEqual(r['remote_writes'],[]);self.assertIn('实际设置 UNKNOWN',r['markdown'])
    def test_R09_original_repair_budget(self):
        r=recommend(read(PKG/'assets/project.example.yaml'),task(task_ref='#new',repair={'rounds':3,'finding_id':'original'}))
        self.assertEqual(r['status'],'BLOCKED')
    def test_S01_system_failure_blocks_stage(self):
        self.assertFalse(delivery_gate(facts(stage=True,system_pass=False))['mechanics_eligible'])
    def test_S02_artifact_mismatch(self):
        self.assertFalse(delivery_gate(facts(artifact_pairing='MISMATCH'))['mechanics_eligible'])
        self.assertFalse(delivery_gate(facts(needs_board=True,board_pass=True,deployment_identity='UNKNOWN'))['mechanics_eligible'])
    def test_M13_model_only_change_keeps_eda_identity(self):
        self.current['model_id']='gpt-6-astra';self.current['reasoning_effort']='xhigh'
        self.assertEqual(self.inspect()['decision'],'REUSE_CANDIDATE')
    def test_U07_unknown_evidence_schema(self):
        self.index['raw_records'][0]['schema_version']=99
        self.assertEqual(self.inspect()['decision'],'UNKNOWN')
    def test_entry_path_changed_invalidates(self):
        self.current['identities']['entry']='different-path'
        self.assertEqual(self.inspect()['decision'],'INVALID')
    def test_missing_identity_is_unknown(self):
        self.current['identities']['constraints']=None
        self.assertEqual(self.inspect()['decision'],'UNKNOWN')
    def test_summary_hash_not_raw(self):
        (self.root/'run.json').write_text('changed report')
        self.assertEqual(self.inspect()['decision'],'INVALID')
    def test_case_variant_is_not_independent_member(self):
        self.assertFalse(delivery_gate(facts(author='Reviewer'))['mechanics_eligible'])
    def test_dismissed_review_not_reused(self):
        f=facts();f['reviews'].append({'actor':'reviewer','state':'DISMISSED','commit':'a'*40})
        self.assertFalse(delivery_gate(f)['mechanics_eligible'])
    def test_missing_author_not_accepted(self):
        self.assertFalse(delivery_gate(facts(author=None))['mechanics_eligible'])
    def test_pinned_native_run_failure_overrules_summary(self):
        import json
        raw={'schema_version':'1.0.0','run_id':'R1','snapshot_id':'S1','command':'sim','working_directory':'.',
             'tool':{'name':'fixture','version':'1'},'evidence_paths':['log'],'exit_code':1}
        (self.root/'run-manifest.json').write_text(json.dumps(raw))
        self.index['raw_records']=[{'schema_version':'1.0.0','local_path':'run-manifest.json','sha256':file_hash(self.root/'run-manifest.json')}]
        r=self.inspect();self.assertEqual(r['decision'],'INVALID');self.assertEqual(r['native_records'][0]['run_id'],'R1')
    def test_pinned_native_zero_activity(self):
        import json
        raw={'schema_version':'1.0.0','run_id':'R1','snapshot_id':'S1','classification':'SIMULATION_PASS',
             'compile_exit_code':0,'elaboration_exit_code':0,'run_exit_code':0,'tests_discovered':1,'tests_executed':0,
             'scoreboard_drained':True,'comparisons':[],'negative_canaries':[{'fault':'mutant','detected':True}],'proof_packet':['trace']}
        (self.root/'simulation-evidence.json').write_text(json.dumps(raw))
        self.index['raw_records']=[{'schema_version':'1.0.0','local_path':'simulation-evidence.json','sha256':file_hash(self.root/'simulation-evidence.json')}]
        self.assertEqual(self.inspect()['decision'],'INVALID')
