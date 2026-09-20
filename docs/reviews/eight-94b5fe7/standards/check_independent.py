import csv,hashlib,json,re,subprocess,wave
from pathlib import Path
import numpy as np
R=Path('F:/NUEC/review-worktrees/eight-94b5fe7')
P=R/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918'
O=Path(__file__).parent
G='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
S='94b5fe79d87e038e895878fb31030cded469bb33'
def git(*args):return subprocess.check_output([G,'-c',f'safe.directory={R.as_posix()}','-c','core.quotepath=false','-C',str(R),*args])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def one(pattern,log):
    m=re.findall(pattern,log,re.M);assert len(m)==1,(pattern,m);return m[0]
manifest=json.loads((P/'evidence/background-confirmation-20260920-01/CURRENT-DATA-SHA256.json').read_text())
assert len(manifest)==72
assert all(sha(P/k)==v for k,v in manifest.items())
diff=git('diff','--name-status',S+'^',S).decode().splitlines()
assert all(x.startswith('A\t'+P.relative_to(R).as_posix()+'/') for x in diff)
rows=[]
for rel in sorted(k for k in manifest if k.endswith('/metadata.json')):
    d=(P/rel).parent;m=json.loads((d/'metadata.json').read_text());raw=(d/'raw.bin').read_bytes();log=(d/'serial.log').read_text(encoding='utf-8-sig')
    u=np.frombuffer(raw,'<u4').reshape(-1,8);ids=u[:,0].astype(np.uint64)+(u[:,1].astype(np.uint64)<<32);pcm=u[:,2:6].view('<i4');n=len(u)
    assert n==288250 and len(raw)==9224000
    assert np.all(np.diff(ids)==1) and np.all(u[:,6:]==0) and pcm.min()>=-8388608 and pcm.max()<=8388607
    assert (m['sample_count'],m['first_id'],m['last_id'])==(n,int(ids[0]),int(ids[-1]))
    assert m['raw_sha256']==sha(d/'raw.bin') and m['samples_sha256']==sha(d/'samples.csv')
    h=2166136261
    for b in raw:h=((h^b)*16777619)&0xffffffff
    v=one(r'^SCENE_INTEGRITY_PASS groups=(\d+) packets=(\d+) bytes=(\d+) fnv1a32=([A-F0-9]+) guard_ok=(\d+)\s*$',log)
    assert (int(v[0]),int(v[1]),int(v[2]),v[3],v[4])==(n,1153,len(raw),f'{h:08X}','1')
    v=one(r'^first=([A-F0-9]+) last=([A-F0-9]+) capture_command_us=(\d+) drain_us=(\d+) max_check_us=(\d+) max_arm_gap_us=(\d+)\s*$',log)
    assert int(v[0],16)==ids[0] and int(v[1],16)==ids[-1]
    with (d/'samples.csv').open(newline='') as f:
        reader=csv.reader(f);assert next(reader)==['sample_id','mic0','mic1','mic2','mic3','stream_error','error_flags']
        for i,row in enumerate(reader):assert row==[str(ids[i]),*[str(x) for x in pcm[i]],'0','']
        assert i+1==n
    for c in range(4):
        vals=one(rf'^mic{c} min=(-?\d+) max=(-?\d+) zeros=(\d+) clip_flags=(\d+)\s*$',log)
        assert tuple(map(int,vals))==(int(pcm[:,c].min()),int(pcm[:,c].max()),int(np.count_nonzero(pcm[:,c]==0)),0)
        expected=np.rint(pcm[:,c].astype(float)*12/256)
        assert expected.min()>=-32768 and expected.max()<=32767
        with wave.open(str(d/f'mic{c}.wav'),'rb') as w:
            assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(1,2,48000,n)
            assert np.array_equal(np.frombuffer(w.readframes(n),'<i2'),expected)
    deps=json.loads((d.parent/'dependencies.json').read_text())
    checked=[]
    for old,digest in deps.items():
        portable=old.replace('\\','/').split('/Competition_fpga/',1)[1]
        assert sha(R/portable)==digest,portable
        checked.append(portable)
    binding=json.loads((d.parent/'version-binding.json').read_text())
    assert binding['sha256']==sha(P/'evidence/preflight-01/result.json')
    record=m['source_placement_record']
    rows.append(dict(capture=d.name,count=n,first=int(ids[0]),last=int(ids[-1]),fnv=f'{h:08X}',kind=record['kind'],dependencies_matched=len(checked),version_binding_is_host_not_readback=True,operator_record=record))
result=dict(sha=S,parent=git('rev-parse',S+'^').decode().strip(),added_files=len(diff),outside_scope=0,current_hashes=72,captures=rows,status='PASS_DATA_CROSSCHECK_ONLY',limits='No board/build/readback; labels are operator reports, not acoustic truth.')
(O/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='captures'},indent=2));print('8 BIN/UART/FNV/CSV/32 WAV exact, 48 repository dependencies matched')
