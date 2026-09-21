import subprocess, pathlib, json, hashlib, os
R=pathlib.Path('F:/NUEC/r/h3r')
O=pathlib.Path(__file__).resolve().parent
P=R/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923/repair-h3-e01-e03/source/prepare.py'
PY='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
env=dict(os.environ,GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0='*')
rows=[]
def run(name,args,needle):
    r=subprocess.run(args,capture_output=True,env=env)
    (O/(name+'.stdout')).write_bytes(r.stdout);(O/(name+'.stderr')).write_bytes(r.stderr)
    assert r.returncode!=0 and needle.encode() in r.stderr,(name,r.returncode,r.stderr)
    rows.append(dict(name=name,command=args,exit=r.returncode,expected=needle))
target=pathlib.Path('F:/NUEC/r/h3r-out01')
before={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
run('existing-output',[PY,'-B',str(P),'--repo',str(R),'--out',str(target)],'REFUSE_OVERWRITE')
after={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
assert before==after
empty=O/'empty-objects'; subprocess.run(['git','init',str(empty)],check=True,capture_output=True)
missing=O/'must-not-exist'
assert not missing.exists()
run('missing-object',[PY,'-B',str(P),'--repo',str(empty),'--out',str(missing)],'CalledProcessError')
assert not missing.exists()
# Check exported files against all recorded hashes and exact Git blobs, not just manifest self-consistency.
bindings=json.loads((target/'bindings.json').read_text())
for b in bindings:
    data=(target/b['file']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==b['sha256']
    if 'commit' in b:
        original=subprocess.check_output(['git','-C',str(R),'show',b['commit']+':'+b['path']],env=env)
        assert data==original
    else: assert data==P.with_name(b['file']).read_bytes()
(O/'entry-results.json').write_text(json.dumps(dict(checks=rows,export_bindings=len(bindings),existing_unchanged=True,missing_output_absent=True),indent=2)+'\n')
print('PASS existing refusal, missing dependency refusal, exact export',len(bindings))
