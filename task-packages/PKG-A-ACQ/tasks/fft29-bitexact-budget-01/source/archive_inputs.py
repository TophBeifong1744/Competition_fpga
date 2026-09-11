"""Export pinned Git blobs byte-for-byte; never regenerate acoustic inputs.

Usage: python archive_inputs.py --repo <B clone> --out <NEW reference directory>
Optional --fetch obtains selected blobs from that clone's origin before export.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

SHA = 'bff45e7bbedab321fc4815e1432f1575c750edc4'
PREFIX = 'task-packages/PKG-B-ALG/tasks/phat-fixed-03/dynamic-range/'
EXPONENTS = [1, 16, 17, 18, 20, 21, 24]
CASES = [g * 24 + e - 1 for g in range(8) for e in EXPONENTS] + list(range(192, 196))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--fetch', action='store_true')
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit('Refusing to overwrite reference directory')
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(a.repo), *args], env=env)
    assert git('rev-parse', SHA).decode().strip() == SHA
    tree = {}
    for entry in git('ls-tree', '-r', '-z', SHA).split(b'\0'):
        if entry:
            meta, name = entry.split(b'\t', 1)
            tree[name.decode()] = meta.split()[2].decode()
    small = ['README.md', 'protocol.json', 'scan.py', 'check_model.py', 'manifest.json',
             'evidence/analytic01/checks.json', 'evidence/run01/summary.json',
             'evidence/run01/frames.json.gz', 'evidence/run01/packing.json']
    names = [PREFIX + p for p in small]
    names += [PREFIX + f'evidence/run01/case-{c:03d}.npz' for c in CASES]
    extra = ['task-packages/PKG-B-ALG/tasks/phat-fixed-03/integration/chain.py',
             'task-packages/PKG-B-ALG/tasks/phat-fixed-03/phat_model.py',
             'task-packages/PKG-B-ALG/tasks/fft-window-02/window_model.py',
             'task-packages/PKG-B-ALG/tasks/fft-bitexact-01/compare_cmodel.py',
             'task-packages/PKG-B-ALG/payload/model/python/six_mic_baseline_core.py']
    names += extra
    absent = [n for n in names if n not in tree]
    if absent:
        raise SystemExit(f'Missing required paths: {absent}')
    fetch_records = []
    if a.fetch:
        # One object per request: multi-blob requests repeatedly timed out here.
        present = set(git('cat-file', '--batch-all-objects', '--batch-check=%(objectname)').decode().split())
        missing = [tree[n] for n in names if tree[n] not in present]
        for offset, oid in enumerate(missing):
            oids = [oid]
            cmd = ['git', '-C', str(a.repo), '-c', 'http.version=HTTP/1.1',
                   '-c', 'http.postBuffer=16777216', '-c', 'credential.interactive=false',
                   'fetch', '--refetch', '--no-filter', '--no-tags', '--no-write-fetch-head', 'origin', *oids]
            for attempt in range(3):
                try:
                    run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         timeout=60, env=env)
                    rc, output = run.returncode, run.stdout.decode(errors='replace')
                except subprocess.TimeoutExpired as e:
                    rc, output = 124, (e.stdout or b'').decode(errors='replace')+'\nTIMEOUT 60s'
                fetch_records.append({'command':cmd,'returncode':rc,'output':output,'attempt':attempt+1})
                print(f'fetch {offset + 1}/{len(missing)} attempt={attempt+1}: {rc}',flush=True)
                if rc == 0:
                    break
                a.out.parent.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
                (a.out.parent / f'fetch-failed-{stamp}.json').write_text(
                    json.dumps(fetch_records, indent=2)+'\n',encoding='utf-8')
            if rc:
                raise SystemExit(output)
    a.out.mkdir(parents=True)
    manifest = json.loads(git('cat-file', 'blob', tree[PREFIX+'manifest.json']))
    records = []
    for name in names:
        data = git('cat-file', 'blob', tree[name])
        digest = hashlib.sha256(data).hexdigest()
        local = name.removeprefix(PREFIX) if name.startswith(PREFIX) else 'dependencies/' + name
        expected = manifest.get(local)
        if expected and digest != expected:
            raise RuntimeError(f'B manifest SHA256 mismatch: {name}')
        blob_hash = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert blob_hash == tree[name]
        target = a.out / local
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append({'source': name, 'local': local, 'git_blob': tree[name],
                        'sha256': digest, 'bytes': len(data), 'b_manifest_verified': bool(expected)})
    summary = json.loads((a.out/'evidence/run01/summary.json').read_bytes())
    for source, expected in summary['sources'].items():
        rel = source.replace('\\','/').split('/task-packages/',1)[1]
        match = next(r for r in records if r['source'] == 'task-packages/'+rel)
        assert match['sha256'] == expected, source
    result = {'source_commit': SHA, 'exponents': EXPONENTS, 'selected_cases': CASES,
              'unselected_cases': [i for i in range(196) if i not in CASES],
              'files': records, 'missing_from_git_but_in_b_manifest':
              [p for p in manifest if PREFIX+p not in tree],
              'fetch_records': fetch_records}
    (a.out/'provenance.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'exported':len(records), 'selected_cases':len(CASES),
                      'unselected_cases':196-len(CASES),
                      'manifest_missing':result['missing_from_git_but_in_b_manifest']}))


if __name__ == '__main__':
    main()
