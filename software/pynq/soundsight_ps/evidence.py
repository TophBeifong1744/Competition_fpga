"""Exclusive output and immutable snapshots, with an append-only audit journal."""
import json
import os
from pathlib import Path
from .contracts import sha256, require


class Evidence:
    def __init__(self, directory):
        self.root = Path(directory)
        # 中文用途：输出目录必须全新，避免覆盖先前失败和原始证据。
        require(not self.root.exists(), "output directory already exists")
        self.root.mkdir(parents=True, exist_ok=False)
        self.sequence = 0
        self.events = []

    def event(self, kind, **fields):
        item = dict(sequence=len(self.events), kind=kind, **fields)
        self.events.append(item)
        with (self.root / "audit.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(item, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return item

    def snapshot(self, label, payload, metadata):
        require(type(payload) is bytes, "immutable bytes required for archive")
        number = self.sequence
        self.sequence += 1
        name = f"{number:06d}-{label}"
        raw_path = self.root / (name + ".bin")
        meta_path = self.root / (name + ".json")
        digest = sha256(payload)
        with raw_path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        value = dict(metadata, raw_file=raw_path.name, bytes=len(payload), sha256=digest)
        with meta_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        require(sha256(raw_path.read_bytes()) == digest, "archive readback mismatch")
        return value

    def report(self, value):
        with (self.root / "result.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
