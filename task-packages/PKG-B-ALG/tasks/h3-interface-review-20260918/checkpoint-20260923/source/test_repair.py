import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import numpy as np
from compare_outputs import compare_json, compare_file, exact_array, exact_file
from prepare_exact import prepare, CHECKPOINT
from verify import check_mapping

class ComparisonTests(unittest.TestCase):
    def test_reported_roundoff(self):
        self.assertEqual(compare_json({'numeric_angle':10.298630873180613},
                                      {'numeric_angle':10.298630873180617})['float_differences'],1)

    def test_angle_outside_tolerance(self):
        with self.assertRaisesRegex(AssertionError,'/numeric_angle'):
            compare_json({'numeric_angle':10.0},{'numeric_angle':10.00000001})

    def test_near_zero_absolute_tolerance(self):
        compare_json({'numeric_angle':0.0},{'numeric_angle':1e-11})
        with self.assertRaises(AssertionError):compare_json({'numeric_angle':0.0},{'numeric_angle':2e-10})

    def test_power_scale_and_golden(self):
        a={'reports':[{'float_power':[1e9],'relative_power_difference':[0.003]}]}
        b=copy.deepcopy(a);b['reports'][0]['float_power'][0]+=1e-4
        compare_json(a,b,golden=True)
        b['reports'][0]['float_power'][0]+=0.1
        with self.assertRaises(AssertionError):compare_json(a,b,golden=True)

    def test_nonfinite_either_side(self):
        for v in [float('nan'),float('inf'),float('-inf')]:
            for a,b in [(v,0.0),(0.0,v),(v,v)]:
                with self.subTest(a=a,b=b),self.assertRaises(AssertionError):
                    compare_json({'numeric_angle':a},{'numeric_angle':b})

    def test_discrete_and_type_tampering(self):
        for a,b in [('LOCKED','HOLD'),(42,43),(True,False),(True,1),(42,42.0),
                    ('abc123','abc124'),(None,0),({'a':1},{'b':1}),([1],[1,2])]:
            with self.subTest(a=a,b=b),self.assertRaises(AssertionError):compare_json(a,b)

    def test_unlisted_float_and_integer_codes_strict(self):
        for a,b in [({'output_fraction':0.5},{'output_fraction':0.500000000000001}),
                    ({'features':{'peak':[4096.0]}},{'features':{'peak':[4096.000000000001]}}),
                    ({'numeric_angle':1},{'numeric_angle':2})]:
            with self.assertRaises(AssertionError):compare_json(a,b)

    def test_array_dtype_shape_and_code(self):
        a=np.array([1,2],dtype=np.int64);exact_array(a,a,'ok')
        for b in [a.astype(np.int32),a.reshape(1,2),a+1,a.astype(float)]:
            with self.assertRaises(AssertionError):exact_array(a,b,'mutated')

    def test_pcm_byte_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.wav';b=Path(d)/'b.wav';a.write_bytes(b'RIFF\x00\x01');b.write_bytes(a.read_bytes())
            exact_file(a,b);b.write_bytes(b'RIFF\x00\x02')
            with self.assertRaises(AssertionError):exact_file(a,b)

    def test_byte_difference_report_and_hash_string(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.json';b=Path(d)/'b.json'
            a.write_text('{"numeric_angle": 10.298630873180613, "hash": "abc"}')
            b.write_text('{"numeric_angle":10.298630873180617,"hash":"abc"}')
            r=compare_file(a,b);self.assertFalse(r['bytes_equal']);self.assertEqual(r['float_differences'],1)
            b.write_text('{"numeric_angle":10.298630873180617,"hash":"abd"}')
            with self.assertRaises(AssertionError):compare_file(a,b)

class PreparationTests(unittest.TestCase):
    def test_exact_blob_export_from_crlf_working_copy(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d)/'repo';repo.mkdir()
            def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.PIPE)
            git('init');git('config','core.autocrlf','false')
            path=repo/'docs/dep.txt';path.parent.mkdir();raw=b'one\ntwo\n';path.write_bytes(raw)
            cp=repo/CHECKPOINT;cp.mkdir(parents=True)
            (cp/'dependencies.json').write_text(json.dumps({'docs/dep.txt':hashlib.sha256(raw).hexdigest()}))
            git('add','.');git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','fixture')
            commit=git('rev-parse','HEAD').decode().strip()
            git('config','core.autocrlf','true');path.write_bytes(raw.replace(b'\n',b'\r\n'))
            out=Path(d)/'exact';receipt=prepare(repo,commit,out)
            self.assertEqual((out/'docs/dep.txt').read_bytes(),raw)
            self.assertEqual(path.read_bytes(),raw.replace(b'\n',b'\r\n'))
            self.assertEqual(receipt['commit'],commit)
            with self.assertRaises(FileExistsError):prepare(repo,commit,out)
            # Arbitrary corruption is not relabelled or repaired as newline conversion.
            path.write_bytes(b'corruption')
            with self.assertRaisesRegex(ValueError,'docs/dep.txt.*expected SHA256'):
                check_mapping(repo,{'docs/dep.txt':hashlib.sha256(raw).hexdigest()},'dependency')
            (cp/'dependencies.json').write_text(json.dumps({'docs/dep.txt':'0'*64}))
            git('add','.');git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','bad manifest')
            with self.assertRaisesRegex(ValueError,'dependency blob mismatch'):
                prepare(repo,'HEAD',Path(d)/'bad')

    def test_missing_dependency_diagnostic(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'missing.json.*actual SHA256=MISSING'):
                check_mapping(Path(d),{'missing.json':'0'*64},'dependency')

if __name__=='__main__':unittest.main()
