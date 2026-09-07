from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_profile.py"
SPEC = importlib.util.spec_from_file_location("validate_profile", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
GOLDEN_SCRIPT = Path(__file__).parents[1] / "scripts" / "compare_golden.py"
GOLDEN_SPEC = importlib.util.spec_from_file_location("compare_golden", GOLDEN_SCRIPT)
assert GOLDEN_SPEC and GOLDEN_SPEC.loader
GOLDEN = importlib.util.module_from_spec(GOLDEN_SPEC)
GOLDEN_SPEC.loader.exec_module(GOLDEN)


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        artifacts = self.root / "artifacts"
        artifacts.mkdir()
        self.bit = artifacts / "demo.bit"
        self.hwh = artifacts / "demo.hwh"
        self.manifest = artifacts / "manifest.json"
        self.profile_path = self.root / "profile.json"
        self.evidence_path = self.root / "evidence.json"
        self.bit.write_bytes(b"mock-bit-for-static-validation-only\n")
        self.hwh.write_text(
            "<HW PART='xc7z020clg400-1'><MODULE INSTANCE='control_regs' NAME='control_regs'/>"
            "<MODULE INSTANCE='axi_dma_0' NAME='axi_dma_0'/></HW>",
            encoding="utf-8",
        )
        self.profile = {
            "schema_version": 1,
            "profile_id": "mock-board-overlay-v1",
            "board": {
                "board_name": "mock-board",
                "board_revision": "rev-a",
                "device_part": "xc7z020clg400-1",
                "pynq_image": "mock-image-v1",
                "compatibility_contains": ["mock,board"],
            },
            "overlay": {
                "bit": "artifacts/demo.bit",
                "hwh": "artifacts/demo.hwh",
                "manifest": "artifacts/manifest.json",
                "build_id": "mock-build-1",
                "interface_version": 7,
                "vivado_version": "2025.2",
                "required_ip": ["control_regs", "axi_dma_0"],
            },
            "register_contract": {
                "ip_name": "control_regs",
                "address_span_bytes": 4096,
                "registers": [
                    {"name": "hardware_id", "offset": 0, "width_bits": 32, "access": "ro"},
                    {"name": "interface_version", "offset": 4, "width_bits": 32, "access": "ro"},
                ],
                "identity": [
                    {"register": "hardware_id", "expected": 0x12345678, "mask": 0xFFFFFFFF},
                    {"register": "interface_version", "expected": 7, "mask": 0xFFFFFFFF},
                ],
            },
            "dma_contract": {
                "ip_name": "axi_dma_0",
                "mode": "simple",
                "mm2s_channel": "sendchannel",
                "s2mm_channel": "recvchannel",
                "stream_data_width_bits": 32,
                "buffer_alignment_bytes": 64,
                "max_transfer_bytes": 8192,
                "cache_policy": {"tx": "flush", "rx": "invalidate"},
                "tlast_required": True,
            },
            "self_tests": [
                {
                    "id": "loopback-4k",
                    "kind": "loopback",
                    "length_bytes": 4096,
                    "pattern": "counter8",
                    "timeout_seconds": 2.0,
                    "golden": "exact",
                }
            ],
            "acceptance": {
                "minimum_throughput_bytes_per_second": 1000,
                "maximum_latency_seconds": 1.0,
                "timing": {"minimum_wns_ns": 0.0},
                "resources": {"lut_max": 1000, "ff_max": 1000, "bram_max": 10, "dsp_max": 10},
            },
        }
        self.write_manifest()
        self.write_profile()
        self.evidence = {
            "evidence_level": "mock",
            "overlay_downloaded": False,
            "artifact_hashes": {"bit": self.hash(self.bit), "hwh": self.hash(self.hwh)},
            "register_reads": {"hardware_id": 0x12345678, "interface_version": 7},
            "dma_runs": [
                {
                    "id": "loopback-4k",
                    "length_bytes": 4096,
                    "timed_out": False,
                    "dma_error": False,
                    "mm2s_completed": True,
                    "s2mm_completed": True,
                    "tlast_observed": True,
                    "cache_operations": ["tx.flush", "rx.invalidate"],
                    "mismatch_count": 0,
                }
            ],
            "performance": {"minimum_throughput_bytes_per_second": 2000, "maximum_latency_seconds": 0.5},
            "timing": {"wns_ns": 0.25, "source": "mock timing report"},
            "resources": {"lut": 10, "ff": 20, "bram": 1, "dsp": 1, "source": "mock utilization report"},
        }
        self.write_evidence()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write_manifest(self) -> None:
        self.manifest.write_text(
            json.dumps(
                {
                    "build_id": "mock-build-1",
                    "interface_version": 7,
                    "vivado_version": "2025.2",
                    "device_part": "xc7z020clg400-1",
                    "bit_sha256": self.hash(self.bit),
                    "hwh_sha256": self.hash(self.hwh),
                }
            ),
            encoding="utf-8",
        )

    def write_profile(self) -> None:
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")

    def write_evidence(self) -> None:
        self.evidence_path.write_text(json.dumps(self.evidence), encoding="utf-8")

    def test_valid_profile_and_mock_evidence_pass_offline(self) -> None:
        report, code = VALIDATOR.validate(self.profile_path, self.evidence_path, "offline")
        self.assertEqual(0, code, report)
        self.assertEqual("PASS", report["status"])
        self.assertEqual("mock", report["evidence_level"])

    def test_manifest_hash_tamper_fails(self) -> None:
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["bit_sha256"] = "0" * 64
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        report, code = VALIDATOR.validate(self.profile_path, None, "offline")
        self.assertEqual(1, code)
        self.assertIn("BIT_HASH", {item["code"] for item in report["issues"]})

    def test_unaligned_dma_length_fails(self) -> None:
        self.profile["self_tests"][0]["length_bytes"] = 4098
        self.write_profile()
        report, code = VALIDATOR.validate(self.profile_path, None, "offline")
        self.assertEqual(1, code)
        codes = {item["code"] for item in report["issues"]}
        self.assertIn("DMA_LENGTH_BEAT", codes)
        self.assertIn("DMA_LENGTH_ALIGNMENT", codes)

    def test_mock_cannot_claim_hardware(self) -> None:
        report, code = VALIDATOR.validate(self.profile_path, self.evidence_path, "hardware")
        self.assertEqual(1, code)
        self.assertIn("FALSE_HARDWARE_CLAIM", {item["code"] for item in report["issues"]})

    def test_golden_comparison_detects_first_mismatch(self) -> None:
        result = GOLDEN.compare_bytes(b"\x00\x01\x02\x03", b"\x00\x01\x09\x03")
        self.assertEqual(1, result["mismatch_count"])
        self.assertEqual(2, result["first_mismatch"])


if __name__ == "__main__":
    unittest.main()
