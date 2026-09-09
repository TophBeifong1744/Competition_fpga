"""Strict historical integrity and bounded numerical comparisons for PR #3.

Current REVIEW.md is appendable. Only its explicitly pinned historical reference
is read from a snapshot; algorithm, protocol and evidence paths are never remapped.
"""
import contextlib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKAGES = ['tonal-edge-01', 'narrowband-guard-01', 'subband-confidence-01',
            'leave-band-out-01', 'effective-perturbation-01', 'stable-wrong-01']
HISTORY_SHA = '25a6257fe3136b058cefa06e86fde0f3c8dd8dff'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def verify_entries(directory, entries):
    for relative, expected in entries.items():
        path = Path(directory)/relative
        assert path.is_file(), f'missing declared file: {path}'
        assert sha(path) == expected, f'file SHA-256: {path}'


def verify_package(root=ROOT):
    root = Path(root)
    binding = read(HERE/'history.json')
    snapshot = HERE/'history/REVIEW.md'
    assert sha(snapshot) == binding['sha256'], 'historical review snapshot'
    blob = snapshot.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest() == binding['git_blob'], 'historical Git blob'
    manifests, frozen = {}, {}
    for name in PACKAGES:
        directory = root/'research'/name
        manifest = read(directory/'files.json')
        entries = manifest.get('files', manifest)
        verify_entries(directory, entries)
        manifests[name] = len(entries)
        for relative, expected in read(directory/'fixed-files.json').items():
            path = snapshot if relative == 'REVIEW.md' else root/relative
            if relative == 'REVIEW.md':
                assert expected == binding['sha256'], 'unexpected historical review version'
            assert path.is_file(), f'missing frozen file: {relative}'
            assert sha(path) == expected, f'frozen SHA-256: {relative}'
            frozen[relative] = expected
    return dict(status='PASS',manifest_counts=manifests,manifest_entries=sum(manifests.values()),
                unique_frozen_files=len(frozen),historical_review=binding,
                current_review_sha256=sha(root/'REVIEW.md'),
                current_review_is_not_historical_evidence=True)


def angle(u, v=(1., 0., 0.)):
    """Scale-invariant atan2 angle; no near-zero arccos cancellation."""
    u, v = np.asarray(u, dtype=float), np.asarray(v, dtype=float)
    assert u.shape == v.shape == (3,) and np.isfinite(u).all() and np.isfinite(v).all()
    assert np.linalg.norm(u) > 0 and np.linalg.norm(v) > 0
    u, v = u / np.linalg.norm(u), v / np.linalg.norm(v)
    return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(u, v)), np.dot(u, v))))


class Differences:
    def __init__(self):
        self.values = {}
        self.inputs = []

    def numeric(self, old, new, field, angular=False, atol=1e-8):
        assert math.isfinite(old) and math.isfinite(new), field
        if angular:
            # IEEE binary64 norm+normalization+3-term dot operation budget.
            # gamma(16) bounds accumulated first-order roundoff in the cosine.
            # Map that cosine interval through acos rather than impose a large
            # constant angular tolerance. 1e-10 deg is the conversion floor.
            epsilon = np.finfo(float).eps
            budget = 16*epsilon/(1-16*epsilon)
            cosine = math.cos(math.radians(new))
            low = math.degrees(math.acos(min(1., cosine+budget)))
            high = math.degrees(math.acos(max(-1., cosine-budget)))
            tolerance = max(new-low, high-new, 1e-10)
        else:
            tolerance = atol
        delta = abs(old-new)
        record = self.values.setdefault(field, dict(count=0, max_absolute_difference=0., max_allowed=0.))
        record['count'] += 1
        record['max_allowed'] = max(record['max_allowed'], tolerance)
        if delta > record['max_absolute_difference']:
            record.update(max_absolute_difference=delta, old_at_max=old, new_at_max=new, allowed_at_max=tolerance)
        assert delta <= tolerance, (field, old, new, delta, tolerance)

    def input(self, historical, rebuilt):
        """Exact-input profile. A mismatch is NEVER numerical equivalence."""
        row = dict(condition=historical['condition'], seed=historical['seed'], hashes={})
        for key in ['input_sha256','target_sha256','noise_sha256','rir_sha256']:
            row['hashes'][key] = dict(historical=historical[key], rebuilt=rebuilt[key], equal=historical[key]==rebuilt[key])
        self.inputs.append(row)
        assert all(v['equal'] for v in row['hashes'].values()), (
            'UNSUPPORTED_EXACT_INPUT_ENVIRONMENT: historical waveform not stored; '
            'hash mismatch does not establish equal input. See environment.json.', row)


DIFF = Differences()


def environment():
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        np.show_runtime()
        np.show_config()
    native = {}
    for folder in [Path(np.__file__).parent, Path(np.__file__).parent.parent/'numpy.libs']:
        if folder.exists():
            for path in sorted(folder.rglob('*')):
                if path.suffix in ['.dll','.pyd','.so']:
                    native[path.name] = sha(path)
    return dict(python=sys.version,executable_sha256=sha(sys.executable),numpy=np.__version__,
                platform=platform.platform(),machine=platform.machine(),processor=platform.processor(),
                byteorder=sys.byteorder,numpy_runtime=buffer.getvalue(),native_sha256=native,
                cpu_environment={k:os.environ.get(k) for k in ['NPY_DISABLE_CPU_FEATURES','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},
                waveform_policy='Exact historical hashes required. Different hashes fail; no claim of cross-environment sample equality without full historical waveforms.')
