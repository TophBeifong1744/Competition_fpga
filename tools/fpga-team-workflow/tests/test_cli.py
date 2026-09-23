from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from helpers import PKG, read, task
from ftw_common import write_json, tree

class CliTests(unittest.TestCase):
    def call(self,*args):
        r=subprocess.run([sys.executable,'-B',str(PKG/'scripts/team_workflow.py'),*args],capture_output=True)
        return r,json.loads(r.stdout.decode())
    def test_M20_apply_is_explicitly_unsupported(self):
        r,out=self.call('model','apply')
        self.assertEqual(r.returncode,4);self.assertEqual(out['application_status'],'UNSUPPORTED');self.assertFalse(out['settings_modified'])
    def test_A04_readonly_recommendation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'task.json';write_json(p,task())
            before=tree(d)
            r,out=self.call('model','recommend','--config',str(PKG/'assets/project.example.yaml'),'--task',str(p))
            self.assertEqual(r.returncode,0);self.assertEqual(tree(d),before);self.assertFalse(out['settings_modified'])
    def test_S03_no_hardware_action_interface(self):
        r=subprocess.run([sys.executable,'-B',str(PKG/'scripts/team_workflow.py'),'hardware','flash','--execute'],capture_output=True)
        self.assertNotEqual(r.returncode,0)
    def test_invalid_input_returns_nonzero_json(self):
        r,out=self.call('model','recommend','--config','nonexistent.yaml')
        self.assertEqual(r.returncode,2);self.assertEqual(out['status'],'BLOCKED')
