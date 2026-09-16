"""Create once, or verify, the E1 publication manifest (old manifests unchanged)."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'publication/PACKAGE-SHA256.json'


def files():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.rglob('*')) if p.is_file() and p != MANIFEST}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    args = parser.parse_args()
    actual = files()
    if args.create:
        with MANIFEST.open('x', encoding='utf-8') as stream:
            json.dump({'scope': 'Exact publication files excluding this manifest; NOT acceptance',
                       'files': actual}, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
    expected = json.loads(MANIFEST.read_text(encoding='utf-8'))['files']
    if expected != actual:
        raise ValueError({'missing': sorted(expected.keys() - actual.keys()),
                          'extra': sorted(actual.keys() - expected.keys()),
                          'changed': [key for key in expected.keys() & actual.keys() if expected[key] != actual[key]]})
    print('PASS_PUBLICATION_MANIFEST files=' + str(len(actual)))


if __name__ == '__main__':
    main()
