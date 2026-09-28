"""Verify a browser-exported #20 camera frame and its paired metadata.

This checks file integrity and internal consistency. It cannot establish which
physical camera produced the frame or prove sustained video performance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("PNG signature missing")
    offset = len(PNG_SIGNATURE)
    dimensions = None
    saw_image_data = False
    saw_end = False
    while offset + 12 <= len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        chunk_type = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"PNG CRC mismatch in {chunk_type!r}")
        if dimensions is None:
            if chunk_type != b"IHDR" or length != 13:
                raise ValueError("invalid first PNG chunk")
            dimensions = struct.unpack_from(">II", payload)
            if not all(dimensions):
                raise ValueError("zero PNG dimension")
        elif chunk_type == b"IDAT":
            saw_image_data = True
        elif chunk_type == b"IEND":
            if length != 0 or end != len(data):
                raise ValueError("invalid PNG end or trailing bytes")
            saw_end = True
            break
        offset = end
    if not (dimensions and saw_image_data and saw_end):
        raise ValueError("PNG is missing image data or IEND")
    return dimensions


def verify(manifest_path: Path) -> dict[str, object]:
    report = json.loads(manifest_path.read_text(encoding="utf-8"))
    if report.get("schema") != "soundsight.camera.capture.v1":
        raise ValueError("unknown capture schema")
    image_name = report.get("image_file")
    if image_name != manifest_path.stem + ".png":
        raise ValueError("image name must match the JSON basename")
    if not isinstance(image_name, str) or Path(image_name).name != image_name:
        raise ValueError("image path must be a local basename")
    image_path = manifest_path.with_name(image_name)
    data = image_path.read_bytes()
    expected_hash = report.get("image_sha256")
    if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
        raise ValueError("invalid recorded SHA-256")
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError("image SHA-256 mismatch")
    if len(data) != report.get("image_bytes"):
        raise ValueError("image byte count mismatch")
    width, height = png_dimensions(data)
    if (width, height) != (report.get("image_width"), report.get("image_height")):
        raise ValueError("PNG dimensions disagree with metadata")
    settings = report.get("negotiated", {})
    if (width, height) != (settings.get("width"), settings.get("height")):
        raise ValueError("PNG dimensions disagree with negotiated stream")
    events = report.get("events")
    if not isinstance(events, list) or not any(e.get("kind") == "frame-captured" for e in events if isinstance(e, dict)):
        raise ValueError("frame-captured event missing")
    return {
        "result": "FILE_INTEGRITY_PASS",
        "image": str(image_path),
        "sha256": actual_hash,
        "width": width,
        "height": height,
        "camera_label_reported_by_browser": report.get("live_track_label"),
        "scope": "file integrity only; camera identity, mounting, movement and sustained frame rate remain separate",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON saved together with its same-named PNG")
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.manifest), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({"result": "FAIL", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
