"""Independent local counterexample; MOCKED tools, never a board-failure claim."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

ENTRY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENTRY))
from test_build_current import SafetyTests

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    old_path = ENTRY / "evidence/run04/build_current.py"
    # Frozen run04 matches the reviewed 050d06 entry, never import mutable code.
    expected = (ENTRY / "evidence/run04/build_current.py").read_bytes()
    assert hashlib.sha256(expected).hexdigest() == "b6414b73897fb7c3a518379c749469d20e7b4d7bd146c2a3760ed6cc927b477c"
    spec = importlib.util.spec_from_file_location("legacy_050d06", old_path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    fixture = SafetyTests()
    fixture.setUp()
    try:
        source = args.source.read_text(encoding="utf-8")
        before = "#define BASE ((UINTPTR)0x01000000U)"
        assert source.count(before) == 1
        mutated = source.replace(before, "#define BASE ((UINTPTR)0x00100000U)")
        (fixture.ps / "main_four_capture.c").write_text(mutated, encoding="utf-8")
        fixture.args.output = args.output
        plan = old.preflight(fixture.args)

        def fake_tool(argv, out, name, cwd=None):
            if name == "hardware":
                (out / "artifacts/hw").mkdir(parents=True)
                shutil.copyfile(fixture.xsa, out / "artifacts/hw/system_c_adapter.xsa")
                (out / "reports").mkdir()
                (out / "reports/timing-values.txt").write_text("setup_slack=4.640\nhold_slack=0.056\n")
                (out / "reports/timing-summary.rpt").write_text(
                    "4.640 0.000 0 41425 0.056 0.000 0 41425 3.000 0.000 0 8391\n")
            if name == "ps-build":
                (cwd / "four_mic_capture.elf").write_bytes(b"MOCK_TOOL_OUTPUT_NOT_AN_ELF")
                (cwd / "four_mic_capture.map").write_text("MOCK ONLY; end=0x00112630")
            if name == "ps-symbols":
                return "00112630 B end\n"
            return "MOCK ONLY\n"

        with patch.object(old, "run_command", side_effect=fake_tool):
            result = old.build(plan)
        report = {
            "kind": "INDEPENDENT_RECONSTRUCTION_WITH_MOCKED_TOOL_RESULTS",
            "not_original_B_counterexample": True, "board_test": "NOT_RUN",
            "legacy_commit": "050d06f5dc6fed4fa476e72fa416e9736bc7fef3",
            "legacy_entry_sha256": hashlib.sha256(expected).hexdigest(),
            "source_version_string_unchanged": True,
            "mutated_BASE": "0x00100000", "simulated_program_end": "0x00112630",
            "actual_overlap_in_fixture": True, "legacy_result": result["status"],
            "false_positive_reproduced": result["status"] == "BUILD_PASS_NOT_BOARD_TEST"
        }
        old.write_json(args.output / "counterexample-summary.json", report)
        print(json.dumps(report, indent=2))
        return 0 if report["false_positive_reproduced"] else 1
    finally:
        fixture.doCleanups()

if __name__ == "__main__":
    raise SystemExit(main())
