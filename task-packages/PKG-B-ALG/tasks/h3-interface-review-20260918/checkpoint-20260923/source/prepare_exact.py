"""Export pinned package and dependencies from Git blobs, never checkout filters."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PACKAGE='task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918'
CHECKPOINT=PACKAGE+'/checkpoint-20260923'

def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args])

def prepare(repo,commit,out):
    repo=Path(repo).resolve();out=Path(out).resolve()
    if out==repo or repo in out.parents: raise ValueError('destination must be outside source checkout')
    if out.exists(): raise FileExistsError('destination must not exist; retain previous runs: '+str(out))
    commit=git(repo,'rev-parse','--verify',commit+'^{commit}').decode().strip()
    deps=json.loads(git(repo,'show',commit+':'+CHECKPOINT+'/dependencies.json'))
    paths=set(git(repo,'ls-tree','-r','--name-only',commit,'--',PACKAGE).decode().splitlines())|set(deps)
    out.mkdir(parents=True)
    records={}
    for name in sorted(paths):
        target=out/name
        if out not in target.resolve().parents: raise ValueError('unsafe Git path: '+name)
        data=git(repo,'show',commit+':'+name)
        expected=hashlib.sha256(data).hexdigest()
        if name in deps and expected!=deps[name]:
            raise ValueError(f'dependency blob mismatch: {name}; manifest={deps[name]} blob={expected}')
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        actual=hashlib.sha256(target.read_bytes()).hexdigest()
        if actual!=expected: raise ValueError('export byte mismatch: '+name)
        records[name]=dict(sha256=actual,bytes=len(data))
    receipt=dict(commit=commit,method='git show raw blob bytes; no filters/config changes',files=records)
    (out/'EXACT-EXPORT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('EXACT_EXPORT_PASS',commit,len(records))
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--repo',default='.');p.add_argument('--commit',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();prepare(a.repo,a.commit,a.out)
