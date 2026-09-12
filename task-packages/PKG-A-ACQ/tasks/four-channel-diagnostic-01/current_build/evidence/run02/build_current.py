"""Snapshot/rebuild the CURRENT four-mic project, never run migration scripts.

check: filesystem/contract checks only; no mkdir, tool launch, build or board IO.
build: exclusive new output, copied inputs, Vivado + existing BSP-linked PS build.
Python >= 3.11, standard library only. Source/tool paths are explicit arguments.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

PART = "xc7z020clg400-2"
VERSION = "2025.2"
HERE = Path(__file__).resolve().parent


class BuildError(RuntimeError):
    pass


def require(ok, message):
    if not ok:
        raise BuildError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def under(path, root):
    return path == root or root in path.parents


def no_links(path):
    """Reject existing symlinks/junctions in the entire path, including leaf."""
    p = Path(os.path.abspath(path))
    for node in (p, *p.parents):
        try:
            s = node.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(s.st_mode) and
                not getattr(s, "st_file_attributes", 0) & 0x400,
                f"Symlink/junction/reparse point not supported: {node}")
    return p.resolve()


def need_file(path):
    p = no_links(path)
    require(p.is_file(), f"Missing required file: {p}")
    return p


def need_tool(path):
    # AMD's Vitis/gnu is an installer-owned junction to the shared toolchain.
    # Resolve read-only executables first; never permit link-based output paths.
    return need_file(Path(path).resolve(strict=True))


def tree_files(root):
    root = no_links(root)
    require(root.is_dir(), f"Missing directory: {root}")
    result = []
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            no_links(Path(parent) / name)
        result.extend(Path(parent) / name for name in sorted(files))
    return sorted(result)


def output_path(value, protected):
    require(Path(value).is_absolute(), "Output must be an absolute new path")
    out = no_links(value)
    require(not os.path.lexists(out), f"Output exists; never overwrite/reuse: {out}")
    require(out.parent.is_dir(), f"Output parent must already exist: {out.parent}")
    for root in protected:
        require(not under(out, root) and not under(root, out),
                f"Output overlaps protected input: {out} <-> {root}")
    return out


def hwh_signature(data):
    root = ET.fromstring(data)
    # HWH wall-clock timestamp is nonfunctional; retain every other attribute.
    for node in root.iter():
        node.attrib.pop("TIMESTAMP", None)
    text = ET.tostring(root, encoding="unicode")
    return hashlib.sha256(ET.canonicalize(text, strip_text=True).encode()).hexdigest()


def xsa_info(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require("system.hwh" in names and "ps7_init.c" in names, "Not a system Zynq XSA")
        hwh = archive.read("system.hwh")
        root = ET.fromstring(hwh)
        info = root.find("SYSTEMINFO")
        require(info is not None and info.get("DEVICE") == "7z020"
                and info.get("PACKAGE") == "clg400" and info.get("SPEEDGRADE") == "-2",
                "XSA part differs from current four-mic target")
        return {"hwh_signature": hwh_signature(hwh),
                "ps7_init_sha256": hashlib.sha256(archive.read("ps7_init.c")).hexdigest()}


def preflight(args):
    project = need_file(args.project)
    require(project.suffix.lower() == ".xpr", "Project must be an existing .xpr")
    vivado, gcc = need_tool(args.vivado), need_tool(args.gcc)
    bsp, ps = no_links(args.bsp), no_links(args.ps_source)
    bsp_xsa = need_file(args.bsp_xsa)
    require(args.jobs >= 1 and args.jobs <= 16, "jobs must be 1..16")
    # .bat launch uses Windows command parsing: fail closed for metacharacters.
    for value in (project, vivado, gcc, bsp, ps, bsp_xsa, args.output, HERE):
        require(not re.search(r'[\r\n"&|<>^%!]', str(value)),
                f"Unsupported command metacharacter in path: {value}")
    out = output_path(args.output, [project.parent, bsp, ps, bsp_xsa,
                                    vivado.parent, gcc.parent, HERE])
    source_root = project.parent / (project.stem + ".srcs")
    generated_root = project.parent / (project.stem + ".gen")
    require(source_root.is_dir(), f"Missing current source tree: {source_root}")
    project_raw = project.read_bytes()
    xml = ET.fromstring(project_raw)
    require(b"2025.2" in project_raw[:600], "XPR must be saved by Vivado 2025.2")
    require(xml.find("./Configuration/Option[@Name='Part']").get("Val") == PART,
            "Unexpected XPR part")
    # Do not execute inherited Tcl hooks or access an external writable IP cache.
    for e in xml.iter():
        name = e.get("Name", "")
        value = e.get("Val", "")
        require(not (value and ("TCL.PRE" in name.upper() or "TCL.POST" in name.upper())),
                f"Run hook requires manual review: {name}")
        if value and re.match(r"^(?:[A-Za-z]:[/\\]|/|\\\\)", value):
            require(name == "ImportPath", f"External XPR setting not supported: {name}={value}")
        for key in ("Dir", "RelSrcDir", "RelGenDir", "AutoIncrementalDir", "AutoRQSDir"):
            raw = e.get(key, "")
            require(not re.match(r"^(?:[A-Za-z]:[/\\]|/|\\\\)", raw),
                    f"Absolute XPR output setting needs review: {key}={raw}")
    roots = {"$PSRCDIR": source_root, "$PGENDIR": generated_root,
             "$PPRDIR": project.parent}
    dependencies = {}
    for node in xml.findall(".//FileSet/File"):
        raw = node.get("Path", "")
        resolved = raw
        for token, root in roots.items():
            resolved = resolved.replace(token, root.as_posix())
        require("$" not in resolved, f"Unknown XPR path variable: {raw}")
        p = Path(resolved)
        if not p.is_absolute():
            p = project.parent / p
        p = need_file(p)
        require(under(p, project.parent), f"External project file needs explicit packaging: {p}")
        dependencies[str(p)] = p.relative_to(project.parent).as_posix()
    # Preserve all .srcs files (including inactive history); do not copy old runs/cache.
    for p in tree_files(source_root):
        dependencies[str(p)] = p.relative_to(project.parent).as_posix()
    bds = [Path(p) for p in dependencies if p.endswith("/system.bd") or p.endswith("\\system.bd")]
    require(len(bds) == 1, "Expected exactly one current system.bd")
    design = json.loads(bds[0].read_text(encoding="utf-8"))["design"]
    require(design["design_info"]["tool_version"] == VERSION and
            design["design_info"]["device"] == PART, "BD tool/part mismatch")
    require("four_mic_top_0" in design["components"] and
            "single_mic_top_0" not in design["components"],
            "Current adapted four-mic BD required; migration is deliberately unsupported")
    require(all(p in design["ports"] for p in
                ("pdm_data", "pdm_clk1", "pdm_clk2", "pdm_clk3", "pdm_clk4")),
            "Current four-CLOCK/four-DATA ports required")
    expected = {"TOTAL_SAMPLES": "32000", "SAMPLES_PER_PACKET": "250",
                "WARMUP_SAMPLES": "4096", "FIFO_LOG2": "10"}
    actual = design["components"]["four_mic_top_0"]["parameters"]
    require(all(actual.get(k, {}).get("value") == v for k, v in expected.items()),
            "Four-mic capture parameters changed; review before building")
    bp = [need_file(bsp / f) for f in (
        "Xilinx.spec", "include/xparameters.h", "include/xaxidma.h", "include/xgpio.h",
        "lib/libxil.a", "lib/libxilstandalone.a", "lib/libxiltimer.a",
        "hw_artifacts/ps7_init.c")]
    for folder in ("include", "lib"):
        bp.extend(tree_files(bsp / folder))
    require("-mcpu=cortex-a9" in (bsp / "cortexa9_toolchain.cmake").read_text(),
            "BSP must target cortex-a9")
    xi = xsa_info(bsp_xsa)
    require(sha(bsp / "hw_artifacts/ps7_init.c") == xi["ps7_init_sha256"],
            "BSP PS initialization does not match supplied BSP XSA")
    sf = [need_file(ps / f) for f in ("main_four_capture.c", "lscript.ld")]
    require("four-channel-c-adapter-v1" in sf[0].read_text(),
            "Wrong PS source/configuration; no automatic source conversion")
    size = need_tool(gcc.with_name(gcc.name.replace("gcc", "size")))
    nm = need_tool(gcc.with_name(gcc.name.replace("gcc", "nm")))
    files = {str(project): "project/" + project.name}
    files.update({p: "project/" + rel for p, rel in dependencies.items()})
    files.update({str(p): "bsp/" + p.relative_to(bsp).as_posix() for p in bp})
    files.update({str(p): "ps/" + p.name for p in sf})
    files[str(bsp_xsa)] = "bsp-reference.xsa"
    # Also protect already-built source-project products, without using them as build input.
    protected = dict(files)
    for p in (project.parent / "system_c_adapter.xsa",
              project.parent / (project.stem + ".runs") / "impl_1/system_wrapper.bit"):
        if p.is_file():
            protected[str(need_file(p))] = "NOT_COPIED_OR_USED"
    hashes = {p: sha(p) for p in protected}
    return {"status": "CHECK_PASS_NOT_BUILD", "project": str(project), "output": str(out),
            "vivado": str(vivado), "gcc": str(gcc), "size": str(size), "nm": str(nm),
            "bsp": str(bsp), "ps_source": str(ps), "bsp_xsa": str(bsp_xsa),
            "part": PART, "version_required": VERSION, "jobs": args.jobs,
            "input_files": files, "protected_sha256": hashes, "bsp_binding": xi,
            "checks": ["new output; no input overlap", "no links/external source/hook",
                       "already-adapted four-mic BD", "required inputs present",
                       "BSP PS init matches reference XSA"],
            "limits": ["check does not launch tools or test licenses",
                       "build uses supplied prebuilt BSP; does not regenerate platform",
                       "no board operation or acceptance", "not a hostile-Tcl sandbox"]}


def write_json(path, obj):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def unchanged(plan):
    return [p for p, h in plan["protected_sha256"].items()
            if not Path(p).is_file() or sha(p) != h]


def stage(plan, out):
    require(not unchanged(plan), "Inputs changed after check; do not build a mixed snapshot")
    inp = out / "inputs"
    for old, rel in plan["input_files"].items():
        dst = inp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        require(not dst.exists(), f"Duplicate snapshot target: {dst}")
        shutil.copyfile(old, dst)  # real copies, never symlinks or hardlinks
        require(sha(dst) == plan["protected_sha256"][old], f"Input changed while copying: {old}")
    clone = inp / "project" / Path(plan["project"]).name
    tree = ET.parse(clone)
    tree.getroot().set("Path", clone.as_posix())
    # Fresh full builds must not depend on a prior incremental DCP/run state.
    for run in tree.findall("./Runs/Run"):
        run.set("AutoIncrementalCheckpoint", "false")
        run.attrib.pop("IncrementalCheckpoint", None)
        run.set("State", "new")
    tree.write(clone, encoding="UTF-8", xml_declaration=True)
    require(not unchanged(plan), "Inputs changed while snapshotting")
    return clone


def run_command(argv, out, name, cwd=None):
    logs = out / "logs"
    logs.mkdir(exist_ok=True)
    write_json(logs / (name + ".command.json"),
               {"argv": list(map(str, argv)), "cwd": str(cwd or out)})
    with (logs / (name + ".log")).open("x", encoding="utf-8") as stream:
        proc = subprocess.run(list(map(str, argv)), cwd=cwd or out,
                              stdout=stream, stderr=subprocess.STDOUT, shell=False)
    require(proc.returncode == 0, f"{name} failed (exit {proc.returncode}); keep logs/output")
    return (logs / (name + ".log")).read_text(encoding="utf-8", errors="replace")


def build(plan):
    out = Path(plan["output"])
    # Atomic claim: existence checked again, no recursive delete, no -force/reuse.
    out.mkdir(exist_ok=False)
    status = {"status": "RUNNING", "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "board_test": "NOT_RUN", "bsp_rebuilt": False}
    write_json(out / "preflight.json", plan)
    try:
        shutil.copyfile(HERE / "build_current.py", out / "build_current.py")
        clone = stage(plan, out)
        shutil.copyfile(HERE / "build_hw.tcl", out / "build_hw.tcl")
        # Windows vivado.bat -version can print a valid version but return 1.
        # build_hw.tcl checks [version -short] and records [version] before open_project.
        run_command([plan["gcc"], "--version"], out, "gcc-version")
        run_command([plan["vivado"], "-mode", "batch", "-notrace", "-nojournal",
                     "-log", "logs/vivado.log", "-source", "build_hw.tcl", "-tclargs",
                     str(out), str(clone), str(plan["jobs"])], out, "hardware")
        rebuilt = xsa_info(out / "artifacts/hw/system_c_adapter.xsa")
        require(rebuilt == plan["bsp_binding"],
                "Rebuilt XSA differs from supplied BSP XSA (HWH/PS init); do not link stale BSP")
        status["bsp_xsa_contract"] = "MATCH_HWH_EXCEPT_TIMESTAMP_AND_PS_INIT"
        # Source bytes must remain unchanged, even in the copy; generated files are separate.
        mutated = []
        for old, rel in plan["input_files"].items():
            if rel.startswith("project/") and Path(old).suffix.lower() in (".v", ".sv", ".bd", ".xdc"):
                if sha(out / "inputs" / rel) != plan["protected_sha256"][old]:
                    mutated.append(rel)
        require(not mutated, f"Copied RTL/BD/XDC changed: {mutated}")
        psout = out / "artifacts/ps"
        psout.mkdir()
        argv = [plan["gcc"], "-DSDT", "-mcpu=cortex-a9", "-mfpu=vfpv3",
                "-mfloat-abi=hard", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0", "-g3",
                "-specs=../../inputs/bsp/Xilinx.spec", "-I../../inputs/bsp/include",
                "../../inputs/ps/main_four_capture.c", "-o", "four_mic_capture.elf",
                "-L../../inputs/bsp/lib", "-Wl,-T,../../inputs/ps/lscript.ld",
                "-Wl,-Map,four_mic_capture.map,--cref", "-Wl,--start-group",
                "-lxilstandalone", "-lxiltimer", "-lxil", "-lgcc", "-lc", "-Wl,--end-group"]
        run_command(argv, out, "ps-build", psout)
        run_command([plan["size"], "four_mic_capture.elf"], out, "ps-size", psout)
        nm = run_command([plan["nm"], "-n", "four_mic_capture.elf"], out, "ps-symbols", psout)
        ends = re.findall(r"(?m)^([0-9a-fA-F]+)\s+\w\s+end$", nm)
        require(len(ends) == 1 and int(ends[0], 16) <= 0x01000000, "Program overlaps RX reservation")
        status["program_end"] = "0x" + ends[0]
        status["rx_guard_end_exclusive"] = "0x010FA040"
        timing = (out / "reports/timing-values.txt").read_text()
        values = dict(line.split("=", 1) for line in timing.splitlines() if "=" in line)
        status["timing"] = values
        require(float(values["setup_slack"]) >= 0 and float(values["hold_slack"]) >= 0,
                "Internal setup/hold violation; artifacts retained, do not label timing PASS")
        status["status"] = "BUILD_PASS_NOT_BOARD_TEST"
        status["limits"] = ["external IO timing/physical clock skew remains deferred",
                            "bit/ELF hashes need not equal old build: timestamps and paths differ",
                            "supplied BSP reused, not regenerated; no new hardware acceptance"]
    except Exception as error:
        status["status"] = "BUILD_FAILED"
        status["error"] = str(error)
    finally:
        changes = unchanged(plan)
        status["protected_inputs_unchanged"] = not changes
        status["changed_inputs"] = changes
        if changes:
            status["status"] = "INPUT_CHANGED_BUILD_INVALID"
        status["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        artifacts = {}
        for directory in ("artifacts", "reports", "logs"):
            if (out / directory).exists():
                for p in tree_files(out / directory):
                    artifacts[p.relative_to(out).as_posix()] = {"bytes": p.stat().st_size, "sha256": sha(p)}
        write_json(out / "artifacts-sha256.json", artifacts)
        write_json(out / "result.json", status)
    return status


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("check", "build"))
    for option in ("project", "vivado", "gcc", "bsp", "bsp-xsa", "ps-source", "output"):
        p.add_argument("--" + option, required=True, type=Path)
    p.add_argument("--jobs", type=int, default=4)
    return p


def main():
    args = parser().parse_args()
    try:
        plan = preflight(args)
        result = plan if args.mode == "check" else build(plan)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] in ("CHECK_PASS_NOT_BUILD", "BUILD_PASS_NOT_BOARD_TEST") else 1
    except (OSError, ValueError, ET.ParseError, BuildError, zipfile.BadZipFile) as error:
        print(json.dumps({"status": "REFUSED_OR_FAILED", "error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
