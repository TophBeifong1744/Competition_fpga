"""Isolated byte-fixture tests; no project files, remote or hardware are changed."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from verify_package import verify


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skill-manifest-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.content = b"versioned original\r\n"
        (self.root / "data.bin").write_bytes(self.content)
        self.row = {"path": "data.bin", "bytes": len(self.content),
                    "sha256": hashlib.sha256(self.content).hexdigest()}
        self.manifest = {"schema_version": 1, "package_version": "test-1", "files": [self.row]}
        self.save()

    def save(self):
        (self.root / "MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_valid(self):
        self.assertEqual(verify(self.root)["checked_files"], 1)

    def test_tamper_then_restore(self):
        (self.root / "data.bin").write_bytes(b"versioned modified\r\n")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify(self.root)
        (self.root / "data.bin").write_bytes(self.content)
        self.assertEqual(verify(self.root)["status"], "PASS_PACKAGE_INTEGRITY_ONLY")

    def test_line_endings_are_not_silently_normalized(self):
        (self.root / "data.bin").write_bytes(self.content.replace(b"\r\n", b"\n"))
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify(self.root)

    def test_missing_file(self):
        (self.root / "data.bin").unlink()
        with self.assertRaisesRegex(ValueError, "Missing file"):
            verify(self.root)

    def test_unlisted_file(self):
        (self.root / "unreviewed.log").write_bytes(b"not approved")
        with self.assertRaisesRegex(ValueError, "File-set mismatch"):
            verify(self.root)

    def test_traversal(self):
        self.row["path"] = "../data.bin"
        self.save()
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            verify(self.root)

    def test_duplicate_casefold(self):
        self.manifest["files"].append(dict(self.row, path="DATA.bin"))
        self.save()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            verify(self.root)

    def test_invalid_hash(self):
        self.row["sha256"] = "not-a-hash"
        self.save()
        with self.assertRaisesRegex(ValueError, "Invalid SHA"):
            verify(self.root)

    def test_empty_manifest(self):
        self.manifest["files"] = []
        self.save()
        with self.assertRaisesRegex(ValueError, "Empty"):
            verify(self.root)

    def test_bad_json(self):
        (self.root / "MANIFEST.json").write_bytes(b"{")
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_cli_success_failure_and_repair(self):
        script = Path(__file__).with_name("verify_package.py")
        def run():
            return subprocess.run([sys.executable, "-B", str(script), str(self.root)],
                                  capture_output=True, text=True, check=False)
        self.assertEqual(run().returncode, 0)
        (self.root / "data.bin").write_bytes(b"broken")
        rejected = run()
        self.assertEqual(rejected.returncode, 1)
        self.assertEqual(json.loads(rejected.stdout)["status"], "FAIL_PACKAGE_INTEGRITY")
        (self.root / "data.bin").write_bytes(self.content)
        self.assertEqual(run().returncode, 0)


if __name__ == "__main__":
    unittest.main()
