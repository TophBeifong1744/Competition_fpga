"""Actual entry refusal checks and unchanged frozen-file audit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from prepare import BASE, PINS

p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--clean',required=True);p.add_argument('--out',required=True)
a=p.parse_args();repo=Path(a.repo).resolve();clean=Path(a.clean).resolve();out=Path(a.out).resolve()
out.mkdir(parents=True,exist_ok=False)
rows=[]
def run(name,args,needle):
    r=subprocess.run(args,capture_output=True,text=True)
    (out/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
    assert r.returncode!=0 and needle in r.stderr,(name,r.returncode,r.stderr)
    rows.append(dict(test=name,exit=r.returncode,result='EXPECTED_REJECTION',command=args))
entry=str(Path(__file__).with_name('prepare.py').resolve())
run('existing_output',[sys.executable,'-B',entry,'--repo',str(repo),'--out',str(clean)],'REFUSE_OVERWRITE')
empty=Path(tempfile.mkdtemp(prefix='h3-empty-'))
r=subprocess.run(['git','init',str(empty)],capture_output=True,text=True)
(out/'empty-init.log').write_text(r.stdout+r.stderr,encoding='utf-8')
r.check_returncode()
run('missing_exact_object',[sys.executable,'-B',entry,'--repo',str(empty),'--out',str(out/'must_not_exist')],'CalledProcessError')
assert not (out/'must_not_exist').exists()
for label,sha,prefix in [('engineering',PINS['engineering'],BASE+'engineering-closeout-20260923/'),
                          ('c_candidate','fbbaa161098582ba1e5e112b86d39533769bb3e7',BASE+'ps-semantic-bridge-candidate-01/')]:
    files=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','--name-only',sha,'--',prefix],text=True).splitlines()
    assert files,label
    for f in files:
        original=subprocess.check_output(['git','-C',str(repo),'show',sha+':'+f])
        current=(repo/f).read_bytes()
        equal=current==original or (b'\0' not in current and current.replace(b'\r\n',b'\n')==original.replace(b'\r\n',b'\n'))
        assert equal,f
        rows.append(dict(kind='preserved',package=label,path=f,sha256=hashlib.sha256(current).hexdigest(),git_sha256=hashlib.sha256(original).hexdigest()))
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('ENTRY_AND_PRESERVATION_PASS',len(rows))
