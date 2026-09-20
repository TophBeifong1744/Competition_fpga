import hashlib,json,subprocess
from pathlib import Path
ROOT=Path('F:/NUEC/review-worktrees/timerfixed-repair2-21c141b')
OUT=Path(__file__).parent
GIT='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
SHA='21c141b223936730c2ce5139624fcedb412adafb'
BASE='17afe32cebcff742bb2f9486388e91d9403f83dd'
PREFIX='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/'
def git(*args):return subprocess.check_output([GIT,'-c','safe.directory='+str(ROOT),'-C',str(ROOT),*args])
assert git('rev-parse','HEAD').decode().strip()==SHA
rows=git('diff','--name-status',BASE,SHA).decode().splitlines()
assert len(rows)==60 and sum(r.startswith('A\t') for r in rows)==58 and sum(r.startswith('M\t') for r in rows)==2
assert all(r.split('\t')[1].startswith(PREFIX) for r in rows)
files=git('ls-tree','-r','-z',SHA,'--',PREFIX).split(b'\0')
verified=[]
for row in filter(None,files):
    meta,name=row.split(b'\t'); oid=meta.split()[2].decode(); name=name.decode()
    data=(ROOT/name).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid,name
    verified.append(name)
assert len(verified)==268
inputs=ROOT/PREFIX/'repair-02/review-inputs'
prov=json.loads((inputs/'PROVENANCE.json').read_text())
for name,digest in prov['files'].items():
    raw=git('show',prov['feedback_commit']+':'+prov['prefix']+name)
    assert raw==(inputs/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==digest
for name in ('README.md','command_contract.py'):
    assert git('show',BASE+':'+PREFIX+name)==(ROOT/PREFIX/'repair-02/originals'/name).read_bytes()
result={'sha':SHA,'baseline':BASE,'status':'PASS','added':58,'modified':2,'outside_scope':0,'package_git_blobs_verified':len(verified),'fixed_B_feedback_blobs_verified':len(prov['files']),'original_mappings_verified':2,'diff':rows}
(OUT/'git-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='diff'}))
