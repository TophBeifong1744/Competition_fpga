import importlib.util
from pathlib import Path
import tempfile,unittest
HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('continuous_entry',HERE/'run.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
class EntryTests(unittest.TestCase):
    def test_refuse_existing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'existing';p.mkdir();(p/'proof').write_bytes(b'KEEP')
            with self.assertRaises(entry.safe.BuildError):entry.fresh(p)
            self.assertEqual((p/'proof').read_bytes(),b'KEEP')
    def test_refuse_source(self):
        with self.assertRaises(entry.safe.BuildError):entry.fresh(HERE/'ps/new')
    def test_refuse_missing_parent(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(entry.safe.BuildError):entry.fresh(Path(d)/'missing/new')
    def test_refuse_relative(self):
        with self.assertRaises(entry.safe.BuildError):entry.fresh('new')
    def test_refuse_metachar(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(entry.safe.BuildError):entry.fresh(Path(d)/'bad&name')
    def test_exclusive_copy(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b';a.write_bytes(b'A');b.write_bytes(b'B')
            with self.assertRaises(entry.safe.BuildError):entry.copy(a,b)
            self.assertEqual(b.read_bytes(),b'B')
    def test_copy_and_hash(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b';a.write_bytes(b'A');entry.copy(a,b)
            self.assertEqual(entry.safe.sha(a),entry.safe.sha(b))
    def test_manifest_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_bytes(b'A');entry.manifest(p)
            with self.assertRaises(FileExistsError):entry.manifest(p)
if __name__=='__main__':unittest.main(verbosity=2)
