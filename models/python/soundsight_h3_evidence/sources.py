"""Explicit read-only capabilities, bounded buffers, ZIP bytes and post identities."""
import io
import os
from pathlib import Path
import re
import stat
import struct
import zipfile

from .contracts import Issue, Resource, MIB, binding, digest, uint


def safe_path(value):
    p = Path(value)
    if (not p.is_absolute() or value.startswith(("\\\\", "//"))
            or re.search(r"[\x00*?%$]", value) or ":" in value[2:]
            or any(x in (".", "..") for x in value.replace("\\", "/").split("/")[1:])):
        raise Issue(2, "UNSAFE_FILE_PATH", {"path": value})
    for item in reversed((p, *p.parents)):
        try:
            s = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
            raise Issue(2, "REPARSE_SOURCE_PATH", {"path": str(item)})
    return p


def stamp(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)


def read_file(value, ceiling):
    p = safe_path(value)
    before = p.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise Issue(2, "NOT_A_REGULAR_SOURCE", {"path": value})
    if before.st_size > ceiling:
        raise Resource("FILE_BYTE_LIMIT", {"length": str(before.st_size)})
    data = bytearray()
    actual = 0
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(p, flags)
    with os.fdopen(fd, "rb") as f:
        if stamp(os.fstat(f.fileno())) != stamp(before):
            raise Issue(4, "SOURCE_CHANGED_AT_OPEN", {"path": value})
        while True:
            b = f.read(min(MIB, ceiling - actual + 1))
            if not b:
                break
            actual += len(b)
            if actual > ceiling:
                raise Resource("FILE_BYTE_LIMIT_DURING_READ")
            data.extend(b)
        after = os.fstat(f.fileno())
    safe_path(value)
    if stamp(before) != stamp(after) or stamp(before) != stamp(p.stat()):
        raise Issue(4, "SOURCE_CHANGED_DURING_READ", {"path": value})
    return data, stamp(after)


def read_control(path):
    try:
        return read_file(str(path), MIB)
    except (OSError, Resource) as e:
        raise Issue(2, "CONTROL_UNAVAILABLE", {"path": str(path), "reason": str(e)}) from e


def zip_directory(data):
    """Check bounded classic central directory BEFORE zipfile builds entry objects."""
    pos = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    if pos < 0 or pos + 22 > len(data):
        raise Issue(3, "ZIP_EOCD_MISSING")
    _, disk, start_disk, on_disk, count, size, offset, comment = struct.unpack_from("<4s4H2IH", data, pos)
    if pos + 22 + comment != len(data) or disk or start_disk or count != on_disk:
        raise Issue(3, "ZIP_STRUCTURE")
    if count == 65535 or size == 0xffffffff or offset == 0xffffffff:
        raise Resource("ZIP64_UNSUPPORTED")
    if count > 4096 or size > MIB:
        raise Resource("ZIP_DIRECTORY_LIMIT")
    if offset + size != pos:
        raise Issue(3, "ZIP_DIRECTORY_RANGE")
    return count


def npy_layout(data):
    """Header and byte-span only, never unpack a correlation code."""
    import ast
    if len(data) < 10 or data[:8] != b"\x93NUMPY\x01\x00":
        raise Issue(3, "NPY_VERSION")
    n = struct.unpack_from("<H", data, 8)[0]
    if n > 4096 or len(data) != 10 + n + 6 * 1024 * 8:
        raise Issue(3, "NPY_HEADER_OR_BYTE_LENGTH")
    try:
        header = ast.literal_eval(data[10:10 + n].decode("ascii").strip())
    except (ValueError, SyntaxError, UnicodeError) as e:
        raise Issue(3, "NPY_HEADER_SYNTAX") from e
    if (type(header) is not dict or set(header) != {"descr", "fortran_order", "shape"}
            or header["descr"] != "<i8" or header["fortran_order"] is not False
            or header["shape"] != (6, 1024)):
        raise Issue(3, "NPY_LAYOUT_UNSUPPORTED")
    return {"version": "1.0", "dtype": "<i8", "fortran_order": False,
            "shape": ["6", "1024"], "data_offset": str(10 + n),
            "code_decode": "NOT_RUN"}


class SourceStore:
    def __init__(self, entries, budget):
        self.entries = entries
        self.budget = min(uint(budget), 64 * MIB)
        self.used = self.expanded = 0
        self.cache = {}  # Only one copy per complete content byte identity.
        self.by_id = {}
        self.records = []
        self.files = {}
        self.edges = []

    def get(self, sid):
        if sid in self.by_id:
            return self.by_id[sid]
        e = self.entries[sid]
        loc, declared = e["location"], uint(e["byte_length"])
        limit = 16 * MIB if loc["kind"] == "FILE" else 8 * MIB
        if declared > limit or self.used + declared > self.budget:
            raise Resource("SOURCE_READ_BUDGET", {"source_id": sid, "declared": str(declared)})
        key = e["ref"]["content_sha256"]
        if loc["kind"] == "FILE":
            try:
                data, st = read_file(loc["path"], min(limit, self.budget - self.used))
            except FileNotFoundError:
                raise Issue(0, "MISSING_SOURCE", {"source_id": sid}) from None
            except PermissionError:
                raise Issue(0, "SOURCE_UNREADABLE", {"source_id": sid}) from None
            self.files[sid] = (loc["path"], binding(data), st)
        else:
            parent = self.get(loc["container_id"])
            self.edges.append({"from": sid, "to": loc["container_id"], "rule": "ZIP_MEMBER_PARENT", "locator": loc["member_name"]})
            count = zip_directory(parent)
            try:
                with zipfile.ZipFile(MemoryReader(parent)) as z:
                    members = z.infolist()
                    names = [m.filename for m in members]
                    if len(members) != count or len(names) != len(set(names)):
                        raise Issue(3, "DUPLICATE_ZIP_MEMBER")
                    if loc["member_name"] not in names:
                        raise Issue(3, "ZIP_MEMBER_MISSING", {"source_id": sid})
                    m = z.getinfo(loc["member_name"])
                    if m.flag_bits & 1:
                        raise Resource("ENCRYPTED_ZIP_UNSUPPORTED")
                    if m.file_size > 8 * MIB or self.expanded + m.file_size > 32 * MIB:
                        raise Resource("ZIP_EXPANSION_LIMIT")
                    if self.used + m.file_size > self.budget:
                        raise Resource("SOURCE_READ_BUDGET_AFTER_PARENT")
                    data, size = bytearray(), 0
                    with z.open(m) as f:
                        while True:
                            b = f.read(min(MIB, 8 * MIB - size + 1))
                            if not b:
                                break
                            size += len(b)
                            if size > 8 * MIB or self.expanded + size > 32 * MIB or self.used + size > self.budget:
                                raise Resource("ZIP_EXPANSION_LIMIT_DURING_READ")
                            data.extend(b)
                    self.expanded += len(data)
            except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError) as err:
                raise Issue(3, "ZIP_MEMBER_READ_CONFLICT", {"reason": str(err)}) from err
        actual = binding(data)
        self.records.append({"id": sid, "ref": e["ref"], "location": loc,
                             "declared": {"sha256": key, "byte_length": e["byte_length"]},
                             "observed": actual, "post": "PENDING"})
        if actual != {"sha256": key, "byte_length": e["byte_length"]}:
            raise Issue(3, "SOURCE_BYTE_IDENTITY", {"source_id": sid, "declared": self.records[-1]["declared"], "observed": actual})
        if key not in self.cache:
            self.used += len(data)
            self.cache[key] = data
        self.by_id[sid] = self.cache[key]
        return self.cache[key]

    def verify_post(self):
        for sid, (path, before, st) in self.files.items():
            try:
                data, after_st = read_file(path, 16 * MIB)
            except (OSError, Issue) as e:
                raise Issue(4, "SOURCE_POST_UNAVAILABLE_OR_CHANGED", {"source_id": sid, "reason": str(e)}) from e
            if binding(data) != before or after_st != st:
                raise Issue(4, "SOURCE_POST_DRIFT", {"source_id": sid, "pre": before, "post": binding(data)})
        for r in self.records:
            r["post"] = "UNCHANGED"


class MemoryReader(io.RawIOBase):
    """Seekable read view; ZIP library does not duplicate the full container."""
    def __init__(self, data):
        self.data, self.position = memoryview(data), 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else len(self.data) + offset
        if self.position < 0:
            raise ValueError("negative seek")
        return self.position

    def read(self, n=-1):
        end = len(self.data) if n < 0 else min(len(self.data), self.position + n)
        result = self.data[self.position:end].tobytes()
        self.position = end
        return result
