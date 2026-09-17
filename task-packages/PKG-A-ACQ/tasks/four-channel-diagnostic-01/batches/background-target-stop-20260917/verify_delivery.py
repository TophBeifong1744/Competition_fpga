"""Read-only archive checks; no live F: project, build or board required."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import wave
import numpy as np
import finish_scene as scene

ROOT = Path(__file__).resolve().parent
D = ROOT / 'delivery-01'
C = D / 'c-scene-20260917-01'
def need(ok, message):
    if not ok:
        raise ValueError(message)
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

manifest = json.loads((D / 'FINAL-SHA256.json').read_text(encoding='utf-8'))['files']
for name, digest in manifest.items():
    p = (D / name).resolve()
    need(p.is_relative_to(D.resolve()), 'Manifest path escape')
    need(sha(p) == digest, 'Hash mismatch: ' + name)
raw = (C / 'raw.bin').read_bytes()
r = scene.verify(raw, (C / 'serial.log').read_text(encoding='utf-8-sig'))
rows = scene.decode(raw)
with (C / 'samples.csv').open(encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    need(next(reader) == scene.HEADER, 'CSV header')
    for actual, expected in zip(reader, rows, strict=True):
        need(actual == [str(x) for x in expected], 'CSV/BIN mismatch')
pcm = np.frombuffer(raw, dtype='<u4').reshape(-1,8)[:,2:6].view('<i4')
for ch in range(4):
    expected = np.rint(pcm[:,ch].astype(np.float64)*12/256)
    need(bool(np.all((expected >= -32768) & (expected <= 32767))), 'WAV clipping')
    with wave.open(str(C / f'mic{ch}.wav'), 'rb') as w:
        need((w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()) == (1,2,48000,len(rows)), 'WAV format')
        need(w.readframes(len(rows)) == expected.astype('<i2').tobytes(), 'WAV samples')
sys.path.insert(0, str(scene.TASK / 'current_build'))
from ps_contract import Elf32
elf = Elf32(D / 'versions/build/four_mic_endurance.elf', 2)
end = elf.symbol_value('end')
sym = elf.symbols['scene_archive']
need(elf.entry == 0x100000, 'ELF entry')
need(sym[2] == 9600128 and sym[1]+64 == r['archive_data'], 'Archive address/size')
need(sym[1]+sym[2] <= end <= 0x1000000, 'Archive/RX overlap')
need(all(0x100000 <= x['start'] < x['end'] <= end for x in elf.loads+elf.allocated), 'Program range')
build = json.loads((D / 'versions/build-result.json').read_text(encoding='utf-8'))
need(build['compiled']['program_end'] == end, 'Archived end mismatch')
need(build['compiled']['elf_sha256'] == sha(D / 'versions/build/four_mic_endurance.elf'), 'ELF binding')
for name,digest in build['source_sha256'].items():
    need(sha(D / 'versions/src' / name) == digest, 'Source binding: '+name)
p = subprocess.run([sys.executable,'-B',str(scene.READER),str(C)], capture_output=True,text=True,encoding='utf-8')
need(p.returncode == 0, 'H1 reader: '+p.stderr)
report = json.dumps(dict(status='PASS_OFFLINE_NOT_B_ACCEPTANCE',manifest_files=len(manifest),groups=r['groups'],fnv=r['fnv1a32'],program_end=hex(end),archive_data=hex(sym[1]+64),reader=json.loads(p.stdout)),ensure_ascii=False,indent=2)
if len(sys.argv) == 2:
    with Path(sys.argv[1]).open('x', encoding='utf-8') as f:
        f.write(report+'\n')
print(report)
