"""A review only: independent CSV/PCM checks, old-bug replay and fresh-frame bridge.

Does not edit B files. Outputs are always created in a new directory.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
import wave

import numpy as np


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def pcm(path):
    with wave.open(str(path), 'rb') as wav:
        assert (wav.getnchannels(), wav.getframerate(), wav.getsampwidth()) == (1, 48000, 3)
        raw = wav.readframes(wav.getnframes())
    return np.array([int.from_bytes(raw[i:i+3], 'little', signed=True)
                     for i in range(0, len(raw), 3)], dtype=np.int64)


def independent_weights(events, size, start, stop, fade):
    # Piecewise reconstruction independent of B's mixer implementation/NPZ.
    deadlines = np.full(size, -np.inf)
    initial = np.zeros(size)
    initial[0] = 1
    initial_time, target, cursor = 0, 0, 0

    def evaluate(t):
        progress = np.clip((t-initial_time)/fade, 0, 1)
        result = np.zeros(size)
        for j in range(1, size):
            now = np.clip((deadlines[j]+1-t)/fade, 0, 1)
            then = np.clip((deadlines[j]+1-initial_time)/fade, 0, 1)
            result[j] = initial[j]*(1-progress)*(now/then if then > 0 else 0)
            if j == target:
                result[j] += progress*now
        result[0] = 1-result[1:].sum()
        return result

    values = []
    for t in range(start, stop):
        while cursor < len(events) and events[cursor]['ready'] <= t:
            e = events[cursor]
            if e['fresh'] or e['target'] != target:
                initial = evaluate(e['ready'])
                target, initial_time = e['target'], e['ready']
                if target:
                    deadlines[target] = e['valid_through']
            cursor += 1
        values.append(evaluate(t))
    return np.array(values)


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--runs', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root, runs, out = args.repo.resolve(), args.runs.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    parent = root/'task-packages/PKG-B-ALG/tasks/four-channel-track-01'
    audio = parent/'audio-01'
    original = {p.relative_to(parent).as_posix(): sha(p) for p in parent.rglob('*') if p.is_file()}
    cfg = read(parent/'config.json')
    rendered = runs/'audio-run01/audio'
    result = read(rendered/'result.json')
    records = []
    for row, source in zip(result['records'], cfg['recordings']):
        assert row['label'] == source['label']
        with (root/source['directory']/'samples.csv').open(newline='', encoding='utf-8') as f:
            raw = list(csv.DictReader(f))
        assert all(r['stream_error'] == '0' and r['error_flags'] == '' for r in raw)
        ids = [int(r['sample_id']) for r in raw]
        assert all(b-a == 1 for a, b in zip(ids, ids[1:]))
        codes = np.array([[int(r[f'mic{ch}']) for ch in range(4)] for r in raw], dtype=np.int64)
        assert np.all((codes >= -2**23) & (codes < 2**23))
        assert row['reference_rows'] == [8, 31992] and row['samples'] == 31984
        assert [row['first_reference_sample_id'], row['last_reference_sample_id']] == [str(ids[8]), str(ids[31991])]
        n = np.arange(8, 31992)
        positions = np.array(cfg['positions_m'], dtype=float)
        delays = [(positions-positions[0])@np.array(v)*48000/343
                  for v in row['bank_vectors'][1:]]
        manual_delay = (positions-positions[0])@np.array([1, 0, 0])*48000/343
        np.testing.assert_allclose(manual_delay, [0, 5.597667638484, 5.597667638484, 0], atol=1e-12, rtol=0)

        def beam(d):
            assert np.all(np.ceil(n[:, None]-d) <= n[:, None]+8)
            return sum(np.interp(n-d[ch], np.arange(len(codes)), codes[:, ch]) for ch in range(4))/4

        bank = np.array([codes[n, 0]]+[beam(d) for d in delays])
        weights = independent_weights(row['events'], len(bank), 8, 31992, 480)
        with np.load(rendered/f'{row["label"]}-interval00-mix.npz') as stored:
            maximum_weight_error = float(np.max(np.abs(weights-stored['weights'])))
            np.testing.assert_allclose(weights, stored['weights'], atol=1e-14, rtol=0)
        expected = dict(single=codes[n, 0], manual=beam(manual_delay),
                        automatic=np.sum(bank.T*weights, axis=1))
        comparisons = []
        for entry in row['files']:
            actual = pcm(rendered/entry['file'])
            wanted = np.rint(expected[entry['branch']]*entry['gain']).astype(np.int64)
            assert np.all((wanted >= -2**23) & (wanted < 2**23))
            np.testing.assert_array_equal(actual, wanted)
            historical = audio/'evidence/run02/audio'/entry['file']
            comparisons.append(dict(file=entry['file'], codes=len(actual), max_code_error=0,
                                    author_bytes_equal=sha(historical)==sha(rendered/entry['file'])))
        first_beam = np.flatnonzero(weights[:, 1:].sum(axis=1) > 0)
        first_beam = int(n[first_beam[0]]) if len(first_beam) else None
        assert first_beam == (12289 if row['label']=='center' else None)
        records.append(dict(label=row['label'], max_weight_error=maximum_weight_error,
                            first_nonzero_beam_reference_row=first_beam, files=comparisons))

    # Replay the exact two current regression tests against the hash-bound OLD
    # implementation, imported under another name; no author file is overwritten.
    tests = module('a_review_audio_tests', audio/'test_audio.py')
    old = module('a_review_before_fix', audio/'history/before-expiry-fix/mixer.py')
    old_tests = ['test_change_direction_during_expiry_fade_is_continuous',
                 'test_release_during_expiry_fade_is_continuous']
    tests.Crossfade = old.Crossfade
    suite = unittest.TestSuite(tests.FadeContract(name) for name in old_tests)
    with (out/'expected-old-failures.log').open('x', encoding='utf-8') as log:
        run = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    assert run.testsRun == 2 and len(run.failures) == 2 and not run.errors
    jumps = []
    for target in (0, 2):
        f = old.Crossfade(3, 4)
        f.select(1, 0, 10)
        before = f.weights(9)
        f.select(target, 9, 100 if target else None)
        jumps.append(float(np.max(np.abs(f.weights(9)-before))))
    assert jumps == [.25, .25]

    # Bridge independently regenerated parent frames to the audio renderer.
    render = sys.modules['render_three']
    bridge = []
    for source, saved in zip(cfg['recordings'], result['records']):
        recording = render.ReaderSession().load(root/source['directory'])
        frames = read(runs/'parent-run01/replay'/f'{source["label"]}-frames.json')
        vectors, events = render.prepare_events(frames, recording.sample_ids, 0, len(recording.samples), 0, cfg)
        fresh = render.render_clean(render.adapt_h1(recording).samples, vectors, events, cfg, result['config'])
        max_float_error = 0.
        for a, b in zip(saved['bank_delays_samples'][1:], fresh['delays'][1:]):
            max_float_error = max(max_float_error, float(np.max(np.abs(np.array(a)-b))))
        for entry in saved['files']:
            actual = pcm(rendered/entry['file'])
            wanted = np.rint(fresh[entry['branch']]*2**23*entry['gain']).astype(np.int64)
            np.testing.assert_array_equal(actual, wanted)
        bridge.append(dict(label=source['label'], max_delay_error=max_float_error, pcm_exact=True))

    refusals = []
    commands = [
        [sys.executable, '-B', str(audio/'reproduce.py'), '--out', str(runs/'audio-run01')],
        [sys.executable, '-B', str(audio/'render_three.py'), '--out', str(rendered)],
        [sys.executable, '-B', str(audio/'audit.py'), '--directory', str(rendered), '--out', str(runs/'audio-run01/audit.json')],
        [sys.executable, '-B', str(parent/'reproduce.py'), '--out', str(runs/'parent-run01')]]
    before_outputs = {p.relative_to(runs).as_posix():sha(p) for p in runs.rglob('*') if p.is_file() and out not in p.parents}
    for i, command in enumerate(commands):
        proc = subprocess.run(command, cwd=root, capture_output=True)
        assert proc.returncode != 0
        (out/f'expected-overwrite-refusal-{i}.log').write_bytes(proc.stdout+proc.stderr)
        refusals.append(dict(command=command, returncode=proc.returncode))
    assert before_outputs == {p.relative_to(runs).as_posix():sha(p) for p in runs.rglob('*') if p.is_file() and out not in p.parents}
    assert original == {p.relative_to(parent).as_posix(): sha(p) for p in parent.rglob('*') if p.is_file()}
    report = dict(status='A_INDEPENDENT_LIMITED_NUMERICAL_CHECK_PASS', records=records,
                  pcm_values=sum(f['codes'] for r in records for f in r['files']),
                  old_regressions=dict(tests=2, expected_failures=2, weight_jumps=jumps),
                  fresh_parent_bridge=bridge, overwrite_refusals=refusals,
                  author_package_unchanged=True, original_outputs_unchanged=True,
                  limits='No target presence, subjective listening by A, acoustic benefit, real-time, board or H3 approval.')
    (out/'independent.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
