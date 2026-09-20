"""Static document/provenance check only; does not run framing or numeric tests."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[3]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    bindings = json.loads((ROOT / 'evidence/response-20260923-bindings.json').read_text(encoding='utf-8'))
    for item in bindings['git_files']:
        raw = subprocess.check_output(['git', 'show', item['commit'] + ':' + item['path']], cwd=REPO)
        assert digest(raw) == item['sha256'], item['path']
    for item in bindings['working_documents']:
        assert digest((ROOT / item['snapshot']).read_bytes()) == item['sha256'], item['snapshot']
    old = json.loads((ROOT / 'evidence/package-seal-before-response-28d5c775.json').read_text(encoding='utf-8'))
    for name, sha in old['files'].items():
        assert digest((ROOT / name).read_bytes()) == sha, name
    assert 4 * 7366 + 6 * 7406 == 73900
    assert 100000000 * 512 // 48000 == 1066666
    assert sum([32768,4096,16416,4104,8192,4096,160,4096,16128,1024]) == 91080
    print('STATIC_RESPONSE_PASS', len(bindings['git_files']), 'git files;', len(old['files']), 'unchanged historical files; 2 working documents')
    print('NOT_RUN: framing differential, fixed4 boundary, AMD simulation, hardware, full WCET')

if __name__ == '__main__':
    main()
