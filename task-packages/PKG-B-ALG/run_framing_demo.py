"""Reproducible framing lesson using four-channel fixed codes, not acoustic simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'payload/model/python'))
from h1_reader import HEADER, ReaderSession
from audio_frames import adapt_h1, iter_frames, framing_summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
        parser.error('output directory must be new or empty')
    args.out.mkdir(parents=True, exist_ok=True)
    input_dir = args.out/'input'
    input_dir.mkdir()
    reference = ROOT/'reference/h1-ss-data-draft-0.3/payload/examples/h1/code-pattern/metadata.json'
    metadata = json.loads(reference.read_text(encoding='utf-8-sig'))
    metadata.update(acquisition_id='b-framing-fixed-code-demo',
                    source_kind='synthetic-code', evidence_level='synthetic')
    (input_dir/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    first = 2**53+1
    rows = [','.join(HEADER)]
    for row in range(3073):
        sample_id = first+row+int(row >= 1536)
        flag = 'drop' if row == 1536 else ''
        rows.append(f'{sample_id},{row},{-row},8388607,-8388608,{int(bool(flag))},{flag}')
    (input_dir/'samples.csv').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    segment = adapt_h1(ReaderSession().load(input_dir))
    frames = list(iter_frames(segment))
    actual = [(f.row_start,f.row_stop,f.reset_before) for f in frames]
    expected = [(0,1024,True),(512,1536,False),(1537,2561,True),(2049,3073,False)]
    if actual != expected:
        raise RuntimeError(f'demo mismatch: {actual} != {expected}')
    report = dict(status='PASS_FRAMING_ONLY',
                  scope='Four-channel fixed code; no acoustic inference or hardware evidence',
                  expected_row_ranges=expected, summary=framing_summary(segment),
                  frames=[f.summary() for f in frames],
                  source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [Path(__file__),ROOT/'payload/model/python/audio_frames.py',
                                           ROOT/'payload/model/python/h1_reader.py']})
    (args.out/'framing.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('PASS_FRAMING_ONLY: 3073 rows, 1 missing sample, 1 error row, 4 frames')
    for frame in frames:
        print(f'frame {frame.index}: rows [{frame.row_start}, {frame.row_stop}), reset={frame.reset_before}')
    return 0


if __name__ == '__main__': sys.exit(main())
