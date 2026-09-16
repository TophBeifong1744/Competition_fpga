"""Read-only Git/raw-byte scope and preservation audit."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path('F:/NUEC/review-worktrees/timerfixed-repair-17afe32')
OUT=Path('F:/NUEC/review-evidence/timerfixed-repair-17afe32')
GIT='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
NEW='17afe32cebcff742bb2f9486388e91d9403f83dd'
OLD='bbe39c38dc36ccb4c0492f492b86f6c46d885fbe'
FB='53018f9256cd209136183679d28b8949b04536f2'
PKG='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01/'
def git(*args):
    return subprocess.check_output([GIT,'-c','safe.directory='+ROOT.as_posix(),'-C',str(ROOT),*args])
assert git('rev-parse','HEAD').decode().strip()==NEW
changes=[s.split('\t',1) for s in git('diff','--name-status',OLD,NEW).decode().splitlines()]
assert all(path.startswith(PKG) for _,path in changes)
assert collections.Counter(s for s,_ in changes)=={'A':122,'M':3}
assert {path[len(PKG):] for s,path in changes if s=='M'}=={'README.md','check_entry.py','load_timerfixed.tcl'}
rows=[]
for raw in git('ls-tree','-r','-z',NEW,'--',PKG).split(b'\0'):
    if not raw: continue
    meta,name=raw.split(b'\t',1)
    mode,typ,oid=meta.decode().split()
    name=name.decode()
    data=(ROOT/name).read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert actual==oid,(name,actual,oid)
    rows.append(dict(path=name,bytes=len(data),blob=oid,sha256=hashlib.sha256(data).hexdigest()))
assert len(rows)==210
originals=[]
for name in ('README.md','check_entry.py','load_timerfixed.tcl','test_load.tcl'):
    data=(ROOT/PKG/'repair-01/originals'/name).read_bytes()
    assert data==git('show',OLD+':'+PKG+name)
    originals.append(name)
feedback={
    'negative_contract_checks.py':'docs/reviews/timerfixed-bbe39c3/negative_contract_checks.py',
    'reproduce_artifact_race.py':'docs/reviews/timerfixed-bbe39c3/standards/reproduce_artifact_race.py',
}
for dest,src in feedback.items():
    assert (ROOT/PKG/'repair-01/review-inputs'/dest).read_bytes()==git('show',FB+':'+src)
assert git('show',OLD+':'+PKG+'DELIVERY-SHA256.json')==(ROOT/PKG/'DELIVERY-SHA256.json').read_bytes()
report=dict(review_sha=NEW,base=OLD,feedback=FB,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    changes=changes,counts=dict(collections.Counter(s for s,_ in changes)),package_files=len(rows),
    all_disk_bytes_match_git_blobs=True,originals_match_old_commit=originals,feedback_scripts_match_commit=feedback,
    old_manifest_unchanged=True,outside_package_changed_files=0,files=rows)
(OUT/'git-byte-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('changes','files')},indent=2))
