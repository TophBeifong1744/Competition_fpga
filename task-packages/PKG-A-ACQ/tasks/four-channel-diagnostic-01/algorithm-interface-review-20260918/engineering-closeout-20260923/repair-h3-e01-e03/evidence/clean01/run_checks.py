"""Standalone affected-contract regression; requires only prepared pinned blobs."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import unittest
from results import Results, freeze, MAX_ID

ROOT = Path(__file__).resolve().parent


def rejects(fn, message):
    try:
        fn()
    except ValueError as e:
        assert str(e) == message, str(e)
        return
    raise AssertionError('Expected rejection: '+message)


class Contracts(unittest.TestCase):
    def committed(self, config='A'):
        m = Results(); m.start()
        k = m.submit(0, 1023, 512, config)
        self.assertEqual(m.finish(k, 1024, config, status=True), 'COMMITTED')
        return m, k

    def test_revocation_late_error(self):
        for reason in ('CLIP', 'STOP', 'RESET'):
            with self.subTest(reason=reason):
                m, k = self.committed(); m.barrier(reason)
                if reason == 'CLIP':
                    m.begin_clean_interval()
                    k2 = m.submit(1, 2047, 512, 'A')
                    self.assertEqual(m.finish(k2, 2048, 'A', status=True), 'COMMITTED')
                m.finish(k, 2048, 'A', error=True)
                self.assertTrue(m.failed)
                self.assertTrue(m.entries[k]['ever_committed'])
                self.assertTrue(all(e['state']=='REVOKED' for e in m.entries.values()))
                rejects(lambda: m.submit(2, 2559, 512, 'A'), 'IDENTITY')
                rejects(m.start, 'SESSION_REUSE_OR_OVERFLOW')

    def test_old_session_callback(self):
        for reason in ('STOP', 'RESET'):
            m, k = self.committed(); m.barrier(reason); m.start()
            k2=m.submit(0, 1023, 512, 'B')
            m.finish(k, 1024, 'A', error=True)
            self.assertFalse(m.failed)
            self.assertEqual(m.audit[-1][0], 'OLD_SESSION_LATE_ERROR')
            self.assertEqual(m.finish(k2,1024,'B',status=True),'COMMITTED')

    def test_config_session(self):
        m,k=self.committed()
        rejects(lambda:m.submit(1,1535,512,'B'),'SESSION_CONFIG_CHANGE')
        m.barrier('CLIP');m.begin_clean_interval()
        rejects(lambda:m.submit(1,1535,512,'B'),'SESSION_CONFIG_CHANGE')
        m.barrier('STOP');m.start()
        k=m.submit(0,1535,512,'B')
        self.assertEqual(m.finish(k,1535,'B',status=True),'COMMITTED')

    def test_nested_snapshot(self):
        a={'config':'A','nested':{'lanes':[0,1,2,3]}}
        original={'config':'A','nested':{'lanes':[0,1,2,3]}}
        m=Results();m.start();k=m.submit(0,1023,512,a)
        a['nested']['lanes'][0]=99;a['config']='B'
        self.assertEqual(m.entries[k]['bindings'],freeze(original))
        rejects(lambda:m.submit(1,1535,512,a),'SESSION_CONFIG_CHANGE')
        self.assertEqual(m.finish(k,1024,original,status=True),'COMMITTED')
        original['nested']['lanes'].append(88)
        self.assertNotEqual(m.entries[k]['bindings'],freeze(original))
        self.assertTrue(m.entries[k]['ever_committed'])

    def test_mutation_wrong_completion(self):
        a={'config':'A'};m=Results();m.start();k=m.submit(0,1023,512,a)
        a['config']='B'
        self.assertEqual(m.finish(k,1024,a,status=True),'REVOKED')
        self.assertFalse(m.entries[k]['ever_committed'])

    def test_control_priority(self):
        m,k=self.committed()
        m.finish(k,1024,'A',stop=True,error=True,status=True)
        self.assertTrue(m.failed)
        m=Results();m.start();k=m.submit(0,1023,512,'A')
        self.assertEqual(m.finish(k,1024,'A',stop=True,status=True),'REVOKED')
        self.assertFalse(m.entries[k]['ever_committed'])

    def test_ttl_identity_bounds(self):
        m=Results();m.start()
        rejects(lambda:m.submit(0,MAX_ID,1,'A'),'TTL_OVERFLOW')
        k=m.submit(0,MAX_ID,0,'A')
        self.assertEqual(m.finish(k,MAX_ID,'A',status=True),'COMMITTED')
        self.assertEqual(m.finish(k,MAX_ID,'A',status=True),'NO_COMMIT')
        rejects(lambda:m.submit(0,1,0,'A'),'IDENTITY')
        m,k=self.committed();m.barrier('CLIP');m.interval=(1<<32)-1
        rejects(m.begin_clean_interval,'INTERVAL_OVERFLOW')
        m=Results(epoch_limit=1);m.start();m.barrier('STOP')
        rejects(m.start,'SESSION_REUSE_OR_OVERFLOW')

    def test_pending_error_and_expiry(self):
        for now,expected in ((1022,'INVALID_TIME'),(1535,'COMMITTED'),(1536,'EXPIRED')):
            m=Results();m.start();k=m.submit(0,1023,512,'A')
            self.assertEqual(m.finish(k,None,'A'),'WAIT')
            self.assertEqual(m.finish(k,now,'A',status=True),expected)
        m=Results();m.start();k=m.submit(0,1023,512,'A')
        m.finish(k,1024,'A',error=True)
        self.assertFalse(m.failed)
        self.assertEqual(m.audit[-1][0],'FRAME_ERROR')

    def test_binding_types(self):
        self.assertNotEqual(freeze(True),freeze(1))
        self.assertNotEqual(freeze([1]),freeze((1,)))
        rejects(lambda:freeze(1.0),'UNSUPPORTED_BINDING')
        rejects(lambda:freeze({1:'A'}),'UNSUPPORTED_BINDING')


def baseline(out):
    script=ROOT/'pinned/review/spec/adversarial.py'
    source=script.read_text(encoding='utf-8')
    # AST replaces ONLY the three local paths; pinned script remains unchanged.
    tree=ast.parse(source)
    paths={'OUT':out,'ep':ROOT/'pinned/engineering/source/engineering_model.py',
           'lp':ROOT/'pinned/logic/source/logic_adapter.py'}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in paths:
            node.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(str(paths[node.targets[0].id]))],keywords=[])
    ast.fix_missing_locations(tree)
    exec(compile(tree,str(script),'exec'),{'__file__':str(script),'__name__':'baseline_probe'})
    findings=json.loads((out/'adversarial-results.json').read_text())['cases']
    assert findings[0]['subsequent_commit']=='COMMITTED' and not findings[0]['failed']
    assert findings[1]['second']=='COMMITTED'
    assert findings[2]['actual']=='COMMITTED'
    # Reproduce E03's exact missing-file dependency without rerunning numeric tests.
    absent=ROOT/'pinned/engineering/increment-20260923/README.md'
    assert not absent.exists()
    try: absent.read_bytes()
    except FileNotFoundError as exc: (out/'e03-original-failure.txt').write_text(str(exc),encoding='utf-8')
    else: raise AssertionError('missing sibling was unexpectedly present')


if __name__=='__main__':
    out=ROOT/'run';out.mkdir(exist_ok=False)
    with (out/'full.log').open('w',encoding='utf-8') as log:
        sys.stdout=log;sys.stderr=log
        rows=json.loads((ROOT/'bindings.json').read_text())
        for row in rows:
            data=(ROOT/row['file']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==row['sha256'],row['file']
        print('Exact prepared inputs verified',len(rows),sys.version)
        baseline(out)
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
        summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                     original_defects_reproduced=3, board='NOT_RUN', realtime='REALTIME_BLOCKED')
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
