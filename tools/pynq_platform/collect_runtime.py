#!/usr/bin/env python3
"""Read runtime metadata only; never initialize PYNQ or access hardware."""

import argparse
import datetime
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import stat
import struct
import sys


SCHEMA = "soundsight-pynq-runtime-metadata-1"
TEXT_LIMIT = 64 * 1024
SOURCE_LIMIT = 2 * 1024 * 1024
SOURCE_TOTAL_LIMIT = 16 * 1024 * 1024
SOURCE_COUNT_LIMIT = 64
PACKAGE_FILE_COUNT_LIMIT = 20000
ARTIFACT_LIMIT = 2 * 1024 * 1024 * 1024
ARTIFACT_TOTAL_LIMIT = 4 * 1024 * 1024 * 1024
ARTIFACT_COUNT_LIMIT = 16
CHUNK_SIZE = 1024 * 1024
SOURCE_GROUPS = {
    "dma": {"dma"},
    "buffer": {"buffer"},
    "allocator": {"allocator", "allocate", "xlnk", "xrt", "xrt_device", "embedded_device"},
    "device": {"device", "embedded_device", "xrt_device"},
    "overlay": {"overlay"},
    "mmio": {"mmio"},
}


# 只保留错误类别和 errno，避免异常中的本机用户名或绝对路径进入报告。
def error_record(exc):
    if isinstance(exc, FileNotFoundError):
        status = "MISSING"
    elif isinstance(exc, PermissionError):
        status = "PERMISSION_DENIED"
    else:
        status = "READ_ERROR"
    return {"status": status, "error_type": type(exc).__name__,
            "errno": getattr(exc, "errno", None)}


def is_network_path(path):
    return str(path).replace("\\", "/").startswith("//")


# 仅打开已核为普通文件的本地路径；固定 proc/sys 元数据也按此检查。
def open_regular(path):
    if is_network_path(path):
        raise ValueError("NETWORK_PATH_REJECTED")
    resolved = Path(path).resolve(strict=True)
    if is_network_path(resolved):
        raise ValueError("NETWORK_PATH_REJECTED")
    before = resolved.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("NON_REGULAR_FILE_REJECTED")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    fd = os.open(str(resolved), flags)
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode)
                or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)):
            raise ValueError("FILE_CHANGED_BEFORE_READ")
        return os.fdopen(fd, "rb"), opened
    except BaseException:
        os.close(fd)
        raise


def read_bytes(path, limit=TEXT_LIMIT):
    try:
        handle, _ = open_regular(path)
        with handle:
            value = handle.read(limit + 1)
        if len(value) > limit:
            return {"status": "LIMIT_EXCEEDED", "limit_bytes": limit}, None
        return {"status": "READ", "bytes_read": len(value)}, value
    except ValueError as exc:
        return {"status": str(exc)}, None
    except (OSError, RuntimeError) as exc:
        return error_record(exc), None


# 分块计算完整文件身份，超限或读取中变化时不输出可能误用的摘要。
def hash_file(path, limit):
    count = 0
    try:
        handle, before = open_regular(path)
        with handle:
            if before.st_size > limit:
                return {"status": "LIMIT_EXCEEDED", "size_bytes": before.st_size,
                        "limit_bytes": limit, "bytes_read": 0}
            digest = hashlib.sha256()
            while True:
                block = handle.read(min(CHUNK_SIZE, limit - count + 1))
                if not block:
                    break
                count += len(block)
                if count > limit:
                    return {"status": "LIMIT_EXCEEDED", "limit_bytes": limit,
                            "bytes_read": count}
                digest.update(block)
            after = os.fstat(handle.fileno())
        if (before.st_size != count or after.st_size != count
                or before.st_mtime_ns != after.st_mtime_ns):
            return {"status": "CHANGED_DURING_READ", "bytes_read": count}
        return {"status": "HASHED", "size_bytes": count,
                "sha256": digest.hexdigest(), "bytes_read": count}
    except ValueError as exc:
        return {"status": str(exc), "bytes_read": count}
    except (OSError, RuntimeError) as exc:
        result = error_record(exc)
        result["bytes_read"] = count
        return result


def text_value(path):
    result, raw = read_bytes(path)
    if raw is not None:
        try:
            result["value"] = raw.decode("utf-8").strip("\x00\r\n")
        except UnicodeDecodeError:
            result["status"] = "DECODE_ERROR"
    return result


def linux_metadata():
    if not sys.platform.startswith("linux"):
        unavailable = {"status": "NOT_APPLICABLE", "reason": "NON_LINUX_RUNTIME"}
        return {"os_release": dict(unavailable), "device_tree": dict(unavailable),
                "memory": dict(unavailable)}
    # 仅取系统发行字段，不读取 hostname、cmdline、串号或 dmesg。
    os_release, raw = read_bytes("/etc/os-release")
    if raw is not None:
        try:
            allowed = {"ID", "ID_LIKE", "NAME", "PRETTY_NAME", "VERSION", "VERSION_ID", "BUILD_ID"}
            os_release["fields"] = {}
            for line in raw.decode("utf-8").splitlines():
                key, sep, value = line.partition("=")
                if sep and key in allowed:
                    # 保留文件中的准确值/引号，不执行 shell 展开。
                    os_release["fields"][key] = value
        except UnicodeDecodeError:
            os_release["status"] = "DECODE_ERROR"
    device_tree = {}
    for root in ("/proc/device-tree", "/sys/firmware/devicetree/base"):
        properties = {name: text_value(Path(root) / name) for name in ("model", "compatible")}
        compatible = properties["compatible"]
        if "value" in compatible:
            compatible["value"] = compatible["value"].split("\x00")
        device_tree[root] = properties
    memory, raw = read_bytes("/proc/meminfo")
    if raw is not None:
        memory["fields"] = {key: {"status": "MISSING"} for key in ("MemTotal", "CmaTotal", "CmaFree")}
        try:
            for line in raw.decode("ascii").splitlines():
                key, sep, value = line.partition(":")
                if sep and key in memory["fields"]:
                    pieces = value.split()
                    if len(pieces) == 2 and pieces[0].isdigit() and pieces[1] == "kB":
                        memory["fields"][key] = {"status": "READ", "value": int(pieces[0]), "unit": "kB"}
                    else:
                        memory["fields"][key] = {"status": "INVALID_FORMAT"}
        except UnicodeDecodeError:
            memory["status"] = "DECODE_ERROR"
    return {"os_release": os_release, "device_tree": device_tree, "memory": memory}


def source_groups(relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "pynq":
        return []
    if path.suffix not in {".py", ".c", ".cpp", ".h", ".hpp"}:
        return []
    return [group for group, stems in SOURCE_GROUPS.items() if path.stem in stems]


# 用发行包元数据定位源码，不 import pynq/numpy，也不调用任何包初始化代码。
def package_metadata(name):
    result = {"requested_distribution": name, "status": "METADATA_RECORDED"}
    try:
        dist = metadata.distribution(name)
        info = dist.metadata
        result["fields"] = {}
        for key in ("Name", "Version", "Requires-Python"):
            value = info.get(key)
            if value is None:
                result["fields"][key] = {"status": "MISSING"}
            elif len(value) > 512:
                result["fields"][key] = {"status": "LIMIT_EXCEEDED", "limit_characters": 512}
            else:
                result["fields"][key] = {"status": "READ", "value": value}
        if name != "pynq":
            return result
        files = dist.files
        if files is None:
            result["sources"] = {"status": "FILE_LIST_UNAVAILABLE"}
            return result
        if len(files) > PACKAGE_FILE_COUNT_LIMIT:
            result["sources"] = {"status": "FILE_LIST_LIMIT_EXCEEDED", "entry_count": len(files)}
            return result
        selected = []
        for entry in files:
            relative = str(entry).replace("\\", "/")
            groups = source_groups(relative)
            if groups:
                selected.append((relative, groups, entry))
        selected.sort(key=lambda row: row[0])
        sources = {"status": "METADATA_RECORDED", "selection": "distribution-listed source basename allowlist",
                   "matched_count": len(selected), "files": [], "groups": {}}
        if len(selected) > SOURCE_COUNT_LIMIT:
            sources["status"] = "SOURCE_COUNT_LIMIT_EXCEEDED"
        used = 0
        for relative, groups, entry in selected[:SOURCE_COUNT_LIMIT]:
            located = dist.locate_file(entry)
            try:
                record = hash_file(os.fspath(located), min(SOURCE_LIMIT, max(0, SOURCE_TOTAL_LIMIT - used)))
            except TypeError:
                record = {"status": "UNSUPPORTED_NON_FILESYSTEM_DISTRIBUTION", "bytes_read": 0}
            used += record["bytes_read"]
            record.update({"relative_path": relative, "groups": groups})
            sources["files"].append(record)
        for group in SOURCE_GROUPS:
            matches = [row for row in sources["files"] if group in row["groups"]]
            sources["groups"][group] = ("HASHED" if matches and all(row["status"] == "HASHED" for row in matches)
                                          else "INCOMPLETE" if matches else "NO_MATCHING_SOURCE_LISTED")
        result["sources"] = sources
    except metadata.PackageNotFoundError:
        result["status"] = "PACKAGE_NOT_FOUND"
    except (OSError, ValueError, RuntimeError, UnicodeError) as exc:
        result.update(error_record(exc))
    return result


def runtime_metadata():
    runtime = {"os": sys.platform, "python": {
        "version": ".".join(str(value) for value in sys.version_info[:3]),
        "releaselevel": sys.version_info.releaselevel, "serial": sys.version_info.serial,
        "implementation": sys.implementation.name, "pointer_bits": struct.calcsize("P") * 8}}
    if hasattr(os, "uname"):
        uname = os.uname()
        runtime.update({"os": uname.sysname, "kernel_release": uname.release, "machine": uname.machine})
    elif sys.platform == "win32":
        version = sys.getwindowsversion()
        runtime["kernel_release"] = "{}.{}.{}".format(version.major, version.minor, version.build)
        machine = os.environ.get("PROCESSOR_ARCHITEW6432", os.environ.get("PROCESSOR_ARCHITECTURE", "UNKNOWN"))
        runtime["machine"] = machine if machine.upper() in {"AMD64", "X86", "ARM", "ARM64", "IA64"} else "UNKNOWN"
        runtime["machine_source"] = "Windows architecture environment (unverified)"
    else:
        runtime.update({"kernel_release": "UNKNOWN", "machine": "UNKNOWN"})
    return runtime


def collect(artifacts):
    runtime = runtime_metadata()
    linux = linux_metadata()
    compatible = []
    for entry in linux["device_tree"].values():
        if isinstance(entry, dict):
            compatible.extend(entry.get("compatible", {}).get("value", []))
    board_like = (sys.platform.startswith("linux") and runtime["machine"] in {"armv7l", "armv8l", "aarch64"}
                  and any(value in {"xlnx,zynq-7000", "xlnx,zynqmp"} for value in compatible))
    environment = "ZYNQ_RUNTIME_METADATA_ONLY" if board_like else "NON_BOARD_ENVIRONMENT"
    report = {
        "schema": SCHEMA, "collected_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "collection_status": "METADATA_RECORDED", "environment_status": environment,
        "environment_basis": "OS, machine and device-tree strings only; no physical identity verification",
        "runtime": runtime, "linux": linux,
        "packages": {name: package_metadata(name) for name in ("pynq", "numpy")},
        "artifacts": [], "hardware_checks": {name: "NOT_RUN" for name in (
            "physical_board_identity", "image_boot_provenance", "overlay_load", "bit_hwh_match",
            "mmio", "irq", "dma", "allocator", "cache_coherency", "barriers",
            "buffer_retirement", "stop_timeout_recovery")},
        "limits": {"fixed_text_bytes_each": TEXT_LIMIT, "source_bytes_each": SOURCE_LIMIT,
                   "source_bytes_total": SOURCE_TOTAL_LIMIT, "source_files": SOURCE_COUNT_LIMIT,
                   "package_file_entries": PACKAGE_FILE_COUNT_LIMIT, "artifact_bytes_each": ARTIFACT_LIMIT,
                   "artifact_bytes_total": ARTIFACT_TOTAL_LIMIT, "artifact_count": ARTIFACT_COUNT_LIMIT,
                   "metadata_field_characters": 512,
                   "distribution_api_note": "importlib.metadata parses installed metadata/file lists internally; no hard byte cap on that stdlib parsing",
                   "io_note": "byte/count limits only; no filesystem I/O time bound"},
        "limitations": [
            "Runtime metadata does not identify the physical board or loaded PL design.",
            "Package versions/source hashes do not verify allocator, cache, barrier or retirement behavior.",
            "Artifact hashes identify only explicitly supplied files; no bit/HWH match is asserted.",
            "The source installation image SHA256 cannot be derived from a running root filesystem.",
            "No hardware access, package import, device allocation, reset or network operation is performed.",
        ],
    }
    used = 0
    for index, path in enumerate(artifacts, start=1):
        record = hash_file(path, min(ARTIFACT_LIMIT, max(0, ARTIFACT_TOTAL_LIMIT - used)))
        used += record["bytes_read"]
        record["argument_index"] = index
        report["artifacts"].append(record)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog="Run after a human boots the board. Hardware checks always remain NOT_RUN.")
    parser.add_argument("--out", required=True, type=Path, help="new JSON file; existing files are refused")
    parser.add_argument("--artifact", action="append", default=[], type=Path,
                        help="explicit local regular file to hash (repeatable, maximum 16); no directories/devices")
    args = parser.parse_args(argv)
    if len(args.artifact) > ARTIFACT_COUNT_LIMIT:
        parser.error("at most 16 explicit --artifact files are supported")
    # 先按原始路径拒绝全部 UNC 输入，避免 resolve 在 Windows 上触及远端。
    if any(is_network_path(path) for path in args.artifact):
        parser.error("network artifact paths are not supported")
    if is_network_path(args.out) or is_network_path(args.out.resolve()):
        parser.error("network output paths are not supported")
    if any(args.out.resolve() == path.resolve() for path in args.artifact):
        parser.error("output cannot also be an artifact input")
    # 排他创建保护已有证据；失败留下不完整文件时必须换新文件名重跑。
    try:
        fd = os.open(str(args.out), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    except FileExistsError:
        print("OUTPUT_EXISTS: refusing to overwrite evidence", file=sys.stderr)
        return 2
    except OSError as exc:
        print("OUTPUT_ERROR: " + json.dumps(error_record(exc)), file=sys.stderr)
        return 2
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            report = collect(args.artifact)
            json.dump(report, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
    except (OSError, ValueError, RuntimeError) as exc:
        print("REPORT_INCOMPLETE: " + json.dumps(error_record(exc)), file=sys.stderr)
        return 2
    print("METADATA_RECORDED; {}; hardware_checks=NOT_RUN".format(report["environment_status"]))
    return 0 if report["environment_status"] == "ZYNQ_RUNTIME_METADATA_ONLY" else 3


if __name__ == "__main__":
    sys.exit(main())
