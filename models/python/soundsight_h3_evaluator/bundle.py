"""Strict evidence loading and original-byte reference verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from . import SCHEMA_VERSION


class BundleError(ValueError):
    """Malformed or incomplete evidence structure (CLI exit 2)."""


class IdentityError(ValueError):
    """Conflicting source identity or changed original bytes (CLI exit 3)."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BundleError(message)


def uint(value: Any, label: str, bits: int = 64) -> int:
    require(type(value) is int and 0 <= value < 1 << bits, f"INVALID_UINT:{label}")
    return value


def missing(value: Any) -> bool:
    return (isinstance(value, dict) and value.get("value", object()) is None
            and value.get("missing_reason") in {
                "NOT_OBSERVED", "NOT_FROZEN", "NOT_APPLICABLE", "LOG_TRUNCATED",
                "SOURCE_CONFLICT", "SYNTHETIC_ONLY", "POLICY_UNRESOLVED"})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_bundle(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise BundleError(f"DUPLICATE_JSON_KEY:{key}")
            obj[key] = value
        return obj

    def reject_constant(value):
        raise BundleError(f"NONFINITE_JSON_NUMBER:{value}")

    try:
        obj = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError(f"BUNDLE_JSON_INVALID:{exc}") from exc
    require(isinstance(obj, dict), "BUNDLE_NOT_OBJECT")
    return obj, raw


def verify_references(bundle: dict, base: Path) -> list[dict]:
    refs = bundle.get("references")
    require(isinstance(refs, list), "REFERENCES_REQUIRED")
    base = base.resolve(strict=True)
    seen: set[str] = set()
    verified = []
    for index, ref in enumerate(refs):
        require(isinstance(ref, dict), f"REFERENCE_OBJECT:{index}")
        name = ref.get("id")
        require(isinstance(name, str) and name and name not in seen, f"REFERENCE_ID:{index}")
        seen.add(name)
        rel = ref.get("path")
        require(isinstance(rel, str) and rel and not Path(rel).is_absolute(), f"REFERENCE_PATH:{name}")
        target = (base / rel).resolve(strict=True)
        require(target.is_relative_to(base) and target.is_file(), f"REFERENCE_ESCAPE:{name}")
        expected = ref.get("sha256")
        require(isinstance(expected, str) and len(expected) == 64 and
                all(c in "0123456789abcdef" for c in expected), f"REFERENCE_SHA:{name}")
        length = uint(ref.get("bytes"), f"reference.{name}.bytes")
        actual_length = target.stat().st_size
        actual = sha256(target)
        if length != actual_length or actual != expected:
            raise IdentityError(f"REFERENCE_MISMATCH:{name}:expected={expected}/{length}:"
                                f"observed={actual}/{actual_length}:path={target}")
        require(isinstance(ref.get("role"), str) and ref["role"], f"REFERENCE_ROLE:{name}")
        require(isinstance(ref.get("producer"), str) and ref["producer"], f"REFERENCE_PRODUCER:{name}")
        verified.append({"id": name, "role": ref["role"], "path": str(target),
                         "sha256": actual, "bytes": actual_length, "producer": ref["producer"]})
    return verified


def _source(obj: dict, refs: set[str], label: str, formal: bool) -> None:
    source = obj.get("source_ref")
    if formal:
        require((isinstance(source, str) and source in refs) or missing(source),
                f"SOURCE_REF_OR_MISSING_REASON_REQUIRED:{label}")
    elif source is not None:
        require(source in refs, f"UNKNOWN_SOURCE_REF:{label}")


def validate_structure(bundle: dict, verified: list[dict]) -> None:
    require(bundle.get("schema_version") == SCHEMA_VERSION, "SCHEMA_VERSION_UNSUPPORTED")
    scope = bundle.get("claim_scope")
    require(scope in {"SYNTHETIC_TEST", "DIRECTION_RUN", "DIRECTION_CELL", "P1_P4_BATCH"},
            "CLAIM_SCOPE_UNSUPPORTED")
    formal = scope != "SYNTHETIC_TEST"
    require(bundle.get("evidence_level") in {"SYNTHETIC", "NATIVE", "INDEPENDENT", "MIXED"},
            "EVIDENCE_LEVEL_REQUIRED")
    require(not formal or bundle["evidence_level"] != "SYNTHETIC", "FORMAL_SCOPE_SYNTHETIC_LEVEL")
    seal = bundle.get("seal")
    require(isinstance(seal, dict) and seal.get("status") in {"SEALED", "PROVISIONAL"},
            "SEAL_STATUS_REQUIRED")
    for name in ("policy_ref", "preregistration", "runs"):
        require(name in bundle, f"TOP_LEVEL_REQUIRED:{name}")
    require(isinstance(bundle["policy_ref"], dict), "POLICY_REF_OBJECT")
    require(isinstance(bundle["preregistration"], list) and bundle["preregistration"],
            "PREREGISTRATION_REQUIRED")
    require(isinstance(bundle["runs"], list) and bundle["runs"], "RUNS_REQUIRED")
    refs = {r["id"] for r in verified}
    if formal:
        if seal["status"] == "SEALED":
            require(isinstance(seal.get("proof_refs"), list) and seal["proof_refs"]
                    and all(r in refs for r in seal["proof_refs"]),
                    "CLAIMED_SEAL_LACKS_PROOF_REFERENCE")
        _source(bundle["policy_ref"], refs, "policy_ref", True)
    prereg = {}
    for slot in bundle["preregistration"]:
        require(isinstance(slot, dict), "PREREGISTRATION_SLOT_OBJECT")
        rid = slot.get("run_id")
        require(isinstance(rid, str) and rid and rid not in prereg, "DUPLICATE_OR_MISSING_RUN_ID")
        require(all(key in slot for key in ("environment", "scenario", "nominal_angle_deg")),
                f"PREREGISTRATION_FIELDS:{rid}")
        _source(slot, refs, f"preregistered.{rid}", formal)
        prereg[rid] = slot
    runs = {}
    for run in bundle["runs"]:
        require(isinstance(run, dict), "RUN_OBJECT")
        rid = run.get("run_id")
        require(rid in prereg and rid not in runs, f"RUN_ID_NOT_PREREGISTERED_OR_DUPLICATE:{rid}")
        slot = prereg[rid]
        for key in ("environment", "scenario", "nominal_angle_deg"):
            if run.get(key) != slot.get(key):
                raise IdentityError(f"PREREGISTRATION_CONFLICT:{rid}.{key}:"
                                    f"preregistered={slot.get(key)!r}:observed={run.get(key)!r}:")
        for key in ("capture", "window_grid", "truth", "algorithm", "time_proof",
                    "watermarks", "target_identity", "audio"):
            require(isinstance(run.get(key), dict), f"RUN_OBJECT_REQUIRED:{rid}.{key}")
        for key in ("capture", "truth", "algorithm", "time_proof", "watermarks"):
            _source(run[key], refs, f"{rid}.{key}", formal)
        capture = run["capture"]
        for key in ("boot_id", "session_id", "interval_id", "algorithm_id", "config_id",
                    "calibration_id"):
            value = capture.get(key)
            require((isinstance(value, str) and bool(value)) or missing(value),
                    f"CAPTURE_ID_OR_MISSING_REASON_REQUIRED:{rid}.{key}")
        for key in ("epoch", "generation", "first_original_id", "stop_original_id"):
            value = capture.get(key)
            if not missing(value):
                uint(value, f"{rid}.{key}")
        first, stop = capture["first_original_id"], capture["stop_original_id"]
        if type(first) is int and type(stop) is int:
            require(stop > first, f"CAPTURE_RANGE:{rid}")
        grid = run["window_grid"]
        if not missing(grid.get("origin_original_id")):
            uint(grid.get("origin_original_id"), f"{rid}.origin")
        require(grid.get("length_samples") == 1024 and grid.get("hop_samples") == 512,
                f"WINDOW_GRID_UNSUPPORTED:{rid}")
        require(isinstance(capture.get("drop_ranges"), list) and
                isinstance(capture.get("clip_ranges"), list), f"CAPTURE_FLAGS_REQUIRED:{rid}")
        require(type(capture.get("flags_sealed")) is bool, f"FLAGS_SEAL_REQUIRED:{rid}")
        for obj, key in ((run["truth"], "windows"), (run["algorithm"], "events"),
                         (run["algorithm"], "required_units"), (run["watermarks"], "streams")):
            require(isinstance(obj.get(key), list) or missing(obj.get(key)),
                    f"LIST_OR_MISSING_REASON_REQUIRED:{rid}.{key}")
        portable = run["algorithm"].get("portable_ref")
        require(portable is None or isinstance(portable, dict), f"PORTABLE_REF_OBJECT:{rid}")
        if isinstance(portable, dict) and not missing(portable):
            for key in ("run_index_ref", "result_ref"):
                require(portable.get(key) in refs, f"PORTABLE_REFERENCE_NOT_BOUND:{rid}.{key}")
        if formal and isinstance(run["algorithm"]["required_units"], list):
            from .events import EXPECTED_UNITS
            require(tuple(run["algorithm"]["required_units"]) == EXPECTED_UNITS,
                    f"FORMAL_REQUIRED_UNITS_MUST_MATCH_FIXED_PORTABLE_PROFILE:{rid}")
        runs[rid] = run
    require(set(runs) == set(prereg), "PREREGISTERED_RUNS_NOT_ALL_RETAINED")
    if scope == "DIRECTION_RUN":
        require(len(runs) == 1, "DIRECTION_RUN_REQUIRES_ONE_RUN")


def portable_link(run: dict, verified: list[dict], planned_m: int | None) -> dict:
    """Audit an optional old portable research output without treating it as real-time evidence."""
    link = run["algorithm"].get("portable_ref")
    if link is None or missing(link):
        return {"status": "NOT_PROVIDED", "reason": "PORTABLE_OUTPUT_REFERENCE_MISSING"}
    by_id = {ref["id"]: ref for ref in verified}
    try:
        run_index = load_bundle(Path(by_id[link["run_index_ref"]]["path"]))[0]
        result = load_bundle(Path(by_id[link["result_ref"]]["path"]))[0]
    except (BundleError, KeyError) as exc:
        raise IdentityError(f"PORTABLE_REFERENCE_CONTENT_INVALID:{run['run_id']}:{exc}") from exc
    actual_result_sha = by_id[link["result_ref"]]["sha256"]
    if run_index.get("outputs_sha256", {}).get("result.json") != actual_result_sha:
        raise IdentityError(f"PORTABLE_INDEX_RESULT_HASH_CONFLICT:{run['run_id']}:")
    count = result.get("planned_frames")
    if planned_m is not None and count is not None and count != planned_m:
        raise IdentityError(f"PORTABLE_FRAME_COUNT_CONFLICT:{run['run_id']}:"
                            f"portable={count}:grid={planned_m}")
    return {"status": "RAW_BYTES_LINKED_RESEARCH_ONLY", "run_index_ref": link["run_index_ref"],
            "result_ref": link["result_ref"], "time_basis": result.get("time_basis"),
            "planned_frames": count, "algorithm_claim": result.get("claim"),
            "warning": "PORTABLE_RESEARCH_OUTPUT_IS_NOT_REAL_TIME_OR_NATIVE_TAKE_PROOF"}


def verify_unchanged(bundle_path: Path, initial_bundle_sha: str, verified: list[dict]) -> None:
    actual = sha256(bundle_path)
    if actual != initial_bundle_sha:
        raise IdentityError(f"BUNDLE_CHANGED_DURING_RUN:{initial_bundle_sha}:{actual}")
    for ref in verified:
        path = Path(ref["path"])
        actual = sha256(path)
        if actual != ref["sha256"] or path.stat().st_size != ref["bytes"]:
            raise IdentityError(f"REFERENCE_CHANGED_DURING_RUN:{ref['id']}:"
                                f"expected={ref['sha256']}:observed={actual}")
