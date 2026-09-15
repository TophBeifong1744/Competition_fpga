"""Read-only publication membership and SHA-256 audit; no hardware operations."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "publication/SHA256.json"

def main():
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    if actual != set(entries) | {"publication/SHA256.json"}:
        raise ValueError("Unlisted or missing package files")
    for name, expected in entries.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("SHA256 mismatch: " + name)
    original = json.loads((ROOT / "PACKAGE-SHA256.json").read_text(encoding="utf-8"))
    for name, expected in original.items():
        if entries.get(name) != expected:
            raise ValueError("Historical manifest changed: " + name)
    for run in ("board-run-20260915-01", "board-run-20260915-02"):
        for line in (ROOT / run / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            expected, name = line.split(maxsplit=1)
            if entries.get(run + "/" + name.lstrip("*")) != expected:
                raise ValueError("Board run manifest mismatch: " + name)
    print(json.dumps({"status": "PUBLICATION_HASH_PASS_NOT_B_ACCEPTANCE",
                      "hashed_files": len(entries), "total_files": len(actual),
                      "historical_manifest_items": len(original)}, indent=2))

if __name__ == "__main__":
    main()
