"""Authoritative offline partial-producer CLI. Exit success is not acceptance."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

from . import __version__
from .contracts import Issue, Resource, SPEC, RAW, binding, bounded_json, validate_controls
from .producer import Producer
from .raw_export import payload, serialize
from .sources import SourceStore, read_control, safe_path

HERE = Path(__file__).resolve().parent
FILES = ("__init__.py", "__main__.py", "contracts.py", "sources.py", "producer.py", "raw_export.py", "README.md")


def code_identity():
    return {n: binding((HERE / n).read_bytes()) for n in FILES}


def peak_memory():
    if os.name != "nt":
        return {"observation": "UNKNOWN", "reason": "No platform-specific peak-working-set reader"}
    try:
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in
                       ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        c = Counters(); c.cb = ctypes.sizeof(c)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
            raise OSError(ctypes.get_last_error())
        return {"observation": "MEASURED", "peak_working_set_bytes": str(c.PeakWorkingSetSize),
                "method": "Windows GetProcessMemoryInfo.PeakWorkingSetSize", "limit": "Measurement only; not a hard RSS bound or WCET"}
    except Exception as e:
        return {"observation": "UNKNOWN", "reason": str(e)}


def write_json(p, obj):
    with p.open("xb") as f:
        f.write(serialize(obj))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Saved-research partial producer. No mathematical V or production PASS.")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("producer")
    for name in ("access-map", "selection", "registry", "out"):
        command.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    out, owned = args.out, False
    producer = store = None
    before = code_identity()
    controls, reads, control_stamps = {}, {}, {}
    run = {"argv": sys.argv if argv is None else argv, "cwd": str(Path.cwd()), "python": sys.version,
           "platform": platform.platform(), "claim": "DIAGNOSTIC_SMOKE_NOT_ACCEPTANCE", "tool_version": __version__,
           "code_before": before, "exit": None, "stages": [], "first_error": None}
    try:
        safe_path(str(out))
        try:
            out.mkdir(parents=True, exist_ok=False)
        except FileExistsError as e:
            raise Issue(2, "OUTPUT_EXISTS") from e
        owned = True
        for name, path in (("registry", args.registry), ("access_map", args.access_map), ("selection", args.selection)):
            b, st = read_control(path)
            reads[name] = b
            control_stamps[name] = (path, st)
            controls[name] = bounded_json(b, control=True)
        am, sel, reg = controls["access_map"], controls["selection"], controls["registry"]
        entries = validate_controls(am, sel, reg)
        # No untrusted control data or source is used before shape and byte binding.
        for declared, actual, name in ((am["registry_binding"], binding(reads["registry"]), "map->registry"),
                                       (sel["registry_binding"], binding(reads["registry"]), "selection->registry"),
                                       (sel["access_map_binding"], binding(reads["access_map"]), "selection->map"),
                                       (reg["decoder_specification"], {"sha256": SPEC, "byte_length": "24400"}, "decoder-spec"),
                                       (reg["raw_specification"], {"sha256": RAW, "byte_length": "12626"}, "RAW-spec")):
            if declared != actual:
                raise Issue(3, "CONTROL_BYTE_BINDING", {"edge": name, "declared": declared, "actual": actual})
        # Validate even unused capability paths, without opening their payload bytes.
        for e in entries.values():
            if e["location"]["kind"] == "FILE":
                safe_path(e["location"]["path"])
        run["stages"].append("CONTROLS_ADMITTED")
        store = SourceStore(entries, am["read_budget_bytes"])
        producer = Producer(am, sel, reg, store)
        report = producer.run()
        run["stages"].append("SAVED_FIELDS_AND_LINKS_PROCESSED")
        store.verify_post()
        for name, (path, st) in control_stamps.items():
            b, after_st = read_control(path)
            if binding(b) != binding(reads[name]) or after_st != st:
                raise Issue(4, "CONTROL_POST_DRIFT", {"control": name})
        if code_identity() != before:
            raise Issue(4, "PRODUCT_CODE_DRIFT")
        run["stages"].append("POST_IDENTITIES_STABLE")
        report["input_bindings"] = {n: binding(b) for n, b in reads.items()}
        report["tool_binding"] = {"version": __version__, "executing_source_files": before, "product_commit": "See run/source identity; no floating-main claim"}
        report["peak_memory"] = peak_memory()
        originals = out / "originals"; originals.mkdir()
        for hashcode, data in store.cache.items():
            (originals / (hashcode + ".bin")).write_bytes(data)
        report["original_source_outputs"] = [{"sha256": h, "byte_length": str(len(b)), "path": "originals/" + h + ".bin"} for h, b in store.cache.items()]
        rawdir = out / "raw"; rawdir.mkdir()
        for v in producer.views:
            b, reason = payload(v, producer)
            if b is None:
                report["unsupported"].append({"id": "raw-" + v["ordinal"], "view_ids": [v["id"]], "rule": "RAW_REPRESENTATION_BLOCKED", "reason": reason, "source_ids": [], "evidence_refs": [], "locator": "", "details": {}})
            else:
                path = "raw/view-" + v["ordinal"] + ".json"
                (out / path).write_bytes(b)
                report["raw_payloads"].append({"view_id": v["id"], "path": path, **binding(b), "audit_result": "NOT_RUN"})
        if not report["conflicts"] and report["unsupported"]:
            report["producer_result"] = "UNSUPPORTED"
        report["counts"]["unsupported"] = str(len(report["unsupported"]))
        exitcode = 3 if report["conflicts"] else 0
        # Report is published only after successful pre/post checks. No later
        # source decoding is performed; output bytes come from verified snapshots.
        write_json(out / "report.json", report)
        run["exit"] = str(exitcode)
        run["code_after"] = code_identity()
        run["peak_memory"] = peak_memory()
        write_json(out / "run.json", run)
        outputs = {str(p.relative_to(out)).replace("\\", "/"): binding(p.read_bytes()) for p in out.rglob("*") if p.is_file()}
        write_json(out / "output-index.json", {"claim_scope": "SAVED_RESEARCH_DIAGNOSTIC", "output_state": "SEALED_REPORT", "exit": str(exitcode), "files": outputs})
        print(json.dumps({"report": str(out / "report.json"), "producer_result": report["producer_result"], "V": "NOT_RUN", "exit": exitcode}))
        return exitcode
    except Exception as e:
        code = e.code if isinstance(e, Issue) and e.code else 4
        reason = e.reason if isinstance(e, Issue) else type(e).__name__
        run["exit"], run["first_error"] = str(code), {"reason": reason, "details": getattr(e, "details", {}), "traceback": traceback.format_exc()}
        run["peak_memory"] = peak_memory()
        if owned:
            # Any partial publication is explicitly invalid, never a successful report.
            for name in ("report.json", "output-index.json"):
                p = out / name
                if p.exists():
                    p.rename(out / ("INVALID-" + name))
            failure = {"output_state": "FAILURE_ONLY", "all_other_outputs": "INVALID_DIAGNOSTIC_ONLY", "V": "NOT_RUN", "run": run,
                       "source_audit": store.records if store else [], "known_conflicts": producer.conflicts if producer else [],
                       "missing": producer.missing if producer else [], "unsupported": producer.unsupported if producer else [],
                       "original_errors": producer.original_errors if producer else []}
            write_json(out / "failure.json", failure)
        print(json.dumps({"exit": code, "reason": reason, "out_owned": owned}), file=sys.stderr)
        return code


if __name__ == "__main__":
    sys.exit(main())
