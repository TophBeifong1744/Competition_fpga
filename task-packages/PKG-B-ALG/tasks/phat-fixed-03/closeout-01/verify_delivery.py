"""Check this delivery's bytes, local links and recorded analysis outputs."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    manifest = json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    assert actual == set(manifest['files']) | {'manifest.json'}, 'Missing or unlisted files'
    for name, digest in manifest['files'].items():
        assert sha(HERE/name) == digest, name
    links = 0
    for p in HERE.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
            assert (p.parent/target).exists(), (p.name,target)
            links += 1
    v = json.loads((HERE/'evidence/run01/verification.json').read_text())
    assert sha(HERE/'analyze.py') == v['analysis_sha256']
    for name, digest in v['output_hashes'].items():
        assert sha(HERE/'evidence/run01'/name) == digest, name
    print(f"Verified {len(manifest['files'])} delivery files, {links} local links, analysis source and outputs")

if __name__ == '__main__': main()
