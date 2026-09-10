import hashlib, json, struct, wave
from pathlib import Path
import numpy as np

root=Path('C:/Users/Toph Beifong/.codex/visualizations/2026/09/05/01a06ff9-0287-7e00-b73d-abf12e6b3035/mono_acceptance_20260910')
report={'manifest_checked':0,'snapshot_checked':0,'manifest_excluded':[], 'records':[]}
for name,key in [('manifest.json','manifest_checked'),('snapshot-manifest.json','snapshot_checked')]:
    for item in json.loads((root/name).read_text()):
        if item['sha256'] is None:
            report['manifest_excluded'].append(item['file']); continue
        raw=(root/item['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==item['sha256'].lower(),item['file']
        if 'bytes' in item: assert len(raw)==item['bytes'],item['file']
        report[key]+=1
for name,fnv,first,last,lo,hi,zeros in [('quiet_03',0xEFFF882A,14223,62222,-23616,26176,168),('music_04',0xC7762DD9,13352,61351,-18816,28288,176)]:
    raw=(root/'quiet_music'/f'{name}.bin').read_bytes()
    assert len(raw)==768000
    h=2166136261; ids=[]; pcm=[]; flags=[]
    for b in raw: h=((h^b)*16777619)%2**32
    for low,high,value,flag in struct.iter_unpack('<IIiI',raw):
        ids.append(low+(high<<32));pcm.append(value);flags.append(flag)
    assert h==fnv and len(ids)==48000
    assert ids==list(range(first,last+1)) and not any(flags)
    assert (min(pcm),max(pcm),pcm.count(0))==(lo,hi,zeros)
    assert all(-8388608<=v<=8388607 for v in pcm)
    with wave.open(str(root/'quiet_music'/f'{name}_original24.wav'),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(1,3,48000,48000)
        blob=w.readframes(48000)
    decoded=[int.from_bytes(blob[i:i+3],'little',signed=True) for i in range(0,len(blob),3)]
    assert decoded==pcm
    a=np.asarray(pcm,dtype=float);a-=a.mean();win=np.hanning(len(a));sp=np.abs(np.fft.rfft(a*win))**2
    sp[1:-1]*=2;sp/=len(a)*np.dot(win,win); f=np.fft.rfftfreq(len(a),1/48000)
    bands={f'{l}-{u}':float(sp[(f>=l)&(f<u)].sum()) for l,u in [(0,100),(100,8000),(1000,8000)]}
    report['records'].append(dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),fnv=f'{h:08X}',samples=len(ids),first_id=ids[0],last_id=ids[-1],flagged=sum(bool(v) for v in flags),wav_exact=True,bands=bands,low_fraction=bands['0-100']/float(sp.sum())))
report['band_change_db']={k:10*np.log10(report['records'][1]['bands'][k]/report['records'][0]['bands'][k]) for k in report['records'][0]['bands']}
report['scope']='Independent file integrity and numerical checks only; not clock, electrical, loaded-image or acoustic-quality approval.'
Path(__file__).with_name('result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
