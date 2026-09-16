"""Verify the delivered bytes, or compare a new real replay with frozen evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def compare_values(a, b, path, stats):
    if isinstance(a, dict):
        if not isinstance(b, dict) or a.keys() != b.keys():
            raise ValueError('DICTIONARY_KEYS: '+path)
        for key in a: compare_values(a[key], b[key], path+'/'+key, stats)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            raise ValueError('LIST_LENGTH: '+path)
        for i, (x,y) in enumerate(zip(a,b)): compare_values(x,y,path+'/'+str(i),stats)
    elif type(a) is float:
        if type(b) is not float or not math.isfinite(a) or not math.isfinite(b):
            raise ValueError('NONFINITE_OR_TYPE: '+path)
        stats['float_values'] += 1
        stats['max_abs_error'] = max(stats['max_abs_error'], abs(a-b))
        if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10):
            raise ValueError('NUMERICAL_DIFFERENCE: '+path)
    else:
        stats['discrete_values'] += 1
        if type(a) is not type(b) or a != b:
            raise ValueError('DISCRETE_DIFFERENCE: '+path)


def verify():
    manifest = load(HERE/'MANIFEST.json')
    actual_files = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    expected_files = set(manifest) | {'MANIFEST.json'}
    if actual_files != expected_files:
        raise ValueError('PACKAGE_FILE_SET_CHANGED: '+str(actual_files ^ expected_files))
    for relative, expected in manifest.items():
        if sha(HERE/relative) != expected: raise ValueError('PACKAGE_HASH: '+relative)
    pins = load(HERE/'pins.json')
    for relative, expected in pins.items():
        if sha(ROOT/relative) != expected: raise ValueError('INPUT_SOURCE_HASH: '+relative)
    source_map = load(HERE/'evidence/run01/replay/summary.json')['sources']
    for relative, expected in source_map.items():
        if sha(ROOT/relative) != expected: raise ValueError('TESTED_SOURCE_HASH: '+relative)
    return dict(status='BYTE_BINDINGS_PASS', package_files=len(manifest), input_source_pins=len(pins),
                tested_sources=len(source_map), approval='author check only')


def compare(other):
    reference = HERE/'evidence/run01/replay'
    stats = dict(float_values=0, discrete_values=0, max_abs_error=0.0)
    byte_comparisons = {}
    for filename in ('center-frames.json','quiet-frames.json'):
        compare_values(load(reference/filename),load(other/filename),filename,stats)
        byte_comparisons[filename] = sha(reference/filename) == sha(other/filename)
    a, b = load(reference/'summary.json'), load(other/'summary.json')
    for key in ('config','effective_tracker','pins','recordings','timing','limits'):
        compare_values(a[key],b[key],'summary/'+key,stats)
    # New verification-only tools may be present in the rerun. Every originally
    # tested executable/config must still match; added files are separately bound.
    for path, digest in a['sources'].items():
        if b['sources'].get(path) != digest: raise ValueError('EXECUTABLE_SOURCE_CHANGED: '+path)
    byte_comparisons['summary.json'] = sha(reference/'summary.json') == sha(other/'summary.json')
    return dict(status='NUMERIC_AND_DISCRETE_REPLAY_PASS', statistics=stats,
                tolerance=dict(atol=1e-10,rtol=1e-10), file_bytes_equal=byte_comparisons,
                reference_environment=a['environment'], new_environment=b['environment'],
                excluded_from_value_comparison=['elapsed_host_seconds','environment','checkout_head',
                                                'additional verification-only source hashes'],
                note='Input/source hashes exact; all frame/recording values checked, not only counts. No acoustic acceptance.')


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--compare', type=Path, help='new run.py output directory')
    args = parser.parse_args()
    result = compare(args.compare) if args.compare else verify()
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
