"""Additional finite-generation neighbors; original33 is reused if src unchanged."""
import argparse, hashlib, json, pathlib, subprocess, sys
here=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--cc',required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--prior',type=pathlib.Path,required=True);a=p.parse_args()
out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
commands=[]
def run(name,args):
    r=subprocess.run(list(map(str,args)),capture_output=True)
    (out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr)
    commands.append(dict(name=name,args=list(map(str,args)),cwd=str(pathlib.Path.cwd()),exit=r.returncode))
    (out/'commands.json').write_text(json.dumps(commands,indent=2))
    r.check_returncode();return r
for name in ('ps_bridge.c','ps_bridge.h'):
    data=(here/'src'/name).read_bytes()
    assert data==(a.prior/'repair-source/src'/name).read_bytes()
    (out/name).write_bytes(data)
for name in ('host.c','run_host.py'):
    assert (here/'tests'/name).read_bytes()==(a.prior/'repair-source/tests'/name).read_bytes()
(out/'repair.c').write_bytes((here/'tests/repair.c').read_bytes())
for opt in ('O0','O2'):
    exe=out/(opt+'.exe')
    run(opt+'-build',[a.cc,'-std=c11','-'+opt,'-Wall','-Wextra','-Wpedantic','-Wconversion','-Wshadow','-Werror','-I',out,out/'ps_bridge.c',out/'repair.c','-o',exe])
    r=run(opt,[exe]);assert b'REPAIR_PASS cases=122' in r.stdout;print(r.stdout.decode(),end='')
assert (out/'O0.stdout').read_bytes()==(out/'O2.stdout').read_bytes()
summary=json.loads((a.prior/'host33/summary.json').read_bytes())
assert summary['passed']==33 and summary['failed']==0
(out/'summary.json').write_text(json.dumps(dict(new_cases=122,source_unchanged=True,original33_reused_from=str(a.prior),host33=summary),indent=2))
(out/'SHA256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir()) if f.is_file()},indent=2))
