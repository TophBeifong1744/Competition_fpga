"""Explicit read-only capabilities, bounded buffers, ZIP bytes and post identities."""
import io
import hashlib
import os
from pathlib import Path
import re
import stat
import struct
import zipfile
import zlib
import binascii

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


def read_file(value, ceiling, identity_only=False, acquired=None):
    p = safe_path(value)
    before = p.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise Issue(2, "NOT_A_REGULAR_SOURCE", {"path": value})
    if before.st_size > ceiling:
        raise Resource("FILE_BYTE_LIMIT", {"length": str(before.st_size)})
    data = None if identity_only else bytearray()
    sha = hashlib.sha256()
    actual = 0
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(p, flags)
    with os.fdopen(fd, "rb") as f:
        if stamp(os.fstat(f.fileno())) != stamp(before):
            raise Issue(4, "SOURCE_CHANGED_AT_OPEN", {"path": value})
        # Do not acquire a +1 probe byte beyond the resource ceiling. The
        # pre-open length bounds this read; final stamps detect growth/shrinkage.
        while actual < before.st_size:
            b = f.read(min(MIB, before.st_size - actual))
            if not b:
                break
            actual += len(b)
            if acquired is not None:
                acquired(b)
            if actual > ceiling:
                raise Resource("FILE_BYTE_LIMIT_DURING_READ")
            sha.update(b)
            if data is not None:
                data.extend(b)
        after = os.fstat(f.fileno())
    safe_path(value)
    if stamp(before) != stamp(after) or stamp(before) != stamp(p.stat()):
        raise Issue(4, "SOURCE_CHANGED_DURING_READ", {"path": value})
    return ({"sha256": sha.hexdigest(), "byte_length": str(actual)} if identity_only else data), stamp(after)


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
        tree = ast.parse(data[10:10 + n].decode("ascii").strip(), mode="eval")
        if not isinstance(tree.body, ast.Dict) or any(not isinstance(k, ast.Constant) or type(k.value) is not str for k in tree.body.keys):
            raise ValueError("header keys")
        keys = [k.value for k in tree.body.keys]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate header keys")
        header = ast.literal_eval(tree)
    except (ValueError, SyntaxError, UnicodeError) as e:
        raise Issue(3, "NPY_HEADER_SYNTAX") from e
    if (type(header) is not dict or set(header) != {"descr", "fortran_order", "shape"}
            or header["descr"] != "<i8" or header["fortran_order"] is not False
            or type(header["shape"]) is not tuple or any(type(x) is not int for x in header["shape"])
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
        self.identity_checked = self.post_checked = 0
        self.cache = {}  # Only one copy per complete content byte identity.
        self.by_id = {}
        self.records = []
        self.files = {}
        self.edges = []
        self.failed = {}  # A failed attempt is not a verified content cache.

    def accounting(self):
        return {"distinct_source_bytes": str(self.used),
                "expanded_member_bytes": str(self.expanded),
                "verified_cache_bytes": str(sum(len(b) for b in self.cache.values())),
                "identity_check_bytes": str(self.identity_checked),
                "post_check_bytes": str(self.post_checked)}

    def get(self, sid):
        if sid in self.by_id:
            return self.by_id[sid]
        if sid in self.failed:
            code, reason, details, resource = self.failed[sid]
            raise Resource(reason, details) if resource else Issue(code, reason, details)
        e = self.entries[sid]
        cached = e["ref"]["content_sha256"] in self.cache
        sha, length = hashlib.sha256(), 0
        record = {"id": sid, "ref": e["ref"], "location": e["location"],
                  "declared": {"sha256": e["ref"]["content_sha256"], "byte_length": e["byte_length"]},
                  "observed": {"sha256": sha.hexdigest(), "byte_length": "0"},
                  "post": "NOT_VERIFIED", "acquisition": {"state": "IN_PROGRESS",
                  "mode": "VERIFIED_CONTENT_LOCATION_CHECK" if cached else "NEW_CONTENT",
                  "charged_bytes": "0", "complete": False}}

        def acquired(b):
            nonlocal length
            if record not in self.records:
                self.records.append(record)
            length += len(b)
            sha.update(b)
            record["observed"] = {"sha256": sha.hexdigest(), "byte_length": str(length)}
            if cached:
                self.identity_checked += len(b)
            else:
                self.used += len(b)
                record["acquisition"]["charged_bytes"] = str(length)
            if e["location"]["kind"] == "ZIP_MEMBER":
                self.expanded += len(b)
            # Callers bound the next FILE/decompress operation before it occurs.
            if self.used > self.budget or self.expanded > 32 * MIB:
                raise Issue(4, "ACQUISITION_ACCOUNTING_BOUND_VIOLATION")
        try:
            data = self._get(sid, acquired, record)
        except Exception as err:
            record["acquisition"].update(state="REJECTED", reason=getattr(err, "reason", type(err).__name__))
            # Keep the failure identity, not a traceback retaining rejected
            # buffers/decoder frames. A retry raises a fresh exception, no read.
            self.failed[sid] = (getattr(err, "code", 4),
                                getattr(err, "reason", type(err).__name__),
                                getattr(err, "details", {}), isinstance(err, Resource))
            raise
        record["acquisition"].update(state="VERIFIED", complete=True)
        return data

    def _get(self, sid, acquired, record):
        e = self.entries[sid]
        loc, declared = e["location"], uint(e["byte_length"])
        key = e["ref"]["content_sha256"]
        cached = key in self.cache
        limit = 16 * MIB if loc["kind"] == "FILE" else 8 * MIB
        if declared > limit or self.used + (0 if cached else declared) > self.budget:
            raise Resource("SOURCE_READ_BUDGET", {"source_id": sid, "declared": str(declared)})
        if loc["kind"] == "FILE":
            try:
                read, st = read_file(loc["path"], limit if cached else min(limit, self.budget - self.used), identity_only=cached, acquired=acquired)
            except FileNotFoundError:
                raise Issue(0, "MISSING_SOURCE", {"source_id": sid}) from None
            except PermissionError:
                raise Issue(0, "SOURCE_UNREADABLE", {"source_id": sid}) from None
            except Resource as err:
                if "length" in err.details and int(err.details["length"]) != declared:
                    raise Issue(3, "SOURCE_DECLARED_LENGTH_CONFLICT", {"source_id": sid, "declared_length": str(declared), "observed_length": err.details["length"], "hash": "NOT_READ_RESOURCE_LIMIT"}) from err
                raise
            actual = read if cached else binding(read)
            self.files[sid] = (loc["path"], actual, st)
            data = self.cache[key] if cached else read
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
                    ceiling = min(8 * MIB, 32 * MIB - self.expanded, self.budget - self.used)
                    data = inflate_member(parent, m, z.start_dir, ceiling, acquired=acquired)
            except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError) as err:
                raise Issue(3, "ZIP_MEMBER_READ_CONFLICT", {"reason": str(err)}) from err
        if loc["kind"] != "FILE":
            actual = binding(data)
        if record not in self.records:
            self.records.append(record)  # Complete empty files are also read sources.
        record.update(observed=actual, post="PENDING")
        record["acquisition"]["complete"] = True
        if actual != {"sha256": key, "byte_length": e["byte_length"]}:
            raise Issue(3, "SOURCE_BYTE_IDENTITY", {"source_id": sid, "declared": record["declared"], "observed": actual})
        if key not in self.cache:
            self.cache[key] = data
        self.by_id[sid] = self.cache[key]
        return self.cache[key]

    def verify_post(self):
        for sid, (path, before, st) in self.files.items():
            try:
                def post_acquired(b):
                    self.post_checked += len(b)
                after, after_st = read_file(path, 16 * MIB, identity_only=True, acquired=post_acquired)
            except (OSError, Issue) as e:
                raise Issue(4, "SOURCE_POST_UNAVAILABLE_OR_CHANGED", {"source_id": sid, "reason": str(e)}) from e
            if after != before or after_st != st:
                raise Issue(4, "SOURCE_POST_DRIFT", {"source_id": sid, "pre": before, "post": after})
        for r in self.records:
            if r["id"] in self.files or r["acquisition"]["state"] == "VERIFIED":
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


def inflate_member(parent, member, directory_start, ceiling, acquired=None):
    """Read the ENTIRE stored/deflate stream, independent of claimed file_size.

    ZipExtFile clamps at a claimed uncompressed size; using that alone would
    miss trailing expansion. Verify true EOF, all stream bytes, size and CRC.
    """
    off = member.header_offset
    if off < 0 or off + 30 > directory_start or parent[off:off + 4] != b"PK\x03\x04":
        raise Issue(3, "ZIP_LOCAL_HEADER")
    flags, method = struct.unpack_from("<HH", parent, off + 6)
    name_len, extra_len = struct.unpack_from("<HH", parent, off + 26)
    start = off + 30 + name_len + extra_len
    end = start + member.compress_size
    if flags != member.flag_bits or method != member.compress_type or start > directory_start or end > directory_start:
        raise Issue(3, "ZIP_LOCAL_CENTRAL_CONFLICT")
    try:
        name = parent[off + 30:off + 30 + name_len].decode("utf-8" if flags & 0x800 else "cp437")
    except UnicodeError as e:
        raise Issue(3, "ZIP_MEMBER_NAME_ENCODING") from e
    if name != member.filename:
        raise Issue(3, "ZIP_MEMBER_NAME_CONFLICT")
    if method not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise Resource("ZIP_COMPRESSION_METHOD_UNSUPPORTED")
    output = bytearray()
    crc = 0
    decoder = zlib.decompressobj(-15) if method == zipfile.ZIP_DEFLATED else None
    def append(b):
        nonlocal crc
        if len(output) + len(b) > ceiling:
            raise Resource("ZIP_EXPANSION_LIMIT_DURING_READ")
        if acquired is not None and b:
            acquired(b)
        output.extend(b)
        crc = binascii.crc32(b, crc)
    try:
        pos = start
        while pos < end:
            remaining = ceiling - len(output)
            if remaining == 0:
                raise Resource("ZIP_EXPANSION_LIMIT_DURING_READ")
            chunk = parent[pos:min(end, pos + (min(MIB, remaining) if decoder is None else MIB))]
            pos += len(chunk)
            if decoder is None:
                append(chunk)
                continue
            pending = chunk
            while pending:
                remaining = ceiling - len(output)
                if remaining == 0:
                    raise Resource("ZIP_EXPANSION_LIMIT_DURING_READ")
                append(decoder.decompress(pending, min(MIB, remaining)))
                pending = decoder.unconsumed_tail
                if decoder.eof:
                    if pending or decoder.unused_data or pos != end:
                        raise Issue(3, "ZIP_TRAILING_COMPRESSED_STREAM")
                    break
        if decoder is not None and not decoder.eof:
            raise Issue(3, "ZIP_DEFLATE_STREAM_NOT_CLOSED")
    except zlib.error as e:
        raise Issue(3, "ZIP_DEFLATE_ERROR", {"reason": str(e)}) from e
    if len(output) != member.file_size:
        raise Issue(3, "ZIP_TRUE_EXPANDED_SIZE_CONFLICT", {"declared": str(member.file_size), "actual": str(len(output))})
    if crc & 0xffffffff != member.CRC:
        raise Issue(3, "ZIP_CRC_CONFLICT")
    return output
