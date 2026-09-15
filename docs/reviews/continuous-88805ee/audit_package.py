import sys,subprocess,json,hashlib,zipfile
from pathlib import Path
r=Path(sys.argv[1]).resolve(); sha='88805ee415f137998b59b7cb197f2eeb988d17b7'; base='058aa3095fd4df7392645004b164adb4eec52041'
rel='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01'
b=r/rel
git='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def g(*a): return subprocess.check_output([git,'-c','safe.directory='+r.as_posix(),'-C',str(r),*a])
changes=g('diff','--name-status',base,sha).decode().splitlines()
assert len(changes)==222 and all(s.startswith('A\t'+rel+'/') for s in changes)
tree=g('ls-tree','-r','-z',sha,'--',rel).split(b'\0'); count=0
for line in tree:
    if not line: continue
    meta,path=line.split(b'\t',1); oid=meta.split()[2].decode(); data=(r/path.decode()).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid,path
    count+=1
assert count==222
m=json.loads((b/'publication/SHA256.json').read_bytes()); assert len(m)==221
assert {p.relative_to(b).as_posix() for p in b.rglob('*') if p.is_file()}==set(m)|{'publication/SHA256.json'}
for name,value in m.items(): assert hashlib.sha256((b/name).read_bytes()).hexdigest()==value,name
zips=list(b.rglob('*.zip'));assert len(zips)==19
for p in zips:
    with zipfile.ZipFile(p) as z: assert z.testzip() is None,p
elf=b/'board-run-20260915-02/runtime/four_mic_continuous.elf'
assert hashlib.sha256(elf.read_bytes()).hexdigest()=='ebc576e2bfe87ca45c06fb62359babc36f8d474505a97ff6d121336d2a3c3fa3'
print(json.dumps({'status':'PASS_B_GIT_MANIFEST_ZIP','audit_sha':sha,'git_files':count,'publication_entries':len(m),'zip_crc_checks':len(zips),'fixed_elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest()},indent=2))
