import csv, hashlib, json, struct, zipfile
from pathlib import Path
import numpy as np

import argparse
parser=argparse.ArgumentParser(description="Optional replay of the historical B diagnostic; not a new acceptance.")
parser.add_argument('--delivery',type=Path,required=True,help='A delivery root from fixed d088e2c commit')
parser.add_argument('--output',type=Path,required=True,help='New JSON output; must not already exist')
args=parser.parse_args()
if args.output.exists(): parser.error('output already exists')
P=args.delivery.resolve()/'payload'
E=Path(__file__).resolve().parent
prefix='task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/'
def sha(b): return hashlib.sha256(b).hexdigest()
reference=json.loads((E/'historical-evidence/08-independent.json').read_text())
branch={'commit':{'sha':reference['review_sha']}}
checked=[]
for entry in reference['git_blob_checks']:
    path=entry['path']
    raw=(args.delivery/path[len(prefix):]).read_bytes()
    assert sha(raw)==entry['sha256'],path
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==entry['git_blob'],path
    checked.append(entry)
snapshot=json.loads((P/'build-snapshot/manifest.json').read_text())
for name,entry in snapshot.items():
    raw=(P/'build-snapshot'/name).read_bytes()
    assert len(raw)==entry['bytes'] and sha(raw)==entry['sha256'],name
bit=(P/'build-snapshot/one/system_wrapper.bit').read_bytes()
assert bit==(P/'build-snapshot/app/loaded_path.bit').read_bytes()
xsa=P/'build-snapshot/one/system_c_adapter.xsa'
assert xsa.read_bytes()==(P/'build-snapshot/platform/system_c_adapter.xsa').read_bytes()
with zipfile.ZipFile(xsa) as z:
    bits=[n for n in z.namelist() if n.endswith('.bit')]
    assert len(bits)==1 and z.read(bits[0])==bit
    init=[n for n in z.namelist() if n.endswith('ps7_init.tcl')]
    assert len(init)==1 and z.read(init[0])==(P/'build-snapshot/app/ps7_init.tcl').read_bytes()
assert b'Sep 11 2026' in (P/'build-snapshot/app/four_mic_capture.elf').read_bytes()
assert b'18:23:59' in (P/'build-snapshot/app/four_mic_capture.elf').read_bytes()
result={'status':'PASS_B_INDEPENDENT_DIAGNOSTIC','review_sha':branch['commit']['sha'],'git_blob_checks':checked,
        'snapshot_entries_verified':len(snapshot),'bit_xsa_init_consistency':True,
        'manifest_sha256':sha((P/'MANIFEST.sha256.json').read_bytes()),
        'reader_sha256':sha((P/'b-reader/payload/model/python/h1_reader.py').read_bytes()),
        'method':'raw <QiiiiII>; zero-lag Pearson on demeaned full segment; spectral estimate 4096-point Hann, hop2048, per-window mean removed, one-sided power; configured Fs48000; no acoustic calibration',
        'segments':[]}
for label in ['dupont-quiet-01','dupont-speech-01']:
    raw=(P/'captures'/label/'raw.bin').read_bytes()
    records=list(struct.iter_unpack('<QiiiiII',raw))
    assert len(records)==32000
    ids=[r[0] for r in records]
    assert ids==list(range(ids[0],ids[0]+32000))
    with (P/'captures'/label/'samples.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==32000
    for a,b in zip(records,rows):
        assert tuple(map(int,[b['sample_id'],b['mic0'],b['mic1'],b['mic2'],b['mic3']]))==a[:5]
        assert a[5:]==(0,0) and b['stream_error']=='0' and b['error_flags']==''
    x=np.array([r[1:5] for r in records],dtype=np.float64)
    assert np.all(x%32==0) and np.all((x>=-8388608)&(x<=8388607))
    n=4096; window=np.hanning(n); freq=np.fft.rfftfreq(n,1/48000)
    powers=[]
    for start in range(0,len(x)-n+1,2048):
        frame=x[start:start+n]; frame=frame-frame.mean(axis=0)
        power=abs(np.fft.rfft(frame*window[:,None],axis=0))**2
        power[1:-1]*=2; powers.append(power)
    power=np.mean(powers,axis=0); total=power[1:].sum(axis=0)
    bands={name:(power[(freq>=lo)&(freq<hi)].sum(axis=0)/total).tolist()
           for name,lo,hi in [('0_to_100Hz',0.0001,100),('100_to_300Hz',100,300),('300_to_4000Hz',300,4000),('4000_to_24000Hz',4000,24000.01)]}
    lanes=[]
    for ch in range(4):
        v=x[:,ch]
        lanes.append(dict(channel=ch,min=int(v.min()),max=int(v.max()),mean=float(v.mean()),rms_raw=float(np.sqrt(np.mean(v*v))),rms_ac=float(v.std()),peak_fraction_full_scale=float(abs(v).max()/8388608),saturation=0,zeros=int(np.count_nonzero(v==0)),constant=bool(np.ptp(v)==0),dominant_nonDC_bin_hz=float(freq[1+power[1:,ch].argmax()])))
    corr=np.corrcoef(x,rowvar=False)
    pairs=[]
    for a in range(4):
        for b in range(a+1,4):
            pairs.append(dict(a=a,b=b,identical=bool(np.array_equal(x[:,a],x[:,b])),pearson_zero_lag=float(corr[a,b]),normalized_difference_rms=float(np.std((x[:,a]-x[:,a].mean())/x[:,a].std()-(x[:,b]-x[:,b].mean())/x[:,b].std()))))
    result['segments'].append(dict(acquisition=label,first_id=ids[0],last_id=ids[-1],groups=32000,pcm_multiple32=True,lanes=lanes,pairs=pairs,band_power_fractions=bands,pearson_matrix=corr.tolist()))
with args.output.open('x',encoding='utf-8') as out:
    out.write(json.dumps(result,indent=2)+'\n')
print('Git blobs',len(checked),'snapshot',len(snapshot))
for s in result['segments']:
    print(s['acquisition'])
    print('lanes',s['lanes'])
    print('Pearson',np.round(s['pearson_matrix'],4))
    print('bands',s['band_power_fractions'])
