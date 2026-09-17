#!/usr/bin/env python3
"""Write or verify a SHA-256 manifest for this task package.

The manifest excludes itself so it can seal every other source, config,
document and evidence file without a self-referential hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


MANIFEST_NAME = "PACKAGE-SHA256.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inventory(root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or path.name == MANIFEST_NAME:
            continue
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    package = args.package.resolve()
    manifest = package / MANIFEST_NAME
    actual = inventory(package)

    if args.verify:
        expected = json.loads(manifest.read_text(encoding="utf-8"))
        if expected.get("files") != actual:
            print("PACKAGE MANIFEST FAIL")
            return 1
        print(f"PACKAGE MANIFEST PASS: files={len(actual)}")
        return 0

    payload = {
        "schema": "soundsight-h3-package-sha256-1",
        "root": "task-packages/PKG-B-ALG/tasks/h3-complete-20260918",
        "excludes": [MANIFEST_NAME],
        "files": actual,
    }
    manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"PACKAGE MANIFEST WRITTEN: files={len(actual)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
