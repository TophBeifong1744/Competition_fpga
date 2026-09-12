"""Lossless packaging of the large metadata file; preserves its exact bytes/hash."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

def digest(data):return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True)
    args=ap.parse_args();root=args.directory.resolve()
    raw_path=root/'frames.json';packed_path=root/'frames.json.gz'
    summary=json.loads((root/'summary.json').read_text())
    for name,expected in summary['sources'].items():
        assert digest(Path(name).read_bytes())==expected, name
    if raw_path.exists():
        raw=raw_path.read_bytes()
    else:
        raw=gzip.decompress(packed_path.read_bytes())
        original=json.loads((root/'packing.json').read_text())
        assert digest(raw)==original['original_sha256']
    records=json.loads(raw)
    for row in records:
        assert digest((root/row['npz']).read_bytes())==row['npz_sha256'],row['npz']
    if raw_path.exists():
        compressed=gzip.compress(raw,compresslevel=9,mtime=0)
        with packed_path.open('xb') as handle:handle.write(compressed)
        assert gzip.decompress(packed_path.read_bytes())==raw
        info=dict(original_name='frames.json',original_bytes=len(raw),original_sha256=digest(raw),
            compressed_name=packed_path.name,compressed_bytes=len(compressed),compressed_sha256=digest(compressed),
            verification='Decompressed bytes exactly equal original; all source and NPZ hashes checked before removing redundant uncompressed metadata.')
        with (root/'packing.json').open('x',encoding='utf-8') as handle:json.dump(info,handle,indent=2)
        # Only the redundant uncompressed copy is removed; gzip retains every byte.
        raw_path.unlink()
    print(f'Verified {len(summary["sources"])} source hashes and {len(records)} NPZ hashes; metadata preserved losslessly.')

if __name__=='__main__':main()
