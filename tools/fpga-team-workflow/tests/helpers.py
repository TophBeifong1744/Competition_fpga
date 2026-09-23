import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode=True
PKG=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PKG/'scripts'))
from ftw_common import read, file_hash, digest, write_json

def cmd(root,*args):
    r=subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True)
    return r.stdout.decode().strip()

class RepoTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='fpga 团队 fixture ')
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.repo=self.base/'工程 with spaces';self.repo.mkdir()
        cmd(self.repo,'init','-b','main')
        cmd(self.repo,'config','user.name','Fixture User')
        cmd(self.repo,'config','user.email','fixture@example.invalid')
        self.config=read(PKG/'assets/project.example.yaml')
        self.config['project']['id']='synthetic-test'
        self.config['layout'].update(project_entry=None,adapter_status='VERIFIED',adapter_evidence_ref='fixture:mechanical-test-only')
        self.put('project/rtl/add.sv','module add(input logic a, output logic b); assign b=a; endmodule\n')
        self.put('project/script/src_list.txt','project/rtl/add.sv\n')
        self.put('simulation/script/src_list.txt','project/rtl/add.sv\n')
        self.put('project/script/run.bat','@echo Synthetic fixture only\n')
        self.put('simulation/script/run.bat','@echo Synthetic fixture only\n')
        self.put('AGENTS.md','Synthetic instructions for dependency retention.\n')
        self.put('.gitignore',(PKG/'assets/repository-gitignore.example').read_text(encoding='utf-8'))
        cmd(self.repo,'add','.');cmd(self.repo,'commit','-m','fixture baseline')
        self.head=cmd(self.repo,'rev-parse','HEAD')
        self.task={'schema_version':1,'task_ref':'#42','actor_ref':'author','phase':'implementation',
                   'execution_kind':'model_assisted','activity':'implementation','contract_trusted':True,
                   'base_commit':self.head,'branch':'task/42-test','dependency_closure_ref':'fixture:filelist'}
        self.occupancy={'schema_version':1,'writer_clear':True,'active':False,'source_ref':'fixture:exclusive-test-process'}
    def put(self,rel,text):
        p=self.repo/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8');return p

def task(**kw):
    return {'schema_version':1,'task_ref':'#42','actor_ref':'author','activity':'implementation',
            'contract_trusted':True,'phase':'implementation',**kw}

def facts(**kw):
    return {'schema_version':1,'author':'author','contributors':[], 'head_commit':'a'*40,'evidence_commit':'a'*40,
            'candidate_commit':'b'*40,'tested_candidate_commit':'b'*40,'required_checks_status':'PASS',
            'reviews':[{'actor':'reviewer','state':'APPROVED','commit':'a'*40}],**kw}
