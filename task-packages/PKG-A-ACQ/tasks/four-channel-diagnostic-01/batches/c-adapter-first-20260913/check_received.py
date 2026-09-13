"""Offline received-file audit; reuse decoder/gate; never operate hardware."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'source'))
from export_c_capture import verify
from export_four import decode

out = ROOT / 'received-01'
out.mkdir(exist_ok=False)
report = {'scope': 'offline integrity and WAV derivation only', 'captures': {}}
for scene in ('quiet', 'speech'):
    folder = out / scene
    folder.mkdir()
    stem = Path('F:/College/verilog_digital_system/Vitis') / f'c_adapter_{scene}_20260913_01'
    for ext in ('bin', 'log'):
        shutil.copyfile(str(stem)+'.'+ext, folder / ('raw.bin' if ext == 'bin' else 'serial.log'))
    raw = (folder/'raw.bin').read_bytes()
    log = (folder/'serial.log').read_text(encoding='utf-8-sig')
    fnv = verify(raw, log)
    rows = decode(raw)
    channels = [[r[c+1] for r in rows] for c in range(4)]
    stats = []
    for c, values in enumerate(channels):
        mean = sum(values)/len(values)
        pcm16 = [round(v*12/256) for v in values]
        assert all(-32768 <= v <= 32767 for v in pcm16)
        payload = struct.pack('<'+'h'*len(pcm16), *pcm16)
        wavpath = folder / f'mic{c}.wav'
        with wave.open(str(wavpath), 'wb') as w:
            w.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
            w.writeframes(payload)
        with wave.open(str(wavpath), 'rb') as w:
            assert w.readframes(32000) == payload and w.getnframes() == 32000
        stats.append({'channel':c, 'min':min(values), 'max':max(values), 'mean':mean,
                      'rms_without_mean':math.sqrt(sum((v-mean)**2 for v in values)/len(values)),
                      'unique_values':len(set(values))})
    report['captures'][scene] = {'bytes':len(raw), 'groups':len(rows), 'first_id':rows[0][0],
        'last_id':rows[-1][0], 'fnv1a32':f'{fnv:08X}', 'error_rows':sum(r[5] for r in rows),
        'identical_channel_pairs':[[a,b] for a in range(4) for b in range(a+1,4) if channels[a] == channels[b]],
        'channels':stats, 'wav_common_gain':12, 'wav_conversion':'round(PCM24*12/256), no filtering',
        'wav_new_clipping':0}
photo = Path('E:/Program/Wechat/xwechat_files/wxid_hoobcdkud28y22_880a/temp/RWTemp/2026-09/84e9c24a02b2d884791537b0fd528dc9/d1a92aeb6f14976bcf3644d14e933e88.jpg')
shutil.copyfile(photo, out/'setup-original.jpg')
report['geometry'] = {'source':'user annotated setup photo', 'photo_top_left':'mic0',
    'photo_bottom_left':'mic1', 'photo_bottom_right':'mic2', 'photo_top_right':'mic3',
    'coordinates_m':None, 'source_position':None, 'independent_acoustic_mapping_verified':False}
(out/'check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
hashes = {p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
(out/'SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
