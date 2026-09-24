import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_receive_profile.py"
SPEC = importlib.util.spec_from_file_location("validate_receive_profile", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


class ReceiveProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        self.bit = self.artifacts / "design.bit"
        self.hwh = self.artifacts / "design.hwh"
        self.manifest = self.artifacts / "build-manifest.json"
        self.schema = self.root / "soundsight-record-v1.json"
        self.profile_path = self.root / "receive-profile.json"
        self.bit.write_bytes(b"synthetic-not-deployable-bit\n")
        self.schema.write_text(json.dumps({
            "schema_version": 1,
            "schema_id": "soundsight-record-v1",
            "record_bytes": 32,
            "words": ["id_lo", "id_hi", "mic0", "mic1", "mic2", "mic3", "flags", "reserved"],
        }), encoding="utf-8")
        self.write_hwh()
        self.profile = {
            "schema_version": 1,
            "profile_id": "synthetic-s2mm-receive",
            "profile_kind": "receive-only-s2mm",
            "board": {
                "board_name": "synthetic-zynq-board",
                "board_revision": "mock-r1",
                "device_part": "xc7z020clg400-2",
                "pynq_image": "synthetic-image-0",
                "compatibility_contains": ["synthetic,zynq-board"],
            },
            "overlay": {
                "bit": "artifacts/design.bit",
                "hwh": "artifacts/design.hwh",
                "manifest": "artifacts/build-manifest.json",
                "build_id": "synthetic-build-20260923",
                "interface_version": "receive-v1",
                "vivado_version": "2025.2",
                "required_interrupts": [],
            },
            "receive_contract": {
                "ip_name": "system_i/axi_dma_0",
                "mode": "simple",
                "s2mm_enabled": True,
                "mm2s_enabled": False,
                "scatter_gather": False,
                "s2mm_dre": False,
                "axis_data_width_bits": 32,
                "memory_data_width_bits": 64,
                "length_width_bits": 14,
                "max_transfer_bytes": 16383,
                "length_granularity_bytes": 4,
                "buffer_alignment_bytes": 64,
                "tlast_required": True,
                "completion_method": "polling",
                "cache_policy": {"rx": "invalidate"},
            },
            "control_contract": {
                "ip_name": "system_i/axi_gpio_run",
                "start_semantics": "level_high_run",
                "stop_semantics": "deassert_run_drain_full_packet",
                "status_semantics": "sticky_error_and_drained",
            },
            "payload_schema": {
                "path": "soundsight-record-v1.json",
                "sha256": self.hash(self.schema),
            },
            "receive_tests": [{
                "id": "capture-8000",
                "kind": "receive",
                "length_bytes": 8000,
                "timeout_seconds": 2.0,
            }],
        }
        self.write_manifest()
        self.write_profile()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write_hwh(self, *, include_dma: bool = True, overrides: dict[str, int] | None = None,
                  part: str | None = "xc7z020clg400-2", decoy: str | None = None) -> None:
        values = {
            "C_INCLUDE_S2MM": 1,
            "C_INCLUDE_MM2S": 0,
            "C_INCLUDE_SG": 0,
            "C_INCLUDE_S2MM_DRE": 0,
            "C_S_AXIS_S2MM_TDATA_WIDTH": 32,
            "C_M_AXI_S2MM_DATA_WIDTH": 64,
            "C_SG_LENGTH_WIDTH": 14,
        }
        values.update(overrides or {})
        dma = ""
        if include_dma:
            params = "".join(f'<PARAMETER NAME="{key}" VALUE="{value}"/>' for key, value in values.items())
            dma = (f'<MODULE FULLNAME="/system_i/axi_dma_0" MODTYPE="axi_dma" '
                   f'VLNV="xilinx.com:ip:axi_dma:7.1"><PARAMETERS>{params}</PARAMETERS></MODULE>')
        part_attribute = "" if part is None else f' PART="{part}"'
        decoy_module = ("" if decoy is None else
                        f'<MODULE FULLNAME="/unrelated_decoy" COMMENT="{decoy}"/>')
        self.hwh.write_text(
            f'<HW{part_attribute}>'
            + dma
            + '<MODULE FULLNAME="/system_i/axi_gpio_run"/>'
            + decoy_module
            + '</HW>',
            encoding="utf-8",
        )

    def write_manifest(self) -> None:
        self.manifest.write_text(json.dumps({
            "build_id": "synthetic-build-20260923",
            "interface_version": "receive-v1",
            "vivado_version": "2025.2",
            "device_part": self.profile["board"]["device_part"],
            "bit": {"file": "design.bit", "sha256": self.hash(self.bit)},
            "hwh": {"file": "design.hwh", "sha256": self.hash(self.hwh)},
            "payload_schema": {"file": self.schema.name, "sha256": self.hash(self.schema)},
        }), encoding="utf-8")

    def write_profile(self) -> None:
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")

    def run_validator(self) -> tuple[dict, int]:
        self.write_profile()
        return VALIDATOR.validate(self.profile_path)

    def codes(self, report: dict) -> set[str]:
        return {item["code"] for item in report["issues"]}

    def test_valid_s2mm_only_profile_passes_static_validation(self) -> None:
        report, code = self.run_validator()
        self.assertEqual(0, code, report)
        self.assertEqual("PASS", report["status"])
        self.assertEqual("static", report["evidence_level"])
        self.assertFalse(report["board_execution"])

    def test_authoritative_part_accepts_case_and_edge_whitespace(self) -> None:
        self.profile["board"]["device_part"] = "  xc7z020clg400-2  "
        self.write_hwh(part="  XC7Z020CLG400-2  ")
        self.write_manifest()
        report, code = self.run_validator()
        self.assertEqual(0, code, report)
        self.assertNotIn("HWH_DEVICE_PART", self.codes(report))

    def test_wrong_part_with_unrelated_attribute_decoy_is_rejected(self) -> None:
        self.write_hwh(part="xc7z010clg400-2", decoy="xc7z020clg400-2")
        self.write_manifest()
        report, code = self.run_validator()
        self.assertEqual(1, code, report)
        self.assertIn("HWH_DEVICE_PART", self.codes(report))

    def test_missing_part_with_unrelated_attribute_decoy_is_rejected(self) -> None:
        self.write_hwh(part=None, decoy="xc7z020clg400-2")
        self.write_manifest()
        report, code = self.run_validator()
        self.assertEqual(1, code, report)
        self.assertIn("HWH_DEVICE_PART", self.codes(report))

    def test_part_substring_and_superstring_are_rejected(self) -> None:
        for part in ("xc7z020clg400", "xc7z020clg400-2-extra"):
            with self.subTest(part=part):
                self.write_hwh(part=part)
                self.write_manifest()
                report, code = self.run_validator()
                self.assertEqual(1, code, report)
                self.assertIn("HWH_DEVICE_PART", self.codes(report))

    def test_missing_or_disabled_s2mm_is_rejected(self) -> None:
        for mode in ("missing", "disabled"):
            with self.subTest(mode=mode):
                self.write_hwh(include_dma=mode != "missing",
                               overrides={"C_INCLUDE_S2MM": 0} if mode == "disabled" else None)
                self.write_manifest()
                report, code = self.run_validator()
                self.assertEqual(1, code, report)
                expected = "HWH_S2MM_INSTANCE" if mode == "missing" else "HWH_C_INCLUDE_S2MM"
                self.assertIn(expected, self.codes(report))

    def test_named_parameter_decoy_is_not_axi_dma(self) -> None:
        text_value = self.hwh.read_text(encoding="utf-8")
        text_value = text_value.replace('MODTYPE="axi_dma" VLNV="xilinx.com:ip:axi_dma:7.1"',
                                        'MODTYPE="not_dma" VLNV="example.invalid:ip:not_dma:1.0"')
        self.hwh.write_text(text_value, encoding="utf-8")
        self.write_manifest()
        report, code = self.run_validator()
        self.assertEqual(1, code, report)
        self.assertIn("HWH_S2MM_IP_TYPE", self.codes(report))

    def test_mode_and_dre_mismatches_are_rejected(self) -> None:
        for field, value, expected in (
            ("mode", "scatter-gather", "CONTRACT_MODE"),
            ("s2mm_dre", True, "CONTRACT_S2MM_DRE"),
            ("scatter_gather", True, "CONTRACT_SCATTER_GATHER"),
        ):
            with self.subTest(field=field):
                original = self.profile["receive_contract"][field]
                self.profile["receive_contract"][field] = value
                report, code = self.run_validator()
                self.assertEqual(1, code, report)
                self.assertIn(expected, self.codes(report))
                self.profile["receive_contract"][field] = original

    def test_axis_memory_and_length_field_mismatches_are_rejected(self) -> None:
        for field, value, expected in (
            ("axis_data_width_bits", 64, "HWH_C_S_AXIS_S2MM_TDATA_WIDTH"),
            ("memory_data_width_bits", 32, "HWH_C_M_AXI_S2MM_DATA_WIDTH"),
            ("length_width_bits", 13, "HWH_C_SG_LENGTH_WIDTH"),
            ("max_transfer_bytes", 16380, "MAX_TRANSFER_LENGTH"),
        ):
            with self.subTest(field=field):
                original = self.profile["receive_contract"][field]
                self.profile["receive_contract"][field] = value
                report, code = self.run_validator()
                self.assertEqual(1, code, report)
                self.assertIn(expected, self.codes(report))
                self.profile["receive_contract"][field] = original

    def test_payload_schema_hash_mismatch_is_rejected(self) -> None:
        self.profile["payload_schema"]["sha256"] = "0" * 64
        report, code = self.run_validator()
        self.assertEqual(1, code, report)
        self.assertIn("PAYLOAD_SCHEMA_HASH", self.codes(report))

    def test_bit_hwh_manifest_build_mismatches_are_rejected(self) -> None:
        original_manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        cases = (
            ("build_id", lambda value: value.__setitem__("build_id", "wrong-build"), "MANIFEST_BUILD_ID"),
            ("bit_hash", lambda value: value["bit"].__setitem__("sha256", "0" * 64), "MANIFEST_BIT_HASH"),
            ("hwh_hash", lambda value: value["hwh"].__setitem__("sha256", "0" * 64), "MANIFEST_HWH_HASH"),
        )
        for name, mutate, expected in cases:
            with self.subTest(name=name):
                value = copy.deepcopy(original_manifest)
                mutate(value)
                self.manifest.write_text(json.dumps(value), encoding="utf-8")
                report, code = self.run_validator()
                self.assertEqual(1, code, report)
                self.assertIn(expected, self.codes(report))
        self.manifest.write_text(json.dumps(original_manifest), encoding="utf-8")

    def test_tlast_control_and_cache_contract_fail_closed(self) -> None:
        cases = (
            ("receive_contract", "tlast_required", False, "CONTRACT_TLAST_REQUIRED"),
            ("receive_contract", "cache_policy", {"rx": "none"}, "RX_CACHE_POLICY"),
            ("control_contract", "stop_semantics", "drop_immediately", "CONTROL_STOP_SEMANTICS"),
        )
        for scope, field, value, expected in cases:
            with self.subTest(field=field):
                original = self.profile[scope][field]
                self.profile[scope][field] = value
                report, code = self.run_validator()
                self.assertEqual(1, code, report)
                self.assertIn(expected, self.codes(report))
                self.profile[scope][field] = original

    def test_receive_length_must_fit_limit_and_axis_beats(self) -> None:
        for length, expected in ((16384, "RECEIVE_TEST_MAX"), (8002, "RECEIVE_TEST_GRANULARITY")):
            with self.subTest(length=length):
                self.profile["receive_tests"][0]["length_bytes"] = length
                report, code = self.run_validator()
                self.assertEqual(1, code, report)
                self.assertIn(expected, self.codes(report))

    def test_absolute_artifact_path_is_rejected(self) -> None:
        self.profile["overlay"]["bit"] = str(self.bit.resolve())
        report, code = self.run_validator()
        self.assertEqual(1, code, report)
        self.assertIn("ABSOLUTE_PATH", self.codes(report))


if __name__ == "__main__":
    unittest.main()
