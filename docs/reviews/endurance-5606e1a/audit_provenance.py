"""Independent raw Git, archive/source identity and UART count audit."""
import collections,datetime,gzip,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(sys.argv[1]);OUT=Path(sys.argv[2]);OUT.mkdir(parents=True,exist_ok=False)
SHA='5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c'
BASE='ad9ca72388fb676946c71b13517ab279c11cfc61'
REL='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01'
E1=ROOT/REL
git=['C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe','-c','safe.directory='+ROOT.as_posix(),'-C',str(ROOT)]
def g(*a):return subprocess.check_output(git+list(a))
changes=g('diff','--name-status',BASE,SHA).decode().splitlines()
assert len(changes)==172 and all(x.startswith('A\t'+REL+'/') for x in changes)
rows=[]
for raw in g('ls-tree','-rz',SHA,'--',REL).split(b'\0'):
    if not raw:continue
    meta,name=raw.split(b'\t',1);oid=meta.decode().split()[2];name=name.decode()
    data=(ROOT/name).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid,name
    rows.append(dict(path=name,blob=oid,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
assert len(rows)==172
sealed=json.loads((E1/'board-run-20260916-01/SHA256.json').read_text())['files']
assert len(sealed)==138
for name,h in sealed.items():assert hashlib.sha256((E1/name).read_bytes()).hexdigest()==h
source_matches=[]
for p in (E1/'proposed-src').rglob('*'):
    if p.is_file():
        rel=p.relative_to(E1/'proposed-src')
        q=E1/'evidence/user-build-20260916-2052/app/src'/rel
        if q.is_file():
            # The policy explicitly hashes LF-normalized source text.
            same=p.read_bytes()==q.read_bytes()
            normalized=p.read_text(encoding='utf-8')==q.read_text(encoding='utf-8')
            assert normalized,str(rel)
            source_matches.append(dict(path=str(rel),raw_equal=same,text_equal=normalized))
text=(E1/'board-run-20260916-01/endurance_300s_10x10s_20260916_01.log').read_text()
sessions=re.findall(r'SESSION (\d+) result=(\w+) groups=(\d+) packets=(\d+) bytes_checked=(\d+) stop_sent=(\d+)',text)
timings=re.findall(r'first=([0-9a-fA-F]{16}) last=([0-9a-fA-F]{16}) capture_command_us=(\d+) drain_us=(\d+) max_check_us=(\d+) max_arm_gap_us=(\d+)',text)
assert len(sessions)==len(timings)==11
segments=[]
for i,(record,timing) in enumerate(zip(sessions,timings)):
    n,status,groups,packets,count,stop=record
    groups,packets,count=map(int,(groups,packets,count));first,last=[int(x,16) for x in timing[:2]]
    assert int(n)==i and status=='OK' and stop=='1'
    assert groups==last-first+1==packets*250 and count==packets*8000
    assert groups==(14400250 if i==0 else 480250)
    assert int(timing[2])>=(300000000 if i==0 else 10000000)
    gap=0 if not i else first-segments[-1]['last_id']-1
    assert gap>=0
    segments.append(dict(index=i,groups=groups,packets=packets,bytes=count,first_id=first,last_id=last,intentional_gap_before=gap,capture_us=int(timing[2]),drain_us=int(timing[3]),max_check_us=int(timing[4]),max_arm_gap_us=int(timing[5])))
assert sum(s['groups'] for s in segments)==19202750
assert sum(s['packets'] for s in segments)==76811
assert sum(s['bytes'] for s in segments)==614488000
stats=re.findall(r'mic([0-3]) min=(-?\d+) max=(-?\d+) zeros=(\d+) clip_flags=(\d+)',text)
assert len(stats)==44 and all(int(x[4])==0 and -8388608<=int(x[1])<int(x[2])<=8388607 for x in stats)
exe=(E1/'evidence/user-build-20260916-2052/app/build/four_mic_endurance.elf').read_bytes()
assert hashlib.sha256(exe).hexdigest()=='75c7e5e2203ed1ba019c83a1123ef79eff0c877286d722eea5b8d9a275c76449'
assert b'Sep 16 2026' in exe and b'20:52:11' in exe and 'Sep 16 2026 20:52:11' in text
check=subprocess.run(git+['diff','--check',BASE,SHA],capture_output=True)
(OUT/'diff-check.txt.gz').write_bytes(gzip.compress(check.stdout+check.stderr,mtime=0))
report=dict(review_sha=SHA,parent=BASE,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    changes=172,outside_scope_changes=0,raw_files=rows,original_manifest_entries=138,originals_including_manifest=139,
    proposed_actual_sources=source_matches,segments=segments,channel_stat_rows=44,
    total_intentional_uncaptured_id_gaps=sum(s['intentional_gap_before'] for s in segments),
    compiler_stamp_and_uart_match=True,diff_check=dict(returncode=check.returncode,trailing_whitespace=check.stdout.count(b'trailing whitespace')),
    limits='Source/build disk evidence and serial/operator declaration; no device readback or full sample BIN')
(OUT/'result.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
print(json.dumps({k:v for k,v in report.items() if k not in ('raw_files','segments')},indent=2))
