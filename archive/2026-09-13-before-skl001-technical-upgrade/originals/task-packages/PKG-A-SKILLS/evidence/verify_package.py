"""Verify an explicitly supplied package manifest without modifying any input.

This is a delivery-integrity check, not Skill behavior or hardware validation.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


def verify(root):
    root = Path(root).resolve(strict=True)
    manifest_path = root / "MANIFEST.json"
    if manifest_path.is_symlink():
        raise ValueError("Manifest must not be a symlink")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("Unsupported manifest schema")
    if not isinstance(manifest.get("package_version"), str) or not manifest["package_version"]:
        raise ValueError("Missing package version")
    rows = manifest.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Empty or malformed file list")
    expected = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Malformed file row")
        name = row.get("path")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.\-/]+", name):
            raise ValueError("Invalid ASCII relative path")
        path = PurePosixPath(name)
        if (path.is_absolute() or path.as_posix() != name
                or any(p in ("", ".", "..") for p in name.split("/"))):
            raise ValueError("Unsafe relative path: " + name)
        if name.casefold() in expected or name.casefold() == "manifest.json":
            raise ValueError("Duplicate or self-referential path: " + name)
        expected.add(name.casefold())
        size, digest = row.get("bytes"), row.get("sha256")
        if type(size) is not int or size < 0:
            raise ValueError("Invalid byte count: " + name)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid SHA-256: " + name)
        target = root / name
        for component in (target, *target.parents):
            if component == root:
                break
            if component.is_symlink():
                raise ValueError("Symlink in package: " + name)
        if not target.is_file():
            raise ValueError("Missing file: " + name)
        if not target.resolve().is_relative_to(root):
            raise ValueError("File escapes package: " + name)
        raw = target.read_bytes()
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("Byte/hash mismatch: " + name)
    actual = set()
    for item in root.rglob("*"):
        name = item.relative_to(root).as_posix()
        if item.is_symlink():
            raise ValueError("Symlink in package: " + name)
        if item.is_file() and name != "MANIFEST.json":
            if name.casefold() in actual:
                raise ValueError("Case-colliding files: " + name)
            actual.add(name.casefold())
    if actual != expected:
        raise ValueError("File-set mismatch: extra=" + repr(sorted(actual - expected))
                         + "; missing=" + repr(sorted(expected - actual)))
    return {"status": "PASS_PACKAGE_INTEGRITY_ONLY", "package_version": manifest["package_version"],
            "checked_files": len(expected),
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.package)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "FAIL_PACKAGE_INTEGRITY", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
