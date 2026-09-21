"""Run exact B reproducers and repair regressions; new output only, no board tools."""
import argparse, hashlib, io, json, pathlib, subprocess, sys, tarfile, time

HERE=pathlib.Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'.git').exists())
BASE='fbbaa161098582ba1e5e112b86d39533769bb3e7'
FEEDBACK='b66da3cd32cf91708cc13bc45608afa3a503bec0'
PREFIX='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
OLD=PREFIX+'ps-semantic-bridge-candidate-01/'
BP='docs/reviews/ps-bridge-fbbaa16/'
ap=argparse.ArgumentParser()
ap.add_argument('--cc',required=True);ap.add_argument('--out',type=pathlib.Path,required=True)
a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
commands=[];bindings=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,data):(out/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def pin(commit,path,target):
    data=git('show',commit+':'+path);dest=out/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    bindings.append(dict(commit=commit,path=path,file=target,sha256=sha(data),blob=git('rev-parse',commit+':'+path).decode().strip()))
    save('bindings.json',bindings);return dest
def run(name,args,expected=0):
    t=time.perf_counter();p=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True)
    (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
    commands.append(dict(name=name,args=list(map(str,args)),cwd=str(ROOT),exit=p.returncode,seconds=time.perf_counter()-t))
    save('commands.json',commands);print(name,p.returncode,flush=True)
    if expected is not None:assert p.returncode==expected,(name,p.returncode,p.stderr[-1000:])
    return p

save('environment.json',dict(python=sys.version,base=BASE,feedback=FEEDBACK,head=git('rev-parse','HEAD').decode().strip()))
run('compiler',[a.cc,'--version'])
# Check original submitted bytes, including original manifest; no new seal of history.
archive=git('archive',BASE,OLD)
with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
    original={m.name:tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
bad=[n for n,data in original.items() if (ROOT/n).read_bytes()!=data]
assert not bad,bad
save('original-preservation.json',dict(files=len(original),bad=bad))
for name in ('host.c','run_host.py'):
    assert (HERE/'tests'/name).read_bytes()==original[OLD+'tests/'+name],name
for name in ('ps_bridge.c','ps_bridge.h'):
    pin(BASE,OLD+'src/'+name,'original-src/'+name)
for name in ('B-REVIEW.md','TO-A.md','spec/SPEC-REVIEW.md','spec/probe.c','spec/generation.c','spec/O0.txt','spec/O2.txt',
             'spec/generation.txt','standards/REPORT.md','standards/generation_max.c','standards/generation_max.stdout.txt'):
    pin(FEEDBACK,BP+name,'feedback/'+name)
# a7 is ONLY a labelled semantic comparison; original host PINS keep 0ab.
pin('0abdc91c57787b7c868a797b88f35129de169faf',PREFIX+'engineering-closeout-20260923/ROUTE.md','comparison/old-0ab-route.md')
pin('a7f70c5149a6503effdbbf16a9903d42c2d39e6d',PREFIX+'engineering-closeout-20260923/repair-h3-e01-e03/source/results.py','comparison/new-a7-results.py')
pin('a7f70c5149a6503effdbbf16a9903d42c2d39e6d',PREFIX+'engineering-closeout-20260923/repair-h3-e01-e03/README.md','comparison/new-a7-readme.md')
# Compile short, byte-bound copies, not the original working sources.
for sub in ('src','tests'):
    for p in (HERE/sub).glob('*'):
        if p.is_file():
            dest=out/'repair-source'/p.relative_to(HERE);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
save('repair-source-sha256.json',{p.relative_to(out/'repair-source').as_posix():sha(p.read_bytes()) for p in (out/'repair-source').rglob('*') if p.is_file()})
flags=['-std=c11','-Wall','-Wextra','-Wpedantic','-Wconversion','-Wshadow','-Werror']
def build(name,src,test,opt):
    exe=out/(name+'.exe')
    run(name+'-build',[a.cc,*flags,opt,'-I',src,src/'ps_bridge.c',test,'-o',exe]);return exe
for opt in ('O0','O2'):
    for label,src in [('original',out/'original-src'),('fixed',out/'repair-source/src')]:
        probe=build(label+'-B-probe-'+opt,src,out/'feedback/spec/probe.c','-'+opt)
        p=run(label+'-B-probe-'+opt,[probe])
        lines=p.stdout.decode().splitlines()
        # Check observations, not merely the recorder's exit code.
        def observation(name):
            line=next(x for x in lines if x.startswith(name+' '))
            return dict(x.split('=',1) for x in line.split()[1:])
        for name in ('full_then_conflicting_partial','full_then_wrong_binding'):
            assert observation(name)['take']==('0' if label=='original' else '2')
        assert observation('unknown_current_out_of_range_error')['failed']==('0' if label=='original' else '1')
        for name in ('conflicting_partial_then_full','wrong_binding_then_full'):
            assert observation(name)['take']=='2'
        for probe_name in ('spec/generation.c','standards/generation_max.c'):
            name=label+'-'+pathlib.Path(probe_name).stem+'-'+opt
            exe=build(name,src,out/'feedback'/probe_name,'-'+opt)
            result=run(name,[exe],expected=None)
            # Exact scripts describe old failure; new result may deliberately exit1.
            text=result.stdout.decode()
            if probe_name.endswith('generation_max.c'):
                assert 'acquire_rc='+('1' if label=='original' else '0') in text
                assert result.returncode==(0 if label=='original' else 1)
            else:
                assert result.returncode in (0,1)  # raw observation kept; new boundary assertions below decide repair
    exe=build('repair-regression-'+opt,out/'repair-source/src',out/'repair-source/tests/repair.c','-'+opt)
    p=run('repair-regression-'+opt,[exe]);assert b'REPAIR_PASS' in p.stdout
# Original 33 cases and 9 C groups: unmodified host/runner and exact original PINS.
run('original-33-runner',[sys.executable,'-B',HERE/'tests/run_host.py','--cc',a.cc,'--out',out/'host33'])
summary=json.loads((out/'host33/summary.json').read_bytes());assert summary['tests']==33 and summary['failed']==0
save('summary.json',dict(result='REPAIR_AUTHOR_PASS_PENDING_B_REVIEW',original_cases=33,
    new_regression=(out/'repair-regression-O2.stdout').read_text().splitlines()[-1],
    original_defects_reproduced=True,sanitizers=summary['sanitizers'],
    ARM='NOT_RUN',BSP='NOT_RUN',board='NOT_RUN',realtime='REALTIME_BLOCKED'))
print('REPAIR_AUTHOR_PASS_PENDING_B_REVIEW',flush=True)
