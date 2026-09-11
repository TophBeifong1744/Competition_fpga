"""Read-only verification of the original local engineering delivery."""
import hashlib
import json
from pathlib import Path


def main():
    task = Path(__file__).resolve().parent
    root = task.parents[3]
    manifest = json.loads((task / "DELIVERY-MANIFEST-20260912.json").read_text(encoding="utf-8-sig"))
    seen = set()
    for entry in manifest["files"]:
        name = entry["path"]
        path = (root / name).resolve()
        if name in seen or not path.is_relative_to(task) or not path.is_file():
            raise SystemExit(f"FAIL missing, duplicate or unsafe path: {name}")
        seen.add(name)
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"].lower():
            raise SystemExit(f"FAIL changed bytes: {name}")
    if len(seen) != 189:
        raise SystemExit("FAIL expected 189 original files")
    print("PASS: 189 original files, byte lengths and SHA-256; not independent engineering approval")


if __name__ == "__main__":
    main()
