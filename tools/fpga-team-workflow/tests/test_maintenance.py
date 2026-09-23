from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from helpers import PKG
from ftw_common import Refusal, tree, digest, file_hash, write_json, read
from skill_maintenance import (propose, candidate, seal, verify_package, install_plan, install, rollback, recover)

class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='安装 回退 ');self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.source=self.base/'source';self.source.mkdir()
        self.target=self.base/'skills'/'fpga-team-workflow'
        for rel,content in {'SKILL.md':'---\nname: fpga-team-workflow\ndescription: Synthetic installation fixture\n---\nTest only.\n',
                            'VERSION':'0.1.0\n','README.md':'synthetic test\n','COMPATIBILITY.md':'fixture only\n',
                            'scripts/team_workflow.py':'# synthetic test\n','scripts/skill_maintenance.py':'# synthetic test\n'}.items():
            p=self.source/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8')
        seal(self.source)
    def install(self):return install(install_plan(self.source,self.target),True,'fixture:authorized')
    def upgrade_source(self):
        (self.source/'VERSION').write_text('0.2.0\n');(self.source/'README.md').write_text('new candidate\n');seal(self.source)
    def test_U01_feedback_proposal_only(self):
        before=tree(self.source)
        f={'schema_version':1,'kind':'outer_rule','problem':'too much rerun','requested_behavior':'reuse evidence'}
        a=propose(f);b=propose(f)
        self.assertEqual(a['change_id'],b['change_id']);self.assertFalse(a['effective_rules_modified']);self.assertEqual(tree(self.source),before)
    def test_U02_minimal_layer_and_candidate(self):
        req={'schema_version':1,'kind':'project_config','problem':'verbose','requested_behavior':'shorter',
             'base_tree_sha256':digest(tree(self.source)),'scope':{'include':['README.md']},
             'protected_invariants':['no self approval'],'acceptance':['concise'],
             'changes':[{'path':'README.md','base_sha256':file_hash(self.source/'README.md'),'content':'short\n'}]}
        before=tree(self.source);dest=self.base/'candidate'
        r=candidate(self.source,req,dest,True)
        self.assertEqual((dest/'README.md').read_text(),'short\n');self.assertEqual(tree(self.source),before)
        self.assertFalse(r['installed_modified'])
    def test_U03_unmanaged_custom_destination(self):
        self.target.mkdir(parents=True);(self.target/'SKILL.md').write_text('custom')
        p=install_plan(self.source,self.target)
        self.assertEqual(p['status'],'BLOCKED')
        with self.assertRaises(Refusal):install(p,True,'fixture')
        self.assertEqual((self.target/'SKILL.md').read_text(),'custom')
    def test_U04_stale_preview(self):
        self.install();self.upgrade_source();plan=install_plan(self.source,self.target)
        (self.target/'README.md').write_text('user changes after preview')
        with self.assertRaises(Refusal):install(plan,True,'fixture')
        self.assertEqual((self.target/'README.md').read_text(),'user changes after preview')
    def test_U05_failure_restores_consistency(self):
        self.install();before=tree(self.target);self.upgrade_source()
        for point in ('after_backup','after_switch'):
            with self.assertRaises(Refusal):install(install_plan(self.source,self.target),True,'fixture',point)
            self.assertEqual(tree(self.target),before)
    def test_U06_rollback_protects_later_edits(self):
        tx=self.install()['transaction'];(self.target/'README.md').write_text('later user change')
        with self.assertRaises(Refusal):rollback(tx,True,'fixture')
        self.assertEqual((self.target/'README.md').read_text(),'later user change')
    def test_U08_modified_package_rejected(self):
        (self.source/'SKILL.md').write_text('remove required metadata and rules')
        self.assertEqual(verify_package(self.source)['status'],'BLOCKED')
        with self.assertRaises(Refusal):install_plan(self.source,self.target)
    def test_U09_local_scope_only(self):
        other=self.base/'other-member';other.mkdir();(other/'VERSION').write_text('old')
        before=tree(other);self.install();self.assertEqual(tree(other),before)
    def test_U10_idempotent(self):
        self.install();before=tree(self.target);second=self.install()
        self.assertTrue(second['idempotent']);self.assertEqual(second['files_changed'],0);self.assertEqual(tree(self.target),before)
    def test_real_upgrade_and_rollback(self):
        self.install();before=tree(self.target);self.upgrade_source();tx=self.install()['transaction']
        self.assertEqual((self.target/'VERSION').read_text().strip(),'0.2.0')
        self.assertTrue(rollback(tx,True,'fixture')['verified']);self.assertEqual(tree(self.target),before)
    def test_initial_install_rollback_to_absence(self):
        tx=self.install()['transaction'];rollback(tx,True,'fixture');self.assertFalse(self.target.exists())
    def test_changed_candidate_stales_plan(self):
        plan=install_plan(self.source,self.target);self.upgrade_source()
        with self.assertRaises(Refusal):install(plan,True,'fixture')
    def test_candidate_cannot_edit_installed_or_upstream(self):
        self.install()
        with self.assertRaises(Refusal):candidate(self.target,{'schema_version':1},self.base/'bad',True)
    def test_dry_run_no_files_written(self):
        before=tree(self.base);plan=install_plan(self.source,self.target);install(plan)
        self.assertEqual(tree(self.base),before)
    def test_explicit_mutation_authorization(self):
        with self.assertRaises(Refusal):install(install_plan(self.source,self.target),True)
    def test_interrupted_recovery(self):
        self.install();before=tree(self.target);self.upgrade_source()
        # Simulate termination after backup by stopping automatic exception recovery.
        with patch('skill_maintenance.recover',side_effect=OSError('simulated process loss')):
            with self.assertRaises(Refusal):install(install_plan(self.source,self.target),True,'fixture','after_backup')
        txs=list((self.target.parent/'.fpga-team-workflow-transactions').iterdir())
        tx=next(p for p in txs if read(p/'transaction.json')['state']=='BACKED_UP')
        recover(tx,True,'fixture');self.assertEqual(tree(self.target),before)
    def test_corrupt_receipt_fails_verification(self):
        self.install()
        (self.target/'.ftw-install.json').write_text('{"schema_version":1,"name":"fpga-team-workflow","installed_files":{}}')
        self.assertEqual(verify_package(self.target)['status'],'BLOCKED')
        self.assertEqual(install_plan(self.source,self.target)['status'],'BLOCKED')
