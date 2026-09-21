import hashlib, json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parent
repo=ROOT/'h3-repair-publication'
rel='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923'
fix=repo/rel/'repair-h3-e01-e03'
out=ROOT/'h3-repair-check02'
logs=ROOT/'h3-repair-publication-evidence'
logs.mkdir(exist_ok=True)
assert not (logs/'commands.json').exists()
manifest=fix/'SHA256.json'
assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='130cf067ca2dcbe21ff3ad3a70fc2d92881bc0aa3948b6d6c4d3dc25988aa6c5'
rows=json.loads(manifest.read_bytes())
assert all(hashlib.sha256((fix/n).read_bytes()).hexdigest()==h for n,h in rows.items())
actual={p.relative_to(fix).as_posix() for p in fix.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts}
assert actual==set(rows)|{'SHA256.json'}, actual-set(rows)
(logs/'manifest-check.json').write_text(json.dumps(dict(files=len(rows),bad=0)))
commands=[]
def run(name,args,cwd):
    r=subprocess.run(args,cwd=cwd,capture_output=True)
    (logs/(name+'.stdout')).write_bytes(r.stdout)
    (logs/(name+'.stderr')).write_bytes(r.stderr)
    commands.append(dict(name=name,args=list(map(str,args)),cwd=str(cwd),exit=r.returncode))
    (logs/'commands.json').write_text(json.dumps(commands,indent=2))
    print(name,r.returncode,flush=True)
    r.check_returncode()
run('prepare',[sys.executable,'-B',fix/'source/prepare.py','--repo',repo,'--out',out],ROOT)
run('regression',[sys.executable,'-B',out/'run_checks.py'],ROOT)
print((out/'run/summary.json').read_text(),flush=True)
run('entry',[sys.executable,'-B',fix/'source/check_entry.py','--repo','E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga','--clean',out,'--out',logs/'entry'],ROOT)
print('PUBLICATION_CHECK_PASS_NOT_B_APPROVAL',flush=True)
