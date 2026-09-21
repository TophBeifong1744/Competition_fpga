"""R1/R2-only regressions; no numeric model, transforms or acoustic imports."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types

BASE = 'd3d2a3d4e78932830bf12bd84c0517b0a2092872'
PACKAGE = 'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921'


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def execute(repo, out):
    out.mkdir(parents=True, exist_ok=False)
    package = repo/PACKAGE
    path = package/'trace_scoreboard.py'
    spec = importlib.util.spec_from_file_location('repaired_trace', path)
    current = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(current)
    original_bytes = subprocess.check_output(['git', 'show', BASE+':'+PACKAGE+'/trace_scoreboard.py'], cwd=repo)
    original = types.ModuleType('original_trace')
    exec(compile(original_bytes, '<original-d3d2a3d>', 'exec'), original.__dict__)
    (out/'original_trace_scoreboard.py').write_bytes(original_bytes)
    fixture = json.loads((package/'evidence/run05/checks/valid-trace.json').read_text())
    cases = []

    def add(name, rows, error=None, units=('fft', 'ifft'), original_accepts=False):
        cases.append(dict(name=name, rows=rows, error=error, units=units, original_accepts=original_accepts))

    def changed(name, mutate, error, original_accepts=False):
        rows = copy.deepcopy(fixture)
        mutate(rows)
        add(name, rows, error, original_accepts=original_accepts)

    # A provided the report, not its probe files. These reproduce its exact
    # described mutations from our original fixture, without claiming A-file receipt.
    changed('A-R1-available-before-final-status', lambda r: r[3]['events'][1].update(available=0),
            'availability precedes required status visibility', True)
    changed('A-R2-float-sample-identity', lambda r: r[9]['payload'].update(source_sample=0.0, available=8.0),
            'integer source_sample required', True)
    add('same-tick-final-status-and-commit', copy.deepcopy(fixture))

    def event_only(*, available=2, expiry=10, commit_now=4, units=('fft', 'ifft'), downstream=False):
        rows = [dict(tick=0, now=0, session='s0', reset=True, valid=False, ready=True,
                     events=[dict(kind='submit', session='s0', frame=0, config='fixed', expected=list(units))]),
                dict(tick=1, now=1, session='s0', valid=False, ready=True,
                     events=[dict(kind='status', session='s0', frame=0, unit='fft')]),
                dict(tick=2, now=2, session='s0', valid=False, ready=True,
                     events=[dict(kind='status', session='s0', frame=0, unit='ifft')])]
        if downstream:
            rows.append(dict(tick=3, now=3, session='s0', valid=False, ready=True,
                             events=[dict(kind='status', session='s0', frame=0, unit='doa')]))
        rows.append(dict(tick=len(rows), now=commit_now, session='s0', valid=False, ready=True,
                         events=[dict(kind='commit', session='s0', frame=0, config='fixed',
                                      available=available, valid_through=expiry)]))
        return rows

    add('delayed-commit-at-completion-time', event_only())
    add('delayed-commit-later-availability', event_only(available=3))
    add('same-sample-different-capture-tick', event_only(commit_now=2))
    add('expiry-equality', event_only(expiry=4))
    add('delayed-commit-backdated', event_only(available=1), 'availability precedes required status visibility', original_accepts=True)
    add('future-commit-availability', event_only(available=5), 'future or expired commit')
    add('expired-delayed-commit', event_only(expiry=3), 'future or expired commit')
    extended = ('fft', 'ifft', 'doa')
    add('downstream-completion-bound', event_only(available=3, units=extended, downstream=True), units=extended)
    add('downstream-cannot-be-backdated', event_only(available=2, units=extended, downstream=True),
        'availability precedes required status visibility', units=extended, original_accepts=True)
    rows = event_only(units=extended)
    add('downstream-missing-blocks-commit', rows, 'non-atomic commit', units=extended)
    rows = event_only()
    rows[-1]['events'].append(dict(kind='error', session='s0', frame=0))
    add('same-tick-error-blocks-delayed-commit', rows, 'non-atomic commit')
    # Independent transaction identity: a previous frame's early completion is insufficient.
    for available, error in ((2, 'availability precedes required status visibility'), (6, None)):
        rows = event_only()
        for now, event in ((5, dict(kind='submit', config='fixed', expected=['fft','ifft'])),
                           (6, dict(kind='status', unit='fft')),
                           (6, dict(kind='status', unit='ifft')),
                           (7, dict(kind='commit', config='fixed', available=available, valid_through=9))):
            rows.append(dict(tick=len(rows), now=now, session='s0', valid=False, ready=True,
                             events=[dict(event, session='s0', frame=1)]))
        add('per-frame-completion-'+str(available), rows, error)
    # Session-local time restarts; old completion must not raise the new lower bound.
    rows = event_only()
    fresh = event_only(commit_now=2)
    for row in fresh:
        row['tick'] += len(rows)
        row['session'] = 's1'
        for event in row['events']:
            event['session'] = 's1'
    add('reset-new-session-restarts-time', rows+fresh)
    maximum = 2**64-1
    rows = event_only(available=maximum, expiry=maximum, commit_now=maximum)
    rows[1]['now'] = maximum-1
    rows[2]['now'] = maximum
    add('uint64-maximum-completion', rows)
    for value in (True, 2.0, -1, 2**64):
        add('commit-available-domain-'+repr(value), event_only(available=value), 'future or expired commit')

    # Check schema before comparisons on every valid beat, whether accepted or held.
    invalid = [('source-float-zero', 9, 'source_sample', 0.0, 'integer source_sample required', True),
               ('source-bool-false', 9, 'source_sample', False, 'integer source_sample required', True),
               ('source-bool-true', 10, 'source_sample', True, 'integer source_sample required', True),
               ('startup-source-float', 1, 'source_sample', -8.0, 'integer source_sample required', True),
               ('source-below-startup', 1, 'source_sample', -9, 'source_sample outside profile domain', False),
               ('source-above-profile', 9, 'source_sample', 2**64-8, 'source_sample outside profile domain', False),
               ('source-uint64-overflow', 9, 'source_sample', 2**64, 'source_sample outside profile domain', False),
               ('available-float', 9, 'available', 8.0, 'uint64 output available required', True),
               ('available-bool-false', 1, 'available', False, 'uint64 output available required', True),
               ('available-bool-true', 2, 'available', True, 'uint64 output available required', True),
               ('available-negative', 1, 'available', -1, 'uint64 output available required', False),
               ('available-overflow', 9, 'available', 2**64, 'uint64 output available required', False),
               ('emit-float', 9, 'emit', 8.0, 'output identity gap/duplicate', False),
               ('emit-bool', 1, 'emit', False, 'output identity gap/duplicate', False)]
    for name, index, field, value, error, old_pass in invalid:
        changed(name, lambda r, i=index, f=field, v=value: r[i]['payload'].update({f:v}), error, old_pass)
    for index, position in ((11, 'first-stall'), (12, 'held-stall'), (13, 'accept-after-stall')):
        for field, value, error in (('source_sample', 2.0, 'integer source_sample required'),
                                    ('available', 10.0, 'uint64 output available required')):
            changed(position+'-'+field, lambda r, i=index, f=field, v=value: r[i]['payload'].update({f:v}), error, True)
    # bool changes equal to 0 must also be rejected after a valid integer was held.
    rows = copy.deepcopy(fixture[:9])
    base = copy.deepcopy(fixture[9])
    for ready, source in ((False, 0), (False, False), (True, 0)):
        row = copy.deepcopy(base)
        row.update(tick=len(rows), ready=ready)
        row['payload']['source_sample'] = source
        rows.append(row)
    add('held-stall-bool-type-change', rows, 'integer source_sample required', original_accepts=True)

    results, unexpected = [], []
    for case in cases:
        rows, units = case['rows'], case['units']
        dump(out/(case['name']+'.json'), rows)
        old_result = None
        if case['original_accepts']:
            old_result = original.check(rows, max_stall_ticks=2, expected_units=units)
            assert old_result['status'] == 'TRACE_MATCHES_CANDIDATE_ONLY'
        error = None
        try:
            result = current.check(rows, max_stall_ticks=2, expected_units=units)
        except current.TraceError as exc:
            error, result = str(exc), None
        matched = (error == case['error'])
        if case['error'] is None:
            matched = matched and result == original.check(rows, max_stall_ticks=2, expected_units=units)
        item = dict(name=case['name'], expected_error=case['error'], actual_error=error,
                    matched=matched, original_misaccepted=old_result is not None, result=result)
        results.append(item)
        if not matched:
            unexpected.append(item)
    dump(out/'cases.json', results)
    summary = dict(status='AUTHOR_R1_R2_PASS' if not unexpected else 'AUTHOR_R1_R2_FAIL',
                   cases=len(cases), expected_rejections=sum(c['error'] is not None for c in cases),
                   expected_acceptances=sum(c['error'] is None for c in cases),
                   original_misacceptances_reproduced=sum(r['original_misaccepted'] for r in results),
                   unexpected=unexpected, base_commit=BASE,
                   source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   original_sha256=hashlib.sha256(original_bytes).hexdigest(),
                   fixture_sha256=hashlib.sha256((package/'evidence/run05/checks/valid-trace.json').read_bytes()).hexdigest(),
                   numeric_fft_amd_rtl_runs=0)
    dump(out/'result.json', summary)
    print(json.dumps(summary, indent=2))
    return bool(unexpected)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    sys.exit(int(execute(a.repo.resolve(), a.out.resolve())))
