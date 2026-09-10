from pathlib import Path
import hashlib,json,wave
import numpy as np

root=Path(__file__).parent
out=root/'quiet_music_03_04_review'
records=[]; signals=[]; binaries=[]
cases=[('quiet_03',0xEFFF882A,0x378F,0xF30E,-23616,26176,168),('music_04',0xC7762DD9,0x3428,0xEFA7,-18816,28288,176)]
for name,expected,start,end,lo,hi,zeros in cases:
    src=Path(f'F:/College/verilog_digital_system/Vitis/mono_{name}.bin')
    raw=src.read_bytes();assert len(raw)==768000
    h=2166136261
    for b in raw:h=((h^b)*16777619)&0xffffffff
    assert h==expected, 'FNV mismatch'
    r=np.frombuffer(raw,dtype='<u4').reshape(-1,4)
    ids=r[:,0].astype(np.uint64)+(r[:,1].astype(np.uint64)<<32)
    x=r[:,2].copy().view('<i4')
    assert ids[0]==start and ids[-1]==end and np.all(np.diff(ids)==1)
    assert np.all(r[:,3]==0) and np.all((x>=-8388608)&(x<=8388607))
    assert (int(x.min()),int(x.max()),int((x==0).sum()))==(lo,hi,zeros)
    ac=x.astype(float)-x.mean()
    window=np.hanning(len(ac))
    spec=np.abs(np.fft.rfft(ac*window))**2
    spec[1:-1]*=2
    # Parseval-normalized, window-weighted band mean square. Not calibrated SPL/SNR.
    spec/=len(ac)*np.sum(window**2)
    f=np.fft.rfftfreq(len(ac),1/48000)
    bands={f'{a}-{b}':float(spec[(f>=a)&(f<b)].sum()) for a,b in [(0,100),(100,1000),(1000,8000),(100,8000),(8000,24001)]}
    records.append(dict(label=name,source=str(src),sha256=hashlib.sha256(raw).hexdigest(),fnv1a32=f'{h:08X}',samples=len(x),first_id=int(ids[0]),last_id=int(ids[-1]),minimum=lo,maximum=hi,zeros=zeros,clipped=0,mean=float(x.mean()),rms_ac=float(np.sqrt(np.mean(ac**2))),band_mean_square=bands,low_frequency_fraction=bands['0-100']/float(spec.sum())))
    signals.append(x);binaries.append(raw)
out.mkdir(exist_ok=False)
def wav(path,blob,width):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(width);w.setframerate(48000);w.writeframes(blob)
for record,x,raw in zip(records,signals,binaries):
    label=record['label'];(out/f'{label}.bin').write_bytes(raw)
    blob=b''.join((int(v)&0xffffff).to_bytes(3,'little') for v in x)
    path=out/f'{label}_original24.wav';wav(path,blob,3)
    with wave.open(str(path),'rb') as w:assert w.getnframes()==48000 and w.readframes(48000)==blob
ac=[x.astype(float)-x.mean() for x in signals]
gain=0.85*8388608/max(float(np.abs(a).max()) for a in ac)
joined=np.concatenate([ac[0],np.zeros(24000),ac[1]])
wav(out/'quiet_then_music_same_gain.wav',np.rint(joined*gain/256).clip(-32768,32767).astype('<i2').tobytes(),2)
summary=dict(validation='PASS length/FNV/IDs/sign/flags/serial-statistics/WAV-round-trip',records=records,total_rms_change_db=float(20*np.log10(records[1]['rms_ac']/records[0]['rms_ac'])),band_change_db={k:float(10*np.log10(records[1]['band_mean_square'][k]/records[0]['band_mean_square'][k])) for k in records[0]['band_mean_square']},listen_gain_db=float(20*np.log10(gain)),processing='Original WAV: exact signed24. Audition: remove each mean, SAME gain, signed16, quiet then 0.5s silence then music.',provenance='User-labelled quiet/music hardware captures, checked against user serial logs. Position/control conditions not independently observed.',limitations=['Configured 48kHz, nominal 1s; actual clock unmeasured.','Band energy ratio is not SNR or frequency response.','No four-channel or external IO timing acceptance.','Loaded bitstream/XSA/ELF identities not yet archived with capture.'],acoustic_acceptance=False)
summary['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
(out/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
