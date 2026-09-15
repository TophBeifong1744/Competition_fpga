"""Read-only verification of the exact candidate files before operator loading."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--release',required=True);a=p.parse_args()
root=Path(a.release).resolve(strict=True)
manifest=json.loads((root/'SHA256.json').read_text(encoding='utf-8'))
for name,digest in manifest.items():
    f=(root/name).resolve(strict=True)
    if root not in f.parents:raise SystemExit('manifest escapes release')
    actual=hashlib.sha256(f.read_bytes()).hexdigest()
    if actual!=digest:raise SystemExit('HASH_MISMATCH '+name)
record=json.loads((root/'VERIFIED-BUILD.json').read_text(encoding='utf-8'))
if record['status']!='CANDIDATE_BUILD_PASS_NOT_BOARD':raise SystemExit('build not ready')
print('RELEASE_HASH_PASS_NOT_BOARD_TEST files='+str(len(manifest)))
for name in ('system_continuous.bit','four_mic_continuous.elf','system_continuous.xsa'):
    print(name+' '+manifest[name])
