import copy, tempfile, unittest
from collections import Counter
from pathlib import Path
import numpy as np
import reference_inputs as r

class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.refs=r.References()
    def test_coverage(self):
        counts=Counter(x['use'] for x in r.required())
        self.assertEqual(counts,{'audit-narrowband-guard-01':10,'audit-subband-confidence-01':8,'audit-leave-band-out-01':8,'audit-effective-perturbation-01':8,'stable-original':26,'stable-dry':26})
    def test_every_reference_bound_and_readable(self):
        for row in self.refs.index['coverage']:
            m=r.historical(row);a,meta=self.refs.make_rir(row['plan'],m['direction'],m['room'],m['seed'])
            self.assertEqual(r.s.array_hash(a),m['rir_sha256'])
            for k in ['source_m','support_first','support_last','paths','rir_sha256']:self.assertEqual(meta[k],m[k])
    def test_unknown_inputs_fail(self):
        row=r.required()[0];m=r.historical(row)
        with self.assertRaisesRegex(AssertionError,'UNDECLARED_REFERENCE_INPUT'):self.refs.make_rir(row['plan'],m['direction'],m['room'],-1)
    def test_corrupt_file_fails(self):
        record=next(iter(self.refs.records.values()))
        with tempfile.TemporaryDirectory() as folder:
            stub=r.References.__new__(r.References);stub.directory=Path(folder)
            data=bytearray((self.refs.directory/record['file']).read_bytes());data[-1]^=1
            (stub.directory/record['file']).write_bytes(data)
            with self.assertRaisesRegex(AssertionError,'reference file bytes'):stub.load(record)
    def test_rehashed_container_cannot_change_historical_array(self):
        record=copy.deepcopy(next(iter(self.refs.records.values())))
        with tempfile.TemporaryDirectory() as folder:
            stub=r.References.__new__(r.References);stub.directory=Path(folder)
            a=self.refs.load(record);a.flat[0]=a.flat[0]+1
            path=stub.directory/record['file'];np.savez_compressed(path,rir=a);record['file_sha256']=r.sha(path)
            with self.assertRaisesRegex(AssertionError,'reference array hash'):stub.load(record)
    def test_exact_input_assertion_remains(self):
        m=r.historical(r.required()[0]);bad=copy.deepcopy(m);bad['input_sha256']='0'*64
        diff=r.common.Differences()
        with self.assertRaisesRegex(AssertionError,'UNSUPPORTED_EXACT_INPUT_ENVIRONMENT'):diff.input(m,bad)
    def test_export_environment_and_sources(self):
        ix=self.refs.index
        self.assertEqual(r.sha(self.refs.directory/'environment.json'),ix['environment_sha256'])
        for path,h in ix['sources'].items():self.assertEqual(r.sha(r.ROOT/path),h)

if __name__=='__main__':unittest.main(verbosity=2)
