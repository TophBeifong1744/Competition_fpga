"""New tests only. Original FFT/IFFT, acoustic inputs and frozen outputs untouched."""
import argparse
import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np
from cordic_candidate import normalized_atan2_q8
from trace_scoreboard import check, TraceError


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def execute(repo, out):
    out.mkdir(parents=True, exist_ok=False)
    tasks = repo / 'task-packages/PKG-B-ALG/tasks'
    fg_path = tasks / 'h3-complete-20260918/source/fixed_golden.py'
    dy_path = tasks / 'h3-interface-review-20260918/dynamic-das-20260921/dynamic_das.py'
    assert hashlib.sha256(fg_path.read_bytes()).hexdigest() == 'f6bb2bc41dee3f1e2e6d93176972d92db12d687978fd3a95a47e85b28f88a74a'
    fg = load('closeout_fg', fg_path)
    dy = load('closeout_dy', dy_path)
    fg.fixed_fft = lambda *args, **kw: (_ for _ in ()).throw(AssertionError('FFT forbidden in increment'))
    vectors = {(x, y) for x in range(-16, 17) for y in range(-16, 17) if x or y}
    for shift in (0, 3, 10, 16, 20):
        for x in (-3, -1, 0, 1, 3):
            for y in (-3, -1, 0, 1, 3):
                if x or y:
                    vectors.add((x << shift, y << shift))
    for x in (-(2**22), -(2**22)+1, -2531477, -1, 0, 1, 2531477, 2**22-1):
        for y in (-(2**22), -(2**22)+1, -1, 0, 1, 2**22-1):
            if x or y:
                vectors.add((x, y))
    rows = []
    for x, y in sorted(vectors):
        ideal = math.degrees(math.atan2(y, x)) * 256
        old = fg.atan2_q8(y, x)
        new = normalized_atan2_q8(y, x, fg.atan2_q8)
        distance = lambda a: abs((a - ideal + 180*256) % (360*256) - 180*256)
        assert distance(new) <= 1, (x, y, new, ideal)
        rows.append(dict(x=x, y=y, original_q8=old, candidate_q8=new,
                         reference_q8_float=ideal, original_error_codes=distance(old),
                         candidate_error_codes=distance(new)))
    failures = [r for r in rows if r['original_error_codes'] > 1]
    assert failures, 'must retain original tiny-vector counterexamples'
    save(out/'cordic-vectors.json', rows)
    save(out/'original-cordic-counterexamples.json', failures)
    rejects = []
    bound = 2**24-1
    for i in range(24):
        bound += (bound + 2**i - 1)//2**i + 1
    assert bound < 2**27
    save(out/'cordic-width.json', dict(normalized_abs_upper=2**24-1,
                                      xy_abs_inclusion_upper=bound, signed_bits=28,
                                      scope='conservative recurrence, not minimum width or error proof'))
    for y, x in ((0, 0), (True, 1), (1.0, 2), (0, 2**22), (0, -2**22-1), (None, 1)):
        try:
            normalized_atan2_q8(y, x, fg.atan2_q8)
        except ValueError as exc:
            rejects.append(str(exc))
        else:
            raise AssertionError(('illegal vector accepted', y, x))
    # Fraction reference is independent of DUT signed divmod implementation.
    arithmetic = []
    for d in (2, 3, 16, 480, 4096, 16384):
        for k in (-2**23, -3, -2, -1, 0, 1, 2, 3, 2**23-1):
            for r in (-1, 0, 1):
                n = k*d + d//2 + r
                expected = round(Fraction(n, d))
                assert fg.rne_div(n, d) == dy.rne(n, d) == expected
                arithmetic.append(dict(n=n, d=d, rne=expected))
    for n in (-2**23-1, -2**23, -2**23+1, 2**23-2, 2**23-1, 2**23):
        assert fg.saturate(n, 24) == (max(-2**23, min(2**23-1, n)), not -2**23 <= n < 2**23)
    save(out/'rne-vectors.json', arithmetic)
    # New dynamic adapter trace: verify actual candidate PCM at S24 extremes,
    # output identity, startup/EOF, and introduce stalls only AFTER production.
    model = dy.DynamicDAS(fade_samples=4)
    model.control(state='LOCKED', delays=[0, -32768, 32768, 1], valid_through=50)
    pcm = np.array([[(-2**23 if (i+c)%2 else 2**23-1) for i in range(24)] for c in range(4)], dtype=np.int64)
    output, traces = model.push(pcm, final=True)
    assert len(output) == 32 and all(output[:8] == 0) and model.max_history <= 17
    assert all(-2**23 <= int(v) < 2**23 for v in output)
    def reference_beam(target, n):
        def sample(ch, k):
            return int(pcm[ch, k]) if 0 <= k < pcm.shape[1] else 0
        if n < 0:
            return 0
        if target is None:
            return sample(0, n)
        total = Fraction(0)
        for ch, delay in enumerate(target):
            pos = Fraction(n) - Fraction(delay, 4096)
            left = math.floor(pos)
            frac = pos-left
            total += sample(ch, left)*(1-frac)+sample(ch, left+1)*frac
        return round(total/4)
    for value, tr in zip(output, traces):
        endpoints = tr['endpoints']
        n = tr['emit']-8
        expected = reference_beam(endpoints[0], n)
        if len(endpoints) == 2:
            expected = round(Fraction(expected*(4096-tr['alpha']) + reference_beam(endpoints[1], n)*tr['alpha'], 4096))
        assert int(value) == expected
    trace = [dict(tick=0, now=0, session='s0', reset=True, valid=False, ready=True,
                  events=[dict(kind='submit', session='s0', frame=0, config='fixture-config', expected=['fft', 'ifft'])])]
    for emit, value in enumerate(output):
        payload = dict(session='s0', emit=emit, source_sample=emit-8, available=emit, pcm=int(value))
        for ready in ([False, False, True] if emit == 10 else [True]):
            trace.append(dict(tick=len(trace), now=max(emit, trace[-1]['now']), session='s0', valid=True, ready=ready, payload=payload.copy()))
    trace[2]['events'] = [dict(kind='status', session='s0', frame=0, unit='fft')]
    trace[3]['events'] = [dict(kind='status', session='s0', frame=0, unit='ifft'),
                          dict(kind='commit', session='s0', frame=0, config='fixture-config', available=2, valid_through=20)]
    valid_result = check(trace, max_stall_ticks=2)
    assert valid_result['accepted'] == 32 and valid_result['commits'] == 1
    save(out/'valid-trace.json', trace)
    mutations = []
    def reject(name, mutate):
        test = copy.deepcopy(trace)
        mutate(test)
        try:
            check(test, max_stall_ticks=2)
        except TraceError as exc:
            mutations.append(dict(name=name, error=str(exc)))
            save(out/(name+'.json'), test)
        else:
            raise AssertionError(('trace mutation accepted', name))
    reject('unstable-stall', lambda t: t[12]['payload'].update(pcm=0))
    reject('early-available', lambda t: t[9]['payload'].update(available=999))
    reject('wrong-sample-id', lambda t: t[9]['payload'].update(source_sample=999))
    reject('stale-session-output', lambda t: t[9]['payload'].update(session='old'))
    reject('missing-status', lambda t: t[3]['events'].pop(0))
    reject('config-mismatch', lambda t: t[3]['events'][1].update(config='other'))
    reject('expired-commit', lambda t: t[3]['events'][1].update(valid_through=1))
    reject('fatal-with-output', lambda t: t[3].update(fatal=True))
    reject('duplicate-status', lambda t: t[3]['events'].insert(0, dict(kind='status', session='s0', frame=0, unit='fft')))
    reject('unbounded-stall', lambda t: t[13].update(ready=False))
    reject('duplicate-commit', lambda t: t[4].update(events=[copy.deepcopy(t[3]['events'][1])]))
    reject('non-s24-output', lambda t: t[9]['payload'].update(pcm=2**23))
    reject('weakened-status-contract', lambda t: t[0]['events'][0].update(expected=['fft']))
    reject('same-tick-error-after-commit', lambda t: t[3]['events'].append(dict(kind='error', session='s0', frame=0)))
    # Late error must suppress output immediately. A new epoch may process an
    # old callback without poisoning its outputs. No attempt to undo old PCM.
    late = copy.deepcopy(trace[:4])
    late.append(dict(tick=4, now=3, session='s0', valid=False, ready=True,
                     events=[dict(kind='error', session='s0', frame=0)]))
    late.append(dict(tick=5, now=0, session='s1', reset=True, valid=False, ready=True,
                     events=[dict(kind='error', session='s0', frame=0)]))
    late_result = check(late, max_stall_ticks=2)
    assert late_result['late_errors'] == late_result['stale_callbacks'] == 1
    save(out/'late-reset-trace.json', late)
    # reset cancels a held output; capture need not drain cancelled session.
    cancelled = copy.deepcopy(trace[:12])
    cancelled.append(dict(tick=12, now=0, session='s1', reset=True, valid=False, ready=True))
    assert check(cancelled, max_stall_ticks=2)['resets'] == 2
    save(out/'reset-cancels-stall.json', cancelled)
    save(out/'expected-rejections.json', mutations)
    summary = dict(status='AUTHOR_INCREMENT_PASS', python=sys.version, numpy=np.__version__,
                   cordic_vectors=len(rows), original_counterexamples=len(failures),
                   max_candidate_error_codes=max(r['candidate_error_codes'] for r in rows),
                   max_original_error_codes=max(r['original_error_codes'] for r in rows),
                   illegal_cordic_rejected=len(rejects), rne_vectors=len(arithmetic), saturation_vectors=6,
                   trace_faults_rejected=len(mutations), dynamic_pcm_samples=len(output),
                   trace=valid_result, late_reset=late_result, fft_runs=0, amd_runs=0, rtl_runs=0,
                   source_sha256={str(p.relative_to(repo)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (fg_path, dy_path)})
    save(out/'result.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    execute(args.repo.resolve(), args.out.resolve())
