"""Add verified RIR input transport to the unchanged PR3 round-one auditors."""
import argparse, importlib.util, subprocess, sys, traceback
from pathlib import Path
import reference_inputs as r
spec=importlib.util.spec_from_file_location('accepted_runner',r.OLD/'run_all.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--stage',choices=['preflight','audit','stable','unit','tests','final']);p.add_argument('--package',default='')
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    r.write(out/'environment.json',r.common.environment()|dict(waveform_policy='Verified historical RIR transport; original four exact input hash checks retained. No numerical waveform acceptance.'))
    if a.stage:
        refs=None
        try:
            if a.stage=='preflight':result=r.preflight(out)
            else:
                # Import the selected auditor first so its historical import ordering
                # stays unchanged; inject only the input generator's RIR dependency.
                if a.stage=='audit':
                    module=__import__('audit_'+a.package.replace('-','_'))
                    refs=r.References();refs.install()
                    result=(module.audit if a.package=='narrowband-guard-01' else module.run)()
                elif a.stage=='stable':
                    import stable_rerun
                    refs=r.References();refs.install();result=old.stable(out)
                else:result=old.stage(a.stage,a.package,out)
            r.write(out/'result.json',result)
        except Exception:
            r.write(out/'failure.json',dict(status='FAIL',traceback=traceback.format_exc()));raise
        finally:
            r.write(out/'differences.json',dict(numerical=r.common.DIFF.values,input_hashes=r.common.DIFF.inputs))
            if refs:r.write(out/'reference-use.json',refs.uses)
        return
    r.write(out/'integrity-before.json',r.common.verify_package())
    stages=[('preflight','')]+[('audit',n) for n in r.common.PACKAGES[1:-1]]+[('stable','')]
    results=[]
    for kind,name in stages:
        key=kind+('-'+name if name else '')
        command=[sys.executable,'-B',str(Path(__file__).resolve()),'--stage',kind,'--package',name,'--out',str(out/key)]
        print('RUN',key,flush=True)
        with (out/(key+'.log')).open('w',encoding='utf-8') as stream:
            completed=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
        results.append(dict(stage=key,command=command,returncode=completed.returncode))
        r.write(out/'stages.json',results);print('PASS' if completed.returncode==0 else 'FAIL',key,flush=True)
    r.write(out/'integrity-after.json',r.common.verify_package())
    r.write(out/'run.json',dict(status='PASS' if all(x['returncode']==0 for x in results) else 'FAIL',stages=results,
        scope='Remaining input blocker only: preflight, four live audits, stable full 2252 controls. Previously accepted tests/finals unchanged.',sources={p.name:r.sha(p) for p in r.HERE.glob('*.py')}))
    if any(x['returncode'] for x in results):raise SystemExit(1)

if __name__=='__main__':main()
