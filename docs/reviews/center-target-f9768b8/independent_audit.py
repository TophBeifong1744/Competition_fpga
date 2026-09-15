import sys, subprocess, json, hashlib, csv, wave, zipfile, re
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]).resolve()
sha='f9768b80e5718dcf29baf48015305780f4b9b8e8'; base='09ecf267813e1ac289dae9358d9e097a87906c86'
rel='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/center-target-20260914'
b=root/rel; d=b/'delivery-01'; c=d/'c-center-target-20260914-01'
git='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def g(*a): return subprocess.check_output([git,'-c','safe.directory='+root.as_posix(),'-C',str(root),*a])
def read(p): return json.loads(p.read_bytes())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
changes=g('diff','--name-status',base,sha).decode().splitlines()
assert len(changes)==76 and all(x.startswith('A\t'+rel+'/') for x in changes)
for row in changes:
    name=row.split('\t')[1]; assert (root/name).read_bytes()==g('show',sha+':'+name),name
counts={}
for folder,name in [(b,'PACKAGE-SHA256.json'),(d,'SHA256.json'),(b/'evidence/preflight-01','SHA256.json'),(b/'evidence/preflight-02','SHA256.json')]:
    m=read(folder/name)
    for n,v in m.items(): assert digest(folder/n)==v,n
    assert {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}==set(m)|{name}
    counts[folder.relative_to(b).as_posix()]=len(m)
assert counts['.']==75
deps=read(d/'dependencies.json')
for name,value in deps.items(): assert digest(root/name)==value,name
raw=(c/'raw.bin').read_bytes(); serial=(c/'serial.log').read_text()
assert len(raw)==1024000
words=np.frombuffer(raw,dtype='<u4').reshape(32000,8)
ids=words[:,0].astype(np.uint64)+(words[:,1].astype(np.uint64)<<32)
pcm=words[:,2:6].view('<i4').astype(np.int64)
assert np.array_equal(ids,np.arange(17413,49413,dtype=np.uint64))
assert not words[:,6:].any() and np.all((pcm>=-(1<<23))&(pcm<(1<<23)))
fnv=2166136261
for byte in raw: fnv=((fnv^byte)*16777619)&0xffffffff
assert f'{fnv:08X}'=='F55CC8CE' and 'F55CC8CE' in serial
for key,name in [('raw','raw.bin'),('serial','serial.log')]: assert digest(c/name)==read(d/'inputs.json')[key]['sha256']
packets=re.findall(r'DONE packet=(\d+) actual_bytes=(\d+) DMA_SR=([0-9A-Fa-f]+)',serial)
assert [(int(i),int(n),int(s,16)) for i,n,s in packets]==[(i,8000,0x1002) for i in range(128)]
with (c/'samples.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.reader(f))
assert rows[0]==['sample_id','mic0','mic1','mic2','mic3','stream_error','error_flags'] and len(rows)==32001
for i,row in enumerate(rows[1:]): assert row==[str(ids[i]),*[str(v) for v in pcm[i]],'0','']
for ch in range(4):
    with wave.open(str(c/f'mic{ch}.wav'),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(1,2,48000,32000)
        actual=np.frombuffer(w.readframes(32000),dtype='<i2')
    expect=np.rint(pcm[:,ch]*12/256)
    assert np.array_equal(actual,expect) and np.all((expect>=-32768)&(expect<=32767))
v=d/'versions'; loading=read(v/'loading-record.json')['loading']
for name,info in loading.items(): assert digest(v/name)==info['sha256'],name
with zipfile.ZipFile(v/'system_c_adapter.xsa') as z:
    for name,suffix in [('system_c_adapter.bit','.bit'),('ps7_init.tcl','ps7_init.tcl')]:
        matches=[n for n in z.namelist() if n.endswith(suffix)]
        assert len(matches)==1 and z.read(matches[0])==(v/name).read_bytes()
elf=(v/'four_mic_capture.elf').read_bytes()
assert all(x in elf for x in [b'Sep 11 2026',b'18:23:59',b'four-channel-c-adapter-v1'])
dc=subprocess.run([git,'-c','safe.directory='+root.as_posix(),'-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(root),'diff','--check',base,sha],capture_output=True,text=True,encoding='utf-8')
warnings=[x for x in dc.stdout.splitlines() if re.match(r'^task-packages/.*:\d+: ',x)]
assert len(warnings)==102 and all('/memory.map:' in x or '/ps7_init.tcl:' in x for x in warnings)
print(json.dumps({'status':'PASS_INDEPENDENT_ARCHIVE_ONLY','sha':sha,'files':76,'manifests':counts,'dependencies':len(deps),'versions':len(loading),'groups':32000,'ids':[17413,49412],'fnv':'F55CC8CE','error_flags':0,'mean':pcm.mean(axis=0).tolist(),'demeaned_rms':pcm.std(axis=0).tolist(),'min':pcm.min(axis=0).tolist(),'max':pcm.max(axis=0).tolist(),'diff_check_exit':dc.returncode,'preserved_tool_whitespace_warnings':len(warnings),'python':sys.version,'numpy':np.__version__},indent=2))
