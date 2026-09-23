from pathlib import Path
from unittest.mock import patch
import copy
import json
import os
import unittest
from helpers import RepoTest, PKG, cmd, read
from ftw_common import Refusal, tree
from workflow_ops import inspect_layout, init_layout, workspace_plan, workspace_apply, snapshot, cleanup_plan, upstream_check, doctor

PROCS={'known':True,'active':[]}

class WorkspaceTests(RepoTest):
    def plan(self,**kw):
        with patch('workflow_ops.process_observation',return_value=PROCS):
            return workspace_plan(self.repo,{**self.task,**kw},self.config,self.occupancy)
    def apply(self,plan,execute=True):
        with patch('workflow_ops.process_observation',return_value=PROCS):
            return workspace_apply(plan,self.config,self.occupancy,execute)
    def test_W01_serial_reuses_checkout(self):
        before=self.repo.resolve(); plan=self.plan();self.assertEqual(plan['strategy'],'reuse')
        self.apply(plan)
        self.assertEqual(self.repo.resolve(),before);self.assertEqual(cmd(self.repo,'branch','--show-current'),'task/42-test')
        self.task['branch']='task/43-test';self.apply(self.plan())
        self.assertEqual(len(cmd(self.repo,'worktree','list','--porcelain').split('worktree '))-1,1)
    def test_W02_dependencies_and_instructions_retained(self):
        self.put('common/package.svh','`define WIDTH 8\n')
        self.put('project/rtl/add.sv','`include "package.svh"\nmodule add; endmodule\n')
        self.put('project/script/src_list.txt','+incdir+common\nproject/rtl/add.sv\n')
        self.put('.agents/skills/local/SKILL.md','local test instructions\n')
        cmd(self.repo,'add','.');cmd(self.repo,'commit','-m','dependencies')
        self.task['base_commit']=cmd(self.repo,'rev-parse','HEAD')
        p=self.plan(sparse_requested=True)
        self.assertIn('common/package.svh',p['dependency_files']);self.assertIn('.agents/skills/local/SKILL.md',p['dependency_files'])
        self.apply(p);self.assertTrue((self.repo/'common/package.svh').exists())
    def test_W03_dirty_and_ignored_protected(self):
        p=self.put('data/local/unique.wav','unique recording')
        plan=self.plan(sparse_requested=True)
        self.assertEqual(plan['status'],'BLOCKED')
        with self.assertRaises(Refusal):self.apply(plan)
        self.assertEqual(p.read_text(),'unique recording')
    def test_W04_active_eda_blocks_switch(self):
        with patch('workflow_ops.process_observation',return_value={'known':True,'active':[['vivado.exe','123']]}):
            plan=workspace_plan(self.repo,self.task,self.config,self.occupancy)
        self.assertEqual(plan['status'],'BLOCKED');self.assertEqual(cmd(self.repo,'branch','--show-current'),'main')
    def test_W05_parallel_worktree_has_separate_output(self):
        p=self.plan(parallel_write=True)
        self.assertEqual(p['strategy'],'isolate')
        dest=self.base/'独立 worktree'
        with patch('workflow_ops.process_observation',return_value=PROCS):
            workspace_apply(p,self.config,self.occupancy,True,dest)
        self.assertTrue((dest/'project/rtl/add.sv').exists())
        self.assertEqual(cmd(self.repo,'branch','--show-current'),'main')
    def test_W06_cleanup_rejects_traversal_and_unknown(self):
        p=self.put('codex_out/run/unique','one')
        r=cleanup_plan(self.repo,{'schema_version':1,'items':[{'path':'codex_out/run','owner':'unknown'}]},self.config)
        self.assertFalse(r['items'][0]['eligible']);self.assertEqual(p.read_text(),'one')
        with self.assertRaises(Refusal): cleanup_plan(self.repo,{'schema_version':1,'items':[{'path':'../outside'}]},self.config)
    def test_W07_unicode_space_snapshot(self):
        self.put('project/rtl/中文 文件.sv','module chinese; endmodule\n')
        r=snapshot(self.repo,{'schema_version':1,'files':['project/rtl/中文 文件.sv']})
        self.assertEqual(r['untracked_inputs'],['project/rtl/中文 文件.sv'])
    def test_D01_init_no_fake_vendor_entry(self):
        dest=self.base/'new project'
        out=init_layout(dest,self.config,True)
        self.assertFalse(out['project_files_created']);self.assertTrue((dest/'project/par').is_dir())
        self.assertEqual(list(dest.rglob('*.xpr')),[]);self.assertFalse((dest/'software').exists())
    def test_D02_existing_mapping_preserves_files(self):
        self.config['layout']['mode']='existing'
        self.config['layout']['document_root']='docs'
        self.put('docs/contract.md','legacy contract')
        before=tree(self.repo)
        r=inspect_layout(self.repo,self.config)
        self.assertEqual(r['layout_mode'],'existing');self.assertEqual(tree(self.repo),before)
    def test_D03_native_inputs_protected(self):
        p='project/par/test.srcs/custom.v';self.put(p,'module custom; endmodule\n')
        self.put('project/par/test.xpr','<SyntheticClassificationFixture/>')
        self.config['layout'].update(project_control='native_project',project_entry='project/par/test.xpr',source_exceptions=['project/par/test.srcs','project/par/test.xpr'])
        r=inspect_layout(self.repo,self.config)
        self.assertNotIn(p,r['ignored_sources']);self.assertFalse(any('without protection' in e for e in r['errors']))
        out=cleanup_plan(self.repo,{'schema_version':1,'items':[{'path':'project/par'}]},self.config)
        self.assertFalse(out['items'][0]['eligible'])
    def test_D04_missing_initialization_detected(self):
        self.put('project/rtl/add.sv','module add; initial $readmemh("rom.mem",x); endmodule')
        r=inspect_layout(self.repo,self.config)
        self.assertTrue(any('Initialization data' in e for e in r['errors']))
    def test_D05_locked_ip_explicit_dependency(self):
        path='project/par/test.gen/locked.dcp';self.put(path,'unique locked checkpoint')
        self.config['layout']['required_inputs']=[path]
        self.config['layout']['source_exceptions']=[path]
        r=inspect_layout(self.repo,self.config)
        self.assertIn(path,r['ignored_sources'])
        self.assertEqual((self.repo/path).read_text(),'unique locked checkpoint')
    def test_D06_duplicate_wrapper(self):
        self.put('project/rtl/generated.sv','module add; endmodule\n')
        self.put('project/script/src_list.txt','project/rtl/add.sv\nproject/rtl/generated.sv\n')
        r=inspect_layout(self.repo,self.config)
        self.assertIn('add',r['dependencies']['duplicate_modules'])
    def test_D07_ignore_reverse_and_tracked_output(self):
        self.put('data/fixtures/rom.mem','ff\n')
        self.config['layout']['required_inputs']=['data/fixtures/rom.mem']
        self.put('.gitignore','*.mem\n')
        self.put('simulation/work/huge.wdb','fixture-small-cache')
        cmd(self.repo,'add','simulation/work/huge.wdb')
        self.config['layout']['regenerable_output_roots']=['simulation/work']
        r=inspect_layout(self.repo,self.config)
        self.assertIn('data/fixtures/rom.mem',r['ignored_sources']);self.assertIn('simulation/work/huge.wdb',r['tracked_outputs'])
    def test_D08_paths_and_overlap(self):
        self.config['layout']['document_root']='../escape'
        with self.assertRaises(Refusal):inspect_layout(self.repo,self.config)
        self.config['layout']['document_root']='document'
        self.config['layout']['runtime_roots']['diagnostics']='project/rtl'
        self.assertTrue(any('without protection' in e for e in inspect_layout(self.repo,self.config)['errors']))
    def test_D09_mapping_not_build_proof(self):
        self.config['layout']['adapter_status']='UNVERIFIED'
        r=inspect_layout(self.repo,self.config)
        self.assertFalse(r['engineering_entry_verified']);self.assertEqual(r['status'],'INCONCLUSIVE')
        self.assertEqual(self.plan(sparse_requested=True)['status'],'BLOCKED')
    def test_D10_no_implicit_migration(self):
        self.config['layout']['mode']='existing'
        before=tree(self.repo)
        with self.assertRaises(Refusal):init_layout(self.repo,self.config,True)
        self.assertEqual(before,tree(self.repo))
    def test_D11_duplicate_active_sources_in_compile_view(self):
        self.put('member-copy/rtl/add.sv',(self.repo/'project/rtl/add.sv').read_text())
        self.put('project/script/src_list.txt','project/rtl/add.sv\nmember-copy/rtl/add.sv\n')
        self.assertEqual(inspect_layout(self.repo,self.config)['status'],'BLOCKED')
    def test_D12_targets_require_selection_and_separate_outputs(self):
        lay=copy.deepcopy(self.config['layout'])
        self.config['targets']=[{'id':'a','layout':lay},{'id':'b','layout':copy.deepcopy(lay)}]
        with self.assertRaises(Refusal):inspect_layout(self.repo,self.config)
        r=inspect_layout(self.repo,self.config,'a')
        self.assertTrue(any('overlap across targets' in e for e in r['errors']))
    def test_G01_snapshots_without_commits(self):
        identities=[]
        for i in range(3):
            self.put('project/rtl/add.sv',f'module add; localparam X={i}; endmodule\n')
            identities.append(snapshot(self.repo,{'schema_version':1,'files':['project/rtl/add.sv']})['input_identity'])
        self.assertEqual(len(set(identities)),3);self.assertEqual(cmd(self.repo,'rev-parse','HEAD'),self.head)
    def test_G02_new_required_input_not_tracked(self):
        self.put('project/rtl/new.sv','module n; endmodule\n')
        self.config['layout']['required_inputs']=['project/rtl/new.sv']
        self.assertIn('project/rtl/new.sv',inspect_layout(self.repo,self.config)['untracked_required'])
    def test_stale_workspace_plan(self):
        p=self.plan();self.put('untracked.txt','new work')
        with self.assertRaises(Refusal):self.apply(p)
    def test_other_base_does_not_reuse_wrong_dependency_view(self):
        self.put('project/rtl/add.sv','module changed; endmodule\n')
        cmd(self.repo,'add','.');cmd(self.repo,'commit','-m','new version')
        self.assertEqual(self.plan()['status'],'BLOCKED')
    def test_cleanup_protects_declared_source_inside_diagnostics(self):
        self.put('codex_out/run/source.mem','unique calibration')
        self.config['layout']['required_inputs']=['codex_out/run/source.mem']
        item={'path':'codex_out/run','owner':'fpga-team-workflow','regenerable':True,'recipe_ref':'fixture',
              'active':False,'unique_data':False,'failed_evidence':False,'owned_files':tree(self.repo/'codex_out/run')}
        out=cleanup_plan(self.repo,{'schema_version':1,'items':[item]},self.config)
        self.assertFalse(out['items'][0]['eligible']);self.assertIn('Protected input overlaps',out['items'][0]['retain_reasons'])
    def test_project_lock_mismatch_is_reported(self):
        lock=read(PKG/'assets/workflow-lock.example.yaml')
        lock['engineering_skill']['source_commit']='0'*40
        self.put('workflow-lock.yaml',json.dumps(lock))
        r=doctor(self.repo,self.config)
        self.assertEqual(r['project_lock_status'],'MISMATCH');self.assertEqual(r['status'],'BLOCKED')
    def test_link_rejected(self):
        if os.name=='nt':
            import subprocess
            subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(self.repo/'link'),str(self.base)],capture_output=True,check=True)
            # Removing an empty junction with rmdir does not recurse into its target.
            self.addCleanup(lambda:(self.repo/'link').rmdir() if (self.repo/'link').exists() else None)
        else:(self.repo/'link').symlink_to(self.base,target_is_directory=True)
        from ftw_common import safe_path
        with self.assertRaises(Refusal):safe_path(self.repo,'link/anything')

class UpstreamTests(unittest.TestCase):
    def test_A06_missing_roles_fail_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            r=upstream_check(Path(d)/'skill',Path(d)/'agents')
            self.assertEqual(r['status'],'BLOCKED');self.assertEqual(len(r['missing']),40)
