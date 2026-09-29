"""I22-B-01 static address-alignment contract tests (synthetic inputs only).

The expected address rule comes from PG021 S2MM_DA without DRE: the destination
address is aligned to the S2MM memory-mapped width, independently of length.
"""

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
EXAMPLE = SKILL / "references" / "example-receive"
VALIDATOR = SKILL / "scripts" / "validate_receive_profile.py"


class I22B01AlignmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.example = self.root / "references" / "example-receive"
        self.example.mkdir(parents=True)
        for name in ("design.bit", "design.hwh", "build-manifest.json", "receive-profile.json"):
            shutil.copyfile(EXAMPLE / name, self.example / name)
        shutil.copyfile(SKILL / "references" / "soundsight-record-v1.json",
                        self.root / "references" / "soundsight-record-v1.json")
        self.original_profile = json.loads((self.example / "receive-profile.json").read_text(encoding="utf-8"))
        self.original_hwh = (self.example / "design.hwh").read_text(encoding="utf-8")
        self.original_manifest = json.loads((self.example / "build-manifest.json").read_text(encoding="utf-8"))

    def run_case(self, name, *, alignment=64, memory_width=64, dre=False, length=8000):
        profile = copy.deepcopy(self.original_profile)
        contract = profile["receive_contract"]
        if alignment is None:
            del contract["buffer_alignment_bytes"]
        else:
            contract["buffer_alignment_bytes"] = alignment
        if memory_width is None:
            del contract["memory_data_width_bits"]
        else:
            contract["memory_data_width_bits"] = memory_width
        contract["s2mm_dre"] = dre
        profile["receive_tests"][0]["length_bytes"] = length
        profile_path = self.example / "receive-profile.json"
        profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")

        hwh = self.original_hwh
        if dre:
            hwh = hwh.replace('NAME="C_INCLUDE_S2MM_DRE" VALUE="0"',
                              'NAME="C_INCLUDE_S2MM_DRE" VALUE="1"')
        if type(memory_width) is int and memory_width > 0:
            hwh = hwh.replace('NAME="C_M_AXI_S2MM_DATA_WIDTH" VALUE="64"',
                              f'NAME="C_M_AXI_S2MM_DATA_WIDTH" VALUE="{memory_width}"')
        hwh_path = self.example / "design.hwh"
        hwh_path.write_text(hwh, encoding="utf-8")
        manifest = copy.deepcopy(self.original_manifest)
        manifest["hwh"]["sha256"] = hashlib.sha256(hwh_path.read_bytes()).hexdigest()
        (self.example / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        report_path = self.root / f"{name}.json"
        command = [sys.executable, "-B", str(VALIDATOR), "--profile", str(profile_path),
                   "--output", str(report_path)]
        completed = subprocess.run(command, cwd=SKILL, text=True, capture_output=True, check=False)
        self.assertTrue(report_path.is_file(), (command, completed.stdout, completed.stderr))
        return completed.returncode, json.loads(report_path.read_text(encoding="utf-8"))

    def assert_result(self, name, expected_exit, expected_first, **changes):
        exit_code, report = self.run_case(name, **changes)
        self.assertEqual(expected_exit, exit_code, report)
        self.assertEqual("PASS" if expected_exit == 0 else "FAIL", report["status"], report)
        issues = [item["code"] for item in report["issues"]]
        self.assertEqual(expected_first, issues[0] if issues else None, report)
        self.assertEqual("static", report["evidence_level"])
        self.assertIs(report["board_execution"], False)
        return report

    def test_no_dre_address_granularity_from_memory_width(self):
        for alignment in (8, 16, 64):
            with self.subTest(alignment=alignment):
                self.assert_result(f"alignment-{alignment}", 0, None, alignment=alignment)
        for alignment in (1, 4, 12):
            with self.subTest(alignment=alignment):
                report = self.assert_result(f"alignment-{alignment}", 1,
                                            "S2MM_ADDRESS_ALIGNMENT", alignment=alignment)
                self.assertEqual(["S2MM_ADDRESS_ALIGNMENT"],
                                 [item["code"] for item in report["issues"]])

    def test_acceptance_checker_negative_canary(self):
        # An obsolete checker that treats 1-byte alignment as PASS must fail.
        exit_code, report = self.run_case("canary-observed-reject", alignment=1)
        self.assertEqual(1, exit_code, report)
        self.assertEqual(["S2MM_ADDRESS_ALIGNMENT"],
                         [item["code"] for item in report["issues"]])
        with self.assertRaises(AssertionError):
            self.assert_result("canary-wrong-pass", 0, None, alignment=1)

    def test_existing_contract_precedes_new_address_gate(self):
        for name, changes, first in (
            ("alignment-bool", {"alignment": True}, "CONTRACT_INTEGER"),
            ("alignment-zero", {"alignment": 0}, "CONTRACT_INTEGER"),
            ("alignment-missing", {"alignment": None}, "CONTRACT_INTEGER"),
            ("width-bool", {"memory_width": True}, "CONTRACT_INTEGER"),
            ("width-zero", {"memory_width": 0}, "CONTRACT_INTEGER"),
            ("width-missing", {"memory_width": None}, "CONTRACT_INTEGER"),
            ("width-nonbyte", {"memory_width": 12}, "BYTE_WIDTH"),
            ("dre", {"alignment": 1, "dre": True}, "CONTRACT_S2MM_DRE"),
        ):
            with self.subTest(name=name):
                report = self.assert_result(name, 1, first, **changes)
                self.assertNotIn("S2MM_ADDRESS_ALIGNMENT",
                                 [item["code"] for item in report["issues"]])

    def test_address_and_length_are_separate(self):
        # 96 is valid for 4-byte AXIS beats and length granularity, although
        # it is not a multiple of the declared 64-byte address alignment.
        report = self.assert_result("length-96", 0, None, alignment=64, length=96)
        profile = json.loads((self.example / "receive-profile.json").read_text(encoding="utf-8"))
        self.assertEqual(96, profile["receive_tests"][0]["length_bytes"])
        self.assertEqual([], report["issues"])
        for code in ("RECEIVE_TEST_LENGTH", "RECEIVE_TEST_GRANULARITY", "RECEIVE_TEST_BEAT"):
            self.assertIn((code, "PASS"),
                          {(item["code"], item["status"]) for item in report["checks"]})


if __name__ == "__main__":
    unittest.main()
