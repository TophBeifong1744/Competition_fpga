"""Freeze the accepted September 10 artifact scope from an exact Git commit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

BASE = '73352fc22ddf3f5aa5b923e7b4fadc5efd8fa6ad'
ACQ = 'task-packages/PKG-A-ACQ/'
SCOPES = {
    'phase-decision': ['docs/phase-review-2026-09-10.md',
                       'docs/reviews/2026-09-10-phase-acceptance/',
                       'docs/deferred-acquisition-risks.md'],
    'A-H1-software-contract': [ACQ+'REVIEW.md', ACQ+'evidence/h1-files.json',
                              ACQ+'payload/docs/minimal-data-interface.md',
                              ACQ+'payload/examples/h1/',
                              ACQ+'payload/scripts/check_h1_fixtures.py'],
    'A-mono-diagnostic': ['task-packages/PKG-A-H2-MONO-DIAGNOSTIC/'],
    'B-receipt-and-recap-only': ['task-packages/PKG-B-ALG/tasks/0910-closeout/'],
    'C-archived-functional-work': [ACQ+'outsourcing/C-RTL-001/',
                                   ACQ+'outsourcing/C-RTL-002/',
                                   ACQ+'outsourcing/C-RTL-003/',
                                   ACQ+'outsourcing/review-status/b-c002003-20260910.md'],
    'C-microphone-evidence': ['hardware/evidence/microphone-c-2026-09-09/'],
}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(out):
    manifest = json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    archive = out/'accepted-artifacts.zip'
    assert digest(archive.read_bytes()) == manifest['archive_sha256'], 'archive SHA mismatch'
    with zipfile.ZipFile(archive) as z:
        assert sorted(z.namelist()) == sorted(f['path'] for f in manifest['files'])
        for f in manifest['files']:
            data = z.read(f['path'])
            assert len(data) == f['bytes'] and digest(data) == f['sha256'], f['path']
    print(f"PASS_SNAPSHOT_INTEGRITY: {len(manifest['files'])} files; not a new functional review")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        verify(args.out)
        return
    if args.repo is None:
        parser.error('--repo required to build')
    args.out.mkdir(parents=True, exist_ok=True)
    archive = args.out/'accepted-artifacts.zip'
    manifest_path = args.out/'manifest.json'
    if archive.exists() or manifest_path.exists():
        raise FileExistsError('Use a new output directory; frozen outputs must not be overwritten')
    tree = git(args.repo, 'ls-tree', '-r', '-z', BASE).split(b'\0')
    records = []
    matched = set()
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for row in tree:
            if not row:
                continue
            meta, raw_path = row.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            path = raw_path.decode('utf-8')
            groups = []
            for group, prefixes in SCOPES.items():
                for prefix in prefixes:
                    if path == prefix or (prefix.endswith('/') and path.startswith(prefix)):
                        matched.add(prefix)
                        groups.append(group)
            if not groups:
                continue
            if kind != 'blob' or mode not in ('100644', '100755'):
                raise ValueError(f'Unexpected entry {path}: {mode}/{kind}')
            data = git(args.repo, 'cat-file', 'blob', oid)
            info = zipfile.ZipInfo(path, date_time=(2026, 9, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = int(mode, 8) << 16
            z.writestr(info, data)
            records.append(dict(path=path, blob=oid, bytes=len(data), sha256=digest(data), scope=groups))
    missing = set(p for prefixes in SCOPES.values() for p in prefixes) - matched
    if missing:
        raise ValueError(f'Missing declared paths: {sorted(missing)}')
    manifest = dict(schema_version=1, source_commit=BASE,
                    scope='September 10 phase accepted artifacts; no full H2/H3/M1 or V1 approval',
                    excludes=['C-RTL-004', 'unreviewed FFT/DDR/algorithm packages',
                              'full six-mic simulation deliverable', 'third-party datasheet PDF'],
                    archive_sha256=digest(archive.read_bytes()), files=records)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    verify(args.out)


if __name__ == '__main__':
    main()
