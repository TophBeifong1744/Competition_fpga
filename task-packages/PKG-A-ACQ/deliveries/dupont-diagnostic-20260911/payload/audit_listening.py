"""Verify listening WAV derivatives against raw PCM; no subjective listening claim."""
import argparse
import hashlib
import json
from pathlib import Path
import wave
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--captures', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
info_path = a.captures/'listening-01/listening-info.json'
info = json.loads(info_path.read_text(encoding='utf-8-sig'))
assert info['common_gain'] == 12 and info['sample_rate_hz'] == 48000
result = {'status':'PASS_WAV_DERIVATION_ONLY', 'gain':12,
          'info_sha256':hashlib.sha256(info_path.read_bytes()).hexdigest(), 'files':[]}
for scene in ('quiet','speech'):
    source = info['sources'][scene]
    raw = (a.captures/source['acquisition_id']/'raw.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source['raw_sha256']
    pcm = np.frombuffer(raw,dtype='<i4').reshape(-1,8)[:,2:6]
    for ch in range(4):
        path = a.captures/f'listening-01/{scene}_mic{ch}.wav'
        with wave.open(str(path),'rb') as w:
            assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes(),w.getcomptype()) == (1,2,48000,32000,'NONE')
            actual = np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
        rounded = np.rint(pcm[:,ch].astype(np.float64)*12/256)
        saturated = np.count_nonzero((rounded < -32768) | (rounded > 32767))
        assert saturated == 0
        assert np.array_equal(actual, rounded.astype('<i2')), path.name
        result['files'].append({'file':path.name, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'raw_source':source['acquisition_id'], 'channel':ch, 'frames':32000,
            'conversion_saturation_count':int(saturated), 'exact_pcm_match':True})
with a.output.open('x',encoding='utf-8') as f:
    json.dump(result,f,indent=2)
    f.write('\n')
print(result['status'],len(result['files']),'WAV files; no additional clipping')
