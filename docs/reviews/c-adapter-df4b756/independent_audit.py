import sys, subprocess, json, hashlib, csv, wave, zipfile
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]).resolve()
sha='df4b756ba49a2d161c03869a0a4a28034dad15b0'
base='99cf1dc2c1e7e2bd60ca843839d47906f9b84770'
rel='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/c-adapter-first-20260913'
b=root/rel; d=b/'delivery-01'
git='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def g(*args): return subprocess.check_output([git,'-c','safe.directory='+root.as_posix(),'-C',str(root),*args])
def read(p): return json.loads(p.read_bytes())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
changed=g('diff','--name-status',base,sha).decode().splitlines()
assert len(changed)==66 and all(x.startswith('A\t'+rel+'/') for x in changed)
for row in changed:
    name=row.split('\t')[1]; assert (root/name).read_bytes()==g('show',sha+':'+name),name
counts={}
for folder,name in [(b,'PACKAGE-SHA256.json'),(d,'SHA256.json'),(b/'received-01','SHA256.json')]:
    m=read(folder/name)
    assert {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}==set(m)|{name}
    for n,v in m.items(): assert digest(folder/n)==v,n
    counts[str(folder.relative_to(b))]=len(m)
stats={}; signals={}
for scene,start,end,fnv_expected in [('quiet',17238,49237,'890EA19D'),('speech',16542,48541,'07739375')]:
    c=d/f'c-adapter-{scene}-20260913-01'; raw=(c/'raw.bin').read_bytes()
    assert len(raw)==1024000
    words=np.frombuffer(raw,dtype='<u4').reshape(32000,8)
    ids=words[:,0].astype(np.uint64)+(words[:,1].astype(np.uint64)<<32)
    pcm=words[:,2:6].view('<i4').astype(np.int64)
    assert np.array_equal(ids,np.arange(start,end+1,dtype=np.uint64))
    assert not words[:,6:].any() and np.all((pcm>=-(1<<23))&(pcm<(1<<23)))
    fnv=2166136261
    for value in raw: fnv=((fnv^value)*16777619)&0xffffffff
    assert f'{fnv:08X}'==fnv_expected and fnv_expected in (c/'serial.log').read_text()
    with (c/'samples.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.reader(f))
    assert rows[0]==['sample_id','mic0','mic1','mic2','mic3','stream_error','error_flags']
    assert len(rows)==32001
    for i,row in enumerate(rows[1:]): assert row==[str(ids[i]),*[str(v) for v in pcm[i]],'0','']
    for name in ['raw.bin','serial.log',*[f'mic{ch}.wav' for ch in range(4)]]:
        assert (c/name).read_bytes()==(b/'received-01'/scene/name).read_bytes()
    for ch in range(4):
        with wave.open(str(c/f'mic{ch}.wav'),'rb') as w:
            assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(1,2,48000,32000)
            actual=np.frombuffer(w.readframes(32000),dtype='<i2')
        expected=np.rint(pcm[:,ch]*12/256)
        assert np.array_equal(actual,expected) and np.max(np.abs(expected))<32767
    centered=pcm-pcm.mean(axis=0)
    rms=np.sqrt(np.mean(centered**2,axis=0))
    assert all(not np.array_equal(pcm[:,i],pcm[:,j]) for i in range(4) for j in range(i))
    stats[scene]={'id_range':[int(ids[0]),int(ids[-1])],'fnv':f'{fnv:08X}','mean':pcm.mean(axis=0).tolist(),'demeaned_rms':rms.tolist(),'peak_abs':np.max(np.abs(pcm),axis=0).tolist(),'channel_correlation':np.corrcoef(centered.T).tolist()}
    signals[scene]=rms
v=d/'versions'; loading=read(v/'loading-record.json')
for name,info in loading['files'].items(): assert digest(v/name)==info['sha256'] and (v/name).stat().st_size==info['bytes']
with zipfile.ZipFile(v/'system_c_adapter.xsa') as z:
    for name,suffix in [('system_c_adapter.bit','.bit'),('ps7_init.tcl','ps7_init.tcl')]:
        matches=[n for n in z.namelist() if n.endswith(suffix)]
        assert len(matches)==1 and z.read(matches[0])==(v/name).read_bytes()
elf=(v/'four_mic_capture.elf').read_bytes()
assert all(s in elf for s in [b'Sep 11 2026',b'18:23:59',b'four-channel-c-adapter-v1'])
print(json.dumps({'status':'PASS_INDEPENDENT_ARCHIVE_ONLY','sha':sha,'git_files':66,'manifest_counts':counts,'versions':len(loading['files']),'stats':stats,'speech_rms_increase_percent':((signals['speech']/signals['quiet']-1)*100).tolist(),'new_board_or_build':False,'python':sys.version,'numpy':np.__version__},indent=2))
