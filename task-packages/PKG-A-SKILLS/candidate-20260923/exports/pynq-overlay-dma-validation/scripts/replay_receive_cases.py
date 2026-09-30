#!/usr/bin/env python3
"""Materialize and replay positive/negative S2MM-only profile fixtures."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from validate_receive_profile import read_json, sha256, validate


Mutation = Callable[[dict[str, Any], Path, Path, Path, Path], None]


def remove_dma(profile: dict[str, Any], bit: Path, hwh: Path, manifest: Path, schema: Path) -> None:
    del profile, bit, manifest, schema
    tree = ET.parse(hwh)
    root = tree.getroot()
    for module in list(root):
        name = module.attrib.get("FULLNAME", "").lstrip("/")
        if name == "system_i/axi_dma_0":
            root.remove(module)
    tree.write(hwh, encoding="unicode")


def set_field(scope: str, field: str, value: Any) -> Mutation:
    def mutate(profile: dict[str, Any], bit: Path, hwh: Path, manifest: Path, schema: Path) -> None:
        del bit, hwh, manifest, schema
        profile[scope][field] = value
    return mutate


def mismatch_build(profile: dict[str, Any], bit: Path, hwh: Path, manifest: Path, schema: Path) -> None:
    del profile, bit, hwh, schema
    value = read_json(manifest)
    value["build_id"] = "different-build"
    manifest.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def mismatch_device_part(profile: dict[str, Any], bit: Path, hwh: Path,
                         manifest: Path, schema: Path) -> None:
    del profile, bit, manifest, schema
    tree = ET.parse(hwh)
    root = tree.getroot()
    root.set("PART", "xc7z010clg400-2")
    ET.SubElement(root, "MODULE", {
        "FULLNAME": "/unrelated_device_part_decoy",
        "COMMENT": "xc7z020clg400-2",
    })
    tree.write(hwh, encoding="unicode")


CASES: tuple[tuple[str, Mutation | None, str, set[str]], ...] = (
    ("valid", None, "PASS", set()),
    ("missing-s2mm", remove_dma, "FAIL", {"HWH_S2MM_INSTANCE"}),
    ("mode-mismatch", set_field("receive_contract", "mode", "scatter-gather"),
     "FAIL", {"CONTRACT_MODE"}),
    ("dre-mismatch", set_field("receive_contract", "s2mm_dre", True),
     "FAIL", {"CONTRACT_S2MM_DRE"}),
    ("axis-width-mismatch", set_field("receive_contract", "axis_data_width_bits", 64),
     "FAIL", {"HWH_C_S_AXIS_S2MM_TDATA_WIDTH"}),
    ("length-mismatch", set_field("receive_contract", "length_width_bits", 13),
     "FAIL", {"HWH_C_SG_LENGTH_WIDTH", "MAX_TRANSFER_LENGTH"}),
    ("payload-hash-mismatch", set_field("payload_schema", "sha256", "0" * 64),
     "FAIL", {"PAYLOAD_SCHEMA_HASH"}),
    ("device-part-mismatch", mismatch_device_part, "FAIL", {"HWH_DEVICE_PART"}),
    ("build-mismatch", mismatch_build, "FAIL", {"MANIFEST_BUILD_ID"}),
)


def write_manifest(profile: dict[str, Any], bit: Path, hwh: Path, manifest: Path, schema: Path) -> None:
    value = read_json(manifest)
    value["bit"] = {"file": bit.name, "sha256": sha256(bit)}
    value["hwh"] = {"file": hwh.name, "sha256": sha256(hwh)}
    value["payload_schema"] = {"file": schema.name, "sha256": sha256(schema)}
    manifest.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path,
                        help="new evidence directory; existing paths are refused")
    args = parser.parse_args()
    source_profile = args.profile.resolve()
    output = args.output.resolve()
    if output.exists():
        parser.error("output exists; choose a fresh directory")
    source = read_json(source_profile)
    source_overlay = source["overlay"]
    source_bit = (source_profile.parent / source_overlay["bit"]).resolve()
    source_hwh = (source_profile.parent / source_overlay["hwh"]).resolve()
    source_manifest = (source_profile.parent / source_overlay["manifest"]).resolve()
    source_schema = (source_profile.parent / source["payload_schema"]["path"]).resolve()
    for path in (source_bit, source_hwh, source_manifest, source_schema):
        if not path.is_file():
            parser.error(f"source fixture is missing: {path}")

    output.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    all_ok = True
    for name, mutation, expected_status, expected_codes in CASES:
        case_dir = output / name
        case_dir.mkdir()
        bit = case_dir / "design.bit"
        hwh = case_dir / "design.hwh"
        manifest = case_dir / "build-manifest.json"
        schema = case_dir / "payload-schema.json"
        profile_path = case_dir / "receive-profile.json"
        shutil.copyfile(source_bit, bit)
        shutil.copyfile(source_hwh, hwh)
        shutil.copyfile(source_manifest, manifest)
        shutil.copyfile(source_schema, schema)
        profile = copy.deepcopy(source)
        profile["overlay"].update(bit=bit.name, hwh=hwh.name, manifest=manifest.name)
        profile["payload_schema"].update(path=schema.name, sha256=sha256(schema))
        if mutation is not None:
            mutation(profile, bit, hwh, manifest, schema)
        write_manifest(profile, bit, hwh, manifest, schema)
        if name == "build-mismatch":
            mismatch_build(profile, bit, hwh, manifest, schema)
        profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
        report, return_code = validate(profile_path)
        report_path = case_dir / "report.json"
        report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        actual_codes = {item["code"] for item in report["issues"]}
        ok = report["status"] == expected_status and expected_codes.issubset(actual_codes)
        all_ok = all_ok and ok
        records.append({
            "case": name,
            "expected_status": expected_status,
            "expected_issue_codes": sorted(expected_codes),
            "actual_status": report["status"],
            "actual_return_code": return_code,
            "actual_issue_codes": sorted(actual_codes),
            "expectation_met": ok,
            "input_sha256": {
                "profile": sha256(profile_path), "bit": sha256(bit), "hwh": sha256(hwh),
                "manifest": sha256(manifest), "payload_schema": sha256(schema),
            },
            "report_sha256": sha256(report_path),
        })
    summary = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all_ok else "FAIL",
        "evidence_level": "static",
        "board_execution": False,
        "source_profile_sha256": sha256(source_profile),
        "cases": records,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
