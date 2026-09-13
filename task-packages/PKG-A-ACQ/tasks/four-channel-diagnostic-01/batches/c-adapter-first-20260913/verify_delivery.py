"""Read-only verification of the archived delivery and exact raw/CSV/WAV mapping."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parent
TASK = ROOT.parents[1]
REPO = TASK.parents[3]
sys.path.insert(0, str(TASK/'source'))
sys.path.insert(0, str(REPO/'task-packages/PKG-B-ALG/payload/model/python'))
from export_c_capture import verify
from export_four import decode
from h1_reader import ReaderSession

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('delivery', type=Path)
parser.add_argument('--report', type=Path, help='Optional new report file outside the archived delivery')
parser.add_argument('--package-manifest', type=Path, help='Optional new hash list of this batch, excluding itself')
args = parser.parse_args()
d = args.delivery.resolve()
manifest = json.loads((d/'SHA256.json').read_text(encoding='utf-8'))
for name, expected in manifest.items():
    p = (d/name).resolve()
    if not p.is_relative_to(d) or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
        raise ValueError(f'Archive hash mismatch: {name}')
files = {p.relative_to(d).as_posix() for p in d.rglob('*') if p.is_file()}
if files != set(manifest)|{'SHA256.json'}:
    raise ValueError('Unlisted or missing archive files')
for name, expected in json.loads((d/'dependencies.json').read_text(encoding='utf-8')).items():
    if hashlib.sha256((REPO/name).read_bytes()).hexdigest() != expected:
        raise ValueError(f'Dependency differs from export run: {name}')
session = ReaderSession()
reports = []
for scene in ('quiet','speech'):
    c = d/f'c-adapter-{scene}-20260913-01'
    raw = (c/'raw.bin').read_bytes()
    fnv = verify(raw, (c/'serial.log').read_text(encoding='utf-8-sig'))
    rows = decode(raw)
    with (c/'samples.csv').open(encoding='utf-8',newline='') as f:
        actual = list(csv.reader(f))
    if actual[1:] != [[str(v) for v in row] for row in rows]:
        raise ValueError('CSV mapping mismatch')
    for ch in range(4):
        with wave.open(str(c/f'mic{ch}.wav'),'rb') as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()) != (1,2,48000,32000):
                raise ValueError('WAV format mismatch')
            samples = struct.unpack('<32000h', w.readframes(32000))
        if list(samples) != [round(row[ch+1]*12/256) for row in rows]:
            raise ValueError('WAV conversion mismatch')
    record = session.load(c)
    op = json.loads((d/'operator-record.json').read_text(encoding='utf-8'))
    if record.metadata['coordinates_m'] != op['geometry']['coordinates_m']:
        raise ValueError('Geometry metadata mismatch')
    reports.append({'scene':scene,'groups':len(rows),'fnv1a32':f'{fnv:08X}',
                    'error_rows':int(record.stream_error.sum())})
result = {'status':'ARCHIVE_CHECK_PASS_NOT_ACCEPTANCE', 'hashed_files':len(manifest), 'captures':reports}
print(json.dumps(result,indent=2))
if args.report:
    if args.report.resolve().is_relative_to(d):
        raise ValueError('Do not add files to the frozen delivery')
    with args.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2)
        f.write('\n')
if args.package_manifest:
    p = args.package_manifest.resolve()
    if p.is_relative_to(d) or not p.is_relative_to(ROOT):
        raise ValueError('Package manifest must be in the batch, outside archived delivery')
    hashes = {f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest()
              for f in sorted(ROOT.rglob('*')) if f.is_file() and f.resolve() != p}
    with p.open('x',encoding='utf-8') as f:
        json.dump(hashes,f,indent=2)
        f.write('\n')
