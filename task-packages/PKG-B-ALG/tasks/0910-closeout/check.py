"""Run requested offline receipt checks; never modifies A originals."""
import csv, hashlib, json, math, platform, struct, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'evidence/run01'
OUT.mkdir(parents=True,exist_ok=False)
mono=ROOT/'task-packages/PKG-A-H2-MONO-DIAGNOSTIC'
commands=[]
for name,script in [('manifest','source/file_manifest.py'),('export','source/mono_delivery.py'),('tests','source/test_delivery.py')]:
    cmd=[sys.executable,'-B',script]+(['verify'] if name!='tests' else [])
    r=subprocess.run(cmd,cwd=mono,capture_output=True,text=True)
    (OUT/(name+'.txt')).write_text(r.stdout+r.stderr,encoding='utf-8')
    commands.append(dict(cwd=str(mono),command=cmd,exit_code=r.returncode))
    assert r.returncode==0,name
records=[]
for name in ('quiet_03','music_04'):
    folder=mono/'data'/name
    meta=json.loads((folder/'metadata.json').read_text())
    with (folder/'samples.csv').open(newline='') as f:
        reader=csv.DictReader(f);assert reader.fieldnames==['sample_id','pcm','flags']
        rows=[tuple(int(row[k]) for k in reader.fieldnames) for row in reader]
    raw=(folder/meta['raw_file']).resolve().read_bytes()
    decoded=[(low+(high<<32),pcm,flags) for low,high,pcm,flags in struct.iter_unpack('<IIiI',raw)]
    assert rows==decoded
    ids,x,flags=zip(*rows);n=len(x);mean=sum(x)/n
    record=dict(name=name,samples=n,first_id=ids[0],last_id=ids[-1],
        gaps=sum(b!=a+1 for a,b in zip(ids,ids[1:])),nonzero_flags=sum(v!=0 for v in flags),
        outside_signed24=sum(not -2**23<=v<2**23 for v in x),
        clipped_endpoints=sum(v in (-2**23,2**23-1) for v in x),
        non_multiple_of_32=sum(v%32!=0 for v in x),minimum=min(x),maximum=max(x),
        mean_pcm=mean,rms_pcm=math.sqrt(sum(v*v for v in x)/n),
        ac_rms_pcm=math.sqrt(sum((v-mean)**2 for v in x)/n),
        peak_fullscale=max(abs(v) for v in x)/2**23,
        first_4800_mean_pcm=sum(x[:4800])/4800,last_4800_mean_pcm=sum(x[-4800:])/4800,
        raw_sha256=hashlib.sha256(raw).hexdigest(),source_kind=meta['source_kind'],
        sample_rate_status=meta['sample_rate_status'],loaded_identity_verified=meta['loaded_identity_verified'])
    records.append(record)
cmd=[sys.executable,'-B',str(ROOT/'task-packages/PKG-A-H3-INTEGRATION/source/verify.py'),'--out',str(OUT/'h3')]
r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
(OUT/'h3.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
commands.append(dict(cwd=str(ROOT),command=cmd,exit_code=r.returncode))
assert r.returncode==0
result=dict(status='PASS_FILE_RECEIPT_AND_H3_ARITHMETIC_NOT_HARDWARE_ACCEPTANCE',
    python=sys.version,platform=platform.platform(),commands=commands,mono_records=records)
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(records,indent=2))
