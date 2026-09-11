"""Generate only stream packing from archived integer windowed inputs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rne(array, shift):
    if shift == 0:
        return array.copy()
    # Floor quotient with nonnegative remainder also implements negative ties.
    q = array >> shift
    rem = array - (q << shift)
    half = 1 << (shift-1)
    return q + ((rem > half) | ((rem == half) & ((q & 1) != 0))).astype(np.int64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reference', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit('Refusing to overwrite vectors')
    provenance = json.loads((a.reference/'provenance.json').read_bytes())
    manifest = json.loads((a.reference/'manifest.json').read_bytes())
    for r in provenance['files']:
        assert sha(a.reference/r['local']) == r['sha256'], r['local']
    frames = json.loads(gzip.decompress((a.reference/'evidence/run01/frames.json.gz').read_bytes()))
    assert len(frames) == 196 and [f['case'] for f in frames] == list(range(196))
    inputs, expected, jobs, adapter = [], [], [], []
    for case in provenance['selected_cases']:
        frame = frames[case]
        rel = f'evidence/run01/case-{case:03d}.npz'
        path = a.reference/rel
        assert sha(path) == manifest[rel] == frame['npz_sha256']
        with np.load(path, allow_pickle=False) as z:
            win = z['windowed']
            raw = z['wide29_raw_fft']
            assert win.shape == (6,1024) and win.dtype == np.int64
            assert raw.shape == (6,1024,2) and raw.dtype == np.int64
            stream = win * 16  # Exact widening, no quantizer/window/acoustic generator.
            assert np.all((stream >= -(1<<28)) & (stream < (1<<28)))
            assert np.all((raw >= -(1<<28)) & (raw < (1<<28)))
            shift = 0
            while not np.all((rne(raw,shift) >= -(1<<24)) & (rne(raw,shift) < (1<<24))):
                shift += 1
            assert shift == frame['candidates']['wide29']['common_right_shift']
            assert np.array_equal(rne(raw,shift),z['wide29_packed_fft'])
            adapter.append({'case':case,'shift':shift,'packed_exact':True,
                            'evidence_level':'independent_software_only_not_RTL'})
            for channel in range(6):
                jobs.append({'job':len(jobs),'case':case,'channel':channel,
                             'backpressure':False,
                             'expected_overflow':frame['candidates']['wide29']['flags']['fft_overflow'][channel],
                             'scenario':frame['scenario'],'peak_exponent':frame['peak_exponent']})
                inputs.append(stream[channel].copy())
                expected.append(raw[channel].copy())
    # Repeat nonzero archived case 000/ch0 under both input gaps and output stalls.
    jobs.append(dict(jobs[0],job=len(jobs),backpressure=True))
    inputs.append(inputs[0].copy())
    expected.append(expected[0].copy())
    a.out.mkdir(parents=True)
    with (a.out/'inputs.mem').open('w',encoding='ascii',newline='\n') as f:
        for vec in inputs:
            for v in vec:
                # S29 real in bits 28:0, three padding bits; imaginary zero in 60:32.
                f.write(f'{int(v)&((1<<29)-1):016x}\n')
    (a.out/'job-count.mem').write_text(str(len(jobs))+'\n',encoding='ascii')
    np.save(a.out/'expected.npy',np.stack(expected),allow_pickle=False)
    result = {'source_commit':provenance['source_commit'],
              'selected_cases':provenance['selected_cases'],
              'unselected_cases':provenance['unselected_cases'],
              'acoustic_frames':len(provenance['selected_cases']),
              'unique_transforms':len(jobs)-1,'backpressure_repeats':1,
              'jobs':jobs,'software_adapter_checks':adapter,
              'inputs_mem_sha256':sha(a.out/'inputs.mem'),
              'expected_npy_sha256':sha(a.out/'expected.npy')}
    (a.out/'selection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('jobs','software_adapter_checks')}))


if __name__ == '__main__':
    main()
