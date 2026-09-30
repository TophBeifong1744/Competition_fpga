#!/usr/bin/env python3
"""Fail-closed static validator for an S2MM-only receive build profile.

This tool validates declarative artifacts only.  It never imports PYNQ,
downloads an overlay, allocates a DMA buffer, or claims board execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HEX64 = re.compile(r"^[0-9a-f]{64}$")
HWH_PARAMETERS = {
    "s2mm_enabled": "C_INCLUDE_S2MM",
    "mm2s_enabled": "C_INCLUDE_MM2S",
    "scatter_gather": "C_INCLUDE_SG",
    "s2mm_dre": "C_INCLUDE_S2MM_DRE",
    "axis_data_width_bits": "C_S_AXIS_S2MM_TDATA_WIDTH",
    "memory_data_width_bits": "C_M_AXI_S2MM_DATA_WIDTH",
    "length_width_bits": "C_SG_LENGTH_WIDTH",
}


class Result:
    def __init__(self, profile_id: str = "unknown") -> None:
        self.profile_id = profile_id
        self.checks: list[dict[str, Any]] = []
        self.issues: list[dict[str, str]] = []
        self.hashes: dict[str, str] = {}
        self.summary: dict[str, Any] = {}

    def check(self, code: str, ok: bool, message: str) -> None:
        self.checks.append({"code": code, "status": "PASS" if ok else "FAIL", "message": message})
        if not ok:
            self.error(code, message)

    def error(self, code: str, message: str) -> None:
        self.issues.append({"severity": "ERROR", "code": code, "message": message})

    @property
    def failed(self) -> bool:
        return bool(self.issues)

    def report(self) -> dict[str, Any]:
        return {
            "tool": "pynq-overlay-dma-validation/validate_receive_profile.py",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "profile_id": self.profile_id,
            "profile_kind": "receive-only-s2mm",
            "evidence_level": "static",
            "board_execution": False,
            "status": "FAIL" if self.failed else "PASS",
            "artifact_hashes": self.hashes,
            "contract_summary": self.summary,
            "checks": self.checks,
            "issues": self.issues,
        }


def read_json(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON value is forbidden: {value}")

    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def child_object(parent: dict[str, Any], name: str, result: Result) -> dict[str, Any]:
    value = parent.get(name)
    if not isinstance(value, dict):
        result.error("FIELD_REQUIRED", f"{name} must be an object")
        return {}
    return value


def text(parent: dict[str, Any], name: str, scope: str, result: Result) -> str:
    value = parent.get(name)
    if not isinstance(value, str) or not value.strip() or value.startswith("replace-with-"):
        result.error("FIELD_REQUIRED", f"{scope}.{name} must be resolved")
        return ""
    return value


def exact_int(value: Any) -> int | None:
    return value if type(value) is int else None


def resolve(base: Path, raw: Any, field: str, result: Result) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        result.error("PATH_REQUIRED", f"{field} must be a non-empty path")
        return None
    path = Path(raw)
    if path.is_absolute():
        result.error("ABSOLUTE_PATH", f"{field} must be relative for a portable candidate")
        return None
    return (base / path).resolve()


def normalize_instance(name: str) -> str:
    return name.strip().lstrip("/")


def normalize_part(value: Any) -> str:
    """Normalize a declared device part without permitting partial matches."""
    return value.strip().casefold() if isinstance(value, str) else ""


def parse_hwh(path: Path, result: Result) -> tuple[str | None, dict[str, dict[str, str]]]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        result.error("HWH_PARSE", f"cannot parse HWH XML: {exc}")
        return None, {}
    # Vivado records the authoritative device in the HWH root PART attribute.
    # Never infer it from MODULE/PARAMETER metadata or arbitrary attribute text.
    part = root.attrib.get("PART")
    modules: dict[str, dict[str, str]] = {}
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].upper() != "MODULE":
            continue
        attrs = {key.upper(): value for key, value in element.attrib.items()}
        raw_name = attrs.get("FULLNAME") or attrs.get("INSTANCE") or attrs.get("NAME")
        if not raw_name:
            continue
        parameters: dict[str, str] = {}
        for child in element.iter():
            if child.tag.rsplit("}", 1)[-1].upper() != "PARAMETER":
                continue
            p_attrs = {key.upper(): value for key, value in child.attrib.items()}
            pname = p_attrs.get("NAME")
            pvalue = p_attrs.get("VALUE")
            if pname and pvalue is not None:
                key = pname.upper()
                if key in parameters and parameters[key] != pvalue.strip():
                    result.error("HWH_PARAMETER_CONFLICT", f"{raw_name} has conflicting {key} values")
                parameters[key] = pvalue.strip()
        parameters["@MODTYPE"] = attrs.get("MODTYPE", "")
        parameters["@VLNV"] = attrs.get("VLNV", "")
        instance = normalize_instance(raw_name)
        if instance in modules:
            result.error("HWH_DUPLICATE_INSTANCE", f"HWH repeats MODULE instance {instance}")
        modules[instance] = parameters
    return part, modules


def hwh_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    aliases = {"TRUE": 1, "FALSE": 0}
    if raw.upper() in aliases:
        return aliases[raw.upper()]
    try:
        return int(raw, 0)
    except ValueError:
        return None


def validate_artifacts(profile_path: Path, profile: dict[str, Any], result: Result) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    board = child_object(profile, "board", result)
    overlay = child_object(profile, "overlay", result)
    for field in ("board_name", "board_revision", "device_part", "pynq_image"):
        text(board, field, "board", result)
    compatibility = board.get("compatibility_contains")
    if not isinstance(compatibility, list) or not compatibility or not all(isinstance(item, str) and item for item in compatibility):
        result.error("BOARD_COMPATIBILITY", "board.compatibility_contains must be a non-empty string list")
    for field in ("build_id", "interface_version", "vivado_version"):
        text(overlay, field, "overlay", result)

    paths: dict[str, Path] = {}
    for field in ("bit", "hwh", "manifest"):
        path = resolve(profile_path.parent, overlay.get(field), f"overlay.{field}", result)
        if path is None:
            continue
        paths[field] = path
        if not path.is_file():
            result.error("ARTIFACT_MISSING", f"overlay.{field} not found: {path}")
        else:
            result.hashes[field] = sha256(path)
    if "bit" in paths and "hwh" in paths:
        result.check("OVERLAY_STEM", paths["bit"].stem == paths["hwh"].stem,
                     ".bit and .hwh must have one basename")
        result.check("OVERLAY_DIRECTORY", paths["bit"].parent == paths["hwh"].parent,
                     ".bit and .hwh must be adjacent")
    if "manifest" in paths and "bit" in paths:
        result.check("MANIFEST_DIRECTORY", paths["manifest"].parent == paths["bit"].parent,
                     "manifest must be adjacent to the bound bit/HWH pair")

    manifest: dict[str, Any] = {}
    if paths.get("manifest") and paths["manifest"].is_file():
        try:
            manifest = read_json(paths["manifest"])
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            result.error("MANIFEST_PARSE", str(exc))
        for field in ("build_id", "interface_version", "vivado_version"):
            result.check(f"MANIFEST_{field.upper()}", manifest.get(field) == overlay.get(field),
                         f"manifest {field} must match overlay {field}")
        result.check("MANIFEST_DEVICE_PART", manifest.get("device_part") == board.get("device_part"),
                     "manifest device_part must match board.device_part")
        for field in ("bit", "hwh"):
            entry = manifest.get(field)
            expected_path = paths.get(field)
            ok_entry = isinstance(entry, dict)
            result.check(f"MANIFEST_{field.upper()}_ENTRY", ok_entry,
                         f"manifest.{field} must be an object")
            if not ok_entry:
                continue
            expected_hash = entry.get("sha256")
            result.check(f"MANIFEST_{field.upper()}_FILE",
                         expected_path is not None and entry.get("file") == expected_path.name,
                         f"manifest.{field}.file must name the selected artifact")
            result.check(f"MANIFEST_{field.upper()}_HASH",
                         isinstance(expected_hash, str) and bool(HEX64.fullmatch(expected_hash))
                         and result.hashes.get(field) == expected_hash,
                         f"manifest.{field}.sha256 must match the selected artifact")

    modules: dict[str, dict[str, str]] = {}
    if paths.get("hwh") and paths["hwh"].is_file():
        part, modules = parse_hwh(paths["hwh"], result)
        device_part = board.get("device_part")
        expected_part = normalize_part(device_part)
        actual_part = normalize_part(part)
        result.check("HWH_DEVICE_PART",
                     bool(expected_part) and bool(actual_part) and actual_part == expected_part,
                     "HWH root PART must exactly match board.device_part after case/edge-space normalization")
    return manifest, modules


def validate_receive(profile_path: Path, profile: dict[str, Any], manifest: dict[str, Any],
                     modules: dict[str, dict[str, str]], result: Result) -> None:
    overlay = child_object(profile, "overlay", result)
    contract = child_object(profile, "receive_contract", result)
    control = child_object(profile, "control_contract", result)
    payload = child_object(profile, "payload_schema", result)

    ip_name = text(contract, "ip_name", "receive_contract", result)
    ip_key = normalize_instance(ip_name) if ip_name else ""
    result.check("HWH_S2MM_INSTANCE", bool(ip_key) and ip_key in modules,
                 f"receive_contract.ip_name {ip_name!r} must be an exact HWH MODULE path")
    parameters = modules.get(ip_key, {})
    result.check("HWH_S2MM_IP_TYPE",
                 parameters.get("@MODTYPE", "").lower() == "axi_dma"
                 and parameters.get("@VLNV", "").lower().startswith("xilinx.com:ip:axi_dma:"),
                 "declared S2MM MODULE must be a Xilinx AXI DMA IP, not just a name/parameter decoy")

    expected_contract = {
        "mode": "simple",
        "s2mm_enabled": True,
        "mm2s_enabled": False,
        "scatter_gather": False,
        "s2mm_dre": False,
        "tlast_required": True,
    }
    for field, expected in expected_contract.items():
        result.check(f"CONTRACT_{field.upper()}", contract.get(field) is expected if type(expected) is bool else contract.get(field) == expected,
                     f"receive_contract.{field} must be {expected!r}")

    numeric_fields = ("axis_data_width_bits", "memory_data_width_bits", "length_width_bits",
                      "max_transfer_bytes", "length_granularity_bytes", "buffer_alignment_bytes")
    numbers: dict[str, int] = {}
    for field in numeric_fields:
        value = exact_int(contract.get(field))
        if value is None or value <= 0:
            result.error("CONTRACT_INTEGER", f"receive_contract.{field} must be a positive integer")
        else:
            numbers[field] = value
    for field in ("axis_data_width_bits", "memory_data_width_bits"):
        if field in numbers:
            result.check("BYTE_WIDTH", numbers[field] % 8 == 0,
                         f"receive_contract.{field} must be byte-addressable")
    # Without S2MM DRE, every address admitted by the declared alignment must
    # also satisfy the memory-mapped data-width alignment required by AXI DMA.
    if (contract.get("s2mm_dre") is False
            and "buffer_alignment_bytes" in numbers
            and "memory_data_width_bits" in numbers
            and numbers["memory_data_width_bits"] % 8 == 0):
        memory_width_bytes = numbers["memory_data_width_bits"] // 8
        result.check("S2MM_ADDRESS_ALIGNMENT",
                     numbers["buffer_alignment_bytes"] % memory_width_bytes == 0,
                     "no-DRE buffer_alignment_bytes must be a multiple of the S2MM memory-mapped data width in bytes")
    if "length_width_bits" in numbers and "max_transfer_bytes" in numbers:
        expected_max = (1 << numbers["length_width_bits"]) - 1
        result.check("MAX_TRANSFER_LENGTH", numbers["max_transfer_bytes"] == expected_max,
                     "max_transfer_bytes must equal the simple-DMA length-register limit")

    for field, parameter in HWH_PARAMETERS.items():
        declared = contract.get(field)
        expected = int(declared) if type(declared) is bool else exact_int(declared)
        actual = hwh_int(parameters.get(parameter))
        result.check(f"HWH_{parameter}", expected is not None and actual == expected,
                     f"HWH {parameter}={actual!r} must match receive_contract.{field}={expected!r}")

    completion = contract.get("completion_method")
    result.check("COMPLETION_METHOD", completion == "polling",
                 "this candidate qualifies polling only; interrupt mode needs a separate adapter review")
    required_interrupts = overlay.get("required_interrupts", [])
    if not isinstance(required_interrupts, list) or not all(isinstance(item, str) and item for item in required_interrupts):
        result.error("INTERRUPT_LIST", "overlay.required_interrupts must be a string list")
    elif required_interrupts:
        result.error("POLLING_INTERRUPT_CONFLICT", "polling profile must not claim unused required interrupts")
    cache_policy = contract.get("cache_policy")
    result.check("RX_CACHE_POLICY", isinstance(cache_policy, dict)
                 and cache_policy.get("rx") == "invalidate",
                 "this candidate requires RX invalidation; coherent mode needs allocator proof and separate review")

    control_ip = text(control, "ip_name", "control_contract", result)
    control_key = normalize_instance(control_ip) if control_ip else ""
    result.check("HWH_CONTROL_INSTANCE", bool(control_key) and control_key in modules,
                 f"control_contract.ip_name {control_ip!r} must be an exact HWH MODULE path")
    result.check("HWH_CONTROL_DMA_DISTINCT", bool(control_key) and bool(ip_key) and control_key != ip_key,
                 "control_contract.ip_name must differ from receive_contract.ip_name after HWH path normalization")
    expected_control = {
        "start_semantics": "level_high_run",
        "stop_semantics": "deassert_run_drain_full_packet",
        "status_semantics": "sticky_error_and_drained",
    }
    for field, expected in expected_control.items():
        result.check(f"CONTROL_{field.upper()}", control.get(field) == expected,
                     f"control_contract.{field} must be {expected!r}")

    schema_path = resolve(profile_path.parent, payload.get("path"), "payload_schema.path", result)
    expected_schema_hash = payload.get("sha256")
    result.check("PAYLOAD_HASH_FORMAT", isinstance(expected_schema_hash, str)
                 and bool(HEX64.fullmatch(expected_schema_hash)),
                 "payload_schema.sha256 must be a lowercase SHA-256")
    if schema_path is not None:
        if not schema_path.is_file():
            result.error("PAYLOAD_MISSING", f"payload schema not found: {schema_path}")
        else:
            result.hashes["payload_schema"] = sha256(schema_path)
            result.check("PAYLOAD_SCHEMA_HASH", result.hashes["payload_schema"] == expected_schema_hash,
                         "external payload schema must match its declared SHA-256")
            entry = manifest.get("payload_schema")
            result.check("MANIFEST_PAYLOAD_ENTRY", isinstance(entry, dict),
                         "manifest.payload_schema must bind the external schema")
            if isinstance(entry, dict):
                result.check("MANIFEST_PAYLOAD_FILE", entry.get("file") == schema_path.name,
                             "manifest payload schema filename must match")
                result.check("MANIFEST_PAYLOAD_HASH", entry.get("sha256") == expected_schema_hash,
                             "manifest payload schema hash must match the profile")

    tests = profile.get("receive_tests")
    if not isinstance(tests, list) or not tests:
        result.error("RECEIVE_TESTS", "receive_tests must be a non-empty list")
        tests = []
    seen: set[str] = set()
    for index, item in enumerate(tests):
        if not isinstance(item, dict):
            result.error("RECEIVE_TEST_ENTRY", f"receive_tests[{index}] must be an object")
            continue
        test_id = item.get("id")
        if not isinstance(test_id, str) or not test_id or test_id in seen:
            result.error("RECEIVE_TEST_ID", f"receive_tests[{index}] needs a unique id")
        else:
            seen.add(test_id)
        result.check("RECEIVE_TEST_KIND", item.get("kind") == "receive",
                     f"receive_tests[{index}].kind must be receive")
        length = exact_int(item.get("length_bytes"))
        valid_length = length is not None and length > 0
        result.check("RECEIVE_TEST_LENGTH", valid_length,
                     f"receive_tests[{index}].length_bytes must be positive")
        if valid_length:
            if "max_transfer_bytes" in numbers:
                result.check("RECEIVE_TEST_MAX", length <= numbers["max_transfer_bytes"],
                             f"receive_tests[{index}] must not exceed max_transfer_bytes")
            if "length_granularity_bytes" in numbers:
                result.check("RECEIVE_TEST_GRANULARITY", length % numbers["length_granularity_bytes"] == 0,
                             f"receive_tests[{index}] length must meet transfer granularity")
            if "axis_data_width_bits" in numbers:
                result.check("RECEIVE_TEST_BEAT", length % (numbers["axis_data_width_bits"] // 8) == 0,
                             f"receive_tests[{index}] length must contain full AXIS beats")
        timeout = item.get("timeout_seconds")
        valid_timeout = (type(timeout) is int and timeout > 0) or (
            type(timeout) is float and math.isfinite(timeout) and timeout > 0)
        result.check("RECEIVE_TEST_TIMEOUT", valid_timeout,
                     f"receive_tests[{index}].timeout_seconds must be finite and positive")

    result.summary = {
        "build_id": overlay.get("build_id"),
        "dma_instance": ip_name,
        "mode": contract.get("mode"),
        "s2mm_enabled": contract.get("s2mm_enabled"),
        "mm2s_enabled": contract.get("mm2s_enabled"),
        "axis_data_width_bits": contract.get("axis_data_width_bits"),
        "memory_data_width_bits": contract.get("memory_data_width_bits"),
        "length_width_bits": contract.get("length_width_bits"),
        "max_transfer_bytes": contract.get("max_transfer_bytes"),
        "tlast_required": contract.get("tlast_required"),
        "completion_method": completion,
        "payload_schema_external": True,
    }


def _validate(profile_path: Path) -> tuple[dict[str, Any], int]:
    profile = read_json(profile_path)
    result = Result(str(profile.get("profile_id", "unknown")))
    result.check("SCHEMA_VERSION", profile.get("schema_version") == 1,
                 "schema_version must be 1")
    result.check("PROFILE_KIND", profile.get("profile_kind") == "receive-only-s2mm",
                 "profile_kind must be receive-only-s2mm")
    manifest, modules = validate_artifacts(profile_path, profile, result)
    validate_receive(profile_path, profile, manifest, modules, result)
    report = result.report()
    return report, 1 if result.failed else 0


def validate(profile_path: Path) -> tuple[dict[str, Any], int]:
    try:
        return _validate(profile_path.resolve())
    except (OSError, ValueError, json.JSONDecodeError, OverflowError, TypeError) as exc:
        result = Result()
        result.error("INPUT_ERROR", f"{type(exc).__name__}: {exc}")
        return result.report(), 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path,
                        help="new JSON report; existing files are never overwritten")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; choose a fresh filename")
    report, code = validate(args.profile)
    encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    print(encoded, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
