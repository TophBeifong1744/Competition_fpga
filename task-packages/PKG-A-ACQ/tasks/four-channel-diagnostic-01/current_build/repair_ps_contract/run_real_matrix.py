"""Real ARM GCC regression matrix; never launches Vivado or a board.
Requires an existing real preflight.json for input locations, NOT contract values.
Every case is rechecked and compiled from an isolated PS/BSP fixture.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ENTRY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENTRY))
import build_current as bc

CASES = [
    ("legal-current", None, None, True, ""),
    ("legal-program-end-at-base", None, None, True, ""),
    ("base-overlaps-program", "BASE", "((UINTPTR)0x00100000U)", False, "Unsupported changed fixed"),
    ("limit-cuts-data", "LIMIT", "((UINTPTR)0x01080000U)", False, "Data/guard exceeds"),
    ("limit-widened", "LIMIT", "((UINTPTR)0x01200000U)", False, "Unsupported changed fixed"),
    ("groups-partial", "GROUPS", "32002U", False, "ps-compile failed"),
    ("word-layout", "WORDS_PER_GROUP", "4U", False, "Unsupported H1"),
    ("bytes-overflow", "BYTES", "1048576U", False, "ps-compile failed"),
    ("guard-overflow", "GUARD", "32768U", False, "ps-compile failed"),
    ("packet-disagrees-bd", "PACKET", "4000U", False, "PS packet/groups differ"),
    ("bsp-ddr-changed", None, None, False, "Compiled BSP DDR bounds differ"),
    ("linked-program-overlap", None, None, False, "Program allocation overlaps"),
    ("lying-end-symbol", None, None, False, "Program end fails to cover"),
    ("unknown-source-body", None, None, False, "Unsupported PS source body"),
]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reference-plan", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    ref = json.loads(args.reference_plan.read_text())
    protected = [Path(ref[k]).resolve() for k in ("project", "bsp", "ps_source", "bsp_xsa")]
    protected[0] = protected[0].parent
    root = bc.output_path(args.output, protected + [ENTRY])
    root.mkdir()
    source = Path(ref["ps_source"]) / "main_four_capture.c"
    linker = Path(ref["ps_source"]) / "lscript.ld"
    source_hash, linker_hash = bc.sha(source), bc.sha(linker)
    results = []
    for name, macro, expression, expect_pass, error_text in CASES:
        fixture = root / ("source-" + name)
        fixture.mkdir()
        raw = source.read_bytes()
        if macro:
            raw, count = re.subn(rb"(?m)^#define " + macro.encode() + rb" [^\r\n]*",
                                 b"#define " + macro.encode() + b" " + expression.encode(), raw)
            assert count == 1
        if name == "unknown-source-body":
            raw = raw.replace(b"volatile u32 *rx=(volatile u32*)BASE;",
                              b"volatile u32 *rx=(volatile u32*)(BASE+4);")
        (fixture / "main_four_capture.c").write_bytes(raw)
        ld = linker.read_bytes()
        if name == "legal-program-end-at-base":
            baseline = json.loads((root / "result-legal-current/result.json").read_text())
            bounds = baseline["ps_contract"]["values"]
            heap = 0x2000 + bounds["rx_start"] - bounds["program_end"]
            old_heap = b"_HEAP_SIZE = DEFINED(_HEAP_SIZE) ? _HEAP_SIZE : 0x2000;"
            assert ld.count(old_heap) == 1
            ld = ld.replace(old_heap, ("_HEAP_SIZE = DEFINED(_HEAP_SIZE) ? _HEAP_SIZE : "
                                      + hex(heap) + ";").encode())
        if name == "linked-program-overlap":
            ld = ld.replace(b"ORIGIN = 0x00100000", b"ORIGIN = 0x00FF0000")
        if name == "lying-end-symbol":
            ld = ld.replace(b"end = .;", b"end = 0x00110000;")
        (fixture / "lscript.ld").write_bytes(ld)
        bsp = Path(ref["bsp"])
        if name == "bsp-ddr-changed":
            bsp = root / "bsp-ddr-fixture"
            shutil.copytree(ref["bsp"], bsp)
            # SDT emits the same DDR macro in both headers. Change the isolated
            # pair coherently so this case reaches the compiled DDR/XSA gate.
            for filename in ("xparameters.h", "xmem_config.h"):
                header = bsp / "include" / filename
                data, count = re.subn(rb"(?m)^(#define XPAR_PS7_DDR_0_HIGHADDRESS\s+)[^\r\n]+",
                                      rb"\g<1>0x1fffffff", header.read_bytes())
                assert count == 1
                header.write_bytes(data)
        out = root / ("result-" + name)
        command = [sys.executable, "-B", str(ENTRY / "build_current.py"), "ps-check"]
        for option, value in (("project",ref["project"]),("vivado",ref["vivado"]),
                              ("gcc",ref["gcc"]),("bsp",str(bsp)),("bsp-xsa",ref["bsp_xsa"]),
                              ("ps-source",str(fixture)),("output",str(out))):
            command += ["--" + option, value]
        proc = subprocess.run(command, capture_output=True, text=True)
        with (root / (name + ".console.log")).open("x", encoding="utf-8") as stream:
            stream.write(proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        expected = ((proc.returncode == 0 and result["status"] == "PS_CONTRACT_PASS_NOT_HW_BUILD")
                    if expect_pass else (proc.returncode != 0 and error_text in result.get("error","")))
        if name == "legal-program-end-at-base" and expected:
            bounds = result["ps_contract"]["values"]
            expected = bounds["program_end"] == bounds["rx_start"]
        row = dict(case=name, command=command, expected_pass=expect_pass,
                   result=result["status"], error=result.get("error"),
                   expectation_met=expected, native_exit_code=proc.returncode,
                   source_sha256=bc.sha(fixture/"main_four_capture.c"),
                   version_string_unchanged=b'four-channel-c-adapter-v1' in raw)
        results.append(row)
        print(json.dumps({k:row[k] for k in ("case","result","error","expectation_met")}), flush=True)
    need_unchanged = source_hash == bc.sha(source) and linker_hash == bc.sha(linker)
    report = {"kind":"REAL_GCC_COMPILE_LINK_CHECK_NOT_HW_BUILD",
              "not_B_21_tests":True, "board_test":"NOT_RUN",
              "actual_source_unchanged":need_unchanged, "cases":results,
              "status":"PASS" if need_unchanged and all(x["expectation_met"] for x in results) else "FAIL"}
    bc.write_json(root / "matrix-result.json", report)
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
