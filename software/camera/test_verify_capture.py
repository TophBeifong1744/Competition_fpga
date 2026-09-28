"""Small integrity canaries for the #20 exported evidence verifier."""

import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from verify_capture import verify


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def one_pixel_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(b"\x00\x07\x08\x09"))
        + chunk(b"IEND", b"")
    )


class CaptureVerificationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="camera-verify-")
        self.root = Path(self.temp.name)
        self.image = self.root / "camera-fixture.png"
        data = one_pixel_png()
        self.image.write_bytes(data)
        self.report = {
            "schema": "soundsight.camera.capture.v1",
            "image_file": self.image.name,
            "image_sha256": hashlib.sha256(data).hexdigest(),
            "image_bytes": len(data),
            "image_width": 1,
            "image_height": 1,
            "negotiated": {"width": 1, "height": 1},
            "events": [{"kind": "frame-captured"}],
        }
        self.manifest = self.root / "camera-fixture.json"
        self.write_report()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_report(self) -> None:
        self.manifest.write_text(json.dumps(self.report), encoding="utf-8")

    def test_consistent_png_and_metadata(self) -> None:
        self.assertEqual(verify(self.manifest)["result"], "FILE_INTEGRITY_PASS")

    def test_changed_image_hash_fails(self) -> None:
        self.report["image_sha256"] = "0" * 64
        self.write_report()
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify(self.manifest)

    def test_changed_dimensions_fail(self) -> None:
        self.report["image_width"] = 2
        self.write_report()
        with self.assertRaisesRegex(ValueError, "dimensions disagree"):
            verify(self.manifest)


if __name__ == "__main__":
    unittest.main()
